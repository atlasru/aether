# Implementation status

Snapshot: 2026-10-17. **Not alpha-ready. No working Aether executable is verified.**

| Area | Current state |
|---|---|
| Upstream | Chromium 155.0.8059.84 / Helium 0.19.4.1 and matching platform revisions pinned |
| Native builds | Real Windows/Linux source preparation, GN and C/C++ compilation attempted on standard GitHub-hosted runners |
| Measured limits | Windows attempt 4 and Linux attempt 1 reached the configured 355-minute job limit with spare disk/RAM |
| Current work | Windows attempt 5 and Linux attempt 2 active; compatible successor jobs queued behind them |
| Incremental CI | Component builds, no symbols/PGO/ThinLTO; output cache, hash-gated input timestamps, pinned selected source SHA |
| Continuation | Bounded controller implemented; real dispatch/queue and guard tests passed; native cache checkpoint round trip still unverified |
| Identity | Independent profile/Windows registration patches; default-path and coexistence runtime tests pending |
| Layouts | Existing native Helium Compact/Classic/Vertical reused; Compact default; GUI validation pending |
| Setup | Six local WebUI steps, native preferences/theme/resource integration and recoverable journal implemented in source |
| Settings | Existing Chromium/Helium settings retained; reopen setup at aether://setup |
| Browser essentials | Inherited engine functionality; linked-browser smoke tests not yet reached |
| Workspaces / command palette / custom NTP / dashboard | Not implemented |
| Updates / signing / installer | Not implemented or produced; Helium update feed explicitly blocked |
| Browser benchmarks | Not run; no speed, battery or memory-efficiency claim |

Source CI [39074683593](https://github.com/atlasru/aether/actions/runs/39074683593)
passed 17 Python tests, 10 Node tests, compiled/executed C++20 policy checks
covering 1,296 configurations, real GRIT compilation and both exact patch jobs.
Earlier local checks covered the initial 11 Python tests and the real pinned
Siso/g++ cache-tool probe. These are not Chromium runtime tests.

Windows attempt 4 reached 27,092/70,804 operations (26,973 local) before GitHub
sent CTRL+C at its job time limit. Linux attempt 1 reached 33,275/65,046.
Aether-owned preferences/handler object compilation was not observed in those
partial logs, so its native C++ API integration remains unverified.
Full evidence: [HOSTED_BUILDS.md](HOSTED_BUILDS.md).

Active native runs:
* [Windows attempt 5](https://github.com/atlasru/aether/actions/runs/39073857721)
* [Linux attempt 2](https://github.com/atlasru/aether/actions/runs/39067527723)

Queued successors use the validated bounded controller:
* [Windows](https://github.com/atlasru/aether/actions/runs/39074702783)
* [Linux](https://github.com/atlasru/aether/actions/runs/39074703970)

The queued jobs preserve active compilation and wait for its output cache.
Automatic successors require a full compile window, newly recorded native object
progress and a registered nonempty cache. Ordinary compiler/test errors stop.
No saved cache, queued run or successful diagnostic job is a browser build pass.

## Remaining alpha gates

Link the Windows browser and validate the extracted executable/runtime archive.
Verify real navigation, setup/skip, theme/layout preference persistence, restart
and private browsing. Validate native Compact/Classic switching and tab/session
preservation, default profile isolation, content blocking, sandbox/site isolation,
downloads, extensions, media, high DPI, keyboard/screen reader and crash recovery.
Review redistributed licenses and installer/COM/service coexistence before an
installable alpha. Linux executable/desktop/package naming remains inherited
and needs finishing before a Linux release.
