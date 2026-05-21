import os
import re


THROMBOSIS_CODE_TO_VALUE = {
    "DVT1": "DVT1",
    "DVT0": "DVT0",
    "X": "",
}

LEGACY_THROMBOSIS_CODE_TO_VALUE = {
    "D": "DVT1",
    "N": "DVT0",
    "X": "",
}

COMPRESSIBILITY_CODE_TO_VALUE = {
    "COMP2": "COMP2",
    "COMP1": "COMP1",
    "COMP0": "COMP0",
    "X": "",
}

LEGACY_COMPRESSIBILITY_CODE_TO_VALUE = {
    "FC": "COMP2",
    "PC": "COMP1",
    "NC": "COMP0",
    "X": "",
}

THROMBOSIS_LABEL_BY_VALUE = {
    "": "",
    "DVT1": "Yes",
    "DVT0": "No",
}

COMPRESSIBILITY_LABEL_BY_VALUE = {
    "": "",
    "COMP2": "Yes",
    "COMP1": "Partial",
    "COMP0": "No",
}

DEFAULT_TAG_LABEL_BY_VALUE = {
    "none": "None",
    "CFVr-L": "Common Femoral Vein Random Image",
    "CFV-L": "Common Femoral Vein",
    "CFVr-R": "Common Femoral Vein Random Image",
    "CFV-R": "Common Femoral Vein",
    "GSVr-L": "Great Saphenous Vein Random Image",
    "GSV-L": "Great Saphenous Vein",
    "GSVr-R": "Great Saphenous Vein Random Image",
    "GSV-R": "Great Saphenous Vein",
    "FVr-L": "Femoral Vein Random Image",
    "FV-L": "Femoral Vein",
    "FVr-R": "Femoral Vein Random Image",
    "FV-R": "Femoral Vein",
    "FV-Dr-L": "Femoral Vein Doppler Random Image",
    "FV-D-L": "Femoral Vein Doppler",
    "FV-Dr-R": "Femoral Vein Doppler Random Image",
    "FV-D-R": "Femoral Vein Doppler",
    "PVr-L": "Popliteal Vein Random Image",
    "PV-L": "Popliteal Vein",
    "PVr-R": "Popliteal Vein Random Image",
    "PV-R": "Popliteal Vein",
    "OPT-L": "Optional View",
    "OPT-R": "Optional View ",
}

DVT_CODE_TO_VALUE = dict(THROMBOSIS_CODE_TO_VALUE)
DVT_CODE_TO_VALUE.update(LEGACY_THROMBOSIS_CODE_TO_VALUE)

VALUE_TO_THROMBOSIS_CODE = {
    "": "X",
    "DVT1": "DVT1",
    "DVT0": "DVT0",
}

VALUE_TO_COMPRESSIBILITY_CODE = {
    "": "X",
    "COMP2": "COMP2",
    "COMP1": "COMP1",
    "COMP0": "COMP0",
}

THROMBOSIS_VALUE_BY_LABEL = {
    "YES": "DVT1",
    "NO": "DVT0",
    "DVT1": "DVT1",
    "DVT0": "DVT0",
    "DVT": "DVT1",
    "NO DVT": "DVT0",
}

COMPRESSIBILITY_VALUE_BY_LABEL = {
    "YES": "COMP2",
    "PARTIAL": "COMP1",
    "NO": "COMP0",
    "COMP2": "COMP2",
    "COMP1": "COMP1",
    "COMP0": "COMP0",
    "FC": "COMP2",
    "PC": "COMP1",
    "NC": "COMP0",
    "FULL": "COMP2",
    "NONE": "COMP0",
}

GROUPED_FILE_NO_PATTERN = re.compile(r"^\d(?:_\d{3})+$")
PLAIN_FILE_NO_PATTERN = re.compile(r"^\d+$")
LEG_NAME_BY_SUFFIX = {
    "-L": "Left",
    "-R": "Right",
}
TAG_SUFFIX_BY_LEG_NAME = {
    "Left": "-L",
    "Right": "-R",
}


def looks_anonymized_filename(filename):
    stem = os.path.splitext(os.path.basename(filename))[0]
    return stem.startswith("anonymized_")


def normalize_tag_values(tag_values):
    normalized = []
    for tag in tag_values or ():
        if not tag:
            continue
        normalized.append(str(tag))
    return sorted(set(normalized), key=len, reverse=True)


def normalize_thrombosis_value(value):
    normalized = str(value or "").strip()
    if not normalized:
        return ""

    upper_value = normalized.upper()
    if normalized in THROMBOSIS_LABEL_BY_VALUE:
        return normalized
    if upper_value in THROMBOSIS_VALUE_BY_LABEL:
        return THROMBOSIS_VALUE_BY_LABEL[upper_value]
    return normalized


def thrombosis_value_to_label(value):
    normalized = normalize_thrombosis_value(value)
    return THROMBOSIS_LABEL_BY_VALUE.get(normalized, normalized)


def thrombosis_label_to_value(label):
    normalized = str(label or "").strip()
    if not normalized:
        return ""
    if normalized in THROMBOSIS_LABEL_BY_VALUE:
        return normalized
    return THROMBOSIS_VALUE_BY_LABEL.get(normalized.upper(), normalized)


def normalize_compressibility_value(value):
    normalized = str(value or "").strip()
    if not normalized:
        return ""

    upper_value = normalized.upper()
    if normalized in COMPRESSIBILITY_LABEL_BY_VALUE:
        return normalized
    if upper_value in COMPRESSIBILITY_VALUE_BY_LABEL:
        return COMPRESSIBILITY_VALUE_BY_LABEL[upper_value]
    return normalized


def compressibility_value_to_label(value):
    normalized = normalize_compressibility_value(value)
    return COMPRESSIBILITY_LABEL_BY_VALUE.get(normalized, normalized)


def compressibility_label_to_value(label):
    normalized = str(label or "").strip()
    if not normalized:
        return ""
    if normalized in COMPRESSIBILITY_LABEL_BY_VALUE:
        return normalized
    return COMPRESSIBILITY_VALUE_BY_LABEL.get(normalized.upper(), normalized)


def encode_thrombosis_code(value):
    return VALUE_TO_THROMBOSIS_CODE.get(normalize_thrombosis_value(value), "X")


def decode_thrombosis_code(code):
    normalized = str(code or "").strip().upper()
    if normalized in THROMBOSIS_CODE_TO_VALUE:
        return THROMBOSIS_CODE_TO_VALUE[normalized]
    return LEGACY_THROMBOSIS_CODE_TO_VALUE.get(normalized, "")


def encode_dvt_code(value):
    return encode_thrombosis_code(value)


def decode_dvt_code(code):
    return decode_thrombosis_code(code)


def encode_compressibility_code(value):
    return VALUE_TO_COMPRESSIBILITY_CODE.get(normalize_compressibility_value(value), "X")


def decode_compressibility_code(code):
    normalized = str(code or "").strip().upper()
    if normalized in COMPRESSIBILITY_CODE_TO_VALUE:
        return COMPRESSIBILITY_CODE_TO_VALUE[normalized]
    return LEGACY_COMPRESSIBILITY_CODE_TO_VALUE.get(normalized, "")


def encode_review_code(reviewed):
    return "R" if bool(reviewed) else "U"


def decode_review_code(code):
    return str(code or "").strip().upper() == "R"


def tag_value_to_display_label(tag_value):
    normalized = str(tag_value or "").strip()
    if not normalized:
        return ""
    return DEFAULT_TAG_LABEL_BY_VALUE.get(normalized, normalized).strip()


def build_tag_display_lookup(tag_values):
    lookup = {}
    for raw_value in tag_values or ():
        if not raw_value:
            continue
        raw_value = str(raw_value)
        label = tag_value_to_display_label(raw_value)
        if label in lookup and lookup[label] != raw_value:
            label = f"{label} [{raw_value}]"
        lookup[label] = raw_value
    return lookup


def split_tag_value_and_leg(tag_value, default_leg="Left"):
    normalized = str(tag_value or "").strip()
    default_leg = default_leg if default_leg in TAG_SUFFIX_BY_LEG_NAME else "Left"
    if not normalized or normalized.lower() == "none":
        return "", default_leg

    for suffix, leg_name in LEG_NAME_BY_SUFFIX.items():
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)], leg_name

    return "", default_leg


def compose_tag_value_with_leg(base_tag, leg_name):
    normalized_base = str(base_tag or "").strip()
    suffix = TAG_SUFFIX_BY_LEG_NAME.get(str(leg_name or "").strip())
    if not normalized_base or suffix is None:
        return ""
    return f"{normalized_base}{suffix}"


def build_side_neutral_tag_display_lookup(tag_values):
    lookup = {}
    for raw_value in tag_values or ():
        base_tag, _ = split_tag_value_and_leg(raw_value)
        if not base_tag:
            continue

        display_label = tag_value_to_display_label(raw_value)
        if not display_label:
            continue

        if display_label in lookup:
            continue
        lookup[display_label] = base_tag
    return lookup


def group_tag_values_by_leg(tag_values):
    grouped = {
        "Left Leg": [],
        "Right Leg": [],
    }
    for raw_value in tag_values or ():
        if not raw_value:
            continue
        raw_value = str(raw_value)
        if raw_value.strip().lower() == "none":
            continue
        if raw_value.endswith("-R"):
            grouped["Right Leg"].append(raw_value)
        else:
            grouped["Left Leg"].append(raw_value)
    return {
        "Left Leg": tuple(grouped["Left Leg"]),
        "Right Leg": tuple(grouped["Right Leg"]),
    }


def format_file_no(file_no):
    if isinstance(file_no, int):
        return f"{file_no:04_}"
    return str(file_no)


def build_anonymized_filename(
    patient_id,
    file_no,
    tag,
    thrombosis="",
    compressibility="",
    reviewed=False,
    include_classification=False,
    extension=".dcm",
    dvt=None,
):
    if dvt is not None and not thrombosis:
        thrombosis = dvt

    file_no_str = format_file_no(file_no)
    stem = f"anonymized_{patient_id}_{file_no_str}_{tag}"
    return f"{stem}{extension}"


def _parse_compact_suffix(suffix):
    if not suffix:
        return {
            "thrombosis": "",
            "dvt": "",
            "compressibility": "",
            "reviewed": False,
        }

    if not suffix.startswith("-"):
        return None

    parts = suffix[1:].split("-")
    if len(parts) != 3:
        return None

    thrombosis_code, compressibility_code, review_code = parts
    thrombosis = decode_thrombosis_code(thrombosis_code)
    return {
        "thrombosis": thrombosis,
        "dvt": thrombosis,
        "compressibility": decode_compressibility_code(compressibility_code),
        "reviewed": decode_review_code(review_code),
    }


def _split_patient_id_and_file_no(prefix):
    parts = prefix.split("_")
    if len(parts) < 2:
        return None

    for tail_size in range(len(parts) - 1, 1, -1):
        file_no = "_".join(parts[-tail_size:])
        if GROUPED_FILE_NO_PATTERN.fullmatch(file_no):
            patient_id = "_".join(parts[:-tail_size])
            if patient_id:
                return patient_id, file_no

    file_no = parts[-1]
    if PLAIN_FILE_NO_PATTERN.fullmatch(file_no):
        patient_id = "_".join(parts[:-1])
        if patient_id:
            return patient_id, file_no

    return None


def _parse_unrecognized_anonymized_payload(payload):
    parts = payload.split("_")
    if len(parts) < 3:
        return None

    candidates = []
    for file_no_start in range(1, len(parts) - 1):
        for file_no_end in range(len(parts) - 1, file_no_start, -1):
            patient_id = "_".join(parts[:file_no_start])
            file_no = "_".join(parts[file_no_start:file_no_end])
            tag = "_".join(parts[file_no_end:])

            if not patient_id or not tag:
                continue
            is_grouped_file_no = GROUPED_FILE_NO_PATTERN.fullmatch(file_no)
            is_plain_file_no = PLAIN_FILE_NO_PATTERN.fullmatch(file_no)
            if is_grouped_file_no or is_plain_file_no:
                candidates.append(
                    (
                        1 if is_grouped_file_no else 0,
                        file_no_start,
                        file_no_end - file_no_start,
                        patient_id,
                        file_no,
                        tag,
                    )
                )

    if not candidates:
        return None

    _, _, _, patient_id, file_no, tag = max(candidates)
    return patient_id, file_no, tag


def parse_anonymized_filename(filename, tag_values):
    stem = os.path.splitext(os.path.basename(filename))[0]
    if not stem.startswith("anonymized_"):
        return None

    payload = stem[len("anonymized_") :]

    for tag in normalize_tag_values(tag_values):
        marker = f"_{tag}"
        marker_index = payload.rfind(marker)
        if marker_index == -1:
            continue

        prefix = payload[:marker_index]
        suffix = payload[marker_index + len(marker) :]
        compact = _parse_compact_suffix(suffix)
        if compact is None:
            continue

        split_result = _split_patient_id_and_file_no(prefix)
        if not split_result:
            continue

        patient_id, file_no = split_result

        return {
            "patient_id": patient_id,
            "file_no": file_no,
            "tag": tag,
            "thrombosis": compact["thrombosis"],
            "dvt": compact["dvt"],
            "compressibility": compact["compressibility"],
            "reviewed": compact["reviewed"],
        }

    fallback = _parse_unrecognized_anonymized_payload(payload)
    if fallback:
        patient_id, file_no, tag = fallback
        return {
            "patient_id": patient_id,
            "file_no": file_no,
            "tag": tag,
            "thrombosis": "",
            "dvt": "",
            "compressibility": "",
            "reviewed": False,
        }

    return None
