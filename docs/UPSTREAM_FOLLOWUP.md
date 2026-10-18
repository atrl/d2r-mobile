# Upstream follow-up (2026-10-18)

See the [Chinese version](UPSTREAM_FOLLOWUP.zh-CN.md). Reviewed open upstream issues and PRs, including the full [Android performance discussion #59](https://github.com/jhaizhou-ops/d2r-mobile/issues/59).

- Submitted [PR #85](https://github.com/jhaizhou-ops/d2r-mobile/pull/85): exclude invalid slow-frame samples and avoid substituting CPU submission timing when presentation timestamps exist without intervals. Four synthetic-log tests pass. This is not an FPS optimization and does not close #59.
- Close-button targets #84 already have PR #82; update-service #79 has PR #80; minimap #49 has PR #61; potion pickup #9 has PR #83. Await upstream review instead of duplicating fixes or merging unverified changes.
- Android asynchronous translation remains disabled pending Vulkan fence, pause and folding-surface lifecycle validation followed by same-process A/B measurements. Metal queue assumptions cannot simply be transferred.
- Pass merging and attachment discard require same-queue sentinel clear/readback checks and deliberately failing counterexamples before optimization. A clean screenshot is insufficient.

Performance acceptance requires user-supplied game data and a Fold5: record device/OS/GPU, rendering resolution and scene level ID/coordinates; alternate A/B within one process and report paired differences and sign tests; warm up for at least five minutes and sample the final 30 seconds after thermal/frequency stabilization; measure actual presentation intervals and distinguish refresh rate from FPS; disable Vulkan validation layers during measurement. CI builds and synthetic tests do not satisfy these device requirements.

The existing weekly workflow continues to check upstream commits and open review PRs. It neither merges automatically nor fixes or replies to upstream issues automatically. This checklist records this investigation.
