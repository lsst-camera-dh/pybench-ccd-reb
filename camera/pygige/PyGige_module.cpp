/**
 * @file    PyGigE_module.cpp
 * @author  J. Kuczewski 
 * @date    September 2015
 * @version 0.1
 * @brief   Python/C wrapper to ZMQ Register server, and low level UDP access to data.
 *          Image ZMQ server is started here to broadcast data out.
 */

//#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION

#include <Python.h>
#include "structmember.h"
#include <numpy/arrayobject.h>
#include <stdlib.h>
#include "fitsio.h"
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <unistd.h>
#include <sys/time.h>
#include <pthread.h>
#include <zmq.h>
#include "gige.h"
#include "reg_client.h"

#define DEBUG 2

#ifdef DEBUG
 #if DEBUG == 1
    #define DBG_PRINT(fmt, args...) fprintf(stdout, fmt, ##args)
 #elif DEBUG == 2
   #define DBG_PRINT(fmt, args...) fprintf(stdout, " %s:%d:%s(): " fmt, \
    __FILE__, __LINE__, __func__, ##args)
  #endif
#else
 #define DBG_PRINT(fmt, args...) /* Don't do anything in release builds */
#endif

#define TOTAL_STRIPES 3
#define CHANNELS      16
#define STRIPE_ADDR   0x400007
#define SLEFT         0x1
#define SMIDDLE       0x2
#define SRIGHT        0x4

#define IFACE                 "eth0"
#define SYNCSERVICE_TCP       "tcp://*:5562"
#define PUB_TCP_PORT          5550
#define PUBLISHER_TCP         "tcp://*:%i"
#define PUBLISHER_IPC         "ipc:///tmp/reb_%i.ipc"
#define CHUNK_SIZE            250000
#define SUBSCRIBERS_EXPECTED  1

// Stripe Structure
typedef struct {
    bool     enabled;
    int      idx;
    size_t   length;
    uint32_t height;
    uint32_t width;
    uint32_t *data;
    uint64_t tag;
    uint32_t cluster;
    uint32_t address;
} stripe_t;

// Thread args for fits file writer
typedef struct {
    stripe_t *current_stripe;
    char     *fname;
} stripe_args_t;

typedef struct {
    PyObject_HEAD
    PyObject              *fits_keywords;
    PyObject              *image_size;
    char                  *iface[512];
    int                   reb_id;
    uint8_t               *adc_buffer;             // Image buffer
    size_t                adc_buffer_length;       // Buffer length
    stripe_t              stripes[TOTAL_STRIPES];  // Allocate 3-Stripes
    pthread_mutex_t       stripe_lock;
    uint8_t               broadcast_data_ready_flag;
    PyObject              *mod_error;
    reg_client_t          *reg;
    gige_data_t           *data;
} PyGigE;

//  Convert C string to 0MQ string and send to socket
static int s_send (void *socket, char *string) {
    int size = zmq_send (socket, string, strlen (string), 0);
    return size;
}

void send_image(void *publisher, stripe_t *curr, char *topic_id)
{
    zmq_msg_t  topic;
    zmq_msg_t  msg;
    char       info_topic[2];
    uint32_t   info_data[6];
    const char char_i          = 'i';
    stripe_t   *current_stripe = curr;
    int        totsize         = current_stripe->length;
    int        pos             = 0;
    int        last            = 0;
    int        count           = 0;

    // Topic for info, append a `i` e.g. Ai
    memcpy(&info_topic[0], &topic_id, 1);
    memcpy(&info_topic[1], &char_i, 1);

    // Publish meta data about the dataset to follow
    memcpy(&info_data[0], &current_stripe->height,  sizeof(uint32_t));
    memcpy(&info_data[1], &current_stripe->width,   sizeof(uint32_t));
    memcpy(&info_data[2], &current_stripe->cluster, sizeof(uint32_t));
    memcpy(&info_data[3], &current_stripe->address, sizeof(uint32_t));
    memcpy(&info_data[4], &current_stripe->tag,     sizeof(uint64_t));

    zmq_msg_init_size(&topic, 2);
    memcpy(zmq_msg_data(&topic), &info_topic, 2);
    zmq_msg_init_size(&msg, sizeof(info_data));
    memcpy(zmq_msg_data(&msg), &info_data, sizeof(info_data));

    zmq_msg_send(&topic, publisher, ZMQ_SNDMORE);
    zmq_msg_send(&msg, publisher, 0);

    // Now publish the image data
    //printf("=>>> topic=%c pub=%p curr=%p\n", topic_id, publisher, curr);
    while (pos < totsize) {
        pos += CHUNK_SIZE;
        if (pos >= totsize)
            pos = totsize;
        count = pos - last;

        zmq_msg_init_size(&topic, 1);
        memcpy(zmq_msg_data(&topic), &topic_id, 1);

        zmq_msg_init_size(&msg, count*sizeof(uint32_t));
        memcpy(zmq_msg_data(&msg), &current_stripe->data[last], count*sizeof(uint32_t));

        zmq_msg_send(&topic, publisher, ZMQ_SNDMORE);
        zmq_msg_send(&msg, publisher, 0);

        last = pos;
    }
    zmq_msg_init_size(&topic, 1);
    memcpy(zmq_msg_data(&topic), &topic_id, 1);
    // Send trailer
    zmq_msg_send(&topic, publisher, ZMQ_SNDMORE);
    s_send(publisher, (char *)"END");
}

void *image_broadcaster(void *args)
{
    PyGigE    *self = (PyGigE *)args;
    stripe_t *current_stripe;
    char     topic      = 'A';
    int      tcp_port   = PUB_TCP_PORT + self->reb_id;
    void     *context   = zmq_ctx_new();
    void     *publisher = zmq_socket(context, ZMQ_PUB);

    char pub_tcp_str[512];
    char ipc_str[512];

    sprintf(pub_tcp_str, PUBLISHER_TCP, tcp_port);
    sprintf(ipc_str, PUBLISHER_IPC, self->reb_id);

    DBG_PRINT("Listening on %s, %s\n", pub_tcp_str, ipc_str);
    int sndhwm = 0;
    zmq_setsockopt(publisher, ZMQ_SNDHWM, &sndhwm, sizeof(int));

    zmq_bind(publisher, pub_tcp_str);
    zmq_bind(publisher, ipc_str);

#ifdef SYNCSERVICE
    char *syncstring;
    int subscribers = 0;
    void *syncservice = zmq_socket (context, ZMQ_REP);
//    int timeout = 1000;
//  zmq_setsockopt(syncservice, ZMQ_RCVTIMEO, &timeout, sizeof(int));
    zmq_bind(syncservice, SYNCSERVICE_TCP);
#endif

    while (1) {
        //  Get synchronization from subscribers
#ifdef SYNCSERVICE
        while (subscribers < SUBSCRIBERS_EXPECTED) {
            //  - wait for synchronization request
            syncstring = s_recv(syncservice);
            s_send(syncservice, "");
            subscribers++;
            //printf("subscribers=%i\n", subscribers);
            syncstrin mg = NULL;
        }
#endif

        pthread_mutex_lock(&(self->stripe_lock));
        if (self->broadcast_data_ready_flag) {
            for (int i = 0; i < TOTAL_STRIPES; i++) {
                current_stripe = &(self->stripes[i]);
                if (current_stripe->enabled) {
            //        printf("*** Sending new data...curr=%p, publisher=%p\n", &(self->stripes[i]), &publisher);
                    send_image(publisher, &(self->stripes[i]), (char *)topic + (char)i);
                }
            }
            self->broadcast_data_ready_flag = 0;
#ifdef SYNCSERVICE
            subscribers = 0;
#endif
        }
        pthread_mutex_unlock(&(self->stripe_lock));
#ifndef SYNCSERVICE
        usleep(100);
#endif
    }

    zmq_close(publisher);
#ifdef SYNCSERVICE
    zmq_close(syncservice);
#endif
    zmq_ctx_destroy(context);

    pthread_exit(NULL);
}

static void PyGigE_dealloc(PyGigE* self)
{
    //Py_XDECREF(self->first);
    //Py_XDECREF(self->last);
    Py_XDECREF(self->fits_keywords);
    self->ob_type->tp_free((PyObject*)self);
}

/**
 * Python: def __new__()
 */
static PyObject *PyGigE_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyGigE *self;

    self = (PyGigE *)type->tp_alloc(type, 0);

    if (self != NULL) {
        self->fits_keywords = PyDict_New();
        if (self->fits_keywords == NULL) {
            Py_DECREF(self);
            return NULL;
        }

        self->mod_error = PyErr_NewException((char *)"gige.error", NULL, NULL);
        if (self->mod_error == NULL) {
            Py_DECREF(self);
            return NULL;
        }

        self->image_size = PyTuple_New(2);
        if (self->image_size == NULL) {
            Py_DECREF(self);
            return NULL;
        }

        pthread_mutex_init(&(self->stripe_lock), NULL);

        for (int i = 0; i < TOTAL_STRIPES; i++) {
            self->stripes[i].data   = NULL;
            self->stripes[i].length = 0;
            self->stripes[i].height = 0;
            self->stripes[i].width  = 0;
        }
    }

    return (PyObject *)self;
}

/**
 * Python: def __init__(self, firt, flast, number)
 */
static int PyGigE_init(PyGigE *self, PyObject *args, PyObject *kwds)
{
    char error[1024];
    int img_enable = 0;
    char *ip_addr = NULL;
    char *iface = NULL;
    PyObject *img_bool    = NULL;
    PyObject *ip_addr_obj = NULL;
    PyObject *iface_obj   = NULL;
    pthread_t image_broadcast_pid;

    static char *kwlist[] = { (char *)"reb_id", (char *)"ip_addr", (char *)"iface", (char *)"image" ,NULL };

    if (! PyArg_ParseTupleAndKeywords(args, kwds, "|iOOO", kwlist,
            &self->reb_id, &ip_addr_obj, &iface_obj, &img_bool))
        return -1;

    if (img_bool != NULL)
        img_enable = PyBool_Check(img_bool);

    if (ip_addr_obj != NULL)
        ip_addr = PyString_AsString(ip_addr_obj);

    if (iface_obj != NULL)
        iface = PyString_AsString(iface_obj);

    if (img_enable) {
        printf("Image service started\n");
        self->data = gige_data_init(self->reb_id, iface);
        pthread_create(&image_broadcast_pid, NULL, image_broadcaster, self);
        Py_XDECREF(img_bool);
    }

    self->reg = reg_client_new(ip_addr, self->reb_id);
    if (self->reg == NULL) {
        sprintf(error, "%s: (reb_id=%i) error: %s\n", __func__,
                self->reb_id,
                "Failed to create register object");
        PyErr_SetString(self->mod_error, error);
        return -1;
    }

    return 0;
}


static PyMemberDef PyGigE_members[] = {
    { (char *)"fits_keywords",  T_OBJECT_EX, offsetof(PyGigE, fits_keywords),  0, (char *)"first name" },
    { (char *)"image_segment_size",  T_OBJECT_EX, offsetof(PyGigE, image_size),  0, (char *)"first name" },
    { (char *)"iface",  T_STRING,    offsetof(PyGigE, iface), 0, (char *)"noddy number" },
    { NULL }  /* Sentinel */
};

static PyObject *PyGigE_read(PyGigE *self, PyObject *args)
{
    char error[1024];
    int addr;
    uint32_t val = 0;
    int rc;

    if (!PyArg_ParseTuple(args, "I", &addr))
        return NULL;

    rc = reg_client_read(self->reg, addr, &val);
    if (rc != 0) {
        sprintf(error, "%s: %s\n", __func__, reg_client_strerr(self->reg));
        PyErr_SetString(self->mod_error, error);
        return NULL;
    }

    return Py_BuildValue("I", val);
}

static PyObject *PyGigE_write(PyGigE *self, PyObject *args)
{
    char error[1024];
    uint32_t addr, val;
    int rc;

    if (!PyArg_ParseTuple(args, "II", &addr, &val))
        return NULL;

    rc = reg_client_write(self->reg, addr, val);
    if (rc != 0) {
        sprintf(error, "%s: %s\n", __func__, reg_client_strerr(self->reg));
        PyErr_SetString(self->mod_error, error);
        return NULL;
    }

    return Py_BuildValue("");
}

inline uint32_t sign_extend_18bpp(uint32_t word) {
    //uint32_t ret = (word & (1 << 17)) >> 17 ? word | 0xfffc0000 : word & 0x0003ffff;
    //ret = (ret * -1) + 131072;
    uint32_t ret = word ^ 0x1ffff
    return ret;
}

inline uint32_t sign_extend_16bpp(uint16_t word) {
    uint32_t ret = (word & (1 << 15)) >> 15 ? word | 0xffff0000 : word & 0x000ffff;
    ret = (ret * -1) + 131072;
    return ret;
}

inline uint32_t uint32_pack(uint8_t c0, uint8_t c1, uint8_t c2, uint8_t c3)
{
    return ((c3 << 24) | (c2 << 16) | (c1 << 8) | c0);
}

uint32_t init_stripes(PyGigE *self)
{
    char error[1024];
    uint32_t val = 0;
    int rc;

    for (int i = 0; i < 3; i++) {
        self->stripes[i].enabled = false;
    }


    if ((rc = reg_client_read(self->reg, STRIPE_ADDR, &val)) != 0) {
        sprintf(error, "%s: %s\n", __func__, reg_client_strerr(self->reg));
        PyErr_SetString(self->mod_error, error);
    }

    if (val & SLEFT)
        self->stripes[0].enabled = true;
    if (val & SMIDDLE)
        self->stripes[1].enabled = true;
    if (val & SRIGHT)
        self->stripes[2].enabled = true;

    return val;
}

int ret_stripe_idx(uint8_t stripe)
{
    int ret = 0;

    if (stripe == SLEFT)
            ret = 0;
    if (stripe == SMIDDLE)
            ret = 1;
    if (stripe == SRIGHT)
            ret = 2;

    return ret;
}

int add_fits_header(fitsfile *fp, const char *key, char *value, const char *comment)
{
    char card[FLEN_CARD];
    char newcard[FLEN_CARD];
    int  keytype, status;

    strcpy(newcard, key);
    strcat(newcard, " = ");
    strcat(newcard, value);
    strcat(newcard, " / ");
    strcat(newcard, comment);

    fits_parse_template(newcard, card, &keytype, &status);
    fits_update_card(fp, key, card, &status);

    return status;
}

int add_fits_header_int(fitsfile *fp, const char *key, int value, const char *comment)
{
    char cval[FLEN_CARD];
    char card[FLEN_CARD];
    char newcard[FLEN_CARD];
    int  keytype, status;

    strcpy(newcard, key);
    strcat(newcard, " = ");
    sprintf(cval, "%d", value);
    strcat(newcard, cval);
    strcat(newcard, " / ");
    strcat(newcard, comment);

    fits_parse_template(newcard, card, &keytype, &status);
    fits_update_card(fp, key, card, &status);

    return status;
}

int write_fits(stripe_t *current_stripe, char *fname)
{
    fitsfile *fptr;
    uint32_t height, width, length;
    int      status  = 0;
    long     fpixel = 1, naxis = 2, nelements;
    char     tmp_value[80];
    uint32_t *chan_data;

    fits_create_file(&fptr, fname, &status);
    fits_create_img(fptr, LONG_IMG, 0, 0, &status);

    long naxes[2] = { (long)current_stripe->width, (long)current_stripe->height };
    nelements = naxes[0] * naxes[1];
    height = current_stripe->height;
    width  = current_stripe->width;
    length = current_stripe->length;

    chan_data = new uint32_t[current_stripe->length];
    int x0 = 0, x1 = 0, y0 = 0, y1 = 0;
    for (uint32_t chan_idx = 0; chan_idx < CHANNELS; chan_idx++) {
        uint32_t x = 0, y = 0, idx;
        for (idx = chan_idx; idx < length; idx += CHANNELS) {
            if (x >= width) {
                x = 0;
                y++;
            }
            //printf("x=%i, y=%i, idx=%i, len=%i\n", x, y, idx, length);
            chan_data[x++ + width * y] = current_stripe->data[idx];
        }
        //printf("%x %x\n", fptr, &fptr);
        fits_create_img(fptr, LONG_IMG, naxis, naxes, &status);

        sprintf(tmp_value, "[%d:%d,%d:%d]", 0, 0, width*(CHANNELS/2), height*2);
        add_fits_header(fptr, "DETSIZE", tmp_value, "Detector Size");

        sprintf(tmp_value, "[%d:%d,%d:%d]", 11, 522, 1, 2002);
        add_fits_header(fptr, "DATASEC", tmp_value, "Data binned size");

        if (chan_idx < (CHANNELS/2)) {
            y0 = 0;
            y1 = height*2;
            x0 = width*((chan_idx % (CHANNELS/2)) + 1);
            x1 = width*(chan_idx % (CHANNELS/2));
        }
        else {
            y0 = height*2;
            y1 = height;
            x0 = width*(((CHANNELS/2) - (chan_idx % (CHANNELS/2))) - 1);
            x1 = width*((CHANNELS/2) - (chan_idx % (CHANNELS/2)));
        }

        sprintf(tmp_value, "[%d:%d,%d:%d]", x0, x1, y0, y1);
        add_fits_header(fptr, "DETSEC", tmp_value, "Unbinned section of detector");

        sprintf(tmp_value, "[%d:%d,%d:%d]", 1, height, 1, 2000);
        add_fits_header(fptr, "TRIMSEC", tmp_value, "Trimmed binned section");

        add_fits_header_int(fptr, "DTV1",   0, "detector transformation vector");
        add_fits_header_int(fptr, "DTV2",   0, "detector transformation vector");
        add_fits_header_int(fptr, "DTM1_1", 1, "detector transformation matrix");
        add_fits_header_int(fptr, "DTM2_2", 1, "detector transformation matrix");

        fits_write_img(fptr, TINT, fpixel, nelements, chan_data, &status);
    }

    sprintf(tmp_value, "%d", CHANNELS);
    add_fits_header(fptr, "NEXTS", tmp_value, "Number of extension images in file");

    sprintf(tmp_value, "[%d:%d,%d:%d]", 0, 0, width*(CHANNELS/2), height*2);
    add_fits_header(fptr, "DETSIZE", tmp_value, "Detector Size");

    sprintf(tmp_value, "[%d:%d,%d:%d]", 11, 522, 1, 2002);
    add_fits_header(fptr, "DATASEC", tmp_value, "Data binned size");

    fits_close_file(fptr, &status);
    fits_report_error(stderr, status);  /* print out any error messages */

    delete chan_data;
    return status;

}

void *fits_writer_thread(void *args)
{
    stripe_args_t *pargs          = (stripe_args_t *)args;
    stripe_t      *current_stripe = pargs->current_stripe;
    char          *fname          = pargs->fname;

    write_fits(current_stripe, fname);

    pthread_exit(NULL);
}


static PyObject *PyGigE_save_fits(PyGigE* self, PyObject* args)
{
    char          *stripe_lookup[3] = {"a", "b", "c"};
    char          *fname = NULL;
    char          fname_org[4096];
    char          newfname[4096];
    char          tmp[4096];
    stripe_t      *current_stripe;
    pthread_t     fits_writers_pid[TOTAL_STRIPES];
    stripe_args_t pargs[TOTAL_STRIPES];

    if (!PyArg_ParseTuple(args, "s", &fname))
        return NULL;

    strcpy(fname_org, fname);

    for (int i = 0; i < TOTAL_STRIPES; i++) {
        current_stripe = &self->stripes[i];
        if (current_stripe->enabled) {
            newfname[0] = '\0';
            strcat(newfname, fname_org);
            sprintf(tmp, ".%i%s.fits", self->reb_id, stripe_lookup[i]);
            strcat(newfname, tmp);

            pargs[i].current_stripe = &self->stripes[i];
            pargs[i].fname = new char[4096];
            strcpy(pargs[i].fname, newfname);
            pthread_create(&fits_writers_pid[i], NULL, fits_writer_thread, &pargs[i]);
        }
    }

    for(int i = 0; i < TOTAL_STRIPES; i++) {
        current_stripe = &self->stripes[i];
        if (current_stripe->enabled) {
            pthread_join(fits_writers_pid[i], NULL);
            delete pargs[i].fname;
        }
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *PyGigE_get_image(PyGigE *self, PyObject *args)
{
    uint32_t img_word_cnt  = 0;
    int      stripe_select = 0;
    uint8_t  stripe_count  = 0;
    uint32_t  stripes_en    = 0;
    uint32_t height, width;
    double bitrate = 0.0;
    stripe_t *current_stripe;
    struct timeval tvBegin, tvEnd, tvDiff;

    //if (!PyArg_ParseTuple(self->image_size, "iii", &height, &width, &stripes_en))
    //    return NULL;
    if (!PyArg_ParseTuple(args, "III", &height, &width, &stripes_en))
      return NULL;

    Py_BEGIN_ALLOW_THREADS
    pthread_mutex_lock(&(self->stripe_lock));
    for (int i = 0; i < 3; i++) {
        self->stripes[i].enabled = false;
    }

    if (stripes_en & SLEFT)
        self->stripes[0].enabled = true;
    if (stripes_en & SMIDDLE)
        self->stripes[1].enabled = true;
    if (stripes_en & SRIGHT)
        self->stripes[2].enabled = true;

    for (int i = 0; i < TOTAL_STRIPES; i++) {
        if (self->stripes[i].enabled) {
            if (self->stripes[i].data == NULL) {
                self->stripes[i].data = new uint32_t[height*width*CHANNELS];
                DBG_PRINT("(%p) Added stripe %i at %p (%i bytes)\n", self, i, &(self->stripes[i]), height*width*CHANNELS*4);
            }

            self->stripes[i].length = 0;
            self->stripes[i].idx    = 0;
            self->stripes[i].height = height;
            self->stripes[i].width  = width;
            stripe_count++;
        }
    }

    current_stripe = &(self->stripes[stripe_select]);
    while (!current_stripe->enabled) {
        stripe_select = (stripe_select + 1) % TOTAL_STRIPES;
        current_stripe = &(self->stripes[stripe_select]);
    }

    uint16_t *pixels = new uint16_t[height*width*stripe_count*CHANNELS];
    int size = gige_data_recv(self->data, pixels);
    if (size <= 0)
        goto bail;

    if ((height*width*stripe_count*CHANNELS) != gige_get_n_pixels(self->data)) {
        DBG_PRINT("*** Unexpected length returned: npix=%i, alloc=%i, "\
                        "expected %i pix, %i bytes\n",
                gige_get_n_pixels(self->data), size,
                (height*width*stripe_count*CHANNELS),
                (height*width*stripe_count*CHANNELS)*sizeof(uint32_t));
        //goto bail;
    }

    for (int i = 0; i < TOTAL_STRIPES; i++) {
        if (self->stripes[i].enabled) {
            self->stripes[i].tag     = 0x0;
            self->stripes[i].cluster = 0x0;
            self->stripes[i].address = 0x0;
        }
    }

    for (int i = 0; i < gige_get_n_pixels(self->data); i++) {
        if (img_word_cnt % CHANNELS == 0 && img_word_cnt > 0) {
            stripe_select = (stripe_select + 1) % TOTAL_STRIPES;
            current_stripe = &(self->stripes[stripe_select]);
            while (!current_stripe->enabled) {
                stripe_select = (stripe_select + 1) % TOTAL_STRIPES;
                current_stripe = &(self->stripes[stripe_select]);
            }
        }
        uint32_t tmp_word = sign_extend_18bpp(htons(pixels[i]) << 2);
        img_word_cnt++;
        memcpy(&current_stripe->data[current_stripe->idx++], &tmp_word, sizeof(uint32_t));
        current_stripe->length++;
    }
    self->broadcast_data_ready_flag = 1;
    delete pixels;
bail:
    Py_END_ALLOW_THREADS
    pthread_mutex_unlock(&(self->stripe_lock));
    Py_INCREF(Py_None);
    return Py_None;

}


static PyMethodDef PyGigE_methods[] = {
    {"read",        (PyCFunction)PyGigE_read,  METH_VARARGS, "Read a register. Requires address."},
    {"write",       (PyCFunction)PyGigE_write, METH_VARARGS, "Write a register. Requires address, value."},
    {"get_image",   (PyCFunction)PyGigE_get_image, METH_VARARGS, "Write a register. Requires address, value."},
    { NULL }  /* Sentinel */
};

static PyTypeObject PyGigE_Type = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "PyGigE",             /*tp_name*/
    sizeof(PyGigE),             /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)PyGigE_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "PyGigE objects",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    PyGigE_methods,             /* tp_methods */
    PyGigE_members,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)PyGigE_init,      /* tp_init */
    0,                         /* tp_alloc */
    PyGigE_new,                 /* tp_new */
};

static PyMethodDef module_methods[] = {
    {NULL}  /* Sentinel */
};

PyMODINIT_FUNC initgige(void)
{
    PyObject *mod;

    if (PyType_Ready(&PyGigE_Type) < 0)
        return;

    mod = Py_InitModule3("gige", module_methods,
                       "Wrapper");

    if (mod == NULL)
      return;

    // Import Numpy array
    import_array();

    Py_INCREF(&PyGigE_Type);
    PyModule_AddObject(mod, "gige", (PyObject *)&PyGigE_Type);

}

