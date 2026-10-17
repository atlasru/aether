#!/usr/bin/env python3
"""Package only a real, smoke-tested Windows build; no stable publication.

Uses Chromium's own FILES.cfg rather than copying arbitrary build intermediates.
SPDX-License-Identifier: GPL-3.0-only
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

from common import ROOT, fingerprint, head, lock, run


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def package(platform_root, report_file, destination):
    if run(["git", "status", "--porcelain"], cwd=ROOT, capture=True).stdout.strip():
        raise RuntimeError("Commit all source before packaging a corresponding source archive")
    source = platform_root / "build/src"
    output = source / "out/Default"
    state = json.loads((source / ".aether-state.json").read_text())
    report = json.loads(report_file.read_text())
    if report.get("commit") != head(ROOT):
        raise RuntimeError("Smoke evidence belongs to another source commit")
    if state.get("status") != "applied" or report.get("result") != "passed" or \
       report.get("source_fingerprint") != fingerprint() or state["fingerprint"] != fingerprint():
        raise RuntimeError("Packaging requires a passing smoke report for the current source")
    for name, key in (("chrome.exe", "binary_sha256"), ("chromedriver.exe", "driver_sha256")):
        if report.get(key) != digest(output / name):
            raise RuntimeError(f"Binary changed after smoke testing: {name}")
    version = (ROOT / "VERSION").read_text().strip()
    destination.mkdir(parents=True, exist_ok=True)
    prefix = f"aether-{version}-windows-x64-alpha-untested-installer"
    # Refuse replacement so one package cannot inherit a stale smoke report.
    portable = destination / (prefix + ".zip")
    installer = destination / (prefix + "-mini-installer.exe")
    if portable.exists() or installer.exists():
        raise FileExistsError("Package destination already exists")
    sys.path.insert(0, str(platform_root / "helium-chromium/utils"))
    import filescfg
    exclusions = {Path(n) for n in ("mini_installer.exe", "setup.exe", "helium.packed.7z")}
    files = tuple(filescfg.filescfg_generator(source / "chrome/tools/build/win/FILES.cfg",
                                              output, "64bit", exclusions))
    if Path("chrome.exe") not in files:
        raise RuntimeError("Chromium FILES.cfg did not include the browser executable")
    filescfg.create_archive(iter(files), tuple(), output, portable, None)
    shutil.copy2(output / "mini_installer.exe", installer)
    # Source archive includes all committed Aether changes. Upstream pins,
    # scripts and notices are inside; upstream trees remain separately fetchable.
    archive = destination / f"aether-{version}-source.tar.gz"
    run(["git", "archive", "--format=tar.gz", "--output", archive, "HEAD"], cwd=ROOT)
    shutil.copy2(output / "args.gn", destination / "args.gn")
    shutil.copy2(report_file, destination / "smoke.json")
    shutil.copy2(ROOT / "LICENSE", destination / "LICENSE")
    provenance = {"commit": head(ROOT), "version": version, "upstream": lock(),
                  "source_fingerprint": fingerprint(), "browser_smoke": "passed",
                  "installer_runtime_test": "NOT RUN", "signed": False, "stable": False,
                  "files": {file.name: digest(file) for file in (portable, installer, archive)}}
    (destination / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    (destination / "SHA256SUMS").write_text("".join(f"{digest(p)}  {p.name}\n" for p in sorted(destination.iterdir())
                                                if p.is_file() and p.name != "SHA256SUMS"))
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True, type=Path)
    parser.add_argument("--smoke-report", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/packages")
    args = parser.parse_args()
    package(args.upstream.resolve(), args.smoke_report.resolve(), args.output.resolve())
