import os
import re


DVT_CODE_TO_VALUE = {
    "D": "DVT",
    "N": "NO DVT",
    "X": "",
}

COMPRESSIBILITY_CODE_TO_VALUE = {
    "FC": "FC",
    "PC": "PC",
    "NC": "NC",
    "X": "",
}

COMPRESSIBILITY_LABEL_BY_VALUE = {
    "": "",
    "FC": "Full",
    "PC": "Partial",
    "NC": "None",
}

COMPRESSIBILITY_VALUE_BY_LABEL = {
    label: value for value, label in COMPRESSIBILITY_LABEL_BY_VALUE.items()
}

REVIEW_CODE_TO_VALUE = {
    "R": True,
    "U": False,
}

VALUE_TO_DVT_CODE = {value: code for code, value in DVT_CODE_TO_VALUE.items()}
VALUE_TO_COMPRESSIBILITY_CODE = {
    value: code for code, value in COMPRESSIBILITY_CODE_TO_VALUE.items()
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


def encode_dvt_code(value):
    return VALUE_TO_DVT_CODE.get(value or "", "X")


def decode_dvt_code(code):
    return DVT_CODE_TO_VALUE.get((code or "").upper(), "")


def encode_compressibility_code(value):
    return VALUE_TO_COMPRESSIBILITY_CODE.get(value or "", "X")


def decode_compressibility_code(code):
    return COMPRESSIBILITY_CODE_TO_VALUE.get((code or "").upper(), "")


def compressibility_value_to_label(value):
    normalized = str(value or "").strip()
    return COMPRESSIBILITY_LABEL_BY_VALUE.get(normalized, normalized)


def compressibility_label_to_value(label):
    normalized = str(label or "").strip()
    if normalized in COMPRESSIBILITY_VALUE_BY_LABEL:
        return COMPRESSIBILITY_VALUE_BY_LABEL[normalized]
    if normalized in COMPRESSIBILITY_LABEL_BY_VALUE:
        return normalized
    return normalized


def encode_review_code(reviewed):
    return "R" if bool(reviewed) else "U"


def decode_review_code(code):
    return REVIEW_CODE_TO_VALUE.get((code or "").upper(), False)


def format_file_no(file_no):
    if isinstance(file_no, int):
        return f"{file_no:04_}"
    return str(file_no)


def build_anonymized_filename(
    patient_id,
    file_no,
    tag,
    dvt="",
    compressibility="",
    reviewed=False,
    include_classification=False,
    extension=".dcm",
):
    file_no_str = format_file_no(file_no)
    stem = f"anonymized_{patient_id}_{file_no_str}_{tag}"
    if include_classification:
        stem = (
            f"{stem}-"
            f"{encode_dvt_code(dvt)}-"
            f"{encode_compressibility_code(compressibility)}-"
            f"{encode_review_code(reviewed)}"
        )
    return f"{stem}{extension}"


def _parse_compact_suffix(suffix):
    if not suffix:
        return {
            "dvt": "",
            "compressibility": "",
            "reviewed": False,
        }

    if not suffix.startswith("-"):
        return None

    parts = suffix[1:].split("-")
    if len(parts) != 3:
        return None

    dvt_code, compressibility_code, review_code = parts
    return {
        "dvt": decode_dvt_code(dvt_code),
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
            "dvt": compact["dvt"],
            "compressibility": compact["compressibility"],
            "reviewed": compact["reviewed"],
        }

    return None
