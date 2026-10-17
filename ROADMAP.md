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

Local checks passed: 5 Python tooling tests, 10 Node setup-state tests, compiled
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
Attempt 3 installs hash/signature-verified SDK 28000 successfully and continues
full preparation/GN/compilation. Linux attempt 1 also continues. Windows attempt 3 completed source preparation, overlay and GN, then executed
1,889/82,373 native build operations before a Clang PCH/module error. Attempt 4
disables PCH and fixes a secondary cp1252 logging crash. No hosted hard resource
failure, compiled executable or runtime smoke success is yet confirmed.
See [HOSTED_BUILDS.md](HOSTED_BUILDS.md) for measurements, run links and exact scope.
