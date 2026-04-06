from __future__ import annotations

import json
import os
import shutil
import zipfile

import pydicom

from annotation_metadata_utils import (
    ensure_annotation_schema,
    export_darwin_annotation,
    export_labelme_annotation,
    import_darwin_annotation,
    import_labelme_annotation,
)
from package_io_utils import find_existing_sidecar_paths, get_preferred_sidecar_paths


def detect_annotation_format_file(json_path: str) -> str | None:
    try:
        with open(json_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return None
    return detect_annotation_format_payload(payload)


def detect_annotation_format_payload(payload) -> str | None:
    if isinstance(payload, dict) and "annotations" in payload and "item" in payload:
        return "darwin"
    if isinstance(payload, dict):
        return "labelme"
    return None


def iter_dicom_files_in_directory(folder_path: str):
    for root_dir, _, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.normpath(os.path.join(root_dir, filename))
            if os.path.isfile(file_path):
                yield file_path


def get_sidecar_dimensions(file_path: str) -> tuple[int, int, int]:
    try:
        ds = pydicom.dcmread(file_path, stop_before_pixels=True)
        columns = int(getattr(ds, "Columns", 0) or 0)
        rows = int(getattr(ds, "Rows", 0) or 0)
        frame_count = int(getattr(ds, "NumberOfFrames", 1) or 1)
        return columns, rows, frame_count
    except Exception:
        return 0, 0, 1


def load_annotation_sidecar_data(file_path: str, package_root: str | None = None):
    existing = find_existing_sidecar_paths(file_path, package_root=package_root)

    for darwin_path in existing["darwin"]:
        payload = _read_json_file(darwin_path)
        if payload is None:
            continue
        return "darwin", ensure_annotation_schema(import_darwin_annotation({}, payload)), darwin_path

    for json_path in existing["generic"]:
        payload = _read_json_file(json_path)
        if payload is None:
            continue
        detected_format = detect_annotation_format_payload(payload)
        if detected_format == "darwin":
            return "darwin", ensure_annotation_schema(import_darwin_annotation({}, payload)), json_path
        if detected_format == "labelme":
            return "labelme", ensure_annotation_schema(import_labelme_annotation({}, payload)), json_path

    return None, None, None


def write_annotation_sidecars(
    file_path: str,
    annotation_data,
    package_root: str | None = None,
    create_missing_format: str | None = None,
    patient_id: str = "",
    clinician_name: str = "",
    clinician_email: str = "",
) -> dict[str, str]:
    annotation_data = ensure_annotation_schema(annotation_data)
    columns, rows, frame_count = get_sidecar_dimensions(file_path)
    existing = find_existing_sidecar_paths(file_path, package_root=package_root)
    preferred = get_preferred_sidecar_paths(file_path, package_root=package_root)

    generic_sidecars = existing["generic"]
    darwin_sidecars = existing["darwin"]
    generic_format = detect_annotation_format_file(generic_sidecars[0]) if generic_sidecars else None
    has_darwin_representation = bool(darwin_sidecars) or generic_format == "darwin"
    has_labelme_representation = generic_format == "labelme"

    if generic_sidecars:
        if generic_format == "darwin":
            _write_darwin_sidecar(
                file_path,
                preferred["generic"],
                annotation_data,
                image_width=columns,
                image_height=rows,
                frame_count=frame_count,
                patient_id=patient_id,
                clinician_name=clinician_name,
                clinician_email=clinician_email,
            )
        else:
            _write_labelme_sidecar(
                file_path,
                preferred["generic"],
                annotation_data,
                image_width=columns,
                image_height=rows,
                patient_id=patient_id,
                clinician_name=clinician_name,
                clinician_email=clinician_email,
            )

    if darwin_sidecars:
        _write_darwin_sidecar(
            file_path,
            preferred["darwin"],
            annotation_data,
            image_width=columns,
            image_height=rows,
            frame_count=frame_count,
            patient_id=patient_id,
            clinician_name=clinician_name,
            clinician_email=clinician_email,
        )

    if create_missing_format == "Darwin V7" and not has_darwin_representation:
        _write_darwin_sidecar(
            file_path,
            preferred["darwin"],
            annotation_data,
            image_width=columns,
            image_height=rows,
            frame_count=frame_count,
            patient_id=patient_id,
            clinician_name=clinician_name,
            clinician_email=clinician_email,
        )
    elif create_missing_format == "LabelMe" and not has_labelme_representation:
        _write_labelme_sidecar(
            file_path,
            preferred["generic"],
            annotation_data,
            image_width=columns,
            image_height=rows,
            patient_id=patient_id,
            clinician_name=clinician_name,
            clinician_email=clinician_email,
        )

    _remove_duplicate_sidecars(generic_sidecars, preferred["generic"])
    _remove_duplicate_sidecars(darwin_sidecars, preferred["darwin"])
    _prune_empty_annotation_directories(file_path, package_root=package_root)

    return preferred


def export_package_to_zip(
    package_root: str,
    save_zip_to: str,
    package_name: str,
    annotation_data_by_file: dict[str, dict],
    annotation_format: str = "Darwin V7",
    patient_id_lookup=None,
    clinician_name: str = "",
    clinician_email: str = "",
) -> str:
    package_root = os.path.normpath(package_root)
    save_zip_to = os.path.normpath(save_zip_to)

    if not os.path.isdir(package_root):
        raise FileNotFoundError(f"Package root does not exist: {package_root}")

    os.makedirs(save_zip_to, exist_ok=True)

    for ann_file_path in iter_dicom_files_in_directory(package_root):
        if not ann_file_path.lower().endswith(".dcm"):
            continue
        patient_id = ""
        if callable(patient_id_lookup):
            patient_id = str(patient_id_lookup(ann_file_path) or "").strip()
        write_annotation_sidecars(
            ann_file_path,
            annotation_data_by_file.get(ann_file_path, {}),
            package_root=package_root,
            create_missing_format=annotation_format,
            patient_id=patient_id,
            clinician_name=clinician_name,
            clinician_email=clinician_email,
        )

    _prune_empty_annotation_directories(package_root, package_root=package_root, treat_as_directory=True)
    zipped_file = os.path.join(save_zip_to, package_name)
    return shutil.make_archive(os.path.normpath(zipped_file), "zip", package_root)


def extract_zip_package(zip_file_path: str, destination_root: str) -> int:
    extracted_count = 0
    zip_file_path = os.path.normpath(zip_file_path)
    destination_root = os.path.normpath(destination_root)

    with zipfile.ZipFile(zip_file_path, "r") as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue

            target_path = os.path.normpath(os.path.join(destination_root, member.filename))
            if os.path.commonpath([destination_root, target_path]) != destination_root:
                continue

            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with archive.open(member) as source_file, open(target_path, "wb") as output_file:
                shutil.copyfileobj(source_file, output_file)
                extracted_count += 1

    return extracted_count


def _write_labelme_sidecar(
    file_path: str,
    output_json_path: str,
    annotation_data,
    image_width: int,
    image_height: int,
    patient_id: str = "",
    clinician_name: str = "",
    clinician_email: str = "",
):
    payload = export_labelme_annotation(
        annotation_data,
        os.path.basename(file_path),
        patient_id=patient_id,
        image_width=image_width,
        image_height=image_height,
        clinician_name=clinician_name,
        clinician_email=clinician_email,
    )
    _write_json_file(output_json_path, payload)


def _write_darwin_sidecar(
    file_path: str,
    output_json_path: str,
    annotation_data,
    image_width: int,
    image_height: int,
    frame_count: int,
    patient_id: str = "",
    clinician_name: str = "",
    clinician_email: str = "",
):
    payload = export_darwin_annotation(
        annotation_data,
        os.path.basename(file_path),
        patient_id=patient_id,
        image_width=image_width,
        image_height=image_height,
        frame_count=frame_count,
        clinician_name=clinician_name,
        clinician_email=clinician_email,
    )
    _write_json_file(output_json_path, payload)


def _remove_duplicate_sidecars(existing_paths: list[str], preferred_path: str):
    preferred_norm = os.path.normpath(preferred_path)
    for path in existing_paths:
        if os.path.normpath(path) != preferred_norm and os.path.isfile(path):
            os.remove(path)


def _prune_empty_annotation_directories(file_path: str, package_root: str | None = None, treat_as_directory: bool = False):
    if treat_as_directory:
        base_dir = os.path.normpath(file_path)
        candidate_dirs = [
            os.path.join(root, dirname)
            for root, dirnames, _ in os.walk(base_dir, topdown=False)
            for dirname in dirnames
            if dirname == "annotations"
        ]
    else:
        base_dir = os.path.dirname(os.path.normpath(file_path))
        parent_dir = os.path.dirname(base_dir)
        candidate_dirs = [
            os.path.join(base_dir, "annotations"),
            os.path.join(parent_dir, "annotations"),
        ]
        if package_root:
            candidate_dirs.append(os.path.join(os.path.normpath(package_root), "annotations"))

    for directory in _unique_paths(candidate_dirs):
        if os.path.isdir(directory) and not os.listdir(directory):
            os.rmdir(directory)


def _read_json_file(json_path: str):
    try:
        with open(json_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


def _write_json_file(json_path: str, payload):
    os.makedirs(os.path.dirname(os.path.normpath(json_path)), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _unique_paths(paths):
    unique = []
    seen = set()
    for path in paths:
        normalized = os.path.normpath(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique
