# Validation — 2026-10-17

**Source milestone only. No Aether browser executable or installer was produced.
The browser acceptance criteria are not met.**

| Check | Observed result | Scope |
|---|---|---|
| Python tooling tests | 4 passed | Pins, patch scope, nested-tarball patching, resource manifest |
| Node setup-state tests | 10 passed | Defaults, recovery/back, schema downgrade, malformed values, preset independence, interrupted reconfiguration |
| Native portable policy | Compiled with g++ C++20, warnings as errors; executed successfully | 1,296 supported combinations plus invalid range/schema rejection; not Chromium C++ integration |
| Windows patches | Passed | 17 touched files reconstructed from pinned Chromium and every relevant common/Windows hunk; zero fuzz |
| Linux patches | Passed | 16 touched files reconstructed from pinned Chromium and every relevant common/Linux hunk; zero fuzz |
| Real GRIT resources | Passed | Real Chromium GRIT generated a v5 `.pak` with 5 local resources and a usable URL map |
| Name substitution | Passed | Real GRIT message fingerprint recalculation; recovery backups excluded |
| Source overlay lifecycle | Passed | Actual sparse patch/overlay application, independent version injection, refresh, idempotence and external-edit rejection; icons/string bulk stage tested separately |
| Branding raster generation | Passed | Seven local PNG sizes: 16/24/32/48/64/128/256 px, transparent corners |
| Workflow YAML | Parsed locally | GitHub execution results are separate |
| Windows build preflight | Failed as expected | Linux host; about 30 GiB free disk and 9.7 GiB RAM; no Windows/VS/SDK |
| Chromium GN/link/browser smoke | Not run | No complete source/build environment |
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
The repository's first CI run will be inspected after the workflow commit; no
successful CI run is implied by merely adding a workflow.
