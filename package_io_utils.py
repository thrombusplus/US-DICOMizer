from __future__ import annotations

import os
from typing import Iterable


def normalize_path(path: str | None) -> str | None:
    if not path:
        return None
    return os.path.normpath(path)


def build_sidecar_candidate_paths(file_path: str, package_root: str | None = None) -> dict[str, list[str]]:
    file_path = os.path.normpath(file_path)
    package_root = normalize_path(package_root)
    file_dir = os.path.dirname(file_path)
    parent_dir = os.path.dirname(file_dir)
    stem = os.path.splitext(os.path.basename(file_path))[0]

    annotation_dirs = _unique_paths(
        [
            file_dir,
            os.path.join(file_dir, "annotations"),
            os.path.join(parent_dir, "annotations"),
            os.path.join(package_root, "annotations") if package_root else None,
        ]
    )

    return {
        "generic": _unique_paths(os.path.join(directory, f"{stem}.json") for directory in annotation_dirs),
        "darwin": _unique_paths(os.path.join(directory, f"{stem}_darwin.json") for directory in annotation_dirs),
    }


def find_existing_sidecar_paths(file_path: str, package_root: str | None = None) -> dict[str, list[str]]:
    candidates = build_sidecar_candidate_paths(file_path, package_root=package_root)
    return {
        sidecar_type: [path for path in paths if os.path.isfile(path)]
        for sidecar_type, paths in candidates.items()
    }


def get_preferred_sidecar_paths(file_path: str, package_root: str | None = None) -> dict[str, str]:
    preferred_dir = os.path.dirname(os.path.normpath(file_path))
    stem = os.path.splitext(os.path.basename(file_path))[0]
    return {
        "generic": os.path.join(preferred_dir, f"{stem}.json"),
        "darwin": os.path.join(preferred_dir, f"{stem}_darwin.json"),
    }


def path_is_within(path: str | None, base_path: str | None) -> bool:
    normalized_path = normalize_path(path)
    normalized_base_path = normalize_path(base_path)
    if not normalized_path or not normalized_base_path:
        return False

    try:
        return os.path.commonpath([normalized_base_path, normalized_path]) == normalized_base_path
    except ValueError:
        return False


def _unique_paths(paths: Iterable[str | None]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()

    for path in paths:
        normalized = normalize_path(path)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)

    return unique
