import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

spec = importlib.util.spec_from_file_location(
    "native_start", Path(__file__).resolve().parents[1] / "start.py"
)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name)
        self.options = self.data / "options.json"
        self.options.write_text("{}")

    def test_fresh_install_has_no_cameras_or_inference(self):
        adapter.bootstrap(self.data)
        config = yaml.safe_load((self.data / "config/config.yml").read_text())
        self.assertEqual(config["cameras"], {})
        self.assertFalse(config["face_recognition"]["enabled"])
        self.assertTrue(config["face_recognition"]["suslik"]["enabled"])
        self.assertFalse(config["mqtt"]["enabled"])
        self.assertFalse(config["record"]["enabled"])
        self.assertTrue((self.data / "media").is_dir())

    def test_restart_never_overwrites_user_configuration_or_data(self):
        adapter.bootstrap(self.data)
        config = self.data / "config/config.yml"
        config.write_text('cameras: {private_camera: {password: "test-secret"}}\n')
        before = config.read_bytes()
        media = self.data / "media/evidence"
        media.write_bytes(b"keep")
        adapter.bootstrap(self.data)
        self.assertEqual(config.read_bytes(), before)
        self.assertEqual(media.read_bytes(), b"keep")

    def test_yaml_extension_and_even_invalid_config_are_preserved(self):
        (self.data / "config").mkdir()
        config = self.data / "config/config.yaml"
        config.write_text("invalid: [")
        adapter.bootstrap(self.data)
        self.assertEqual(config.read_text(), "invalid: [")
        self.assertFalse((self.data / "config/config.yml").exists())

    def test_missing_invalid_or_unknown_options_fail_closed(self):
        for value in (
            "[]",
            "{",
            json.dumps({"unknown": "test-secret"}),
            json.dumps({"plus_api_key": 123}),
        ):
            self.options.write_text(value)
            with self.assertRaises(ValueError) as error:
                adapter.bootstrap(self.data)
            self.assertNotIn("test-secret", str(error.exception))
            self.assertFalse((self.data / "config/config.yml").exists())
        self.options.unlink()
        with self.assertRaises(ValueError):
            adapter.bootstrap(self.data)

    def test_write_failure_does_not_leave_partial_config(self):
        with patch.object(adapter.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                adapter.bootstrap(self.data)
        self.assertEqual(list((self.data / "config").iterdir()), [])

    def test_plus_secret_stays_in_supervisor_options(self):
        self.options.write_text(json.dumps({"plus_api_key": "test-secret"}))
        adapter.bootstrap(self.data)
        self.assertNotIn("test-secret", (self.data / "config/config.yml").read_text())
