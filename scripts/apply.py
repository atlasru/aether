#!/usr/bin/env python3
"""Apply only Aether-owned changes to a fully prepared, locked Helium tree.

Backups permit incremental Aether rebuilds without downloading Chromium again.
SPDX-License-Identifier: GPL-3.0-only
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from common import ROOT, fingerprint, git_apply, head, lock, run, series
from verify_patches import blocks


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(source: Path, platform: str, platform_root: Path, *, refresh=False,
          strings=True, resources=True):
    version = dict(line.split("=", 1) for line in (source / "chrome/VERSION").read_text().splitlines() if "=" in line)
    actual = ".".join(version[key] for key in ("MAJOR", "MINOR", "BUILD", "PATCH"))
    if actual != lock()["chromium"]:
        raise RuntimeError(f"Expected Chromium {lock()['chromium']}, found {actual}")
    for name, path in ((platform, platform_root), ("helium", platform_root / "helium-chromium")):
        if head(path) != lock()["repositories"][name]["revision"]:
            raise RuntimeError(f"Unexpected {name} revision")
    stamp = source / ".aether-state.json"
    backup = source / ".aether-backup"
    if stamp.exists():
        state = json.loads(stamp.read_text())
        for name, entry in state["files"].items():
            path = source / name
            if not path.is_file() or digest(path) != entry["after"]:
                raise RuntimeError(f"Aether source was edited outside the patch layer: {name}")
        if state["fingerprint"] == fingerprint() and state.get("status") == "applied":
            print("Aether source matches the current patch layer.")
            return
        if not refresh:
            raise RuntimeError("Aether patches changed or application was interrupted; rerun with --refresh")
        for name, entry in state["files"].items():
            path = source / name
            if entry["existed"]:
                shutil.copyfile(backup / name, path)
            else:
                path.unlink()
        stamp.unlink()
        shutil.rmtree(backup)
    if backup.exists():
        raise RuntimeError(f"Unfinished unjournaled backup exists: {backup}")

    state = {"status": "applying", "fingerprint": fingerprint(), "files": {}}
    def save():
        # Atomic metadata replacement; do not leave a truncated recovery record.
        tmp = stamp.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        tmp.replace(stamp)

    def remember(path):
        name = path.relative_to(source).as_posix()
        if name in state["files"]:
            return
        existed = path.is_file()
        if existed:
            copy = backup / name
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, copy)
        state["files"][name] = {"existed": existed, "after": digest(path) if existed else None}
        save()

    def write(path, content):
        remember(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        state["files"][path.relative_to(source).as_posix()]["after"] = digest(path)
        save()

    try:
        for directory in (ROOT / "patches/common", ROOT / f"patches/{platform}"):
            for patch in series(directory):
                git_apply(source, patch, check=True)
                names = [name for name, _, _ in blocks(patch.read_text())]
                for name in names:
                    remember(source / name)
                git_apply(source, patch)
                for name in names:
                    state["files"][name]["after"] = digest(source / name)
                save()
        for path in (ROOT / "src").rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                write(source / path.relative_to(ROOT / "src"), path.read_bytes())
        write(source / "components/helium_onboarding/aether.svg", (ROOT / "assets/aether.svg").read_bytes())
        # Preserve Chromium's generation while using Helium's existing product
        # version resource plumbing for Aether's independent version.
        product_version = (ROOT / "VERSION").read_text().strip().split(".")
        if len(product_version) != 4 or not all(part.isdecimal() for part in product_version):
            raise ValueError("VERSION must contain four decimal components")
        lines = []
        product = dict(zip(("HELIUM_MAJOR", "HELIUM_MINOR", "HELIUM_PATCH", "HELIUM_PLATFORM"), product_version))
        for line in (source / "chrome/VERSION").read_text().splitlines():
            key = line.partition("=")[0]
            lines.append(f"{key}={product.pop(key)}" if key in product else line)
        lines += [f"{key}={value}" for key, value in product.items()]
        write(source / "chrome/VERSION", ("\n".join(lines) + "\n").encode())
        import branding
        if resources:
            branding.install(source, platform_root, write)
        if strings:
            branding.rebrand_strings(source, platform_root, write)
        state["status"] = "applied"
        save()
    except Exception:
        # All writes above are backed up. Keep the record to diagnose/recover;
        # do not pretend a partially applied tree is ready to compile.
        save()
        raise
    print(f"Applied Aether: {len(state['files'])} files, {state['fingerprint']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=("windows", "linux"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    apply(args.source.resolve(), args.platform, args.upstream.resolve(), refresh=args.refresh)
