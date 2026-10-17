# Implementation status

Status on 2026-10-17. **Not alpha-ready. No compiled Aether browser.**

| Area | Current state |
|---|---|
| Repository investigation | Completed for locked common/Windows/Linux sources |
| Base/build reproducibility | Pinned bootstrap and real upstream build driver implemented; actual hosted Windows/Linux build attempts underway; executable not yet verified |
| Identity/profiles | Source patches for Windows and Linux; runtime coexistence untested |
| Original branding | SVG/native vector/raster build generation; OS appearance untested |
| Compact/Classic/Vertical | Existing Helium native implementations reused; Compact default patched; Aether runtime untested |
| Local onboarding | Six real UI steps, bounded model, draft persistence, native message handler and preference application implemented in source |
| Themes/accent/density | Native integration source; browser compile/GUI tests pending |
| Resource profiles | Existing Chromium settings wired; no custom discard scheduler |
| Browser essentials | Inherited from Helium; navigation/download/extension/session smoke tests pending |
| Settings | Existing Chromium/Helium settings retained; reopen setup at `aether://setup`; no new category system |
| Workspaces | Not implemented |
| Command palette | Not implemented |
| Original new-tab page | Not implemented; upstream page retained |
| Performance dashboard | Not implemented |
| Benchmarks | Methodology only; no measurements |
| Auto-updates/signing | Not implemented; Helium update fetch explicitly blocked |
| Windows executable/installer | Not produced |
| Linux executable/package | Not produced |
| CI | Hosted Windows/Linux full build driver running; Windows spawn defect fixed; SDK 28000 install verified on Windows; native browser result pending. Source checks remain separate. |

Local checks passed: 11 Python tooling tests, 10 Node setup-state tests, compiled
C++20 policy checks covering 1,296 supported configurations, Windows/Linux exact
patch application, actual GRIT `.pak`/URL-map compilation, and source-overlay
refresh/idempotence/manual-edit protection. These are not browser runtime tests.
Linux profile isolation is patched; Linux executable/desktop/package naming is
still inherited and requires finishing before a Linux release.

## Alpha gates still open

Compile and link the browser on Windows x64; fix GN/API integration errors. Run
actual navigation, setup/skip, policy handling, persistence and restart tests.
Validate native Compact/Classic and their switching without WebContents/session
loss. Verify sandbox/site isolation, content-blocking filters, private windows,
downloads, extensions, media/calls and excluded tabs. Check high DPI, narrow
windows, keyboard/screen reader and reduced motion. Verify separate profiles and
installer/COM/service coexistence with installed Helium and Chromium. Review
inherited download-reputation policy and every redistributed asset license.
Only then produce and test an explicitly labeled alpha package.

Actual builds run on standard GitHub-hosted runners. Windows attempt 1 failed in
upstream name-substitution worker imports before GN; the driver is fixed and a
spawn regression passes. Measured D: free space is 236 GB, so no Windows disk
exhaustion is claimed. Attempt 2 was superseded after observing only SDK 26100.
Attempt 3 installed hash/signature-verified SDK 28000 successfully. It completed source preparation, overlay and GN, then executed
1,889/82,373 native build operations before a Clang PCH/module error. Attempt 4
disables PCH and fixes a secondary cp1252 logging crash. Its available log reaches
19,590 native operations without those errors; the final result remains pending.
Compatible out/Default caching and bounded compile windows are implemented for
future hosted attempts, including hash-gated input timestamp restoration. A local
real Siso/g++ probe verifies unchanged output reuse and dependent-header rebuild;
GitHub native-browser cache save/restore remains unverified. Linux attempt 1
reached its configured 355-minute job limit at 33,275/65,046 native operations.
Its 705 samples demonstrate spare disk/RAM, not exhaustion. A four-worker cached
Linux retry is requested; Windows attempt 4 remains independent. No compiled
browser executable or runtime smoke success is yet confirmed.
Future builds smoke-test the extracted runtime archive and record its checksum;
archive IO/path checks are local tooling tests, not native-browser smoke passes.
See [HOSTED_BUILDS.md](HOSTED_BUILDS.md) for measurements, run links and exact scope.

Windows attempt 4 has now reached the configured 355-minute job limit:
27,092/70,804 operations, 26,973 local. 604 samples show at least 193.7 GiB
free disk and 7.25 GiB available physical RAM. Four running commands were
interrupted; no separate compiler diagnostic was found. Windows attempt 5 is
requested with resumable outputs and extracted-bundle smoke validation.
Linux retry 39067527723 remains running. Neither platform has a verified browser
executable yet. Detailed immutable run/artifact links are in HOSTED_BUILDS.md.

Bounded native checkpoint continuation is implemented: only time-bounded
compilation with newly recorded object progress and a registered output cache
can dispatch another pinned-source pass (maximum four continuations). Compiler
errors stop. New guard tests and the queued dispatch are awaiting CI verification;
a cache-driven end-to-end native continuation is not yet verified.
