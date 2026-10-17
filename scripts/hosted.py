#!/usr/bin/env python3
"""Measure and execute a real build on an ephemeral GitHub-hosted VM.

Cleanup is restricted to known disposable image packages and hosted runners.
SPDX-License-Identifier: GPL-3.0-only
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from threading import Thread, Event
import time

from common import ROOT
from doctor import inspect


def configure_console():
    # Siso emits Unicode resource charts even when Windows defaults to cp1252.
    # A diagnostic must never abort the compiler's log stream.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def command(args):
    try:
        result = subprocess.run(args, text=True, encoding="utf-8", errors="replace",
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        return {"command": args, "exit_code": result.returncode, "output": result.stdout}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"command": args, "error": str(error)}


def select_path(target):
    if target == "windows":
        # Probe real volumes. The 20261007 VS2026 image provides a large D:
        # workspace disk; older images may only provide C:. Never assume either.
        candidates = [p for p in (Path("C:/"), Path("D:/")) if p.is_dir()]
        drive = max(candidates, key=lambda p: shutil.disk_usage(p).free)
        work = drive / "aether"
    else:
        work = Path(os.environ["RUNNER_TEMP"]) / "aether"
    with Path(os.environ["GITHUB_ENV"]).open("a", encoding="utf-8") as stream:
        stream.write(f"AETHER_WORK_DIR={work.as_posix()}\n")
    print(f"AETHER: selected {work} with {shutil.disk_usage(work.anchor or work.parent).free} free bytes", flush=True)


def snapshot(target, work):
    report = inspect(target, work)
    report.update(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  cpu_count=os.cpu_count(), runner_image=os.environ.get("ImageVersion"),
                  runner_os=os.environ.get("RUNNER_OS"))
    if os.name == "nt":
        report["system"] = command(["powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory | ConvertTo-Json; Get-Volume | Select-Object DriveLetter,FileSystem,Size,SizeRemaining | ConvertTo-Json"])
    else:
        report["system"] = command(["bash", "-c", "df -B1; free -b; lscpu; cat /proc/meminfo | head -8"])
    return report


def prepare(target, work):
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted":
        raise RuntimeError("Image cleanup is allowed only on ephemeral GitHub-hosted runners")
    evidence = ROOT / "dist/hosted"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "before-cleanup.json").write_text(json.dumps(snapshot(target, work), indent=2))
    if target == "windows":
        paths = [Path(x) for x in [r"C:\Android", r"C:\ghcup", r"C:\Program Files\Java",
                 r"C:\Program Files\dotnet", r"C:\Program Files\Android", r"C:\Miniconda",
                 r"C:\Program Files\PostgreSQL", r"C:\Program Files\Microsoft SDKs\Azure"]]
        cache = Path(os.environ.get("RUNNER_TOOL_CACHE", r"C:\hostedtoolcache\windows"))
        paths += [cache / name for name in ("Go", "Java_Temurin-Hotspot_jdk", "Ruby", "CodeQL")]
        tools = [command([r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe", "-all", "-format", "json"]),
                 command(["powershell", "-NoProfile", "-Command", r"Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\Include' | Select-Object Name | ConvertTo-Json"])]
    else:
        paths = [Path(x) for x in ["/usr/local/lib/android", "/opt/ghc", "/usr/share/dotnet",
                 "/usr/local/share/powershell", "/opt/az", "/usr/local/.ghcup",
                 "/opt/hostedtoolcache/CodeQL", "/opt/hostedtoolcache/Java_Temurin-Hotspot_jdk"]]
        tools = [command(["clang", "--version"]), command(["g++", "--version"]), command(["ldd", "--version"])]
        command(["sudo", "docker", "system", "prune", "-a", "-f", "--volumes"])
    cleanup = []
    for path in paths:
        if not path.exists():
            continue
        before = shutil.disk_usage(path).free
        print(f"AETHER: freeing disposable hosted-image package {path}", flush=True)
        if os.name == "nt":
            result = command(["cmd", "/c", "rmdir", "/s", "/q", str(path)])
        else:
            result = command(["sudo", "rm", "-rf", "--", str(path)])
        cleanup.append({"path": str(path), "free_before": before,
                        "free_after": shutil.disk_usage(work if work.exists() else ROOT).free,
                        "result": result})
    work.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        # Standard NTFS per-directory compression, inherited by new source/obj files.
        tools.append(command(["compact.exe", "/C", "/I", str(work)]))
        command(["git", "config", "--global", "core.longpaths", "true"])
    (evidence / "toolchains.json").write_text(json.dumps(tools, indent=2))
    (evidence / "cleanup.json").write_text(json.dumps(cleanup, indent=2))
    after = snapshot(target, work)
    (evidence / "after-cleanup.json").write_text(json.dumps(after, indent=2))
    print(json.dumps(after, indent=2), flush=True)


def build(target, work, jobs):
    configure_console()
    evidence = ROOT / "dist/hosted"
    evidence.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, "-u", str(ROOT / "scripts/build.py"), target,
            "--work-dir", str(work), "--attempt", "--low-resource", "--browser-only", "-j", str(jobs)]
    start = time.monotonic()
    stop = Event()
    def monitor():
        with (evidence / "resources.jsonl").open("a", encoding="utf-8") as stream:
            while not stop.is_set():
                sample = snapshot(target, work)
                stream.write(json.dumps(sample) + "\n")
                stream.flush()
                print(f"AETHER RESOURCE: elapsed={time.monotonic()-start:.1f}s free_bytes={sample['free_disk_bytes']}", flush=True)
                stop.wait(30)
    thread = Thread(target=monitor, daemon=True)
    thread.start()
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding="utf-8", errors="replace", bufsize=1)
    try:
        with (evidence / "build.log").open("w", encoding="utf-8") as stream:
            for line in process.stdout:
                stream.write(line)
                stream.flush()
                print(line, end="", flush=True)
        result = process.wait()
    finally:
        stop.set()
        thread.join(timeout=5)
    report = {"command": args, "exit_code": result, "elapsed_seconds": time.monotonic()-start,
              "final": snapshot(target, work), "scope": "Actual upstream source preparation, GN and Chromium compilation attempt"}
    (evidence / "result.json").write_text(json.dumps(report, indent=2))
    source = work / target / "build/src"
    for name in ("args.gn", ".ninja_log", ".ninja_deps"):
        path = source / "out/Default" / name
        if path.is_file() and path.stat().st_size < 64 * 1024**2:
            shutil.copy2(path, evidence / name.lstrip("."))
    print(json.dumps(report, indent=2), flush=True)
    return result


if __name__ == "__main__":
    configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("select-path", "prepare", "build"))
    parser.add_argument("platform", choices=("windows", "linux"))
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("-j", "--jobs", type=int, default=2)
    args = parser.parse_args()
    if args.action == "select-path":
        select_path(args.platform)
        sys.exit(0)
    if args.work_dir is None:
        parser.error("--work-dir is required for prepare/build")
    if args.action == "prepare":
        prepare(args.platform, args.work_dir.resolve())
    else:
        sys.exit(build(args.platform, args.work_dir.resolve(), args.jobs))
