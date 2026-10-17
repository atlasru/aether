# Architecture

## Boundaries

`upstream.lock.json` fixes Chromium `155.0.8059.84`, Helium `0.19.4.1`,
and mutually consistent Windows/Linux platform revisions. Bootstrap verifies
both the platform's gitlink and the common Helium revision.

`patches/common` applies after the entire Helium patch series and platform patches.
Platform-only changes live in `patches/windows` and `patches/linux`. New code is
copied from `src/` into the prepared Chromium tree. Upstream checkouts stay unchanged.
Blink, V8, networking and sandbox source are outside the Aether patch layer.

## Native interface

The inspected Helium revision already has Classic, Compact, Vertical and Dynamic
layouts. Aether uses its `HeliumLayoutStateController` and `TabStripModel`, sets
Compact by default and exposes the first three choices in setup. Layout changes
write the existing native preference; no tabs or WebContents are reconstructed
by Aether. Session/navigation guarantees still require runtime validation.

Density is a per-profile integer observed by `ToolbarView`. Desktop toolbar
vertical padding is 6 DIP for Comfortable, 5 DIP for Compact. Touch UI keeps its
existing metrics. Aether does not globally replace Chromium's sizing system.

## Setup and preferences

The existing `chrome://setup` WebUI host, resource allocation and startup entry
are reused. The user-facing internal alias becomes `aether://`. Only three Aether
messages are registered: read state, save validated draft and apply validated
configuration. The old arbitrary Helium-pref setter/extension installer bridge
is absent from this page. Default Chromium CSP and Trusted Types remain enabled.

`src/chrome/browser/aether/config.h` is a small C++20 policy model, independently
compilable for range/schema tests. `preferences.cc` integrates real PrefService,
ThemeService and Chromium resource preferences. The frontend is static local
HTML/CSS/ES modules compiled into browser resources, with no npm build or network.

All setup state is one unsynced `aether.setup` dictionary. Drafts contain a schema
version, selections and a bounded step. Live browser preferences change only on
Finish or first-run Skip. Managed/unavailable settings reject before application.

Commit order is: persist pending configuration → apply native profile/global
preferences → flush global Local State → clear pending and mark completed in
profile Preferences → flush profile and acknowledge. Startup replays pending
transactions. Completed journals are not replayed, so later native settings
edits remain valid. A newer schema is read-only on downgrade. Disk write failure,
multi-profile races and abrupt power-loss behavior need native integration tests;
PrefService callbacks do not expose every filesystem failure as a success flag.

Memory/Battery Saver and freezing are browser-global in this Chromium version.
The UI states this explicitly. Aether does not create a second discard policy,
polling service or alternate tab lifecycle. Chromium activity protection and
site exclusions remain responsible for discard eligibility.

## Identity and updates

Windows uses `%LOCALAPPDATA%\Aether\User Data`, `AetherHTM`/`AetherPDF`, distinct
application/Active Setup, toast, elevation service/interface/type-library and
tracing service IDs. Linux uses `$XDG_CONFIG_HOME/io.github.atlasru.aether`
(or `~/.config/...`) plus upstream's `.dev` suffix for non-official builds.
Profiles are never imported or opened from Helium automatically.

The compiled Windows file remains `chrome.exe` for native installer compatibility.
Its product/icon metadata changes. Installer payload archive internals retain
their upstream names. WinSparkle is off and the shared update-service predicate
always rejects Aether requests. Signing and authenticated Aether updates are
unimplemented. Other optional Helium services retain upstream consent behavior.

## Hosted build control

The engine checkout and output remain outside this repository. Hosted jobs
prepare locked source before restoring out/Default. Compatibility keys bind the
image, absolute path, upstream pins and GN arguments; exact keys also bind source
fingerprints. Siso handles normal dependency/command invalidation. Hash-verified
input timestamp metadata avoids false cache misses from repeated preparation.

A build-only cursor in the output cache bounds checkpoint continuation. It is
separate from browser profiles and onboarding state. Explicit requests initialize
a bound; automatic pinned-source passes preserve it and stop on missing/invalid
state. Continuation requires observed new object history and a GitHub-registered
cache. Ordinary compiler failures stop. A step-scoped Actions token dispatches
successors after cache/evidence upload, without source-write or release rights.
The request job pins its selected SHA before queued browser jobs start.

Packaging verifies the applied Aether source state, excludes build-tool metadata,
includes license texts and records an archive checksum. Future browser smoke
checks execute the extracted distributable. A headless pass still does not verify
native layout geometry, default OS profile registration or an installer.
