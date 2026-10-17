"""Tests for build isolation and resource integration, not Chromium execution."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from common import git_apply, lock, series
from verify_patches import blocks


class ToolingTest(unittest.TestCase):
    def test_pins_are_full_and_platforms_have_patch_series(self):
        for entry in lock()["repositories"].values():
            self.assertRegex(entry["revision"], r"^[0-9a-f]{40}$")
            self.assertTrue(entry["url"].startswith("https://github.com/imputnet/"))
        for platform in ("common", "windows", "linux"):
            paths = list(series(ROOT / "patches" / platform))
            self.assertTrue(paths)
            for patch in paths:
                self.assertTrue(list(blocks(patch.read_text())))

    def test_no_engine_or_sandbox_modifications(self):
        for directory in (ROOT / "patches").iterdir():
            for patch in series(directory):
                for name, _, _ in blocks(patch.read_text()):
                    self.assertFalse(name.startswith(("v8/", "third_party/blink/", "sandbox/", "net/")))

    def test_git_apply_works_in_tarball_nested_under_another_git_repo(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", root], check=True)
            source = root / ".work/build/src"
            source.mkdir(parents=True)
            (source / "file.txt").write_text("before\n")
            patch = root / "change.patch"
            patch.write_text("--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-before\n+after\n")
            git_apply(source, patch, check=True)
            git_apply(source, patch)
            self.assertEqual((source / "file.txt").read_text(), "after\n")
            self.assertFalse((root / "file.txt").exists())

    def test_grit_resources_have_local_paths_and_stable_index(self):
        path = ROOT / "src/components/helium_onboarding/generate_grd.py"
        spec = importlib.util.spec_from_file_location("generate_grd", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "resources.grd"
            module.generate(output)
            tree = ET.parse(output)
            includes = tree.findall(".//include")
            outputs = tree.findall("./outputs/output")
            self.assertTrue(any(entry.get("type") == "resource_file_map_source" for entry in outputs))
            self.assertEqual(len(includes), 5)
            self.assertEqual(includes[0].get("name"), "IDR_HELIUM_ONBOARDING_INDEX_HTML")
            for entry in includes:
                self.assertTrue((path.parent / entry.get("file")).is_file() or entry.get("file") == "aether.svg")
                self.assertNotIn("://", entry.get("file"))


if __name__ == "__main__":
    unittest.main()
