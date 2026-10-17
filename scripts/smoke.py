#!/usr/bin/env python3
"""Exercise an ACTUAL compiled Aether binary through its compiled ChromeDriver.

No mock navigation or sandbox-disabling switches. Requires a usable sandbox and
a regular user on Linux. Headless checks do not validate native chrome geometry.
SPDX-License-Identifier: GPL-3.0-only
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
from threading import Thread
import time
import urllib.error
import urllib.request

from common import ROOT, fingerprint, head, lock


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class Fixture(BaseHTTPRequestHandler):
    def do_GET(self):
        title = "AETHER_SECOND_PAGE" if self.path == "/two" else "AETHER_NAVIGATION_OK"
        data = f"<!doctype html><title>{title}</title><h1>{title}</h1><script>document.body.dataset.script='executed'</script>".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def log_message(self, *args):
        pass


class Driver:
    def __init__(self, executable, binary):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]
        self.log = tempfile.TemporaryFile(mode="w+")
        self.process = subprocess.Popen([str(executable), f"--port={self.port}", "--allowed-ips=127.0.0.1"],
                                        stdout=self.log, stderr=subprocess.STDOUT)
        self.binary = binary
        self.session = None
        self.http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            self.wait(lambda: self.request("GET", "/status"), timeout=20)
        except Exception:
            self.close()
            raise

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data,
            method=method, headers={"Content-Type": "application/json"})
        try:
            with self.http.open(request, timeout=45) as response:
                value = json.load(response)["value"]
        except urllib.error.HTTPError as exc:
            raise RuntimeError(exc.read().decode("utf-8", "replace")) from exc
        if isinstance(value, dict) and "error" in value:
            raise RuntimeError(json.dumps(value))
        return value

    def wait(self, condition, timeout=20):
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.log.seek(0)
                raise RuntimeError("ChromeDriver exited: " + self.log.read())
            try:
                result = condition()
                if result:
                    return result
            except (urllib.error.URLError, RuntimeError) as error:
                last = error
            time.sleep(.1)
        raise TimeoutError(f"Browser condition timed out: {last}")

    def start(self, profile, *, incognito=False):
        args = ["--headless=new", f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check"]
        if incognito:
            args.append("--incognito")
        result = self.request("POST", "/session", {"capabilities": {"alwaysMatch": {
            "browserName": "chrome", "goog:chromeOptions": {"binary": str(self.binary), "args": args}}}})
        self.session = result["sessionId"]
        return result["capabilities"]

    def command(self, method, path, body=None):
        return self.request(method, f"/session/{self.session}{path}", body)
    def execute(self, script):
        return self.command("POST", "/execute/sync", {"script": script, "args": []})
    def navigate(self, url):
        return self.command("POST", "/url", {"url": url})
    def stop(self):
        if self.session:
            try:
                self.command("DELETE", "")
            finally:
                self.session = None
    def close(self):
        try:
            self.stop()
        finally:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.log.close()


def click(driver, selector):
    driver.execute(f"document.querySelector({json.dumps(selector)}).click()")


def setup(driver, *, skip=False):
    driver.navigate("chrome://setup/")
    driver.wait(lambda: driver.execute("return document.querySelector('#shell')?.getAttribute('aria-busy') === 'false'"))
    if skip:
        click(driver, "#skip")
    else:
        click(driver, "#next")
        click(driver, "input[name=layout][value='0']")
        click(driver, "#next")
        click(driver, "input[name=experience][value='2']")
        click(driver, "#next")
        click(driver, "input[name=appearance][value='2']")
        click(driver, "input[name=density][value='1']")
        click(driver, "#next")
        click(driver, "#next")
        click(driver, "#next")
    driver.wait(lambda: driver.command("GET", "/url").startswith(("chrome://newtab", "aether://newtab")))


def perform(source: Path, output: Path):
    state = json.loads((source / ".aether-state.json").read_text())
    if state.get("status") != "applied" or state["fingerprint"] != fingerprint():
        raise RuntimeError("Build source does not match this Aether checkout")
    if os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() == 0:
        raise RuntimeError("Run Linux browser smoke tests as a regular user with its sandbox intact")
    directory = source / "out/Default"
    binary = directory / ("chrome.exe" if os.name == "nt" else "helium")
    driver_binary = directory / ("chromedriver.exe" if os.name == "nt" else "chromedriver")
    for file in (binary, driver_binary):
        if not file.is_file():
            raise FileNotFoundError(file)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    driver = Driver(driver_binary, binary)
    passed = []
    try:
        with tempfile.TemporaryDirectory(prefix="aether-smoke-") as temp:
            profile = Path(temp) / "regular"
            capabilities = driver.start(profile)
            driver.navigate(base + "/one")
            assert driver.command("GET", "/title") == "AETHER_NAVIGATION_OK"
            assert driver.execute("return document.body.dataset.script") == "executed"
            driver.navigate(base + "/two")
            assert driver.command("GET", "/title") == "AETHER_SECOND_PAGE"
            driver.command("POST", "/back", {})
            assert driver.command("GET", "/title") == "AETHER_NAVIGATION_OK"
            driver.command("POST", "/forward", {})
            assert driver.command("GET", "/title") == "AETHER_SECOND_PAGE"
            driver.command("POST", "/refresh", {})
            passed += ["real HTTP navigation", "renderer JavaScript", "back/forward/reload"]
            handles = driver.command("GET", "/window/handles")
            second = driver.command("POST", "/window/new", {"type": "tab"})
            driver.command("POST", "/window", {"handle": second["handle"]})
            driver.navigate(base + "/one")
            driver.command("DELETE", "/window")
            driver.command("POST", "/window", {"handle": handles[0]})
            assert len(driver.command("GET", "/window/handles")) == len(handles)
            passed.append("create/navigate/close tab")
            setup(driver)
            driver.stop()
            stored = json.loads((profile / "Default/Preferences").read_text())
            journal = stored["aether"]["setup"]
            assert journal["completed"] and not journal["pending"]
            assert journal["config"]["layout"] == 0
            assert journal["config"]["appearance"] == 2
            assert journal["config"]["density"] == 1
            assert stored["helium"]["browser"]["layout"] == 0
            passed += ["six-step setup and native preference bridge", "on-disk configuration"]
            driver.start(profile)
            driver.navigate("chrome://setup/")
            driver.wait(lambda: driver.execute("return document.querySelector('#shell')?.getAttribute('aria-busy') === 'false'"))
            assert driver.execute("return document.querySelector('input[name=layout][value=\"0\"]').checked")
            assert driver.execute("return document.querySelector('input[name=appearance][value=\"2\"]').checked")
            driver.stop()
            passed.append("restart/reopen persistence")
            skipped = Path(temp) / "skipped"
            driver.start(skipped)
            setup(driver, skip=True)
            driver.stop()
            skipped_state = json.loads((skipped / "Default/Preferences").read_text())["aether"]["setup"]
            assert skipped_state["completed"] and skipped_state["config"]["layout"] == 1
            passed.append("skip setup with safe defaults")
            driver.start(Path(temp) / "private", incognito=True)
            driver.navigate(base + "/one")
            assert driver.command("GET", "/title") == "AETHER_NAVIGATION_OK"
            driver.stop()
            passed.append("private navigation")
        report = {"result": "passed", "commit": head(ROOT), "source_fingerprint": fingerprint(),
                  "binary_sha256": digest(binary), "driver_sha256": digest(driver_binary),
                  "upstream": lock(), "capabilities": capabilities, "checks": passed,
                  "limits": "Headless smoke only. No GUI layout, OS installer, download security, extension, crash-injection or public-network validation."}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        driver.close()
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/smoke.json")
    args = parser.parse_args()
    perform(args.source.resolve(), args.output.resolve())
