#!/usr/bin/env python3
"""Archive a compiled component browser and its runtime, excluding object files.
SPDX-License-Identifier: GPL-3.0-only
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import zipfile
from common import ROOT, head, lock, fingerprint


def package(source, target, destination):
    state = json.loads((source / ".aether-state.json").read_text())
    if state.get("status") != "applied" or state.get("fingerprint") != fingerprint():
        raise RuntimeError("Refusing to label a different source tree as Aether")
    output = source / "out/Default"
    browser = output / ("chrome.exe" if target == "windows" else "helium")
    if not browser.is_file():
        raise FileNotFoundError(browser)
    destination.mkdir(parents=True, exist_ok=True)
    selected = []
    notices = {"LICENSE": ROOT / "LICENSE", "LICENSES.md": ROOT / "LICENSES.md",
               "CHROMIUM_LICENSE": source / "LICENSE",
               "HELIUM_LICENSE": source.parents[1] / "helium-chromium/LICENSE"}
    for path in notices.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    for path in output.iterdir():
        if path.name.startswith("siso") or path.name == "compile_commands.json":
            continue
        if path.is_file() and (path.name in {browser.name, "chrome_sandbox", "chrome-sandbox", "chromedriver"}
            or path.suffix in {".dll", ".exe", ".pak", ".dat", ".bin", ".json"}
            or ".so" in path.name):
            selected.append(path)
        elif path.is_dir() and path.name in {"locales", "resources", "swiftshader", "WidevineCdm", "MEIPreload"}:
            selected.extend(file for file in path.rglob("*") if file.is_file())
    prefix = "aether-component-" + target + "-x64"
    archive = destination / (prefix + (".zip" if target == "windows" else ".tar.gz"))
    if target == "windows":
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as stream:
            for path in selected:
                stream.write(path, prefix + "/" + path.relative_to(output).as_posix())
            for name, path in notices.items():
                stream.write(path, prefix + "/" + name)
    else:
        with tarfile.open(archive, "w:gz", compresslevel=6, dereference=True) as stream:
            for path in selected:
                stream.add(path, prefix + "/" + path.relative_to(output).as_posix(), recursive=False)
            for name, path in notices.items():
                stream.add(path, prefix + "/" + name, recursive=False)
    with archive.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    report = {"commit": head(ROOT), "upstream": lock(), "source_fingerprint": fingerprint(),
              "browser": browser.name, "runtime_files": len(selected),
              "notice_files": list(notices),
              "archive": archive.name, "archive_sha256": checksum,
              "archive_bytes": archive.stat().st_size, "installer": False,
              "status": "compiled; see separate smoke report for runtime validation"}
    (destination / "runtime.json").write_text(json.dumps(report, indent=2))
    shutil.copy2(ROOT / "LICENSE", destination / "LICENSE")
    shutil.copy2(ROOT / "LICENSES.md", destination / "LICENSES.md")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=("windows", "linux"))
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/runtime")
    args = parser.parse_args()
    package(args.source.resolve(), args.platform, args.output.resolve())
