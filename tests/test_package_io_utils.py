import tempfile
import unittest
from pathlib import Path

from package_io_utils import (
    build_sidecar_candidate_paths,
    find_existing_sidecar_paths,
    get_preferred_sidecar_paths,
    path_is_within,
)


class PackageIoUtilsTests(unittest.TestCase):
    def test_candidate_paths_include_package_annotations_folder(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dcm_path = root / "anonymized_case" / "scan.dcm"
            dcm_path.parent.mkdir(parents=True)
            dcm_path.write_bytes(b"")

            candidates = build_sidecar_candidate_paths(str(dcm_path), package_root=str(root))

            self.assertIn(str(root / "annotations" / "scan.json"), candidates["generic"])
            self.assertIn(str(root / "annotations" / "scan_darwin.json"), candidates["darwin"])

    def test_existing_sidecars_are_found_in_annotations_folder(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dcm_path = root / "anonymized_case" / "scan.dcm"
            ann_dir = root / "annotations"
            dcm_path.parent.mkdir(parents=True)
            ann_dir.mkdir(parents=True)
            dcm_path.write_bytes(b"")
            (ann_dir / "scan.json").write_text("{}", encoding="utf-8")

            existing = find_existing_sidecar_paths(str(dcm_path), package_root=str(root))

            self.assertEqual(existing["generic"], [str(ann_dir / "scan.json")])
            self.assertEqual(existing["darwin"], [])

    def test_preferred_sidecar_path_uses_dicom_directory_even_when_annotations_exist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            dcm_path = root / "anonymized_case" / "scan.dcm"
            ann_dir = root / "annotations"
            dcm_path.parent.mkdir(parents=True)
            ann_dir.mkdir(parents=True)
            dcm_path.write_bytes(b"")
            (ann_dir / "scan.json").write_text("{}", encoding="utf-8")

            preferred = get_preferred_sidecar_paths(str(dcm_path), package_root=str(root))

            self.assertEqual(preferred["generic"], str(dcm_path.with_suffix(".json")))
            self.assertEqual(
                preferred["darwin"],
                str(dcm_path.with_name(f"{dcm_path.stem}_darwin.json")),
            )

    def test_path_is_within_handles_similar_prefixes_safely(self):
        self.assertTrue(path_is_within(r"C:\workspace\output\case", r"C:\workspace\output"))
        self.assertFalse(path_is_within(r"C:\workspace\output_backup\case", r"C:\workspace\output"))


if __name__ == "__main__":
    unittest.main()
