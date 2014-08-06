/* ======================================================================== *
 * 
 * SkyDice
 * pulse analysis Python wrapper
 *
 * Author: Laurent Le Guillou <llg@lpnhe.in2p3.fr>
 * ======================================================================== *
 *
 * Python module for the pulse analysis - version 0.1
 * 2011 Laurent Le Guillou <llg@lpnhe.in2p3.fr>
 * LPNHE/UPMC, Campus Jussieu, 75005 Paris, France
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301  USA
 *
 * ======================================================================== */

#define VERSION "0.1"

/* ======================================================================== */

#include <Python.h>
// #include <numpy/arrayobject.h>  // For Numpy (unused here)
// #include <bytearrayobject.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <stdio.h>
#include <math.h>

/* ======================================================================== */

long int pulse_analysis(FILE *f, 
			//
			long int before_start,
			long int before_stop,
			double *before_mean,
			double *before_var,
			long int *before_n,
			//
			long int in_start,
			long int in_stop,
			double *in_mean,
			double *in_var,
			long int *in_n,
			//
			long int after_start,
			long int after_stop,
			double *after_mean,
			double *after_var,
			long int *after_n);

/* ======================================================================== */
/* Pulse Analysis */

static PyObject *
_pulse_analysis(PyObject *self, PyObject *args, PyObject *keywds) {

  char *filename = "test.data";

  long pre_start,     pre_stop,     pre_n;
  long signal_start,  signal_stop,  signal_n;
  long post_start,    post_stop,    post_n;

  double pre_mean,    pre_var;
  double signal_mean, signal_var;
  double post_mean,   post_var;

  FILE *f;
  long ret;

  static char *kwlist[] = {"filename",
			   "pre_start",    "pre_stop",
			   "signal_start", "signal_stop",
			   "post_start",   "post_stop", 
			   NULL};
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "siiiiii|", kwlist, 
				   &filename,
				   &pre_start,    &pre_stop,
				   &signal_start, &signal_stop,
				   &post_start,   &post_stop)) {
    return NULL; 
  }


  f = fopen(filename, "r");
  if (f == NULL) {
    PyErr_SetString(PyExc_IOError, "Failed to open data file");
    return NULL;
  }

  ret = pulse_analysis(f,
		       pre_start, pre_stop, 
		       &pre_mean, &pre_var, &pre_n,
		       signal_start, signal_stop, 
		       &signal_mean, &signal_var, &signal_n,
		       post_start, post_stop, 
		       &post_mean, &post_var, &post_n);

  printf("ret = %ld\n", ret);

  if (ret < 0) {
    PyErr_SetString(PyExc_ValueError, "Failed to process open data file (too short ? missing data ?)");
    return NULL;
  }

  return Py_BuildValue("{s:{s:l,s:d,s:d},s:{s:l,s:d,s:d},s:{s:l,s:d,s:d}}", 
		       "pre",
		       "n",        pre_n,
		       "mean",     pre_mean,    
		       "variance", pre_var,
		       "signal",
		       "n",        signal_n,
		       "mean",     signal_mean,    
		       "variance", signal_var,
		       "post",
		       "n",        post_n,
		       "mean",     post_mean,    
		       "variance", post_var);
}

/* ======================================================================== *
 * 
 * Declaration of all the defined methods for Python
 *
 */

static PyMethodDef pulse_wrapper_methods[] = {
  /* -------------------------------------------------------------------- */
  {"analysis", (PyCFunction)_pulse_analysis,
   METH_VARARGS | METH_KEYWORDS,
   "analysis(filename, pre_start, pre_stop, signal_start, signal_stop, post_start, post_stop)\n\nmean/variance analysis of a pulse datafile."},
  /* -------------------------------------------------------------------- */
  {NULL, NULL, 0, NULL}        /* Sentinel */
  /* -------------------------------------------------------------------- */
};

/* ======================================================================== *
 * 
 * Module initialization function
 *
 */

PyMODINIT_FUNC
initpulse_wrapper(void) {

  PyObject *_module;
  _module = Py_InitModule("pulse_wrapper", pulse_wrapper_methods);

  /* ----- Defining a specific Exception ---------------------------------- */

  /* ----- Defining some constants in Python namespace -------------------- */

  /* ----- __version__ constant ------------------ */

  PyModule_AddObject(_module, "__version__", Py_BuildValue("s", VERSION));

  /* ----- Devices available --------------------- */

  // PyModule_AddObject(_module, "DEV_NONE", PyInt_FromLong(DEV_NONE));

  /* --------------------------------------------- */
}

/* ======================================================================== */
