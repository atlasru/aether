#!/usr/bin/env python3
"""Build the real Chromium/Helium browser with Aether's separate patch layer.

The platform upstream checkouts remain unmodified. Build outputs are persistent.
SPDX-License-Identifier: GPL-3.0-only
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

from bootstrap import bootstrap
from common import ROOT, run
from doctor import inspect


class PreparationFinished(Exception):
    pass


def windows_module(root):
    spec = importlib.util.spec_from_file_location("helium_windows_build", root / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_windows(platform_root, source):
    module = windows_module(platform_root)
    original = module._configure_remoteexec
    def stop_after_preparation(tree):
        original(tree)
        raise PreparationFinished()
    module._configure_remoteexec = stop_after_preparation
    previous = sys.argv
    try:
        sys.argv = [str(platform_root / "build.py"), "--tarball"]
        try:
            module.main()
        except PreparationFinished:
            return
    finally:
        sys.argv = previous
    raise RuntimeError("Locked Windows preparation hook was not reached")


def prepare_linux(platform_root):
    # Source only the functions. The upstream build.sh removes out/ on every
    # invocation; keeping preparation separate preserves incremental builds.
    script = '''set -euo pipefail
source "$1/scripts/shared.sh"
setup_environment
fetch_sources false false
apply_patches
apply_domsub
helium_substitution
helium_apply_translations
helium_version
helium_resources
'''
    subprocess.run(["bash", "-c", script, "aether-prepare", str(platform_root)], check=True)


def gn_arguments(platform_root, target):
    arguments = {}
    for filename in (platform_root / "helium-chromium/flags.gn",
                     platform_root / ("flags.windows.gn" if target == "windows" else "flags.linux.gn")):
        for line in filename.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key, separator, value = line.partition("=")
                if not separator:
                    raise ValueError(f"Unsupported GN flag syntax: {line}")
                arguments[key.strip()] = value.strip()
    arguments.update(target_cpu='"x64"', is_debug="false", is_component_build="false",
                     is_official_build="true")
    if target == "windows":
        # No Helium signing identities or feed trust are inherited from env.
        arguments["enable_winsparkle"] = "false"
    if os.environ.get("SISO_REAPI_ADDRESS"):
        raise RuntimeError("Remote compilation needs a separately reviewed Aether runner configuration")
    if shutil_which("sccache"):
        arguments["cc_wrapper"] = '"sccache"'
    return "\n".join(f"{key} = {value}" for key, value in sorted(arguments.items())) + "\n"


def shutil_which(name):
    import shutil
    return shutil.which(name)


def build(target, work, *, prepare_only=False, refresh=False, jobs=None):
    preflight = inspect(target, work if work.exists() else ROOT)
    if not preflight["ready"]:
        print(json.dumps(preflight, indent=2))
        raise RuntimeError("Build preflight failed; source download and compilation were not started")
    work.mkdir(parents=True, exist_ok=True)
    platform_root = bootstrap(target, work)
    source = platform_root / "build/src"
    if not (source / ".aether-state.json").exists():
        if (source / "BUILD.gn").exists():
            raise RuntimeError(f"Unstamped Chromium source exists at {source}; inspect the failed preparation before retrying")
        if target == "windows":
            prepare_windows(platform_root, source)
        else:
            prepare_linux(platform_root)
    from apply import apply
    apply(source, target, platform_root, refresh=refresh)
    if prepare_only:
        return source

    output = source / "out/Default"
    output.mkdir(parents=True, exist_ok=True)
    content = gn_arguments(platform_root, target)
    args_file = output / "args.gn"
    if not args_file.exists() or args_file.read_text() != content:
        args_file.write_text(content, encoding="utf-8")
    if target == "windows":
        module = windows_module(platform_root)
        os.environ.setdefault("SISO_PATH", str(source / "third_party/siso/cipd/siso.exe"))
        os.chdir(source)
        module._run_build_process("buildtools\\win\\gn.exe", "gen", "out\\Default", "--fail-on-unused-args")
        command = [sys.executable, "third_party\\depot_tools\\autoninja.py", "-C", "out\\Default"]
        if jobs:
            command.extend(["-j", str(jobs)])
        module._run_build_process(*command, "chrome", "chromedriver", "setup", "mini_installer")
    else:
        run([source / "buildtools/linux64/gn", "gen", output, "--fail-on-unused-args"], cwd=source)
        os.environ.setdefault("SISO_PATH", str(source / "third_party/siso/cipd/siso"))
        command = [sys.executable, source / "third_party/depot_tools/autoninja.py", "-C", output]
        if jobs:
            command += ["-j", str(jobs)]
        run(command + ["chrome", "chromedriver"], cwd=source)
    return source


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=("windows", "linux"))
    parser.add_argument("--work-dir", type=Path,
                        default=Path(os.environ.get("AETHER_WORK_DIR", ROOT / ".work")))
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("-j", "--jobs", type=int)
    args = parser.parse_args()
    try:
        print(build(args.platform, args.work_dir.resolve(), prepare_only=args.prepare_only,
                    refresh=args.refresh, jobs=args.jobs))
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
