from __future__ import annotations

import io
import os
import tempfile

try:
    from ctypes import windll
except Exception:
    windll = None


INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
FILE_ATTRIBUTE_HIDDEN = 0x2


def dump_config(config) -> str:
    buffer = io.StringIO()
    config.write(buffer)
    return buffer.getvalue()


def get_windows_file_attributes(path: str) -> int | None:
    if windll is None or not os.path.exists(path):
        return None

    attrs = windll.kernel32.GetFileAttributesW(str(path))
    if attrs == INVALID_FILE_ATTRIBUTES:
        return None
    return int(attrs)


def set_windows_file_attributes(path: str, attrs: int | None):
    if windll is None or attrs is None or not os.path.exists(path):
        return
    windll.kernel32.SetFileAttributesW(str(path), int(attrs))


def write_text_atomic(path: str, text: str, encoding: str = "utf-8"):
    path = os.path.normpath(path)
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    previous_attrs = get_windows_file_attributes(path)
    fd, temp_path = tempfile.mkstemp(
        dir=parent_dir or None,
        prefix=f"{os.path.basename(path)}.",
        suffix=".tmp",
    )

    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(text)
        os.replace(temp_path, path)
        set_windows_file_attributes(path, previous_attrs)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def write_config_atomic(path: str, config, encoding: str = "utf-8"):
    write_text_atomic(path, dump_config(config), encoding=encoding)
