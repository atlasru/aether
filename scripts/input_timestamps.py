"""Preserve timestamps of preparation-rewritten inputs across output-cache reuse.

File contents are never restored from a cache. Only byte-identical inputs get
their recorded mtime; changed inputs are marked fresh for Siso/Ninja.
SPDX-License-Identifier: GPL-3.0-only
"""
import hashlib
import json
import os
from pathlib import Path
import time

MARKER = ".aether-prepared-after-ns"
MANIFEST = "out/Default/.aether-input-times.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(source):
    path = source / MANIFEST
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not isinstance(data.get("files"), dict):
        raise ValueError("Unsupported source timestamp cache schema")
    for name, entry in data["files"].items():
        path = source / name
        if (not name or not Path(name).parts or "\\" in name or Path(name).is_absolute() or
                ".." in Path(name).parts or not path.resolve().is_relative_to(source.resolve()) or
                Path(name).parts[0] == "out" or
                any(part in (".git", ".aether-backup") for part in Path(name).parts) or
                Path(name).name.startswith(".aether-") or
                not isinstance(entry, dict) or
                type(entry.get("mtime_ns")) is not int or not 0 <= entry["mtime_ns"] < 2**63 or
                type(entry.get("size")) is not int or entry["size"] < 0 or
                not isinstance(entry.get("sha256"), str) or len(entry["sha256"]) != 64 or
                any(c not in "0123456789abcdef" for c in entry["sha256"])):
            raise ValueError(f"Invalid cached input timestamp: {name}")
    return data["files"]


def capture(source):
    previous = load(source)
    marker = source / MARKER
    # Old persistent developer trees have no marker: hash all inputs safely.
    cutoff = int(marker.read_text()) if marker.exists() else 0
    entries = {}
    for directory, folders, files in os.walk(source):
        folders[:] = [name for name in folders if name not in (".git", ".aether-backup")
                      and not (Path(directory) == source and name == "out")]
        for name in files:
            path = Path(directory) / name
            if path.is_symlink() or path.name == ".git" or path.name.startswith(".aether-"):
                continue
            relative = path.relative_to(source).as_posix()
            stat = path.stat()
            # Tarball inputs retain their original mtimes. Retain restored
            # entries too: their timestamps now predate this preparation.
            if stat.st_mtime_ns < cutoff and relative not in previous:
                continue
            digest = sha256(path)
            after = path.stat()
            if (stat.st_mtime_ns, stat.st_size) != (after.st_mtime_ns, after.st_size):
                raise RuntimeError(f"Input changed during cache capture: {relative}")
            entries[relative] = {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": digest}
    manifest = source / MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest.with_suffix(".tmp")
    temporary.write_text(json.dumps({"schema": 1, "files": entries}, separators=(",", ":")), encoding="utf-8")
    temporary.replace(manifest)
    return {"captured_inputs": len(entries), "manifest_bytes": manifest.stat().st_size}


def restore(source):
    restored = changed = missing = 0
    for name, entry in load(source).items():
        path = source / name
        if not path.is_file() or path.is_symlink():
            missing += 1
            continue
        stat = path.stat()
        if stat.st_size == entry["size"] and sha256(path) == entry["sha256"]:
            os.utime(path, ns=(stat.st_atime_ns, entry["mtime_ns"]))
            restored += 1
        else:
            # Even a patch that preserved the old mtime must rebuild.
            os.utime(path, ns=(stat.st_atime_ns, time.time_ns()))
            changed += 1
    return {"restored_inputs": restored, "changed_inputs": changed, "missing_inputs": missing}
