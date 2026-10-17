"""Regression for the Windows spawn failure observed in Actions attempt 1."""
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WindowsPreparationTest(unittest.TestCase):
    def test_upstream_worker_can_import_its_module_under_spawn(self):
        # A tiny build-tool fixture exercises actual spawned interpreters without
        # downloading Chromium. Browser compilation remains a separate CI job.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            utils = root / "helium-chromium/utils"
            utils.mkdir(parents=True)
            (utils / "name_substitution.py").write_text(
                "def worker():\n    return 'SPAWN_IMPORT_OK'\n")
            (root / "build.py").write_text(textwrap.dedent('''\
                import sys
                import multiprocessing
                from concurrent.futures import ProcessPoolExecutor
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent / 'helium-chromium/utils'))
                import name_substitution
                sys.path.pop(0)
                def _configure_remoteexec(tree):
                    pass
                def main():
                    with ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context('spawn')) as pool:
                        assert pool.submit(name_substitution.worker).result(timeout=15) == 'SPAWN_IMPORT_OK'
                    print('SPAWN_IMPORT_OK')
                    _configure_remoteexec(Path('.'))
                '''))
            entry = root / "exercise.py"
            entry.write_text(textwrap.dedent(f'''\
                import sys
                from pathlib import Path
                sys.path.insert(0, {str(ROOT / 'scripts')!r})
                from build import prepare_windows
                if __name__ == '__main__':
                    prepare_windows(Path(sys.argv[1]), Path(sys.argv[1]) / 'build/src')
                '''))
            result = subprocess.run([sys.executable, str(entry), str(root)],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SPAWN_IMPORT_OK", result.stdout)
