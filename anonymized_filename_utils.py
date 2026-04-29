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
    return DEFAULT_TAG_LABEL_BY_VALUE.get(normalized, normalized)


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

    return None
