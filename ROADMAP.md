# Implementation status

Status on 2026-10-17. **Not alpha-ready. No compiled Aether browser.**

| Area | Current state |
|---|---|
| Repository investigation | Completed for locked common/Windows/Linux sources |
| Base/build reproducibility | Pinned bootstrap and real upstream build driver implemented; full build untested |
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

Full Chromium build is blocked in the current Linux workspace by approximately
30 GiB available storage, 9.7 GiB RAM and absent Windows/VS/SDK tooling. Source
and lightweight integration work continue independently of that blocker.
