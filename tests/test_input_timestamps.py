"""Exercise hash-gated source metadata restoration used by native output caches."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import input_timestamps as timestamps


class InputTimestampsTest(unittest.TestCase):
    def test_unchanged_inputs_restore_but_changed_bytes_force_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cutoff = time.time_ns()
            (root / timestamps.MARKER).write_text(str(cutoff))
            stable = root / "tarball.h"
            stable.write_text("old tarball input")
            os.utime(stable, ns=(cutoff - 1000000000, cutoff - 1000000000))
            rewritten = root / "patched.h"
            rewritten.write_text("value=0")
            saved_time = rewritten.stat().st_mtime_ns
            self.assertEqual(timestamps.capture(root)["captured_inputs"], 1)
            os.utime(rewritten, ns=(saved_time + 1000000, saved_time + 1000000))
            self.assertEqual(timestamps.restore(root)["restored_inputs"], 1)
            self.assertEqual(rewritten.stat().st_mtime_ns, saved_time)
            # A later preparation must retain entries restored to older mtimes.
            (root / timestamps.MARKER).write_text(str(time.time_ns()))
            self.assertEqual(timestamps.capture(root)["captured_inputs"], 1)
            rewritten.write_text("value=7")
            os.utime(rewritten, ns=(saved_time, saved_time))
            self.assertEqual(timestamps.restore(root)["changed_inputs"], 1)
            self.assertEqual(rewritten.read_text(), "value=7")
            self.assertGreater(rewritten.stat().st_mtime_ns, saved_time)

    def test_cached_paths_cannot_escape_source_or_mutate_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "src"
            manifest = source / timestamps.MANIFEST
            manifest.parent.mkdir(parents=True)
            outside = Path(directory) / "outside"
            outside.write_text("untouched")
            mtime = outside.stat().st_mtime_ns
            entry = {"size": outside.stat().st_size, "sha256": timestamps.sha256(outside), "mtime_ns": 1}
            for name in ("../outside", str(outside), "out/Default/browser", ".aether-state.json"):
                manifest.write_text(json.dumps({"schema": 1, "files": {name: entry}}))
                with self.assertRaises(ValueError):
                    timestamps.restore(source)
            self.assertEqual(outside.read_text(), "untouched")
            self.assertEqual(outside.stat().st_mtime_ns, mtime)


if __name__ == "__main__":
    unittest.main()
