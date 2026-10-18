# Screen aspect rendering and opt-in live diagnostics

The user reports vivo V2436A can run with built-in Turnip in preview.12, while the system driver still exits. This is a device-side startup confirmation, not a full gameplay/performance/fold acceptance result. The user wants less unused display area while preserving proportions and explicitly authorized a Cloudflare diagnostic upload channel.

## Rendering

The fourth resolution choice adapts to wide screens, capped at 2560x900. Narrow/inner displays use 1600x900 and proportional fitting: a real emulator run at native 1000x900 failed with `Vulkan scissor outside target` in character selection, so that unsafe mode is deliberately excluded. Existing game resolution/aspect hooks expand wide views without stretching. Native input and overlay placement use the selected aspect. Fold/resizing preserves the session and refits the viewport; restart to recalculate the startup resolution.

## Touch and controls

Android previously routed only front-end taps through dm_ui_touch and treated in-game screen presses as A. It now uses the existing shared live pointer adapter in touch_mac.c, including inventory gestures, world targeting/walking, menu tabs and the game's HUD. Enable after module gates are loaded in front_run; enabling before dm_main aborts because OBS_UIMSG is not registered yet. Android uses the game's controller HUD because the iOS-specific drawn skill bar is absent; visible skills/potions are touch targets.

Optional gamepad buttons are collapsed behind one edge entry by default, collapse again on menu/world/panel transitions, and can be expanded manually. One-time contextual Toast hints can be replayed by holding the entry. On inner screens the entry uses top letterbox space, and expanded controls shrink into available bottom/top margins where possible. A completely filled display has no outside-picture area; expanded fallback controls necessarily overlap it. Physical-controller detection and lifecycle releases remain active. Android cancel and queue overflow release pointer ownership and held HUD skills without synthesizing item drops/clicks.

## Diagnostics

Automatic diagnostics is off by default. The player pastes a session-specific HTTPS receiver URL and explicitly enables it. The app process uploads StartupDiagnostics every30 seconds on a background executor, including device metadata/config and bounded tails of the last three game logs; it excludes saves/assets. Character names/local paths may appear in logs, as disclosed in the dialog. A crashed process cannot upload until the launcher is reopened; startup resumes collection. No Android background service or automatic device identifiers are installed. Disable in the same dialog. No endpoint/token is embedded in the APK or committed.

The receiver binds loopback and is exposed through a Cloudflare Quick Tunnel. A secret path authenticates write-only requests; public GET only exposes health. Max262144 bytes/request,12 accepted requests/minute,100 retained reports, permissions0600. Temporary hostname may change on tunnel restart; update the player's configured address then. Local receiver config and reports live under ~/.local/share/d2r-diagnostics, outside the repository. User services d2r-diagnostic-receiver and d2r-diagnostic-tunnel run the receiver and tunnel. No promise of permanent uptime or an agent monitoring while the conversation is inactive.

Validation:28 Linux checks pass (including 33 shared live-input assertions), signed local Android APK builds, real external HTTPS health and authenticated upload return200/202. Android15 emulator was configured via the visible dialog; it uploaded a66116-byte report through the actual HTTPS tunnel, with model/APK identifying emulator evidence. vivo network delivery remains pending the user's setup. Screen rendering runtime evidence is recorded after inspection, separately from configuration/unit tests.

Runtime evidence: a signed preview13 test APK on Android15 emulator at 1280x1152 entered the existing TestHero save by a direct menu tap; a waypoint tap walked the player from 5389,4014 to 5397,4014 and opened WaypointsPanelExpansion. A potion-bar tap logged the fourth belt slot and RIGHT. Wide rendering had already reached camp at 1600x720. This does not establish vivo frame rate, physical fold transitions, or all inventory/combat gestures. Emulator host gfxstream can fail during replacement installs; subsequent clean-emulator streamed install succeeded.

Additional real gesture checks: tapping an inventory scroll positioned the cursor on that scroll and displayed its identification-scroll tooltip; tapping the Skills tab switched from inventory to the skill tree. Screenshots retained locally under /tmp/d2r-touch-item.png and /tmp/d2r-touch-tab.png. These establish selection and tab navigation, not complete item drag/use acceptance.
