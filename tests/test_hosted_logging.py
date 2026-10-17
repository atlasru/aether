"""Regression for the real Windows cp1252 logger crash in hosted attempt 3."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HostedLoggingTest(unittest.TestCase):
    def test_unicode_compiler_diagnostics_survive_legacy_console_encoding(self):
        message = "compiler resource chart: ▸ → █"
        code = ("import sys; sys.path.insert(0, " + repr(str(ROOT / "scripts")) +
                "); from hosted import configure_console; configure_console(); print(" +
                repr(message) + ")")
        environment = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
        result = subprocess.run([sys.executable, "-c", code], env=environment,
                                capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertIn(message, result.stdout.decode("utf-8"))
