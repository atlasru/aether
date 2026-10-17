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


def inspect(target: str, directory: Path, minimum_disk_gib=120) -> dict:
    while not directory.exists() and directory.parent != directory:
        directory = directory.parent
    disk = shutil.disk_usage(directory)
    memory = None
    if hasattr(os, "sysconf"):
        memory = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    elif platform.system() == "Windows":
        import ctypes
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in
                ("physical", "available", "page_total", "page_available",
                 "virtual_total", "virtual_available", "extended")]
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            memory = status.physical
    blockers = []
    # Conservative project guardrails, not Chromium's universal minimums.
    if disk.free < minimum_disk_gib * 1024**3:
        blockers.append(f"At least {minimum_disk_gib} GiB free disk required by Aether build preflight")
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
