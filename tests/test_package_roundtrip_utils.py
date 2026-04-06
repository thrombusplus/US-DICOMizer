import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from annotation_metadata_utils import export_darwin_annotation
from package_roundtrip_utils import (
    export_package_to_zip,
    load_annotation_sidecar_data,
    write_annotation_sidecars,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DICOM = REPO_ROOT / ".samples" / "FR1-0017" / "anonymized_FR1-0017_0_001_CFVr-R.dcm"


class PackageRoundTripUtilsTests(unittest.TestCase):
    def test_write_annotation_sidecars_migrates_legacy_annotations_folder_to_root(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            package_root = Path(tmp_dir) / "folder_case"
            dcm_path = package_root / SAMPLE_DICOM.name
            annotations_dir = package_root / "annotations"
            annotations_dir.mkdir(parents=True)
            shutil.copy2(SAMPLE_DICOM, dcm_path)

            legacy_payload = export_darwin_annotation(
                {
                    "classification": {
                        "thrombosis": "DVT0",
                        "compressibility": "COMP0",
                        "_reviewed": False,
                        "_reviewed_timestamp": "",
                        "protocol_deviation": False,
                        "protocol_deviation_notes": "",
                    }
                },
                dcm_path.name,
                patient_id="PAT-LEGACY",
            )
            legacy_json_path = annotations_dir / f"{dcm_path.stem}.json"
            legacy_json_path.write_text(json.dumps(legacy_payload, indent=2), encoding="utf-8")

            detected_format, annotation_data, source_path = load_annotation_sidecar_data(
                str(dcm_path),
                package_root=str(package_root),
            )

            self.assertEqual(detected_format, "darwin")
            self.assertEqual(Path(source_path), legacy_json_path)

            annotation_data["classification"]["protocol_deviation"] = True
            annotation_data["classification"]["protocol_deviation_notes"] = "roundtrip-folder-check"
            annotation_data["classification"]["_reviewed"] = True
            annotation_data["classification"]["_reviewed_timestamp"] = "2026-04-06T18:00:00"

            write_annotation_sidecars(
                str(dcm_path),
                annotation_data,
                package_root=str(package_root),
                create_missing_format="Darwin V7",
                patient_id="PAT-UPDATED",
            )

            root_json_path = package_root / f"{dcm_path.stem}.json"
            darwin_suffix_path = package_root / f"{dcm_path.stem}_darwin.json"
            self.assertTrue(root_json_path.exists())
            self.assertFalse(darwin_suffix_path.exists())
            self.assertFalse(legacy_json_path.exists())
            self.assertFalse(annotations_dir.exists())

            exported_payload = json.loads(root_json_path.read_text(encoding="utf-8"))
            properties = {
                prop["name"]: prop["value"]
                for ann in exported_payload.get("annotations", [])
                for prop in ann.get("properties", [])
            }
            self.assertEqual(properties["Protocol Deviation"], "true")
            self.assertEqual(properties["Protocol Deviation Notes"], "roundtrip-folder-check")
            self.assertEqual(properties["_reviewed"], "true")
            self.assertEqual(properties["_reviewed_timestamp"], "2026-04-06T18:00:00")

    def test_export_package_to_zip_persists_updated_root_sidecars(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            package_root = Path(tmp_dir) / "zip_case"
            export_dir = Path(tmp_dir) / "exports"
            extract_dir = Path(tmp_dir) / "extracted"
            dcm_path = package_root / SAMPLE_DICOM.name
            annotations_dir = package_root / "annotations"
            annotations_dir.mkdir(parents=True)
            export_dir.mkdir(parents=True)
            shutil.copy2(SAMPLE_DICOM, dcm_path)

            old_payload = export_darwin_annotation(
                {
                    "classification": {
                        "thrombosis": "DVT0",
                        "compressibility": "COMP0",
                        "_reviewed": False,
                        "_reviewed_timestamp": "",
                        "protocol_deviation": False,
                        "protocol_deviation_notes": "stale-value",
                    }
                },
                dcm_path.name,
                patient_id="PAT-OLD",
            )
            (package_root / f"{dcm_path.stem}.json").write_text(json.dumps(old_payload, indent=2), encoding="utf-8")
            (annotations_dir / f"{dcm_path.stem}.json").write_text(json.dumps(old_payload, indent=2), encoding="utf-8")

            updated_annotations = {
                str(dcm_path): {
                    "classification": {
                        "thrombosis": "DVT1",
                        "compressibility": "COMP2",
                        "_reviewed": True,
                        "_reviewed_timestamp": "2026-04-06T18:05:00",
                        "protocol_deviation": True,
                        "protocol_deviation_notes": "roundtrip-zip-check",
                    }
                }
            }

            zip_path = export_package_to_zip(
                str(package_root),
                str(export_dir),
                "zip_case_export",
                updated_annotations,
                annotation_format="Darwin V7",
                patient_id_lookup=lambda _: "PAT-NEW",
            )

            self.assertTrue(Path(zip_path).exists())

            with zipfile.ZipFile(zip_path, "r") as archive:
                zip_members = set(archive.namelist())
                self.assertIn(f"{dcm_path.stem}.json", zip_members)
                self.assertNotIn(f"{dcm_path.stem}_darwin.json", zip_members)
                self.assertNotIn("annotations/", zip_members)
                self.assertNotIn(f"annotations/{dcm_path.stem}.json", zip_members)

            with zipfile.ZipFile(zip_path, "r") as archive:
                archive.extractall(extract_dir)

            exported_json_path = extract_dir / f"{dcm_path.stem}.json"
            self.assertTrue(exported_json_path.exists())
            exported_payload = json.loads(exported_json_path.read_text(encoding="utf-8"))
            properties = {
                prop["name"]: prop["value"]
                for ann in exported_payload.get("annotations", [])
                for prop in ann.get("properties", [])
            }

            self.assertEqual(properties["Thrombosis"], "DVT1")
            self.assertEqual(properties["Compressibility"], "COMP2")
            self.assertEqual(properties["Protocol Deviation"], "true")
            self.assertEqual(properties["Protocol Deviation Notes"], "roundtrip-zip-check")
            self.assertEqual(properties["_reviewed"], "true")
            self.assertEqual(properties["_reviewed_timestamp"], "2026-04-06T18:05:00")


if __name__ == "__main__":
    unittest.main()
