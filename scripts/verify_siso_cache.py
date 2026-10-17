#!/usr/bin/env python3
"""Exercise real Siso incremental output restoration on a small C++ tool test.

This verifies build tooling only, never substitutes for a Chromium build.
Run on Linux with the pinned source tree's Siso and a local g++ or clang++.
SPDX-License-Identifier: GPL-3.0-only
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import time

import input_timestamps


def verify(siso, compiler):
    version = subprocess.check_output([str(siso), "version"], text=True)
    stages = []
    with tempfile.TemporaryDirectory(prefix="aether-siso-cache-") as directory:
        root = Path(directory)
        output = root / "out/Default"
        output.mkdir(parents=True)
        (root / input_timestamps.MARKER).write_text(str(time.time_ns()))
        (root / ".gn").write_text("")
        source = root / "main.cc"
        source.write_text('#include "value.h"\nint main() { return value(); }\n')
        header = root / "value.h"
        header.write_text("inline int value() { return 0; }\n")
        command = shlex.quote(compiler)
        (output / "build.ninja").write_text(
            "rule cxx\n  command = " + command + " -c $in -o $out -MMD -MF $out.d && echo cxx >> ../../commands.log\n"
            "  depfile = $out.d\n  deps = gcc\nrule link\n  command = " + command + " $in -o $out && echo link >> ../../commands.log\n"
            "build main.o: cxx ../../main.cc\nbuild probe: link main.o\ndefault probe\n")
        args = [str(siso), "ninja", "--offline", "--load=", "--local_jobs=1",
                "--quiet", "--heartbeat_period=1s", "--cache_dir=" + str(root / "cache"),
                "-C", str(output), "probe"]
        for phase in ("initial", "restored", "changed_header"):
            if phase == "restored":
                input_timestamps.capture(root)
                archive = root / "outputs.tar.gz"
                # actions/cache uses GNU tar POSIX archives. Preserve exact
                # nanosecond mtimes; Python tarfile's float mtimes can round.
                subprocess.run(["tar", "--posix", "-czf", str(archive), "-C", str(root / "out"), "Default"], check=True)
                shutil.rmtree(output)
                shutil.rmtree(root / "cache", ignore_errors=True)
                subprocess.run(["tar", "-xzf", str(archive), "-C", str(root / "out")], check=True)
                os.utime(source, None)
                os.utime(header, None)
                input_timestamps.restore(root)
            elif phase == "changed_header":
                header.write_text("inline int value() { return 7; }\n")
            log = root / "commands.log"
            before = len(log.read_text().splitlines()) if log.exists() else 0
            result = subprocess.run(args, cwd=root, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode:
                raise RuntimeError(result.stdout)
            # Fast no-op builds may retain the preceding metrics file. Count
            # actual compiler/linker invocations rather than stale diagnostics.
            local = len(log.read_text().splitlines()) - before
            code = subprocess.run([str(output / "probe")]).returncode
            expected = 7 if phase == "changed_header" else 0
            if code != expected or (phase == "restored" and local != 0) or (phase != "restored" and local < 2):
                raise RuntimeError(f"Unexpected {phase} result: exit={code}, local steps={local}")
            stages.append({"phase": phase, "siso_exit_code": result.returncode,
                           "local_steps": local, "program_exit_code": code})
    return {"scope": "Local Siso/g++ tooling probe; not Chromium or a GitHub cache-service test",
            "siso_version": version, "siso_sha256": hashlib.sha256(siso.read_bytes()).hexdigest(),
            "compiler": subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
            "stages": stages}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--siso", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.name != "posix":
        parser.error("This tooling probe currently requires Linux")
    compiler = shutil.which("g++") or shutil.which("clang++")
    if not compiler:
        parser.error("g++ or clang++ is required")
    report = verify(args.siso.resolve(), compiler)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
