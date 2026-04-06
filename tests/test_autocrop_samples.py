import json
import unittest
import warnings
from pathlib import Path

import pydicom

from annotation_metadata_utils import import_darwin_annotation, import_labelme_annotation
from autocrop_utils import detect_dicom_autocrop_box


SAMPLES_DIR = Path(__file__).resolve().parents[1] / ".samples"
ANNOTATION_TOLERANCE_PX = 6.0

warnings.filterwarnings(
    "ignore",
    message=r".*Photometric Interpretation.*JFIF APP marker.*",
    category=UserWarning,
    module=r"pydicom\.pixels\.decoders\.base",
)


def _iter_sample_dicoms():
    return sorted(SAMPLES_DIR.rglob("*.dcm"))


def _find_annotation_path(dcm_path: Path) -> Path | None:
    candidates = [
        dcm_path.with_suffix(".json"),
        dcm_path.parent / "annotations" / f"{dcm_path.stem}.json",
    ]
    return next((path for path in candidates if path.exists()), None)


def _load_annotation_polygons(json_path: Path):
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if payload.get("version") == "2.0" and "annotations" in payload:
        normalized = import_darwin_annotation({}, payload)
    else:
        normalized = import_labelme_annotation({}, payload)
    return normalized.get("frames", {})


class AutoCropSampleRegressionTests(unittest.TestCase):
    def test_sample_bank_produces_valid_crop_boxes(self):
        if not SAMPLES_DIR.exists():
            self.skipTest(f"Samples directory not found: {SAMPLES_DIR}")

        sample_count = 0
        for dcm_path in _iter_sample_dicoms():
            ds = pydicom.dcmread(str(dcm_path))
            x0, y0, x1, y1 = detect_dicom_autocrop_box(ds, preferred_frame_index=0, method="hybrid")
            width = int(getattr(ds, "Columns", 0))
            height = int(getattr(ds, "Rows", 0))

            self.assertGreater(x1, x0, msg=dcm_path.name)
            self.assertGreater(y1, y0, msg=dcm_path.name)
            self.assertGreaterEqual(x0, 0, msg=dcm_path.name)
            self.assertGreaterEqual(y0, 0, msg=dcm_path.name)
            self.assertLessEqual(x1, width, msg=dcm_path.name)
            self.assertLessEqual(y1, height, msg=dcm_path.name)
            sample_count += 1

        self.assertGreaterEqual(sample_count, 100)

    def test_sample_bank_keeps_spatial_annotations_inside_crop(self):
        if not SAMPLES_DIR.exists():
            self.skipTest(f"Samples directory not found: {SAMPLES_DIR}")

        checked_cases = 0
        failures = []

        for dcm_path in _iter_sample_dicoms():
            annotation_path = _find_annotation_path(dcm_path)
            if annotation_path is None:
                continue

            frames = _load_annotation_polygons(annotation_path)
            points = []
            for frame_key, polygons in frames.items():
                for polygon in polygons:
                    for x, y in polygon.get("points", []):
                        points.append((float(x), float(y), int(frame_key)))

            if not points:
                continue

            checked_cases += 1
            ds = pydicom.dcmread(str(dcm_path))
            x0, y0, x1, y1 = detect_dicom_autocrop_box(ds, preferred_frame_index=0, method="hybrid")

            min_x = min(point[0] for point in points)
            min_y = min(point[1] for point in points)
            max_x = max(point[0] for point in points)
            max_y = max(point[1] for point in points)

            if not (
                min_x >= x0 - ANNOTATION_TOLERANCE_PX
                and min_y >= y0 - ANNOTATION_TOLERANCE_PX
                and max_x <= x1 + ANNOTATION_TOLERANCE_PX
                and max_y <= y1 + ANNOTATION_TOLERANCE_PX
            ):
                failures.append(
                    f"{dcm_path.name}: crop={(x0, y0, x1, y1)} "
                    f"annotation_bounds={(round(min_x, 2), round(min_y, 2), round(max_x, 2), round(max_y, 2))}"
                )

        self.assertGreaterEqual(checked_cases, 40)
        self.assertEqual([], failures, msg="\n".join(failures[:20]))


if __name__ == "__main__":
    unittest.main()
