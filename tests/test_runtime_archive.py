"""Archive IO checks only; these never construct or launch a browser substitute."""
import io
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from smoke import runtime_directory


class RuntimeArchiveTest(unittest.TestCase):
    def test_distributed_resource_is_read_from_extracted_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prefix = "aether-component-" + ("windows" if os.name == "nt" else "linux") + "-x64"
            name = prefix + "/locales/en-US.pak"
            resource = b"archive resource IO fixture"
            archive = root / "bundle.tar.gz"
            with tarfile.open(archive, "w:gz") as stream:
                entry = tarfile.TarInfo(name)
                entry.size = len(resource)
                stream.addfile(entry, io.BytesIO(resource))
            with runtime_directory(root / "unused-source", archive) as extracted:
                self.assertEqual((extracted / "locales/en-US.pak").read_bytes(), resource)
                self.assertNotEqual(extracted, root / "unused-source/out/Default")
            self.assertFalse(extracted.exists())
            archive = root / "bundle.zip"
            with zipfile.ZipFile(archive, "w") as stream:
                stream.writestr(name, resource)
            with runtime_directory(root / "unused-source", archive) as extracted:
                self.assertEqual((extracted / "locales/en-US.pak").read_bytes(), resource)

    def test_zip_paths_cannot_escape_extraction_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as stream:
                stream.writestr("../escaped-resource", b"unsafe path fixture")
            with self.assertRaises(ValueError):
                with runtime_directory(root, archive):
                    self.fail("Unsafe archive path was accepted")
            self.assertFalse((root / "escaped-resource").exists())


if __name__ == "__main__":
    unittest.main()
