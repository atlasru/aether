#!/usr/bin/env python3
"""Build real .pak / C++ resource maps with the pinned Chromium GRIT tool.

This validates embedded setup resources, not the browser executable.
SPDX-License-Identifier: GPL-3.0-only
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import struct
import sys
import tempfile
import urllib.request

from common import ROOT, lock, run


def fetch_grit():
    revision = lock()["chromium_revision"]
    root = ROOT / ".cache/grit" / revision
    prefix = f"https://raw.githubusercontent.com/chromium/chromium/{revision}/"
    manifest = root / "tools/grit/grit.pydeps"
    if not manifest.exists():
        with urllib.request.urlopen(prefix + "tools/grit/grit.pydeps", timeout=60) as response:
            data = response.read()
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_bytes(data)
    paths = []
    for line in manifest.read_text().splitlines():
        if not line.startswith("//tools/grit/"):
            continue
        name = line[2:]
        if ".." in PurePosixPath(name).parts:
            raise ValueError("Unsafe GRIT manifest path")
        paths.append(name)
    def download(name):
        target = root / name
        if not target.exists():
            with urllib.request.urlopen(prefix + name, timeout=60) as response:
                data = response.read()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(download, paths))
    return root / "tools/grit"


def verify(grit_root: Path, output: Path):
    ROOT.joinpath(".work").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="resources-", dir=ROOT / ".work") as temp:
        temp = Path(temp)
        component = temp / "component"
        shutil.copytree(ROOT / "src/components/helium_onboarding", component,
                        ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(ROOT / "assets/aether.svg", component / "aether.svg")
        run([sys.executable, component / "generate_grd.py", temp / "resources.grd"])
        run([sys.executable, grit_root / "grit.py", "-i", temp / "resources.grd", "build", "-o", temp / "generated"])
        generated = temp / "generated"
        mapping = (generated / "grit/helium_onboarding_generated_map.cc").read_text()
        paths = ["index.html", "setup.css", "setup.js", "state.mjs", "aether.svg"]
        for path in paths:
            if f'{{"{path}",' not in mapping:
                raise RuntimeError(f"Embedded WebUI resource is not routable: {path}")
        data = (generated / "helium_onboarding_generated.pak").read_bytes()
        if struct.unpack_from("<I", data)[0] != 5:
            raise RuntimeError("Unexpected GRIT data-pack format")
        sys.path.insert(0, str(grit_root))
        from grit.format import data_pack
        pack = data_pack.ReadDataPack(generated / "helium_onboarding_generated.pak")
        if len(pack.resources) != len(paths):
            raise RuntimeError("Unexpected number of packed WebUI resources")
        report = {"result": "passed", "scope": "Actual Chromium GRIT resource compilation; browser not compiled",
                  "chromium_revision": lock()["chromium_revision"], "paths": paths,
                  "pak_bytes": len(data), "pak_sha256": hashlib.sha256(data).hexdigest(),
                  "resource_map_sha256": hashlib.sha256(mapping.encode()).hexdigest()}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--grit-root", type=Path, help="Pinned Chromium's tools/grit directory")
    choice.add_argument("--download-grit", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / ".work/resource-evidence.json")
    args = parser.parse_args()
    verify(fetch_grit() if args.download_grit else args.grit_root.resolve(), args.output.resolve())
