#pragma once
#include <stdint.h>
typedef struct { int x, y, width, height; } dm_viewport;
static inline dm_viewport dm_viewport_fit(int width, int height, int source_width, int source_height) {
    if (width <= 0 || height <= 0 || source_width <= 0 || source_height <= 0) return (dm_viewport){0};
    int w = width, h = (int)((int64_t)width * source_height / source_width);
    if (h > height) { h = height; w = (int)((int64_t)height * source_width / source_height); }
    return (dm_viewport){(width-w)/2, (height-h)/2, w, h};
}
static inline int dm_viewport_touch(dm_viewport v, float x, float y, float *nx, float *ny) {
    if (v.width <= 0 || v.height <= 0 || x < v.x || y < v.y || x >= v.x+v.width || y >= v.y+v.height) return 0;
    *nx = (x-v.x)/v.width; *ny = (y-v.y)/v.height; return 1;
}
