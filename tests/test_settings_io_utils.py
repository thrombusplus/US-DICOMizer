import configparser
import tempfile
import unittest
from pathlib import Path

from settings_io_utils import (
    FILE_ATTRIBUTE_HIDDEN,
    get_windows_file_attributes,
    write_config_atomic,
    write_text_atomic,
)


class SettingsIoUtilsTests(unittest.TestCase):
    def test_write_text_atomic_updates_hidden_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "settings.ini"
            settings_path.write_text("original", encoding="utf-8")

            attrs = get_windows_file_attributes(str(settings_path))
            if attrs is not None:
                from settings_io_utils import set_windows_file_attributes

                set_windows_file_attributes(str(settings_path), attrs | FILE_ATTRIBUTE_HIDDEN)

            with self.assertRaises(PermissionError):
                settings_path.write_text("direct-write", encoding="utf-8")

            write_text_atomic(str(settings_path), "atomic-write", encoding="utf-8")

            self.assertEqual(settings_path.read_text(encoding="utf-8"), "atomic-write")
            updated_attrs = get_windows_file_attributes(str(settings_path))
            if attrs is not None and updated_attrs is not None:
                self.assertTrue(updated_attrs & FILE_ATTRIBUTE_HIDDEN)

    def test_write_config_atomic_serializes_configparser(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings_path = Path(tmp_dir) / "settings.ini"
            config = configparser.ConfigParser()
            config["settings"] = {
                "annotation_format": "Darwin V7",
                "debug_allow_all_steps": "yes",
            }

            write_config_atomic(str(settings_path), config)

            written = settings_path.read_text(encoding="utf-8")
            self.assertIn("[settings]", written)
            self.assertIn("annotation_format = Darwin V7", written)
            self.assertIn("debug_allow_all_steps = yes", written)


if __name__ == "__main__":
    unittest.main()
