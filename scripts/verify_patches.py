#!/usr/bin/env python3
"""Verify Aether patches against exact Chromium files plus ALL applicable upstream hunks.

This is a sparse source integration check, not a Chromium compilation.
SPDX-License-Identifier: GPL-3.0-only
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.error
import urllib.request

from bootstrap import bootstrap
from common import ROOT, git_apply, lock, run, series


def blocks(text: str):
    starts = list(re.finditer(r"^--- (?:a/[^\n]+|/dev/null)\n\+\+\+ (?:b/[^\n]+|/dev/null)\n", text, re.M))
    for i, match in enumerate(starts):
        block = text[match.start():starts[i + 1].start() if i + 1 < len(starts) else len(text)]
        before, after = block.splitlines()[:2]
        name = (after[6:] if after != "+++ /dev/null" else before[6:]).split("\t")[0]
        yield name, before == "--- /dev/null", block


def upstream_blocks(platform_root: Path):
    for directory in (platform_root / "helium-chromium/patches", platform_root / "patches"):
        for patch in series(directory):
            yield patch, list(blocks(patch.read_text(encoding="utf-8")))


def prepare(platform: str, platform_root: Path, destination: Path, paths=None):
    own = list(series(ROOT / "patches/common")) + list(series(ROOT / f"patches/{platform}"))
    if paths is None:
        paths = {name for patch in own for name, created, _ in blocks(patch.read_text()) if not created}
    upstream = list(upstream_blocks(platform_root))
    created = {name for _, entries in upstream for name, new, _ in entries if new}
    destination.mkdir(parents=True, exist_ok=True)

    def download(name):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://raw.githubusercontent.com/chromium/chromium/{lock()['chromium']}/{name}"
        cache = ROOT / ".cache/chromium" / lock()["chromium"] / name
        if not cache.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(data)
        shutil.copyfile(cache, target)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(download, sorted(paths - created)))
    for patch, entries in upstream:
        selected = "".join(block for name, _, block in entries if name in paths)
        if selected:
            result = subprocess.run(["patch", "--batch", "--forward", "--fuzz=0", "-p1"],
                                    input=selected, text=True, encoding="utf-8", cwd=destination,
                                    capture_output=True)
            if result.returncode:
                raise RuntimeError(f"Upstream integration failed: {patch}\n{result.stdout}\n{result.stderr}")
    return own, paths


def verify(platform, platform_root, destination):
    if destination.exists():
        raise FileExistsError(f"Use a new fixture directory: {destination}")
    own, paths = prepare(platform, platform_root, destination)
    baseline = {name: hashlib.sha256((destination / name).read_bytes()).hexdigest()
                for name in sorted(paths)}
    for patch in own:
        git_apply(destination, patch, check=True)
        git_apply(destination, patch)
    report = {"scope": "Sparse patch application only; no GN, C++ browser compilation or runtime validation",
              "platform": platform, "upstream": lock(), "baseline_sha256": baseline,
              "patches": [str(p.relative_to(ROOT)) for p in own], "result": "passed"}
    (destination / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=("windows", "linux"))
    parser.add_argument("--upstream", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    upstream = args.upstream or bootstrap(args.platform, ROOT / ".work/upstream")
    verify(args.platform, upstream.resolve(), args.destination.resolve())
