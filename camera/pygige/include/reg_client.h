#ifndef __REGCLI_H_INCLUDED__
#define __REGCLI_H_INCLUDED__
#include <zmq.h>
#include <stdint.h>

#define CMD_REG_READ       0
#define CMD_REG_WRITE      1
#define CMD_ERROR          2

#define REG_SERVER_PORT 5542
#define REB_READ_FAILURE -2
#define REB_WRITE_FAILURE -3

typedef struct {
    void *ctx;
    void *zsock;
    char error_str[512];
} reg_client_t;

#ifdef __cplusplus
extern "C" {
#endif

reg_client_t *reg_client_new(char *ip_addr, int id);
int reg_client_read(reg_client_t *rcli, uint32_t addr, uint32_t *value);
int reg_client_write(reg_client_t *rcli, uint32_t addr, uint32_t value);
int reg_client_close(reg_client_t *rcli);
char *reg_client_strerr(reg_client_t *rcli);

#ifdef __cplusplus
}
#endif


#endif  //  __REGCLI_H_INCLUDED__
