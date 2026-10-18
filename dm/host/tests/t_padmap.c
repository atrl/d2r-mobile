// 实体手柄面键映射（dm_padmap.h）：真实手柄 × 四颗面键，从「按了哪颗物理键」走到「游戏收到哪个键」。
// 每行三列都按事实手写，不跑被测代码：
//   系统给哪个（buttonA/B/X/Y）：任天堂手柄按键帽字母给（日志；SDL 苹果手柄实现把任天堂的 buttonA 当右键），Xbox 字母与位置一致，PS 按菱形位置（下 = buttonA）；
//   期望游戏键：印字母的 = 印的那个字母（Switch 原版同名键，右 A 确认）；没字母的 = Xbox 同位置的字母（下方键确认）。
// 旧映射（认出任天堂后把 buttonA 当下方键、换成 B）在任天堂各行会红，Xbox / PS 行新旧一样。
// Physical controller face-button mapping (dm_padmap.h): real controllers × four face buttons, from "which physical button was pressed" to "which button the game receives".
// Each row's three columns are written by hand from facts, without running the code under test:
//   which one the system reports (buttonA/B/X/Y): Nintendo controllers by keycap letter (logs; SDL's Apple controller code treats Nintendo's buttonA as the right button), Xbox letters match positions, PS by diamond position (bottom = buttonA);
//   expected game button: printed letter = that letter (same-named Switch button, right A confirms); no letter = the Xbox letter at the same position (bottom button confirms).
// The old mapping (after recognizing Nintendo, treat buttonA as the bottom button and swap to B) fails on every Nintendo row; Xbox / PS rows are the same old and new.
#include <stdio.h>
#include "../dm_padmap.h"
#include "../dm_input.h"
static int checks, fails;
#define CHECK(c, ...) do { checks++; if (c) printf("  ✓ "); else { fails++; printf("  ✗ "); } printf(__VA_ARGS__); printf("\n"); } while (0)
enum { GA, GB, GX, GY };   // 系统给的 buttonA / B / X / Y | The system's buttonA / B / X / Y
int main(void) {
    static const struct { const char *cat, *ven, *pos, *cap; int sys; uint64_t want; } r[] = {
        { "Switch Pro Controller", "Pro Controller", "右", "A", GA, DM_BTN_A }, { "Switch Pro Controller", "Pro Controller", "下", "B", GB, DM_BTN_B },
        { "Switch Pro Controller", "Pro Controller", "上", "X", GX, DM_BTN_X }, { "Switch Pro Controller", "Pro Controller", "左", "Y", GY, DM_BTN_Y },
        { "Nintendo Switch Joy-Con (L/R)", "Joy-Con (L/R)", "右", "A", GA, DM_BTN_A }, { "Nintendo Switch Joy-Con (L/R)", "Joy-Con (L/R)", "下", "B", GB, DM_BTN_B },
        { "Nintendo Switch Joy-Con (L/R)", "Joy-Con (L/R)", "上", "X", GX, DM_BTN_X }, { "Nintendo Switch Joy-Con (L/R)", "Joy-Con (L/R)", "左", "Y", GY, DM_BTN_Y },
        { "Xbox One", "Xbox Wireless Controller", "下", "A", GA, DM_BTN_A }, { "Xbox One", "Xbox Wireless Controller", "右", "B", GB, DM_BTN_B },
        { "Xbox One", "Xbox Wireless Controller", "左", "X", GX, DM_BTN_X }, { "Xbox One", "Xbox Wireless Controller", "上", "Y", GY, DM_BTN_Y },
        { "DualSense", "DualSense Wireless Controller", "下", "×", GA, DM_BTN_A }, { "DualSense", "DualSense Wireless Controller", "右", "○", GB, DM_BTN_B },
        { "DualSense", "DualSense Wireless Controller", "左", "□", GX, DM_BTN_X }, { "DualSense", "DualSense Wireless Controller", "上", "△", GY, DM_BTN_Y } };
    static const char *const nm[] = { "A", "B", "X", "Y" };
    for (unsigned i = 0; i < sizeof r / sizeof *r; i++)
        CHECK(dm_padmap_face(r[i].sys == GA, r[i].sys == GB, r[i].sys == GX, r[i].sys == GY) == r[i].want, "%s：按%s键（印 %s，系统给 button%s）→ 游戏 %s", r[i].cat, r[i].pos, r[i].cap, nm[r[i].sys], nm[__builtin_ctzll(r[i].want)]);
    CHECK(dm_padmap_face(1, 1, 0, 0) == (DM_BTN_A | DM_BTN_B), "两颗同时按：各算各的"); CHECK(dm_padmap_face(0, 0, 0, 0) == 0, "都没按 = 0");
    // 十字键的 HAT 轴映射（dm_input.h）：先按安卓惯例 —— HAT_Y 负为上、正为下；阈值 ±0.5 容忍模拟量；两轴同过阈值给斜向两位。
    // 上下方向若在真机上相反，看 [android-pad] 那行日志即可确认，改这里一处。
    // HAT-axis mapping for the D-pad (dm_input.h), starting from the Android convention: HAT_Y negative is up and
    // positive is down; ±0.5 tolerates analogue hats; both axes over the threshold give two diagonal bits. If up
    // and down turn out swapped on a real pad, the [android-pad] log line shows it and only this needs changing.
    CHECK(dm_pad_hat_buttons(0, 0) == 0, "HAT 居中 = 无方向");
    CHECK(dm_pad_hat_buttons(-1, 0) == DM_BTN_LEFT, "HAT 左 = Left");
    CHECK(dm_pad_hat_buttons(1, 0) == DM_BTN_RIGHT, "HAT 右 = Right");
    CHECK(dm_pad_hat_buttons(0, -1) == DM_BTN_UP, "HAT 上（Y 负）= Up");
    CHECK(dm_pad_hat_buttons(0, 1) == DM_BTN_DOWN, "HAT 下（Y 正）= Down");
    CHECK(dm_pad_hat_buttons(-1, -1) == (DM_BTN_LEFT | DM_BTN_UP), "HAT 左上 = Left+Up");
    CHECK(dm_pad_hat_buttons(1, 1) == (DM_BTN_RIGHT | DM_BTN_DOWN), "HAT 右下 = Right+Down");
    CHECK(dm_pad_hat_buttons(0.4f, -0.4f) == 0, "低于阈值不触发（容忍模拟量漂移）");
    CHECK(dm_pad_hat_buttons(-0.5f, 0) == DM_BTN_LEFT, "恰好 -0.5 算触发（边界含）");
    // 扳机 ZL/ZR 的模拟轴映射（dm_input.h）：Xbox 的 LT/RT 在安卓上是 0–1 的轴、不是键码；阈值 0.5（实测轴的
    // flat 区约 0.06，离噪声足够远）。真机若手感偏重/偏轻，改 dm_input.h 里那一个阈值即可。
    // Analogue-axis mapping for the ZL/ZR triggers (dm_input.h): an Xbox pad reports LT/RT as 0-1 axes, not
    // keycodes; the threshold is 0.5 (the axis flat region measures about 0.06, well clear of the noise). If the
    // feel is too heavy or too light on a real pad, the single threshold in dm_input.h is the place to change.
    CHECK(dm_pad_trigger_buttons(0, 0) == 0, "扳机松开 = 不按");
    CHECK(dm_pad_trigger_buttons(1, 0) == DM_BTN_ZL, "LT 到底 = ZL");
    CHECK(dm_pad_trigger_buttons(0, 1) == DM_BTN_ZR, "RT 到底 = ZR");
    CHECK(dm_pad_trigger_buttons(1, 1) == (DM_BTN_ZL | DM_BTN_ZR), "两个扳机各给一位");
    CHECK(dm_pad_trigger_buttons(0.4f, 0.4f) == 0, "半按不到阈值不算按下");
    CHECK(dm_pad_trigger_buttons(0.5f, 0) == DM_BTN_ZL, "恰好 0.5 算按下（边界含）");
    CHECK(dm_pad_trigger_buttons(0.06f, 0.06f) == 0, "flat 区抖动不触发");
    printf("== %d 项，失败 %d ==\n", checks, fails);
    return fails != 0;
}
