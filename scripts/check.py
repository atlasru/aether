#!/usr/bin/env python3
"""Run lightweight checks without pretending they compile Chromium."""
from pathlib import Path
import compileall
import shutil
import subprocess
import sys

from common import ROOT, run

if not compileall.compile_dir(ROOT / "scripts", quiet=1):
    sys.exit(1)
run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], cwd=ROOT)
run(["node", "--test", "tests/setup_state.test.mjs"], cwd=ROOT)
for path in (ROOT / "src/components/helium_onboarding").glob("*.js"):
    subprocess.run(["node", "--input-type=module", "--check"],
                   input=path.read_text(), text=True, check=True)
compiler = shutil.which("g++") or shutil.which("clang++")
if not compiler:
    raise RuntimeError("C++20 compiler required to run native configuration tests")
output = ROOT / ".work/tests/config_test"
output.parent.mkdir(parents=True, exist_ok=True)
run([compiler, "-std=c++20", "-Wall", "-Wextra", "-Werror", "-pedantic", "-I", ROOT / "src",
     ROOT / "tests/config_test.cc", "-o", output], cwd=ROOT)
run([output], cwd=ROOT)
print("PASS: repository tooling, setup state and portable C++ policy. Chromium integration remains separate.")
