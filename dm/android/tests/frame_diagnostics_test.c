#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <sys/stat.h>
#include <string.h>
static uint64_t now_ns;
static unsigned frequency_reads;
static uint64_t dm_android_clock_ns(clockid_t clock) { (void)clock; return now_ns; }
static int probe_open(const char *path, int flags, ...) {
    (void)flags; assert(strstr(path,"/cpufreq/scaling_cur_freq")); frequency_reads++; return -1;
}
#define LOG(...) ((void)0)
#define open probe_open
#include "../native/nvn_vulkan_cpu_phases.inc"
#undef open
int main(void) {
    char directory[]="/tmp/d2r-frame-diag-XXXXXX";
    assert(mkdtemp(directory)); assert(!setenv("DM_DATA",directory,1));
    // Two seconds of sustained 30 FPS, real production logger, denied sysfs reads as on restricted devices.
    for(unsigned frame=1;frame<=60;frame++) {
        now_ns=frame*33333334ull;
        dm_cpu_phase_ns[DM_CPU_PHASE_DRAW]+=20000000;
        dm_cpu_phase_calls[DM_CPU_PHASE_DRAW]+=1000;
        dm_abnormal_frame(frame,33333334,25000000,12000000,frame*1000,frame*50,0,frame*6000000ull,frame*1000,frame*500);
    }
    printf("slow frames=60 records=%llu frequency_opens=%u\n",(unsigned long long)dm_abnormal_records,frequency_reads);
    fflush(stdout);
    assert(dm_abnormal_records<=4);
    assert(frequency_reads<=36);
    // Normal frames never perform frequency I/O, but still advance the phase counters.
    unsigned before=frequency_reads;
    now_ns+=1000000000; dm_cpu_phase_calls[DM_CPU_PHASE_DRAW]+=1;
    dm_abnormal_frame(61,16000000,12000000,8000000,60001,3000,0,360000000,60000,30000);
    assert(frequency_reads==before);
    char path[256];snprintf(path,sizeof path,"%s/abnormal-frames.log",directory);
    FILE *file=fopen(path,"r");assert(file);char contents[8192];size_t n=fread(contents,1,sizeof contents-1,file);contents[n]=0;fclose(file);
    assert(strstr(contents,"draw=20.000/1000")); // sampling must not turn per-frame deltas into accumulated windows
    assert(strstr(contents,"suppressed=14"));
    assert(!fseek(dm_abnormal_file, DM_ABNORMAL_FILE_LIMIT, SEEK_SET));
    // The production stream is append-only: write enough bytes to cross its cap.
    char block[4096]={0};
    for(int i=0;i<1025;i++) assert(fwrite(block,1,sizeof block,dm_abnormal_file)==sizeof block);
    fflush(dm_abnormal_file);
    now_ns+=1000000000;
    dm_abnormal_frame(62,40000000,25000000,12000000,61001,3050,0,366000000,61000,30500);
    struct stat info;assert(!stat(path,&info));assert(info.st_size>0 && info.st_size<8192);
    fclose(dm_abnormal_file);
    unlink(path);rmdir(directory);puts("frame diagnostics bounded-I/O regression passed");
}
