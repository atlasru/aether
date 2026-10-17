#!/usr/bin/env python3
"""Continue a time-bounded native build only after real object/cache progress.

Ordinary compiler/test errors never trigger an automatic retry.
SPDX-License-Identifier: GPL-3.0-only
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.parse
import urllib.request

MAX_CONTINUATIONS = 4
COMPILE_WINDOW_SECONDS = 240 * 60

def eligible(*, elapsed, result_exists, native_started, new_objects, cache_bytes, count):
    return (0 <= count < MAX_CONTINUATIONS and
            elapsed >= COMPILE_WINDOW_SECONDS - 30 and not result_exists and
            native_started and new_objects > 0 and cache_bytes > 0)

def recent_native_objects(path, started):
    if not path.is_file():
        return 0
    cutoff = int((started - 60) * 1000000000)
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split("\t")
        if len(fields) < 4 or not fields[3].endswith((".obj", ".o")):
            continue
        try:
            count += int(fields[2]) >= cutoff
        except ValueError:
            continue
    return count

def api(path, body=None):
    headers = {"Accept": "application/vnd.github+json",
               "Authorization": "Bearer " + os.environ["AETHER_ACTIONS_TOKEN"]}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    request = urllib.request.Request("https://api.github.com/repos/" +
        os.environ["GITHUB_REPOSITORY"] + path, headers=headers, data=data,
        method="POST" if body is not None else "GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
        return json.loads(data) if data else None

def dispatch(platform, count, runner_label=""):
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if not re.fullmatch("[0-9a-f]{40}", source):
        raise ValueError("A pinned source commit is required")
    for attempt in range(12):
        query = urllib.parse.urlencode({"head_sha": source, "per_page": 30})
        runs = api("/actions/runs?" + query)["workflow_runs"]
        checks = [run for run in runs if run["head_sha"] == source and run["name"] == "Validate source"]
        if checks and checks[0]["status"] == "completed":
            if checks[0]["conclusion"] != "success":
                raise RuntimeError("Source CI failed; native dispatch not sent")
            break
        if attempt == 11:
            raise RuntimeError("Source CI is not yet verified; native dispatch not sent")
        time.sleep(5)
    api("/actions/workflows/build.yml/dispatches", {
        "ref": "dev", "inputs": {"source_ref": source, "platform": platform,
        "runner_label": runner_label, "queue_after_current": True,
        "continuation": count}})
    print(json.dumps({"dispatch_accepted": True, "source_ref": source,
                      "platform": platform, "continuation": count}))

def resume(platform, count, key, runner_label):
    jobs = api("/actions/runs/" + os.environ["GITHUB_RUN_ID"] + "/jobs")["jobs"]
    job = next(job for job in jobs if job["name"] == f"Real Chromium build ({platform})")
    step = next(step for step in job["steps"] if step["name"] == "Actually generate GN and compile Chromium")
    start = datetime.datetime.fromisoformat(step["started_at"].replace("Z", "+00:00")).timestamp()
    end = datetime.datetime.fromisoformat(step["completed_at"].replace("Z", "+00:00")).timestamp()
    evidence = Path("dist/hosted")
    log = evidence / "build.log"
    native_started = log.is_file() and "AETHER: starting real" in log.read_text(encoding="utf-8", errors="replace")
    progress = recent_native_objects(evidence / "ninja_log", start)
    base = dict(elapsed=end-start, result_exists=(evidence / "result.json").exists(),
                native_started=native_started, new_objects=progress, count=count)
    if not eligible(**base, cache_bytes=1):
        print(json.dumps({"continuation_skipped": "not a native checkpoint window", **base}))
        return
    cache_bytes = 0
    for attempt in range(6):
        query = urllib.parse.urlencode({"key": key, "ref": os.environ["GITHUB_REF"]})
        entries = api("/actions/caches?" + query)["actions_caches"]
        cache_bytes = next((entry["size_in_bytes"] for entry in entries if entry["key"] == key), 0)
        if cache_bytes:
            break
        if attempt < 5:
            time.sleep(5)
    if not eligible(**base, cache_bytes=cache_bytes):
        print(json.dumps({"continuation_skipped": "no registered nonempty output cache", **base}))
        return
    dispatch(platform, count + 1, runner_label)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("windows", "linux", "both"), required=True)
    parser.add_argument("--count", type=int, default=0)
    parser.add_argument("--queue", action="store_true", help="Explicitly queue the next authorized native build")
    parser.add_argument("--cache-key", default="")
    parser.add_argument("--runner-label", default="")
    args = parser.parse_args()
    if not 0 <= args.count <= MAX_CONTINUATIONS:
        parser.error("continuation must be between zero and four")
    if args.queue:
        dispatch(args.platform, args.count, args.runner_label)
    elif args.platform == "both":
        parser.error("checkpoint continuation requires one platform")
    else:
        resume(args.platform, args.count, args.cache_key, args.runner_label)
