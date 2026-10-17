"""Offline tests for the SteamOS launcher; no Deck or network required."""
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nucleus_deck as nd


class ReleaseTests(unittest.TestCase):
    def test_selects_verified_steamos_asset(self):
        digest = "b" * 64
        result = nd.choose_asset({"assets": [
            {"name": "partydeck-linux.AppImage", "browser_download_url": "https://github.com/a", "digest": "sha256:" + digest},
            {"name": "partydeck-v1-SteamOS-x86_64.tar.gz",
             "browser_download_url": "https://github.com/partydeck/partydeck/releases/download/v1/test.tar.gz",
             "digest": "sha256:" + digest},
        ]})
        self.assertEqual(result[2], digest)

    def test_rejects_missing_digest(self):
        with self.assertRaises(RuntimeError):
            nd.choose_asset({"assets": [
                {"name": "partydeck-v1-SteamOS-x86_64.tar.gz",
                 "browser_download_url": "https://github.com/partydeck/partydeck/releases/download/v1/a.tar.gz"}
            ]})

    def test_rejects_other_host(self):
        with self.assertRaises(RuntimeError):
            nd.choose_asset({"assets": [
                {"name": "partydeck-v1-SteamOS-x86_64.tar.gz",
                 "browser_download_url": "https://example.com/partydeck/partydeck/releases/download/v1/a.tar.gz",
                 "digest": "sha256:" + "a" * 64}
            ]})


class ArchiveTests(unittest.TestCase):
    def make_archive(self, archive, entries):
        with tarfile.open(archive, "w:gz") as tar:
            for name, mode, data in entries:
                item = tarfile.TarInfo(name)
                item.mode = 0o755
                if mode == "file":
                    item.size = len(data)
                    tar.addfile(item, io.BytesIO(data))
                elif mode == "symlink":
                    item.type = tarfile.SYMTYPE
                    item.linkname = "/etc/passwd"
                    tar.addfile(item)

    def test_extract_and_locate_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "good.tar.gz"
            self.make_archive(archive, [("release/partydeck", "file", b"game launcher")])
            nd.extract_safe(archive, root / "extract")
            self.assertEqual((root / "extract/release/partydeck").read_bytes(), b"game launcher")
            self.assertIsNotNone(nd.find_executable(root / "extract", "partydeck"))

    def test_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "bad.tar.gz"
            self.make_archive(archive, [("../escape.txt", "file", b"oops")])
            with self.assertRaises(RuntimeError):
                nd.extract_safe(archive, root / "extract")
            self.assertFalse((root / "escape.txt").exists())

    def test_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "bad.tar.gz"
            self.make_archive(archive, [("release/external", "symlink", b"")])
            with self.assertRaises(RuntimeError):
                nd.extract_safe(archive, root / "extract")


if __name__ == "__main__":
    unittest.main()
