# Aether

A desktop browser fork built directly on Helium / Chromium. Windows x64 first;
Linux x64 secondary. Native Chromium Views remain the browser chrome.

**Development source, not a usable alpha yet. No Aether browser executable has
been compiled or launched.** Do not use this branch for daily browsing.

Implemented source includes an independent application/profile identity,
Compact as the default native layout, the inherited Classic and Vertical layouts,
six-step local setup, native theme/accent application, toolbar density, resource
settings and a recoverable preference journal. Runtime behavior awaits a full
Chromium build. There is no Aether auto-updater or signed release channel.

## Quick verification

Python 3.11+, Git, Node.js 22+ and a C++20 compiler:

```sh
python3 scripts/check.py
python3 scripts/bootstrap.py windows
python3 scripts/verify_patches.py windows --upstream .work/windows --destination .work/verify-win
python3 scripts/verify_patches.py linux --destination .work/verify-linux
```

Each verification destination must be new. These checks validate tooling,
configuration state and patch application; they do not compile Chromium.

## Windows build

Use a dedicated Windows x64 machine with Visual Studio 2022 Desktop development
with C++, the Windows SDK/components required by the pinned Chromium generation,
Python with `requests` and `Pillow`, Git and 7-Zip on PATH. Enable Windows long
paths. Reserve at least 120 GiB free disk and 16 GiB RAM for the project preflight;
32–64 GiB RAM and 250+ GiB disk are recommended. Peak requirements vary.

```powershell
python scripts/doctor.py --target windows --require-build
python scripts/build.py windows --work-dir D:\aether-build -j 12
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

Use the dependencies in the pinned `helium-linux/docker/Dockerfile` on a dedicated
Debian-based x64 host, as a regular user with a functioning Chromium sandbox.

```sh
python3 scripts/doctor.py --target linux --require-build
python3 scripts/build.py linux --work-dir /opt/aether-build -j 12
```

Linux compilation and packaging are not validated yet. See [DEVELOPMENT.md](DEVELOPMENT.md),
[ROADMAP.md](ROADMAP.md), [PERFORMANCE.md](PERFORMANCE.md) and [LICENSES.md](LICENSES.md).
