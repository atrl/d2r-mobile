# Android menu touch verification

2026-10-18, Android 15 x86_64 emulator with ARM64 translation, 1280×720.

## Reproduction and change

Published preview.7 (versionCode 10025) loaded the existing TestHero character,
but tapping Enter game and pressing the virtual A button left character selection
open. The log recorded ControllerActionBegin and ClosePanel TouchNoop.
Android sent raw HID touch plus A for every surface tap. The iOS frontend instead
uses dm_ui_touch for frontend pages; those events are queued for the guest UI thread.

The candidate routes the first surface finger through dm_ui_touch outside a run,
tracks its pointer ID, and cancels on pause, resize, input destruction or departure
from the rendered viewport. Virtual gamepad controls retain their existing path.
In-run panel interactions are not changed by this patch and need separate validation.

## Observed candidate result

A locally signed preview.8-test APK (versionCode 10025, not a public release) was
built from the preview.7 source plus this patch and installed over preview.7.
A short adb input tap at (640,648) entered the camp with the existing TestHero.
The log loaded the gameplay panels and unloaded LoadScreenPanel. A three-second
joystick drag from (177,488) to (240,488) moved the character and camera; pressing
plus opened the inventory panel. All 20 Linux CI checks passed. The existing CI
suite does not itself test these live guest UI interactions.

Local evidence: /tmp/d2r-menu-touch-game.log, /tmp/d2r-menu-touch-result.png,
/tmp/d2r-menu-touch-move.png, /tmp/d2r-menu-touch-pause.png.

Still unverified: repeated save/exit/reload, combat, multitouch cancellation on a
real foldable, vivo installation and sustained performance. This is not evidence
of complete playability, and the candidate is not yet published.

## Download progress follow-up

The 6,147,543,691-byte download used integer percentages, so its first 61 MB
were displayed as 0%. The candidate now refreshes byte progress at most twice
per second and reports connection, retry and part verification separately.
A real GitHub transfer in the emulator displayed 0.40%, 23.7 / 5862.8 MiB;
the partial file measured 25,291,096 bytes shortly after the screenshot.
Evidence: /tmp/d2r-download-status.png. Cancellation retained partial data.
A 16-byte range probe against the production first part returned HTTP 206.
These observations establish this test network worked, not the user's network.
