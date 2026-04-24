from __future__ import annotations

import argparse
import ctypes
import os
import subprocess
import sys
import time
from typing import Callable


STILL_ACTIVE = 259


def build_installer_command(installer_path: str, log_path: str | None = None) -> list[str]:
    command = [
        installer_path,
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
    ]
    if log_path:
        command.append(f'/LOG="{log_path}"')
    return command


def windows_process_exists(pid: int) -> bool:
    if pid <= 0:
        return False

    kernel32 = ctypes.windll.kernel32
    process_query_limited_information = 0x1000
    handle = kernel32.OpenProcess(process_query_limited_information, False, int(pid))
    if not handle:
        return False

    exit_code = ctypes.c_ulong()
    try:
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def posix_process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def default_process_exists(pid: int) -> bool:
    if os.name == "nt":
        return windows_process_exists(pid)
    return posix_process_exists(pid)


def wait_for_process_exit(
    pid: int,
    *,
    timeout_seconds: float = 120,
    sleep_seconds: float = 0.5,
    process_exists: Callable[[int], bool] = default_process_exists,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() <= deadline:
        if not process_exists(pid):
            return True
        time.sleep(sleep_seconds)
    return False


def run_installer(
    installer_path: str,
    log_path: str | None = None,
    *,
    runner: Callable = subprocess.run,
) -> int:
    completed = runner(build_installer_command(installer_path, log_path))
    return int(completed.returncode)


def relaunch_app(app_executable_path: str, *, popen_factory: Callable = subprocess.Popen):
    popen_factory([app_executable_path])


def write_log(log_path: str | None, message: str):
    if not log_path:
        return
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {message}\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install a downloaded US-DICOMizer update.")
    parser.add_argument("--installer", required=True, help="Downloaded setup executable.")
    parser.add_argument("--app-exe", required=True, help="Installed US-DICOMizer executable to relaunch.")
    parser.add_argument("--app-pid", required=True, type=int, help="PID of the running app to wait for.")
    parser.add_argument("--log", default="", help="Updater log path.")
    parser.add_argument("--wait-timeout", default=120, type=float, help="Seconds to wait for the app to exit.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    log_path = args.log or os.path.join(os.path.dirname(args.installer), "update.log")

    write_log(log_path, f"Waiting for app PID {args.app_pid} to exit.")
    if not wait_for_process_exit(args.app_pid, timeout_seconds=args.wait_timeout):
        write_log(log_path, "Timed out waiting for app to exit.")
        return 2

    if not os.path.isfile(args.installer):
        write_log(log_path, f"Installer not found: {args.installer}")
        return 3

    write_log(log_path, f"Running installer: {args.installer}")
    return_code = run_installer(args.installer, log_path)
    write_log(log_path, f"Installer exited with code {return_code}.")
    if return_code != 0:
        return return_code

    if os.path.isfile(args.app_exe):
        write_log(log_path, f"Relaunching app: {args.app_exe}")
        relaunch_app(args.app_exe)
    else:
        write_log(log_path, f"Installed app executable not found for relaunch: {args.app_exe}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
