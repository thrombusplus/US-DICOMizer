import os
import tempfile
import unittest
from pathlib import Path

from update_service import (
    build_updater_command,
    can_apply_installer_update,
    get_installer_download_path,
    is_newer_version,
    select_setup_asset,
)


class UpdateServiceTests(unittest.TestCase):
    def test_is_newer_version_compares_numeric_release_tags(self):
        self.assertTrue(is_newer_version("5.2", "v5.10"))
        self.assertFalse(is_newer_version("5.10", "v5.2"))
        self.assertFalse(is_newer_version("5.2", "v5.2"))

    def test_select_setup_asset_uses_single_installer_exe(self):
        release = {
            "prerelease": False,
            "tag_name": "v5.3",
            "assets": [
                {
                    "name": "US-DICOMizer-Windows-v5.3.zip",
                    "browser_download_url": "https://example.invalid/zip",
                },
                {
                    "name": "US-DICOMizer-Setup-v5.3.exe",
                    "browser_download_url": "https://example.invalid/setup",
                },
                {
                    "name": "US-DICOMizer-Updater.exe",
                    "browser_download_url": "https://example.invalid/updater",
                },
            ],
        }

        asset = select_setup_asset(release)

        self.assertEqual(asset["name"], "US-DICOMizer-Setup-v5.3.exe")
        self.assertEqual(asset["browser_download_url"], "https://example.invalid/setup")

    def test_select_setup_asset_ignores_prerelease(self):
        release = {
            "prerelease": True,
            "tag_name": "v5.3",
            "assets": [
                {
                    "name": "US-DICOMizer-Setup-v5.3.exe",
                    "browser_download_url": "https://example.invalid/setup",
                }
            ],
        }

        self.assertIsNone(select_setup_asset(release))

    def test_get_installer_download_path_stays_inside_updates_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = get_installer_download_path(
                tmp_dir,
                r"..\US-DICOMizer-Setup-v5.3.exe",
            )

            expected = Path(tmp_dir) / "updates" / "US-DICOMizer-Setup-v5.3.exe"
            self.assertEqual(Path(path), expected)

    def test_build_updater_command_passes_installer_app_and_pid(self):
        command = build_updater_command(
            updater_path=r"C:\Users\me\AppData\Local\Programs\US-DICOMizer\US-DICOMizer-Updater.exe",
            installer_path=r"C:\Users\me\.anonymizer\updates\US-DICOMizer-Setup-v5.3.exe",
            app_executable_path=r"C:\Users\me\AppData\Local\Programs\US-DICOMizer\US-DICOMizer.exe",
            app_pid=1234,
        )

        self.assertEqual(command[0], r"C:\Users\me\AppData\Local\Programs\US-DICOMizer\US-DICOMizer-Updater.exe")
        self.assertIn("--installer", command)
        self.assertIn(r"C:\Users\me\.anonymizer\updates\US-DICOMizer-Setup-v5.3.exe", command)
        self.assertIn("--app-exe", command)
        self.assertIn(r"C:\Users\me\AppData\Local\Programs\US-DICOMizer\US-DICOMizer.exe", command)
        self.assertIn("--app-pid", command)
        self.assertIn("1234", command)

    def test_can_apply_installer_update_requires_frozen_installed_app_with_updater(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_app_data = Path(tmp_dir) / "LocalAppData"
            install_dir = local_app_data / "Programs" / "US-DICOMizer"
            install_dir.mkdir(parents=True)
            app_exe = install_dir / "US-DICOMizer.exe"
            updater_exe = install_dir / "US-DICOMizer-Updater.exe"
            app_exe.write_text("app", encoding="utf-8")
            updater_exe.write_text("updater", encoding="utf-8")

            self.assertTrue(
                can_apply_installer_update(
                    is_frozen=True,
                    app_executable_path=str(app_exe),
                    updater_path=str(updater_exe),
                    local_app_data=str(local_app_data),
                )
            )
            self.assertFalse(
                can_apply_installer_update(
                    is_frozen=False,
                    app_executable_path=str(app_exe),
                    updater_path=str(updater_exe),
                    local_app_data=str(local_app_data),
                )
            )
            self.assertFalse(
                can_apply_installer_update(
                    is_frozen=True,
                    app_executable_path=os.path.join(tmp_dir, "US-DICOMizer.exe"),
                    updater_path=str(updater_exe),
                    local_app_data=str(local_app_data),
                )
            )


if __name__ == "__main__":
    unittest.main()
