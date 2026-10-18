#pragma once
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>

/* Bounded stack storage and POSIX signal-safe I/O; avoid the dynamic-loader lock. */
static uint64_t dm_map_hex(const char **cursor) {
    uint64_t value=0;const char *p=*cursor;
    for(;;p++){
        unsigned digit;
        if(*p>='0'&&*p<='9')digit=(unsigned)(*p-'0');
        else if(*p>='a'&&*p<='f')digit=(unsigned)(*p-'a'+10);
        else break;
        value=(value<<4)|digit;
    }
    *cursor=p;return value;
}
static void dm_crash_maps(int output,uint64_t pc,uint64_t lr) {
    int fd=open("/proc/self/maps",O_RDONLY|O_CLOEXEC);if(fd<0)return;
    char block[4096],line[2048];size_t used=0;int overflow=0;ssize_t count;
    while((count=read(fd,block,sizeof block))>0){
        for(ssize_t i=0;i<count;i++){
            char c=block[i];
            if(c!='\n'){if(used<sizeof line-1)line[used++]=c;else overflow=1;continue;}
            line[used]=0;
            if(!overflow){
                const char *p=line;uint64_t low=dm_map_hex(&p);
                if(*p=='-'){
                    p++;uint64_t high=dm_map_hex(&p);
                    if((pc>=low&&pc<high)||(lr>=low&&lr<high)){
                        const char prefix[]="[dm] crash-mapping ";
                        (void)write(output,prefix,sizeof prefix-1);
                        (void)write(output,line,used);(void)write(output,"\n",1);
                    }
                }
            }
            used=0;overflow=0;
        }
    }
    close(fd);
}
