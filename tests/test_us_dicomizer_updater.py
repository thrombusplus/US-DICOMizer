import subprocess
import unittest
from unittest.mock import Mock

from us_dicomizer_updater import (
    build_installer_command,
    relaunch_app,
    run_installer,
    wait_for_process_exit,
)


class UsDicomizerUpdaterTests(unittest.TestCase):
    def test_build_installer_command_uses_silent_inno_setup_arguments(self):
        command = build_installer_command(
            installer_path=r"C:\Users\me\.anonymizer\updates\US-DICOMizer-Setup-v5.3.exe",
            log_path=r"C:\Users\me\.anonymizer\updates\update.log",
        )

        self.assertEqual(command[0], r"C:\Users\me\.anonymizer\updates\US-DICOMizer-Setup-v5.3.exe")
        self.assertIn("/VERYSILENT", command)
        self.assertIn("/SUPPRESSMSGBOXES", command)
        self.assertIn("/NORESTART", command)
        self.assertIn(r'/LOG="C:\Users\me\.anonymizer\updates\update.log"', command)

    def test_wait_for_process_exit_returns_true_when_process_is_already_gone(self):
        result = wait_for_process_exit(
            pid=1234,
            timeout_seconds=0.1,
            sleep_seconds=0,
            process_exists=lambda pid: False,
        )

        self.assertTrue(result)

    def test_wait_for_process_exit_times_out_while_process_stays_running(self):
        result = wait_for_process_exit(
            pid=1234,
            timeout_seconds=0.01,
            sleep_seconds=0,
            process_exists=lambda pid: True,
        )

        self.assertFalse(result)

    def test_run_installer_returns_completed_process_code(self):
        runner = Mock(return_value=subprocess.CompletedProcess(args=["installer"], returncode=0))

        return_code = run_installer(
            installer_path=r"C:\setup.exe",
            log_path=r"C:\update.log",
            runner=runner,
        )

        self.assertEqual(return_code, 0)
        runner.assert_called_once()
        self.assertIn("/VERYSILENT", runner.call_args.args[0])

    def test_relaunch_app_starts_app_without_waiting(self):
        popen_factory = Mock()

        relaunch_app(r"C:\Program Files\US-DICOMizer\US-DICOMizer.exe", popen_factory=popen_factory)

        popen_factory.assert_called_once_with([r"C:\Program Files\US-DICOMizer\US-DICOMizer.exe"])


if __name__ == "__main__":
    unittest.main()
