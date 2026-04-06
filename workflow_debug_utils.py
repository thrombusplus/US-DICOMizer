TRUE_VALUES = {"1", "true", "yes", "y", "on"}


def parse_debug_allow_all_steps(value) -> bool:
    return str(value or "").strip().lower() in TRUE_VALUES


def should_force_annotation_stage(source_stage: str, is_annotation_ready: bool, debug_allow_all_steps: bool) -> bool:
    return source_stage != "Anonymized files" and is_annotation_ready and not debug_allow_all_steps
