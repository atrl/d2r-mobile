#include "viewport.h"
#include <assert.h>
#include <math.h>
int main(void) {
    const int windows[][2] = {{2480,2200},{2748,1172},{1172,2748},{800,600},{400,900},{1,1},{0,0}};
    for (unsigned i=0; i<sizeof windows/sizeof windows[0]; i++) {
        int w=windows[i][0],h=windows[i][1]; dm_viewport v=dm_viewport_fit(w,h,16,9);
        assert(v.x>=0 && v.y>=0 && v.x+v.width<=w && v.y+v.height<=h);
        float x,y;
        if (v.width && v.height) {
            assert(dm_viewport_touch(v,v.x+v.width*.5f,v.y+v.height*.5f,&x,&y));
            assert(fabsf(x-.5f)<.001f && fabsf(y-.5f)<.001f);
            assert(!dm_viewport_touch(v,v.x-1,v.y,&x,&y));
            assert(!dm_viewport_touch(v,v.x+v.width,v.y,&x,&y));
        } else assert(!dm_viewport_touch(v,0,0,&x,&y));
    }
    return 0;
}
