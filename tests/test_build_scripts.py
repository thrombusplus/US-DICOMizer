import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class BuildScriptInterpreterTests(unittest.TestCase):
    def assert_no_bare_python_tool_invocations(self, relative_path):
        script_path = REPO_ROOT / relative_path
        text = script_path.read_text(encoding="utf-8")

        bare_tool_patterns = {
            "pip": r"(?m)^\s*pip\s+install\b",
            "pyinstaller": r"(?m)^\s*pyinstaller\b",
            "pyi-archive_viewer": r"(?m)^\s*pyi-archive_viewer\b",
        }

        for tool_name, pattern in bare_tool_patterns.items():
            with self.subTest(script=str(relative_path), tool=tool_name):
                self.assertIsNone(
                    re.search(pattern, text),
                    f"{relative_path} invokes {tool_name} directly; use "
                    f"python -m so package installation and packaging use the "
                    f"same interpreter.",
                )

    def test_local_build_script_uses_selected_python_for_packaging_tools(self):
        self.assert_no_bare_python_tool_invocations(Path("build.ps1"))

    def test_github_workflow_uses_selected_python_for_packaging_tools(self):
        self.assert_no_bare_python_tool_invocations(
            Path(".github") / "workflows" / "build.yml"
        )

    def test_local_build_script_rejects_unsupported_python_versions(self):
        text = (REPO_ROOT / "build.ps1").read_text(encoding="utf-8")

        self.assertRegex(
            text,
            r"sys\.version_info\s*<\s*\(3,\s*10\)",
            "build.ps1 should fail early when run with Python older than 3.10.",
        )

    def test_local_build_script_prefers_project_virtualenv(self):
        text = (REPO_ROOT / "build.ps1").read_text(encoding="utf-8")

        self.assertIn(
            '$VenvPython = Join-Path $ScriptDir ".venv\\Scripts\\python.exe"',
            text,
        )
        self.assertRegex(
            text,
            r"Test-Path\s+\$VenvPython",
            "build.ps1 should use the project virtualenv when setup.ps1 has created it.",
        )


class InstallerScriptTests(unittest.TestCase):
    def setUp(self):
        self.text = (REPO_ROOT / "installer" / "US-DICOMizer.iss").read_text(
            encoding="utf-8"
        )

    def assert_inno_setting(self, setting_name, expected_value):
        pattern = rf"(?m)^{re.escape(setting_name)}={re.escape(expected_value)}$"
        self.assertRegex(
            self.text,
            pattern,
            f"installer should define {setting_name}={expected_value}",
        )

    def assert_inno_define(self, define_name, expected_value):
        pattern = rf'(?m)^#define {re.escape(define_name)} "{re.escape(expected_value)}"$'
        self.assertRegex(
            self.text,
            pattern,
            f"installer should define {define_name} as {expected_value}",
        )

    def test_installer_defaults_to_program_files_for_all_users(self):
        self.assert_inno_setting("ArchitecturesAllowed", "x64compatible")
        self.assert_inno_setting(
            "ArchitecturesInstallIn64BitMode", "x64compatible"
        )
        self.assert_inno_setting("DefaultDirName", r"{autopf}\{#MyAppName}")
        self.assert_inno_setting("PrivilegesRequired", "admin")

    def test_installer_allows_installation_folder_selection(self):
        self.assert_inno_setting("DisableDirPage", "no")

    def test_installer_exposes_application_description(self):
        expected_description = (
            "US-DICOMizer is an advanced application designed for anonymizing "
            "ultrasound diagnostic DICOM images. This tool ensures compliance "
            "with data privacy regulations by securely removing "
            "patient-identifiable information from DICOM files, making them "
            "suitable for research, sharing, and analysis."
        )

        self.assert_inno_define("MyAppDescription", expected_description)
        self.assert_inno_setting("AppComments", "{#MyAppDescription}")
        self.assert_inno_setting("WelcomeLabel2", "{#MyAppDescription}")

    def test_installer_can_launch_application_after_install_by_default(self):
        run_entry_match = re.search(
            r'(?m)^Filename: "\{app\}\\US-DICOMizer\.exe"; '
            r'Description: "\{cm:LaunchProgram,\{#MyAppName\}\}"; '
            r"Flags: (?P<flags>[^;]+)$",
            self.text,
        )

        self.assertIsNotNone(
            run_entry_match,
            "installer should define a post-install launch option.",
        )
        flags = run_entry_match.group("flags").split()
        self.assertIn("postinstall", flags)
        self.assertIn("nowait", flags)
        self.assertIn("skipifsilent", flags)
        self.assertNotIn("unchecked", flags)
        self.assertRegex(
            self.text,
            r"(?m)^DisableFinishedPage=no$",
            "installer should show the finished page so the launch option is visible.",
        )


if __name__ == "__main__":
    unittest.main()
