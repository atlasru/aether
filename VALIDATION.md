# Validation — 2026-10-17

**No Aether browser executable or installer was produced.
The browser acceptance criteria are not met.**

| Check | Observed result | Scope |
|---|---|---|
| Python tooling tests | 9 passed | Pins, patch scope, resources, actual spawn/encoding regression, compatible output-cache identity and hash-gated input metadata |
| Node setup-state tests | 10 passed | Defaults, recovery/back, schema downgrade, malformed values, preset independence, interrupted reconfiguration |
| Native portable policy | Compiled with g++ C++20, warnings as errors; executed successfully | 1,296 supported combinations plus invalid range/schema rejection; not Chromium C++ integration |
| Windows patches | Passed | 17 touched files reconstructed from pinned Chromium and every relevant common/Windows hunk; zero fuzz |
| Linux patches | Passed | 16 touched files reconstructed from pinned Chromium and every relevant common/Linux hunk; zero fuzz |
| Real GRIT resources | Passed | Real Chromium GRIT generated a v5 `.pak` with 5 local resources and a usable URL map |
| Name substitution | Passed | Real GRIT message fingerprint recalculation; recovery backups excluded |
| Source overlay lifecycle | Passed | Actual sparse patch/overlay application, independent version injection, refresh, idempotence and external-edit rejection; icons/string bulk stage tested separately |
| Branding raster generation | Passed | Seven local PNG sizes: 16/24/32/48/64/128/256 px, transparent corners |
| Hosted GitHub Actions | Passed, 3/3 jobs | Tooling/configuration + real GRIT, exact Windows patches, exact Linux patches |
| Local Windows build preflight | Failed as expected | Linux host; about 30 GiB free disk and 9.7 GiB RAM; no Windows/VS/SDK |
| Full hosted Windows/Linux build attempts | Windows attempt 4 running; Linux attempt 1 reached configured job time limit | Actual Chromium compilation, not sparse validation |
| Windows SDK installation | Passed on actual runner | Pinned SHA-256, Microsoft Authenticode, exit 0, required SDK files, Debugging Tools 10.0.28000.2526 |
| Windows Chromium GN | Passed on actual Windows runner | 35,610 targets / 5,000 files; --fail-on-unused-args |
| Windows native C++ compilation | Attempt 3 failed after 1,889 operations; corrected attempt 4 log reaches 19,590 operations | Clang PCH fix active; full result pending |
| Linux Chromium GN | Passed on actual runner | 35,794 targets / 5,027 files; 10,856 ms |
| Linux native C++ compilation | Configured 355-minute job limit; log reaches 33,275/65,046 operations | No compiler/linker error found; no linked browser; measured disk and RAM remain available |
| Local Siso cache tooling | Passed with pinned v1.6.1 and actual g++ | 2 initial compiler/linker calls, 0 after hash/mtime-verified restore, 2 after changing a dependent header; not Chromium or GitHub cache-service verification |
| Browser link/smoke | Not reached on Windows | No executable or browser smoke pass confirmed |
| Browser/installer/GUI/security validation | Not run | Native layout, downloads, extension compatibility, sandbox runtime, OS registration, DPI, accessibility and crash injection remain open |
| Performance benchmarks | Not run | No browser comparison or performance claim |

GRIT verification caught a wrong resource-map output type: symbolic IDs would
have been exposed as paths instead of `setup.js`/`setup.css`. The generator now
uses `resource_file_map_source`; the emitted paths and packed entry count were
checked with the real pinned tool. This fixes source integration, not proof that
the browser executable launches.

The first source milestone was published to `dev` at
`4e20a33dc40d5f5385d48236b3e4dcf28c56e50d`. Later commits contain CI, recovery
hardening and this evidence. Remote branch heads must be verified after each push.
The main branch contains only the project entry point, license and manual build
workflow, so uncompiled browser source is not presented as stable.

Exact per-file baseline/patch hashes and resource compilation evidence are in
`docs/validation/2026-10-17/`. CI uploads fresh reports for the checked commit.
Observed GitHub run: [Validate source #1](https://github.com/atlasru/aether/actions/runs/39040530229),
commit `63906e7e9b62b8713491fd87d97f323754304bed`, completed successfully.
All three jobs and their resource/artifact upload steps were inspected. These
source checks are separate from the real browser build attempts now launched:
[attempt 1 Windows/Linux](https://github.com/atlasru/aether/actions/runs/39041366048),
[attempt 2 Windows](https://github.com/atlasru/aether/actions/runs/39043691087),
and [attempt 3 Windows](https://github.com/atlasru/aether/actions/runs/39044290753).
Windows attempt 1 failed in Python spawn imports before GN; fixed in the driver.
Attempt 2 was cancelled after its early SDK diagnostic showed 26100 instead of
Chromium's pinned 28000. Attempt 3 installed the SDK, passed GN, then exposed a
Clang PCH error. Corrected [Windows attempt 4](https://github.com/atlasru/aether/actions/runs/39047759315)
continues. Linux attempt 1 reached the configured 355-minute job cap after actual
native compilation. A new Linux request enables four workers and resumable
output caching. Latest reviewed source CI: [39065460460](https://github.com/atlasru/aether/actions/runs/39065460460)
at `fbe8383a38d0ee91279947fd4dd0675fefd83e81`, all three jobs passed.
[HOSTED_BUILDS.md](HOSTED_BUILDS.md) records
measurements and durable evidence. No working executable is claimed yet.
