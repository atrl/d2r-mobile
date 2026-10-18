#pragma once

#include <stdint.h>

int dm_touch_host_enabled(void);
void dm_touch_host_game_start(uint64_t now);
void dm_touch_host_step(uint64_t now, uint64_t *buttons, int32_t *lx, int32_t *ly, int32_t *rx, int32_t *ry);

int dm_touch_host_world_active(void);   // 游戏线程：当前是否允许消费 Mac 鼠标世界指令；脚本不受此限制 | Game thread: whether Mac mouse world commands may be consumed now; scripts are unaffected

// Shared live pointer adapter: call enable before the guest starts; 0 down, 1 move, 2 up, 3 cancel.
void dm_touch_host_live_enable(void);
void dm_touch_host_live(int op, float nx, float ny);
