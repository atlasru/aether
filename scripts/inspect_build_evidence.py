#!/usr/bin/env python3
"""Summarize real uploaded build evidence without executing artifact contents."""
import argparse
import json
import os
from pathlib import Path
import re
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--job-id", type=int, required=True)
args = parser.parse_args()
root = args.root.resolve()
log = next(root.rglob("build.log"))
directory = log.parent
lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
samples = []
for line in (directory / "resources.jsonl").read_text(encoding="utf-8").splitlines():
    try:
        samples.append(json.loads(line))
    except json.JSONDecodeError:
        pass
available = []
for sample in samples:
    text = sample.get("system", {}).get("output", "")
    match = re.search(r'"FreePhysicalMemory":\s*(\d+)', text)
    if not match:
        match = re.search(r"^MemAvailable:\s+(\d+) kB", text, re.M)
    if match:
        available.append(int(match[1]) * 1024)
request = urllib.request.Request(
    f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/check-runs/{args.job_id}/annotations",
    headers={"Accept": "application/vnd.github+json",
             "Authorization": "Bearer " + os.environ["AETHER_ACTIONS_TOKEN"]})
with urllib.request.urlopen(request, timeout=30) as response:
    annotations = json.load(response)
report = {
    "job_id": args.job_id,
    "annotations": annotations,
    "stages": [line for line in lines if re.search(
        r"Applied Aether|Made [0-9]+ targets|starting real|ninja: Entering", line)],
    "last_progress": [line for line in lines if re.match(r"\[\d+/\d+\]", line)][-1:],
    "errors": [line[:6000] for line in lines if re.search(
        r"\berror(?:\[[^\]]+\])?:|^FAILED:|fatal error|No space left|out of memory|Traceback|KeyboardInterrupt",
        line, re.I)][-20:],
    "failure_contexts": [[entry[:1800] for entry in lines[max(0, index-1):index+7]]
                         for index, value in enumerate(lines) if value.startswith("FAILED:")][-6:],
    "aether_objects": [line for line in lines if re.search(
        r"aether[/\\](?:aether[/\\])?preferences|aether_setup_handler", line)][-10:],
    "tail": lines[-24:],
    "resource_samples": len(samples),
    "minimum_free_disk_bytes": min(s["free_disk_bytes"] for s in samples),
    "minimum_available_memory_bytes": min(available) if available else None,
    "final_sample": samples[-1],
    "after_cleanup": json.loads((directory / "after-cleanup.json").read_text()),
}
destination = Path("dist/inspection")
destination.mkdir(parents=True, exist_ok=True)
(destination / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AETHER_EVIDENCE_REPORT=" + json.dumps(report, separators=(",", ":")))
