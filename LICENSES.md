# Licenses and attribution

Aether-original code and assets in this repository are GPL-3.0-only.
See `LICENSE`. Original Aether icon/wordmark geometry is project-authored. System
fonts are referenced by family name, never bundled or downloaded.

Helium common and Windows unique code/patches are GPL-3.0; their README files
explicitly retain the original licenses of imported material. The Linux repository
also declares GPL-3.0 for its unique material. Existing notices are preserved in
patch contexts and copied source. Aether does not submit these changes upstream.

Imported ungoogled-chromium material retains BSD-3-Clause; see
`licenses/LICENSE.ungoogled_chromium`. Chromium and its large dependency tree have
their own BSD/other licenses; their source notices and generated credits must
accompany a distribution. This repository intentionally does not vendor the engine.

The locked dependency set includes GPL-3.0 uBlock Origin 1.75.0 from Helium's fork,
its separately licensed filter assets, and `helium-nonfree-assets` search-engine
data. The name of a repository is not a license grant. Search-data and filter
asset redistribution terms require an explicit review before binary release.
The inspected `helium-nonfree-assets/nonfree/COPYRIGHT` explicitly says its notice
does not grant downstream rights to the logos/marks. Aether's replacement setup
uses none of those onboarding logos; native search-engine logos remain upstream.
Proprietary codec/patent and optional DRM availability also depend on platform
and distribution terms; compilation flags do not grant redistribution rights.

Distribution must make the corresponding modified source, patch ordering,
build scripts, base/dependency versions and GPL notices available to recipients.
Do not offer only a binary with an unrelated upstream-source link. Keep source
release archives/commit identity together with the exact build configuration.
Installation information/source obligations depend on the distribution context.
No assertion is made that an unbuilt source tree has passed a complete binary
license audit. No signed/stable binaries are published by this milestone.

Upstreams: https://github.com/imputnet/helium,
https://github.com/imputnet/helium-windows,
https://github.com/imputnet/helium-linux,
https://www.chromium.org/ and https://github.com/ungoogled-software/ungoogled-chromium.
