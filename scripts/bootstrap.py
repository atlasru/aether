#!/usr/bin/env python3
"""Fetch exact upstream revisions without vendoring Chromium. GPL-3.0-only."""
from __future__ import annotations

import argparse
from pathlib import Path

from common import ROOT, head, lock, run


def checkout(name: str, destination: Path) -> Path:
    spec = lock()["repositories"][name]
    if not (destination / ".git").exists():
        destination.mkdir(parents=True, exist_ok=True)
        run(["git", "init", destination])
        run(["git", "remote", "add", "origin", spec["url"]], cwd=destination)
    else:
        origin = run(["git", "remote", "get-url", "origin"], cwd=destination,
                     capture=True).stdout.strip()
        if origin != spec["url"]:
            raise RuntimeError(f"Unexpected origin for {destination}: {origin}")
        if run(["git", "status", "--porcelain", "--untracked-files=no"],
               cwd=destination, capture=True).stdout.strip():
            raise RuntimeError(f"Refusing to overwrite modified upstream: {destination}")
    run(["git", "fetch", "--depth=1", "origin", spec["revision"]], cwd=destination)
    run(["git", "checkout", "--detach", spec["revision"]], cwd=destination)
    if head(destination) != spec["revision"]:
        raise RuntimeError(f"Revision mismatch: {destination}")
    return destination


def bootstrap(platform: str, work: Path) -> Path:
    platform_tree = checkout(platform, work / platform)
    helium = checkout("helium", platform_tree / "helium-chromium")
    recorded = run(["git", "ls-tree", "HEAD", "helium-chromium"],
                   cwd=platform_tree, capture=True).stdout.split()[2]
    if recorded != head(helium):
        raise RuntimeError("Platform submodule differs from locked Helium revision")
    if (helium / "chromium_version.txt").read_text().strip() != lock()["chromium"]:
        raise RuntimeError("Locked Chromium version does not match upstream")
    return platform_tree


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=("windows", "linux"))
    parser.add_argument("--work-dir", type=Path, default=ROOT / ".work")
    args = parser.parse_args()
    print(bootstrap(args.platform, args.work_dir.resolve()))
