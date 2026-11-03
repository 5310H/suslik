import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "wyze_setup", Path(__file__).resolve().parents[1] / "wyze_setup.py"
)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def source(model="WYZEDB3", address="192.0.2.35"):
    return {
        "url": f"wyze://{address}?model={model}&uid=test-uid&enr=private-test-key&mac=AABBCCDDEEFF&dtls=true"
    }


class WyzeDiscoveryTests(unittest.TestCase):
    def test_selects_doorbell_without_using_v3(self):
        result = {"sources": [source("WYZE_CAKP2JFUS"), source()]}
        selected = setup.select_doorbell(result, "192.0.2.35")
        self.assertIn("model=WYZEDB3", selected)

    def test_unique_doorbell_can_use_current_dhcp_address(self):
        selected = setup.select_doorbell({"sources": [source()]}, "192.0.2.99")
        self.assertTrue(selected.startswith("wyze://192.0.2.99?"))

    def test_ambiguous_cameras_and_missing_keys_are_rejected(self):
        for sources in (
            [],
            [source("WYZE_CAKP2JFUS")],
            [source(address="192.0.2.1"), source(address="192.0.2.2")],
            [{"url": source()["url"].replace("dtls=true", "dtls=false")}],
            [{"url": source()["url"].replace("enr=private-test-key", "enr=")}],
        ):
            with self.subTest(sources=sources), self.assertRaises(ValueError):
                setup.select_doorbell({"sources": sources}, "192.0.2.35")

    def test_preserves_existing_camera_and_detector_configuration(self):
        current = {
            "cameras": {"existing": {"enabled": True}},
            "detectors": {"coral": {"type": "edgetpu", "device": "usb"}},
            "go2rtc": {"streams": {"existing": ["rtsp://example.invalid/live"]}},
        }
        updated = setup.add_camera(current, "doorbell", source()["url"])
        self.assertEqual(updated["cameras"]["existing"], current["cameras"]["existing"])
        self.assertEqual(updated["detectors"], current["detectors"])
        self.assertNotIn("doorbell", current["cameras"])
        self.assertFalse(updated["cameras"]["doorbell"]["record"]["enabled"])
        self.assertEqual(updated["cameras"]["doorbell"]["objects"]["track"], ["person"])

    def test_name_collision_does_not_overwrite_stream(self):
        for config in (
            {"cameras": {"doorbell": {}}},
            {"go2rtc": {"streams": {"doorbell": []}}},
        ):
            with self.assertRaises(ValueError):
                setup.add_camera(config, "doorbell", source()["url"])
        with self.assertRaises(ValueError):
            setup.add_camera({}, "../doorbell", source()["url"])


@unittest.skipUnless(
    importlib.util.find_spec("frigate"), "requires the real Frigate runtime schema"
)
class WyzeSaveTests(unittest.TestCase):
    def setUp(self):
        from ruamel.yaml import YAML

        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "config.yml"
        self.original = b"# keep this comment\nmqtt:\n  enabled: false\ncameras: {}\nrecord:\n  enabled: false\n"
        self.path.write_bytes(self.original)
        self.config = setup.add_camera(
            YAML().load(self.original.decode()), "doorbell", source()["url"]
        )

    def test_atomic_save_preserves_comment_and_private_backup(self):
        backup = setup.save_config(self.path, self.config, self.original)
        self.assertEqual(backup.read_bytes(), self.original)
        self.assertIn("# keep this comment", self.path.read_text())
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o600)

    def test_concurrent_edit_is_preserved(self):
        self.path.write_text("# changed while discovering\n")
        with self.assertRaises(ValueError):
            setup.save_config(self.path, self.config, self.original)
        self.assertEqual(self.path.read_text(), "# changed while discovering\n")

    def test_failed_replace_preserves_original(self):
        with (
            patch.object(setup.os, "replace", side_effect=OSError("test failure")),
            self.assertRaises(OSError),
        ):
            setup.save_config(self.path, self.config, self.original)
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_validation_errors_do_not_expose_device_keys(self):
        self.config["invalid_config_field"] = "private-test-key"
        with self.assertRaises(ValueError) as error:
            setup.save_config(self.path, self.config, self.original)
        self.assertNotIn("private-test-key", str(error.exception))
        self.assertEqual(self.path.read_bytes(), self.original)
