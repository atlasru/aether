# Development

Work on `dev` or `feature/*`. Fetch before committing/pushing. Keep `main` for
validated milestones; this source-only milestone is not an alpha release.

## Upstream inspection (2026-10-17)

Helium is a patchset, not a full Chromium checkout. `patches/series` orders common
patches; platform repos point to common Helium via `helium-chromium` gitlink.
Windows `build.py` downloads hash-checked archives/dependencies, prunes, applies
common then Windows patches, substitutes domains/names, adds translations/version
and resources, generates GN, and runs autoninja/Siso. `package.py` supports ZIP,
mini-installer and NSIS packaging. Linux `scripts/shared.sh` provides analogous
functions; `scripts/build.sh` deletes `out/`, so Aether calls the functions instead.

Helium's existing setup is a local WebUI with a separately downloaded Svelte
resource component. Aether replaces its resource build and message handler while
retaining the host/resource-ID/browser startup plumbing. The old downloaded
strings include remains because other upstream string targets reference it.

## Validation levels

1. `python3 scripts/check.py`: Python tooling tests, Node setup-state tests,
   compiled/executed portable C++ configuration tests and JS syntax checks.
2. `scripts/verify_patches.py`: download only touched original Chromium files;
   apply every relevant hunk from the FULL pinned common/platform series with
   zero fuzz; check/apply Aether patches. This is not full-tree preparation, GN,
   linking or runtime validation. Reports include baseline SHA-256 hashes.
   `scripts/verify_resources.py --download-grit` separately fetches Chromium's
   pinned GRIT Python dependency manifest/modules and builds a real `.pak` and
   resource map. It checks five URL paths, catching unusable WebUI mappings.
3. Full self-hosted build: prepare Chromium, overlay Aether, GN dependency checks,
   compile browser/driver/installer, then run browser smoke tests.
4. GUI/manual validation: native layouts at narrow widths, keyboard, screen
   reader, DPI, touch, sessions, crash recovery, extensions, downloads and installer.

The pinned Chromium tag resolves to commit
`5869fe313571d75152b77813cf0a4ee26a4e6df0`; sparse source/tool retrieval uses this
full SHA rather than a moving version tag. Full preparation retains upstream's
archive hashes and dependency configuration at the platform/common pins.

The manual build workflow exists on the default branch so it can be dispatched
without merging uncompiled browser code into `main`. It resolves `source_ref`
once in validation, then checks out that exact SHA for build, packaging and draft
release. Ordinary PRs never execute on the self-hosted build runner.

## Incremental source preparation

`AETHER_WORK_DIR` or `--work-dir` keeps upstream source, download cache and output
outside an ephemeral CI checkout. `scripts/apply.py` records touched-file backups
and post-apply hashes. `build.py --refresh` restores only known Aether changes
before reapplying. Unexpected manual changes abort. Preserve evidence if initial
upstream preparation or a filesystem write was interrupted; the driver refuses
to blindly rerun over an unstamped tree. Never delete a developer's source tree
automatically to work around a failed build.

## Updating the base

Select mutually consistent platform/common commits and update the lock. Review
upstream security changes, source archive/dependency hashes, licensing and flags.
Run sparse patch checks for both platforms. Refresh failing hunks against exact
post-Helium source; never use fuzzy application in CI. Rebuild on trusted Windows
hardware, run smoke/GUI tests and retain exact source/config hashes with artifacts.

Upstream's core flags include `safe_browsing_mode=0`. Aether does not silently
change this inherited policy and must not advertise Google Safe Browsing download
reputation protection. Sandbox/site isolation are not changed by Aether. The
download/safe-browsing baseline needs a deliberate product decision before alpha.
