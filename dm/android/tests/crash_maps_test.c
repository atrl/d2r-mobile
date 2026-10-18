#define _GNU_SOURCE
#include <stdio.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include "../../host/dm_crash_maps.h"
static int output;
int main(void);
static void handler(int signal){(void)signal;dm_crash_maps(output,(uintptr_t)&main,(uintptr_t)&raise);}
int main(void){
 char path[]="/tmp/d2r-crash-maps-XXXXXX";output=mkstemp(path);if(output<0)return 1;unlink(path);
 struct sigaction action={.sa_handler=handler};sigemptyset(&action.sa_mask);if(sigaction(SIGUSR1,&action,NULL))return 2;
 raise(SIGUSR1);lseek(output,0,SEEK_SET);char buffer[8192];ssize_t n=read(output,buffer,sizeof buffer-1);close(output);if(n<1)return 3;buffer[n]=0;
 if(!strstr(buffer,"crash-mapping")||!strstr(buffer,"libc.so"))return 4;
 puts("Actual signal handler maps executable and libc addresses without loader calls");return 0;
}
