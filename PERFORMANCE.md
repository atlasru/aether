# Performance

**No Helium/Aether browser benchmarks have been run. No speed, RAM, battery or
restoration improvement is claimed.** No Adaptive Resource Manager or performance
dashboard has been added. Aether configures existing Chromium resource controls.

## Baseline protocol

Use the exact common/platform pins in `upstream.lock.json`. Build unmodified Helium
and Aether with the same compiler, architecture, optimization/PGO settings and
Chromium generation. Record GN args, revision hashes, OS build, CPU, RAM, storage,
GPU/driver, display scaling/refresh and power plan. Freeze extensions and their
versions, site corpus and network conditions; consent/service settings must match.

Use separate fresh profiles for first-run testing and cloned, identically seeded
profiles for steady-state workloads. Never point either browser at the other's
live profile. Complete setup before measurements. Randomize AB/BA order and run
at least 10 samples per condition; save raw values, median, p95 and range.

| Metric | Measurement |
|---|---|
| Cold startup | OS-cache-controlled launch → first visible, interactive window; label reboot/cache method |
| Warm startup | Same profile/cached files; fresh process → first interactive window |
| First navigation | Deterministic local corpus plus separately recorded real network sites |
| RAM at 1/5/20/50 tabs | Fixed settling period; process-tree private bytes/PSS where available; report RSS limitations |
| Idle CPU | Process tree CPU time over a 60 s quiet interval; repeat after backgrounding |
| Tab switching | Browser input → presented frame, not WebDriver request completion alone |
| Workspace switching | Not available; do not invent a number |
| Discard/restore | Eligible tab state, exclusion cases, restore-to-first-frame and usable time |
| UI stability | Chromium tracing/frame presentation; dropped frames and distribution |
| Battery | Controlled screen brightness/network, real unplugged hardware or power meter |

Keep active downloads, audio, video calls, capture, forms with unsaved changes,
and explicit exclusions in a protection workload. Record whether upstream
detects each case; Aether adds no stronger protection guarantee than Chromium.
No cache flush performed by a script should be described as a cold boot unless
that condition was actually achieved. Local fixture navigation is not a substitute
for a representative web workload.
