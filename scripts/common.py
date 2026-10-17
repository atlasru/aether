"""Small, dependency-free shared build utilities. SPDX-License-Identifier: GPL-3.0-only"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def lock() -> dict:
    return json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))


def run(args, *, cwd=None, capture=False):
    return subprocess.run([str(x) for x in args], cwd=cwd, check=True,
                          text=True, encoding="utf-8",
                          stdout=subprocess.PIPE if capture else None)


def head(path: Path) -> str:
    return run(["git", "rev-parse", "HEAD"], cwd=path, capture=True).stdout.strip()


def fingerprint() -> str:
    digest = hashlib.sha256()
    for entry in [ROOT / "upstream.lock.json", ROOT / "VERSION"] + sorted(
            p for directory in ("patches", "src", "assets", "scripts")
            for p in (ROOT / directory).rglob("*") if p.is_file()
            and "__pycache__" not in p.parts):
        digest.update(entry.relative_to(ROOT).as_posix().encode())
        digest.update(entry.read_bytes())
    return digest.hexdigest()


def series(directory: Path):
    for line in (directory / "series").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            path = directory / line
            if not path.is_file() or not path.resolve().is_relative_to(directory.resolve()):
                raise ValueError(f"Invalid patch entry: {line}")
            yield path


def git_apply(source: Path, patch: Path, *, check=False):
    # Tarball builds have no .git. Prevent discovery of the outer Aether repo,
    # which would silently skip patches whose paths are outside its cwd prefix.
    env = dict(os.environ, GIT_CEILING_DIRECTORIES=str(source.resolve().parent))
    command = ["git", "apply"] + (["--check"] if check else []) + [str(patch)]
    subprocess.run(command, cwd=source, env=env, check=True)
