#!/usr/bin/env python3
"""Report actual build capacity; never download a Chromium tree on an undersized host."""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path

from common import ROOT


def inspect(target: str, directory: Path) -> dict:
    disk = shutil.disk_usage(directory)
    memory = None
    if hasattr(os, "sysconf"):
        memory = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    blockers = []
    # Conservative project guardrails, not Chromium's universal minimums.
    if disk.free < 120 * 1024**3:
        blockers.append("At least 120 GiB free disk required by Aether build preflight")
    if memory is not None and memory < 16 * 1024**3:
        blockers.append("At least 16 GiB RAM required by Aether build preflight")
    if target == "windows" and platform.system() != "Windows":
        blockers.append("Windows x64 build requires Windows and Visual Studio 2022 C++ / Windows SDK")
    if target == "linux" and platform.system() != "Linux":
        blockers.append("Linux build requires a Linux host")
    return {"host": platform.platform(), "target": target,
            "free_disk_bytes": disk.free, "physical_memory_bytes": memory,
            "tools": {name: shutil.which(name) for name in
                      ("git", "python3", "patch", "clang++", "g++", "ninja", "docker")},
            "blockers": blockers, "ready": not blockers}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("windows", "linux"), default="windows")
    parser.add_argument("--require-build", action="store_true")
    parser.add_argument("--directory", type=Path, default=ROOT)
    args = parser.parse_args()
    result = inspect(args.target, args.directory)
    print(json.dumps(result, indent=2))
    sys.exit(1 if args.require_build and not result["ready"] else 0)
