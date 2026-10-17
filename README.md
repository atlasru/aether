# Aether

A desktop browser fork built directly on Helium / Chromium. Windows x64 first;
Linux x64 secondary. Native Chromium Views remain the browser chrome.

**Development source, not a usable alpha yet. No working Aether executable has
been verified.** Do not use this branch for daily browsing.

Implemented source includes an independent application/profile identity,
Compact as the default native layout, the inherited Classic and Vertical layouts,
six-step local setup, native theme/accent application, toolbar density, resource
settings and a recoverable preference journal. Runtime behavior awaits a full
Chromium build. There is no Aether auto-updater or signed release channel.

## Quick verification

Python 3.11+, Git, Node.js 22+ and a C++20 compiler:

```sh
python3 scripts/check.py
python3 scripts/verify_resources.py --download-grit
python3 scripts/bootstrap.py windows
python3 scripts/verify_patches.py windows --upstream .work/windows --destination .work/verify-win
python3 scripts/verify_patches.py linux --destination .work/verify-linux
```

Each verification destination must be new. These checks validate tooling,
configuration state and patch application; they do not compile Chromium.

## Windows build

Use a dedicated Windows x64 machine with Visual Studio 2026 (18.0+) Desktop development
with C++ and MFC/ATL, Windows SDK 10.0.28000.2270 and Debugging Tools
10.0.26100.3323+ required by the pinned Chromium revision,
Python with `requests` and `Pillow`, Git and 7-Zip on PATH. Enable Windows long
paths. Reserve at least 120 GiB free disk and 16 GiB RAM for the project preflight;
32–64 GiB RAM and 250+ GiB disk are recommended. Peak requirements vary.

```powershell
python scripts/doctor.py --target windows --require-build
python -m pip install -r requirements-build.txt
python scripts/build.py windows --work-dir D:\aether-build -j 12
python scripts/smoke.py --source D:\aether-build\windows\build\src --output dist\smoke.json
python scripts/package.py --upstream D:\aether-build\windows --smoke-report dist\smoke.json
```

The real browser output is `D:\aether-build\windows\build\src\out\Default\chrome.exe`.
`chrome.exe` is Chromium's internal binary name; its compiled product identity,
icon and installer identity are Aether. Do not rename it independently of the
installer. Source pins live in [upstream.lock.json](upstream.lock.json).

The build driver uses the locked upstream preparation pipeline, applies Aether
after Helium, and keeps `out/` for incremental builds. After changing Aether
patches, pass `--refresh`. It refuses to overwrite unexpected source edits.
No Chromium source, dependency downloads or binaries are checked into this repo.

## Linux build

Use the dependencies in the pinned `helium-linux/docker/build.Dockerfile` on a dedicated
Debian-based x64 host, as a regular user with a functioning Chromium sandbox.

```sh
python3 scripts/doctor.py --target linux --require-build
python3 scripts/build.py linux --work-dir /opt/aether-build -j 12
```

Linux compilation and packaging are not validated yet. See [DEVELOPMENT.md](DEVELOPMENT.md),
[ROADMAP.md](ROADMAP.md), [PERFORMANCE.md](PERFORMANCE.md) and [LICENSES.md](LICENSES.md).

## CI

[Source checks](https://github.com/atlasru/aether/actions/workflows/validate.yml)
run on pushes/PRs: portable tests, actual GRIT resource compilation and exact
Windows/Linux sparse patch checks. [Compile Aether browser](https://github.com/atlasru/aether/actions/workflows/build.yml)
uses GitHub-hosted `windows-2025-vs2026` and `ubuntu-24.04` runners. A push changing
`ci/build-request.json` on `dev` starts its selected Windows/Linux platforms. Manual dispatch can select a
platform. The dev definition also has an existing larger-runner label input;
API dispatch input registration must be synchronized before relying on extra fields. Full Chromium compilation runs,
regardless of the advisory preflight's disk/RAM warnings (`--attempt`).

The hosted configuration uses release component builds, zero debug symbols,
no PGO/ThinLTO and four concurrent compiler jobs. It omits installer targets and
preserves browser features and the sandbox. Before/after runner measurements,
periodic resource samples, build logs and GN arguments upload even on failure.
Successful compilation archives the executable with component runtime files,
then runs real browser smoke tests from the extracted archive. Runtime artifacts alone do not imply that
smoke tests passed. No stable release is automatically published.

Verified scope and exact limitations: [VALIDATION.md](VALIDATION.md).

Full native attempts have now demonstrated the configured 355-minute execution
limit with spare disk/RAM: Windows 27,092/70,804 operations and Linux
33,275/65,046. Cached retries are active. Successors are queued and a bounded
controller can continue verified native checkpoints without treating partial
compilation as success. End-to-end native cache continuation and the executable
remain unverified. See [HOSTED_BUILDS.md](HOSTED_BUILDS.md) for exact evidence.
