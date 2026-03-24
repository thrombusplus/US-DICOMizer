import copy
import json
import uuid
from datetime import datetime

from anonymized_filename_utils import (
    normalize_compressibility_value,
    normalize_thrombosis_value,
)


TRUE_VALUES = {"1", "true", "yes", "y", "on", "reviewed"}
FALSE_VALUES = {"0", "false", "no", "n", "off", "unreviewed"}


def coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)

    normalized = str(value or "").strip().lower()
    if not normalized:
        return False
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return bool(value)


def build_labelme_annotator(clinician_name="", clinician_email=""):
    return {
        "full_name": str(clinician_name or "").strip(),
        "email": str(clinician_email or "").strip(),
    }


def build_darwin_annotator_actor(clinician_name="", clinician_email=""):
    full_name = str(clinician_name or "").strip()
    email = str(clinician_email or "").strip()
    if not full_name or not email:
        return None
    return {
        "full_name": full_name,
        "email": email,
    }


def ensure_annotation_schema(data):
    if not isinstance(data, dict):
        data = {}

    if "classification" not in data or not isinstance(data["classification"], dict):
        data["classification"] = {}

    classification = data["classification"]
    legacy_review_status = classification.get("review_status")
    if not isinstance(legacy_review_status, dict):
        legacy_review_status = {}

    reviewed = classification.get("_reviewed", legacy_review_status.get("reviewed", False))
    reviewed_timestamp = classification.get(
        "_reviewed_timestamp",
        legacy_review_status.get("timestamp", ""),
    )

    classification["thrombosis"] = normalize_thrombosis_value(
        classification.get("thrombosis", classification.get("dvt", ""))
    )
    classification["compressibility"] = normalize_compressibility_value(
        classification.get("compressibility", "")
    )
    classification["_reviewed"] = coerce_bool(reviewed)
    classification["_reviewed_timestamp"] = str(reviewed_timestamp or "").strip()
    classification["protocol_deviation"] = coerce_bool(
        classification.get("protocol_deviation", False)
    )
    classification["protocol_deviation_notes"] = str(
        classification.get("protocol_deviation_notes", "") or ""
    ).strip()

    if not classification["_reviewed"]:
        classification["_reviewed_timestamp"] = ""
    if not classification["protocol_deviation"]:
        classification["protocol_deviation_notes"] = ""

    classification.pop("dvt", None)
    classification.pop("review_status", None)

    if "frames" not in data or not isinstance(data["frames"], dict):
        data["frames"] = {}

    if "frame_grading" not in data or not isinstance(data["frame_grading"], dict):
        data["frame_grading"] = {}

    return data


def export_labelme_annotation(
    data,
    file_path,
    patient_id="",
    image_width=0,
    image_height=0,
    clinician_name="",
    clinician_email="",
):
    normalized = ensure_annotation_schema(copy.deepcopy(data))
    classification = normalized["classification"]

    shapes = []
    for frame_key, polygons in normalized["frames"].items():
        for poly in polygons:
            shapes.append(
                {
                    "label": poly["label"],
                    "points": poly["points"],
                    "group_id": None,
                    "description": "",
                    "shape_type": "polygon",
                    "frame": int(frame_key),
                    "flags": {},
                }
            )

    return {
        "version": "1.0",
        "annotator": build_labelme_annotator(clinician_name, clinician_email),
        "flags": {
            "patient_id": patient_id,
            "thrombosis": classification.get("thrombosis", ""),
            "compressibility": classification.get("compressibility", ""),
            "_reviewed": bool(classification.get("_reviewed", False)),
            "_reviewed_timestamp": classification.get("_reviewed_timestamp", ""),
            "protocol_deviation": bool(classification.get("protocol_deviation", False)),
            "protocol_deviation_notes": classification.get("protocol_deviation_notes", ""),
        },
        "frame_gradings": dict(normalized.get("frame_grading", {})),
        "shapes": shapes,
        "imagePath": file_path,
        "imageWidth": image_width,
        "imageHeight": image_height,
    }


def import_labelme_annotation(data, ann):
    normalized = ensure_annotation_schema(data)
    flags = ann.get("flags", {}) if isinstance(ann, dict) else {}
    classification = normalized["classification"]

    classification["thrombosis"] = normalize_thrombosis_value(
        flags.get("thrombosis", flags.get("dvt", ""))
    )
    classification["compressibility"] = normalize_compressibility_value(
        flags.get("compressibility", "")
    )
    classification["_reviewed"] = coerce_bool(
        flags.get("_reviewed", flags.get("reviewed", False))
    )
    classification["_reviewed_timestamp"] = str(
        flags.get("_reviewed_timestamp", flags.get("reviewed_timestamp", "")) or ""
    ).strip()
    classification["protocol_deviation"] = coerce_bool(flags.get("protocol_deviation", False))
    classification["protocol_deviation_notes"] = str(
        flags.get("protocol_deviation_notes", "") or ""
    ).strip()

    for frame_key, grading_value in (ann.get("frame_gradings", {}) or {}).items():
        if grading_value:
            normalized["frame_grading"][str(frame_key)] = grading_value

    for shape in ann.get("shapes", []) or []:
        frame_key = str(shape.get("frame", 0))
        if frame_key not in normalized["frames"]:
            normalized["frames"][frame_key] = []
        normalized["frames"][frame_key].append(
            {
                "label": shape.get("label", "polygon"),
                "points": shape.get("points", []),
            }
        )

    return ensure_annotation_schema(normalized)


def _darwin_updated_at(now=None):
    current_time = now or datetime.now()
    return current_time.strftime("%Y-%m-%dT%H:%M:%S")


def build_darwin_tag_annotation(name, value, frame_index=0, annotator=None, now=None):
    annotators = [annotator] if annotator else []
    return {
        "annotators": annotators,
        "frames": {
            str(frame_index): {
                "keyframe": True,
                "tag": {},
            }
        },
        "id": str(uuid.uuid4()),
        "name": name,
        "properties": [
            {
                "frame_index": frame_index,
                "name": name,
                "value": value,
            }
        ],
        "ranges": [[frame_index, frame_index + 1]],
        "reviewers": [],
        "slot_names": ["0"],
        "updated_at": _darwin_updated_at(now=now),
    }


def export_darwin_annotation(
    data,
    dcm_filename,
    patient_id="",
    image_width=0,
    image_height=0,
    frame_count=1,
    clinician_name="",
    clinician_email="",
    now=None,
):
    normalized = ensure_annotation_schema(copy.deepcopy(data))
    classification = normalized["classification"]
    annotator = build_darwin_annotator_actor(clinician_name, clinician_email)
    annotations_list = []

    for frame_key, polygons in normalized["frames"].items():
        for poly in polygons:
            pts = poly["points"]
            if len(pts) < 3:
                continue

            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            annotations_list.append(
                {
                    "annotators": [annotator] if annotator else [],
                    "frames": {
                        str(int(frame_key)): {
                            "bounding_box": {
                                "x": min(xs),
                                "y": min(ys),
                                "w": max(xs) - min(xs),
                                "h": max(ys) - min(ys),
                            },
                            "keyframe": True,
                            "polygon": {
                                "paths": [[{"x": p[0], "y": p[1]} for p in pts]]
                            },
                        }
                    },
                    "global_sub_types": {},
                    "id": str(uuid.uuid4()),
                    "interpolate_algorithm": "linear-1.1",
                    "interpolated": True,
                    "name": poly.get("label", "polygon"),
                    "properties": [],
                    "ranges": [[int(frame_key), int(frame_key) + 1]],
                    "reviewers": [],
                    "slot_names": ["0"],
                    "updated_at": _darwin_updated_at(now=now),
                }
            )

    for grading_frame_key, grading_value in normalized.get("frame_grading", {}).items():
        if grading_value:
            annotations_list.append(
                build_darwin_tag_annotation(
                    "ACEP Grading Score",
                    grading_value.replace("Grade ", ""),
                    int(grading_frame_key),
                    annotator=annotator,
                    now=now,
                )
            )

    if classification.get("thrombosis"):
        annotations_list.append(
            build_darwin_tag_annotation(
                "Thrombosis",
                classification["thrombosis"],
                annotator=annotator,
                now=now,
            )
        )

    if classification.get("compressibility"):
        annotations_list.append(
            build_darwin_tag_annotation(
                "Compressibility",
                classification["compressibility"],
                annotator=annotator,
                now=now,
            )
        )

    annotations_list.append(
        build_darwin_tag_annotation(
            "_reviewed",
            "true" if classification.get("_reviewed") else "false",
            annotator=annotator,
            now=now,
        )
    )

    if classification.get("_reviewed") and classification.get("_reviewed_timestamp"):
        annotations_list.append(
            build_darwin_tag_annotation(
                "_reviewed_timestamp",
                classification["_reviewed_timestamp"],
                annotator=annotator,
                now=now,
            )
        )

    annotations_list.append(
        build_darwin_tag_annotation(
            "Protocol Deviation",
            "true" if classification.get("protocol_deviation") else "false",
            annotator=annotator,
            now=now,
        )
    )

    if classification.get("protocol_deviation") and classification.get("protocol_deviation_notes"):
        annotations_list.append(
            build_darwin_tag_annotation(
                "Protocol Deviation Notes",
                classification["protocol_deviation_notes"],
                annotator=annotator,
                now=now,
            )
        )

    return {
        "version": "2.0",
        "schema_ref": "https://darwin-public.s3.eu-west-1.amazonaws.com/darwin_json/2.0/schema.json",
        "item": {
            "name": dcm_filename,
            "path": "/",
            "source_info": {
                "item_id": str(uuid.uuid4()),
                "patient_id": patient_id,
                "dataset": {
                    "name": "",
                    "slug": "",
                    "dataset_management_url": "",
                },
                "team": {
                    "name": "",
                    "slug": "",
                },
                "workview_url": "",
            },
            "slots": [
                {
                    "type": "dicom",
                    "slot_name": "0",
                    "width": image_width,
                    "height": image_height,
                    "fps": None,
                    "thumbnail_url": "",
                    "source_files": [
                        {
                            "file_name": dcm_filename,
                            "url": "",
                        }
                    ],
                    "frame_count": frame_count,
                    "frame_urls": [],
                    "metadata": {
                        "handler": None,
                        "shape": None,
                        "colorspace": "RGB",
                        "primary_plane": "AXIAL",
                    },
                }
            ],
        },
        "annotations": annotations_list,
        "properties": [],
    }


def import_darwin_annotation(data, darwin):
    normalized = ensure_annotation_schema(data)
    classification = normalized["classification"]

    for ann in (darwin.get("annotations", []) if isinstance(darwin, dict) else []):
        if ann.get("properties"):
            for prop in ann.get("properties", []):
                prop_name = prop.get("name", "")
                prop_value = prop.get("value", "")
                if prop_name == "ACEP Grading Score":
                    frame_idx = prop.get("frame_index", 0)
                    grading_str = f"Grade {prop_value}" if prop_value else ""
                    if grading_str:
                        normalized["frame_grading"][str(frame_idx)] = grading_str
                elif prop_name in ("Thrombosis", "DVT Status"):
                    classification["thrombosis"] = normalize_thrombosis_value(prop_value)
                elif prop_name == "Compressibility":
                    classification["compressibility"] = normalize_compressibility_value(prop_value)
                elif prop_name in ("_reviewed", "Review Status"):
                    classification["_reviewed"] = coerce_bool(prop_value)
                elif prop_name in ("_reviewed_timestamp", "Reviewed Timestamp"):
                    classification["_reviewed_timestamp"] = str(prop_value or "").strip()
                elif prop_name == "Protocol Deviation":
                    classification["protocol_deviation"] = coerce_bool(prop_value)
                elif prop_name == "Protocol Deviation Notes":
                    classification["protocol_deviation_notes"] = str(prop_value or "").strip()
            continue

        for frame_key, frame_content in ann.get("frames", {}).items():
            polygon_data = frame_content.get("polygon", {})
            for path in polygon_data.get("paths", []):
                points = [[pt["x"], pt["y"]] for pt in path]
                if len(points) < 3:
                    continue
                if frame_key not in normalized["frames"]:
                    normalized["frames"][frame_key] = []
                normalized["frames"][frame_key].append(
                    {
                        "label": ann.get("name", "polygon"),
                        "points": points,
                    }
                )

    return ensure_annotation_schema(normalized)


def dumps_pretty_json(payload):
    return json.dumps(payload, indent=2, ensure_ascii=False)
