"""Guard native checkpoint continuations; no browser substitute or HTTP mock."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from continue_build import eligible, recent_native_objects

class ContinuationTest(unittest.TestCase):
    def setUp(self):
        self.context = dict(elapsed=14400, result_exists=False, native_started=True,
                            new_objects=10, cache_bytes=10000, count=0)
    def test_only_real_cached_native_progress_can_continue(self):
        self.assertTrue(eligible(**self.context))
        for key, value in (("elapsed", 100), ("native_started", False),
                           ("new_objects", 0), ("cache_bytes", 0)):
            with self.subTest(key=key):
                self.assertFalse(eligible(**dict(self.context, **{key: value})))
    def test_normal_completion_and_compiler_failure_do_not_repeat(self):
        self.assertFalse(eligible(**dict(self.context, result_exists=True)))
    def test_continuation_is_bounded(self):
        for count in (-1, 4, 5):
            self.assertFalse(eligible(**dict(self.context, count=count)))
        self.assertTrue(eligible(**dict(self.context, count=3)))
    def test_progress_comes_from_recent_real_object_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ninja_log"
            path.write_text("# ninja log v5\n0\t1\t1000000000\told.obj\thash\n"
                            "0\t1\t1000000000000\tnew.obj\thash\n"
                            "0\t1\t1000000000000\tcopy.pak\thash\n")
            self.assertEqual(recent_native_objects(path, 1000), 1)
            self.assertEqual(recent_native_objects(path, 2000), 0)
if __name__ == "__main__":
    unittest.main()
