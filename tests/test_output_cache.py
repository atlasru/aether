"""Reject incompatible native output caches; this does not compile Chromium."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import common
import hosted


class OutputCacheTest(unittest.TestCase):
    def test_cache_tracks_source_flags_image_and_absolute_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("scripts", "src", "patches", "assets"):
                (root / name).mkdir()
            (root / "upstream.lock.json").write_text("{}")
            (root / "VERSION").write_text("0.1.0.0")
            code = root / "src/source.cc"
            code.write_text("int value = 1;")
            work = root / "work"
            platform = work / "linux"
            (platform / "helium-chromium").mkdir(parents=True)
            (platform / "helium-chromium/flags.gn").write_text("")
            flags = platform / "flags.linux.gn"
            flags.write_text("use_sysroot = true\n")

            def identity():
                hosted.cache_info("linux", work)
                return json.loads((root / "dist/hosted/output-cache.json").read_text())

            with patch.object(common, "ROOT", root), patch.object(hosted, "ROOT", root), \
                 patch.dict(os.environ, {"ImageVersion": "image-a", "GITHUB_OUTPUT": str(root / "outputs")}), \
                 contextlib.redirect_stdout(io.StringIO()):
                initial = identity()
                output = platform / "build/src/out/Default/test.o"
                output.parent.mkdir(parents=True)
                output.write_bytes(b"compiled output fixture")
                measured = identity()
                self.assertEqual(initial["cache_prefix"], measured["cache_prefix"])
                self.assertEqual(measured["output_files"], 1)
                self.assertEqual(measured["output_logical_bytes"], output.stat().st_size)
                code.write_text("int value = 2;")
                self.assertNotEqual(initial["cache_prefix"], identity()["cache_prefix"])
                code.write_text("int value = 1;")
                flags.write_text("use_sysroot = false\n")
                self.assertNotEqual(initial["cache_prefix"], identity()["cache_prefix"])
                flags.write_text("use_sysroot = true\n")
                with patch.dict(os.environ, {"ImageVersion": "image-b"}):
                    self.assertNotEqual(initial["cache_prefix"], identity()["cache_prefix"])
                # The generated source root is absolute and part of identity.
                moved = root / "moved"
                work.rename(moved)
                hosted.cache_info("linux", moved)
                changed = json.loads((root / "dist/hosted/output-cache.json").read_text())
                self.assertNotEqual(initial["cache_prefix"], changed["cache_prefix"])
                with patch.dict(os.environ, {"ImageVersion": ""}):
                    with self.assertRaisesRegex(RuntimeError, "ImageVersion"):
                        hosted.cache_info("linux", moved)


if __name__ == "__main__":
    unittest.main()
