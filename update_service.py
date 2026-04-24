from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import PureWindowsPath
from typing import Callable


GITHUB_RELEASES_API = "https://api.github.com/repos/thrombusplus/US-DICOMizer/releases/latest"
APP_NAME = "US-DICOMizer"
UPDATER_EXE_NAME = "US-DICOMizer-Updater.exe"
SETUP_ASSET_RE = re.compile(r"^US-DICOMizer-Setup-v\d+(?:\.\d+)*\.exe$", re.IGNORECASE)


def parse_version(value: str) -> tuple[int, ...]:
    text = str(value or "").strip()
    if text.lower().startswith("v"):
        text = text[1:]

    match = re.match(r"(\d+(?:\.\d+)*)", text)
    if not match:
        return (0,)

    return tuple(int(part) for part in match.group(1).split("."))


def is_newer_version(current_version: str, latest_tag: str) -> bool:
    return parse_version(latest_tag) > parse_version(current_version)


def select_setup_asset(release: dict) -> dict | None:
    if not release or release.get("prerelease"):
        return None

    tag_name = release.get("tag_name", "")
    expected_name = f"{APP_NAME}-Setup-{tag_name}.exe" if tag_name else ""
    assets = release.get("assets", [])

    for asset in assets:
        if asset.get("name") == expected_name and asset.get("browser_download_url"):
            return asset

    for asset in assets:
        name = asset.get("name", "")
        if SETUP_ASSET_RE.match(name) and asset.get("browser_download_url"):
            return asset

    return None


def get_updates_dir(app_directory: str) -> str:
    return os.path.join(app_directory, "updates")


def get_installer_download_path(app_directory: str, asset_name: str) -> str:
    safe_name = os.path.basename(PureWindowsPath(asset_name).name)
    return os.path.join(get_updates_dir(app_directory), safe_name)


def get_installed_updater_path(app_executable_path: str | None = None) -> str:
    app_path = app_executable_path or sys.executable
    return os.path.join(os.path.dirname(os.path.abspath(app_path)), UPDATER_EXE_NAME)


def expected_install_dir(local_app_data: str | None = None) -> str:
    base = local_app_data or os.environ.get("LOCALAPPDATA", "")
    return os.path.normpath(os.path.join(base, "Programs", APP_NAME))


def path_is_within(child_path: str, parent_path: str) -> bool:
    try:
        child = os.path.normcase(os.path.abspath(os.path.normpath(child_path)))
        parent = os.path.normcase(os.path.abspath(os.path.normpath(parent_path)))
        return os.path.commonpath([child, parent]) == parent
    except (OSError, ValueError):
        return False


def can_apply_installer_update(
    *,
    is_frozen: bool,
    app_executable_path: str,
    updater_path: str,
    local_app_data: str | None = None,
) -> bool:
    return (
        is_frozen
        and os.path.isfile(updater_path)
        and path_is_within(app_executable_path, expected_install_dir(local_app_data))
    )


def build_updater_command(
    *,
    updater_path: str,
    installer_path: str,
    app_executable_path: str,
    app_pid: int,
    log_path: str | None = None,
) -> list[str]:
    command = [
        updater_path,
        "--installer",
        installer_path,
        "--app-exe",
        app_executable_path,
        "--app-pid",
        str(app_pid),
    ]
    if log_path:
        command.extend(["--log", log_path])
    return command


def fetch_latest_release(
    api_url: str = GITHUB_RELEASES_API,
    *,
    timeout: int = 10,
    opener: Callable = urllib.request.urlopen,
) -> dict:
    request = urllib.request.Request(api_url, headers={"User-Agent": APP_NAME})
    with opener(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def download_file(
    url: str,
    destination_path: str,
    *,
    timeout: int = 30,
    opener: Callable = urllib.request.urlopen,
    progress_callback: Callable[[int, int | None], None] | None = None,
) -> str:
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    temp_path = f"{destination_path}.download"
    request = urllib.request.Request(url, headers={"User-Agent": APP_NAME})

    with opener(request, timeout=timeout) as response:
        total = response.headers.get("Content-Length")
        total_bytes = int(total) if total and total.isdigit() else None
        downloaded = 0

        with open(temp_path, "wb") as handle:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                handle.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded, total_bytes)

    os.replace(temp_path, destination_path)
    return destination_path


def remove_download(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def clear_old_downloads(updates_dir: str, keep_path: str):
    if not os.path.isdir(updates_dir):
        return

    keep_path = os.path.abspath(keep_path)
    for entry in os.listdir(updates_dir):
        path = os.path.abspath(os.path.join(updates_dir, entry))
        if path == keep_path or not entry.lower().endswith(".exe"):
            continue
        try:
            os.remove(path)
        except OSError:
            pass
