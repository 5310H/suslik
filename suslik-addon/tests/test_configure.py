import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("configure", ROOT / "configure.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name)
        self.options = self.data / "options.json"
        self.options.write_text('{}', encoding="utf-8")
        self.store = self.data / "config" / "config.json"

    def write_options(self, options):
        self.options.write_text(json.dumps(options), encoding="utf-8")

    def read_store(self):
        return json.loads(self.store.read_text(encoding="utf-8"))

    def test_fresh_wizard_without_credentials(self):
        adapter.configure(self.data)
        self.assertEqual(self.read_store(), {"backend": "cpu"})

    def test_restart_and_upgrade_preserve_data_and_secrets(self):
        self.store.parent.mkdir()
        original = {"frigate_password": "secret", "mqtt": {"password": "token"},
                    "frigate_url": "http://old", "cameras": ["driveway"]}
        self.store.write_text(json.dumps(original), encoding="utf-8")
        evidence = self.data / "reference.bin"
        evidence.write_bytes(b"learned-face")
        self.write_options({"frigate_url": "http://frigate:5000/", "poll_interval": 15,
                            "cpu_threads": 0})
        adapter.configure(self.data)
        adapter.configure(self.data)
        self.write_options({"frigate_url": ""})
        adapter.configure(self.data)
        result = self.read_store()
        self.assertEqual(result["frigate_password"], "secret")
        self.assertEqual(result["mqtt"], original["mqtt"])
        self.assertEqual(result["cameras"], original["cameras"])
        self.assertEqual(result["frigate_url"], "http://frigate:5000")
        self.assertEqual(result["poll_interval"], 15)
        self.assertEqual(result["cpu_threads"], 0)
        self.assertEqual(evidence.read_bytes(), b"learned-face")

    def test_invalid_options_do_not_mutate_store(self):
        adapter.configure(self.data)
        before = self.store.read_bytes()
        for options in ({"poll_interval": True}, {"poll_interval": 4},
                        {"poll_interval": 301}, {"cpu_threads": -1},
                        {"cpu_threads": 65}, {"cpu_threads": "2"},
                        {"unknown": "secret"}, {"frigate_url": None},
                        {"frigate_url": "http://user:secret@host"},
                        {"frigate_url": "file:///etc/passwd"},
                        {"frigate_url": "http://host:bad"},
                        {"frigate_url": "http://host/?token=secret"}):
            with self.subTest(options=options):
                self.write_options(options)
                with self.assertRaises(adapter.ConfigurationError) as error:
                    adapter.configure(self.data)
                self.assertNotIn("secret", str(error.exception))
                self.assertEqual(self.store.read_bytes(), before)

    def test_corrupt_json_is_not_overwritten(self):
        adapter.configure(self.data)
        for content in ('{"password":"secret",', '[]', 'null'):
            self.store.write_text(content, encoding="utf-8")
            with self.assertRaises(adapter.ConfigurationError):
                adapter.configure(self.data)
            self.assertEqual(self.store.read_text(encoding="utf-8"), content)

    def test_missing_and_malformed_options(self):
        for content in ('[]', '{', 'null'):
            self.options.write_text(content, encoding="utf-8")
            with self.assertRaises(adapter.ConfigurationError):
                adapter.configure(self.data)
            self.assertFalse(self.store.exists())
        self.options.unlink()
        with self.assertRaises(adapter.ConfigurationError):
            adapter.configure(self.data)

    def test_disk_failure_preserves_previous_store(self):
        adapter.configure(self.data)
        before = self.store.read_bytes()
        self.write_options({"poll_interval": 20})
        with patch.object(adapter.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                adapter.configure(self.data)
        self.assertEqual(self.store.read_bytes(), before)
        self.assertEqual(list(self.store.parent.iterdir()), [self.store])


if __name__ == "__main__":
    unittest.main()
