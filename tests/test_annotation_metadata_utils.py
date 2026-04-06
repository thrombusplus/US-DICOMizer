import unittest

from annotation_metadata_utils import (
    ensure_annotation_schema,
    export_darwin_annotation,
    export_labelme_annotation,
    import_darwin_annotation,
    import_labelme_annotation,
)


class AnnotationMetadataUtilsTests(unittest.TestCase):
    def test_ensure_annotation_schema_migrates_legacy_fields(self):
        data = ensure_annotation_schema(
            {
                "classification": {
                    "dvt": "NO DVT",
                    "compressibility": "FC",
                    "review_status": {
                        "reviewed": True,
                        "timestamp": "2026-03-24T10:00:00",
                    },
                    "protocol_deviation": False,
                    "protocol_deviation_notes": "should be cleared",
                }
            }
        )

        self.assertEqual(data["classification"]["thrombosis"], "DVT0")
        self.assertEqual(data["classification"]["compressibility"], "COMP2")
        self.assertTrue(data["classification"]["_reviewed"])
        self.assertEqual(data["classification"]["_reviewed_timestamp"], "2026-03-24T10:00:00")
        self.assertFalse(data["classification"]["protocol_deviation"])
        self.assertEqual(data["classification"]["protocol_deviation_notes"], "")

    def test_export_labelme_annotation_uses_new_flags_and_annotator(self):
        payload = export_labelme_annotation(
            {
                "classification": {
                    "thrombosis": "DVT1",
                    "compressibility": "COMP1",
                    "_reviewed": True,
                    "_reviewed_timestamp": "2026-03-24T10:00:00",
                    "protocol_deviation": True,
                    "protocol_deviation_notes": "motion artifact",
                },
                "frame_grading": {"0": "Grade 3"},
                "frames": {
                    "0": [
                        {
                            "label": "Clot",
                            "points": [[1, 1], [4, 1], [4, 5]],
                        }
                    ]
                },
            },
            "scan.dcm",
            patient_id="PAT-1",
            image_width=640,
            image_height=480,
            clinician_name="Dr Example",
            clinician_email="dr@example.com",
        )

        self.assertEqual(payload["annotator"]["full_name"], "Dr Example")
        self.assertEqual(payload["annotator"]["email"], "dr@example.com")
        self.assertEqual(payload["flags"]["thrombosis"], "DVT1")
        self.assertEqual(payload["flags"]["compressibility"], "COMP1")
        self.assertTrue(payload["flags"]["_reviewed"])
        self.assertTrue(payload["flags"]["protocol_deviation"])
        self.assertEqual(payload["flags"]["protocol_deviation_notes"], "motion artifact")
        self.assertEqual(payload["frame_gradings"]["0"], "Grade 3")
        self.assertEqual(payload["shapes"][0]["frame"], 0)

    def test_import_labelme_annotation_accepts_legacy_flags(self):
        data = import_labelme_annotation(
            {},
            {
                "flags": {
                    "dvt": "DVT",
                    "compressibility": "NC",
                    "reviewed": True,
                    "reviewed_timestamp": "2026-03-24T11:00:00",
                    "protocol_deviation": False,
                    "protocol_deviation_notes": "should be cleared",
                },
                "frame_gradings": {"2": "Grade 4"},
                "shapes": [
                    {
                        "label": "Vein",
                        "points": [[0, 0], [2, 0], [2, 2]],
                        "frame": 2,
                    }
                ],
            },
        )

        self.assertEqual(data["classification"]["thrombosis"], "DVT1")
        self.assertEqual(data["classification"]["compressibility"], "COMP0")
        self.assertTrue(data["classification"]["_reviewed"])
        self.assertEqual(data["classification"]["_reviewed_timestamp"], "2026-03-24T11:00:00")
        self.assertFalse(data["classification"]["protocol_deviation"])
        self.assertEqual(data["classification"]["protocol_deviation_notes"], "")
        self.assertEqual(data["frame_grading"]["2"], "Grade 4")
        self.assertEqual(data["frames"]["2"][0]["label"], "Vein")

    def test_export_darwin_annotation_uses_new_properties_and_annotators(self):
        payload = export_darwin_annotation(
            {
                "classification": {
                    "thrombosis": "DVT0",
                    "compressibility": "COMP2",
                    "_reviewed": True,
                    "_reviewed_timestamp": "2026-03-24T12:00:00",
                    "protocol_deviation": True,
                    "protocol_deviation_notes": "wrong window",
                },
                "frame_grading": {"0": "Grade 5"},
                "frames": {
                    "0": [
                        {
                            "label": "Clot",
                            "points": [[1, 1], [3, 1], [3, 3]],
                        }
                    ]
                },
            },
            "scan.dcm",
            patient_id="PAT-2",
            image_width=320,
            image_height=240,
            frame_count=3,
            clinician_name="Dr Example",
            clinician_email="dr@example.com",
        )

        property_names = {
            prop["name"]
            for ann in payload["annotations"]
            for prop in ann.get("properties", [])
        }
        self.assertIn("Thrombosis", property_names)
        self.assertIn("Compressibility", property_names)
        self.assertIn("_reviewed", property_names)
        self.assertIn("_reviewed_timestamp", property_names)
        self.assertIn("Protocol Deviation", property_names)
        self.assertIn("Protocol Deviation Notes", property_names)

        annotators = [ann["annotators"] for ann in payload["annotations"]]
        self.assertTrue(all(actor_list == [{"full_name": "Dr Example", "email": "dr@example.com"}] for actor_list in annotators))

    def test_import_darwin_annotation_accepts_legacy_and_new_properties(self):
        data = import_darwin_annotation(
            {},
            {
                "annotations": [
                    {
                        "name": "DVT Status",
                        "properties": [{"frame_index": 0, "name": "DVT Status", "value": "NO DVT"}],
                    },
                    {
                        "name": "Compressibility",
                        "properties": [{"frame_index": 0, "name": "Compressibility", "value": "PC"}],
                    },
                    {
                        "name": "Review Status",
                        "properties": [{"frame_index": 0, "name": "Review Status", "value": "Reviewed"}],
                    },
                    {
                        "name": "Reviewed Timestamp",
                        "properties": [{"frame_index": 0, "name": "Reviewed Timestamp", "value": "2026-03-24T13:00:00"}],
                    },
                    {
                        "name": "Protocol Deviation",
                        "properties": [{"frame_index": 0, "name": "Protocol Deviation", "value": "true"}],
                    },
                    {
                        "name": "Protocol Deviation Notes",
                        "properties": [{"frame_index": 0, "name": "Protocol Deviation Notes", "value": "wrong probe"}],
                    },
                    {
                        "name": "ACEP Grading Score",
                        "properties": [{"frame_index": 1, "name": "ACEP Grading Score", "value": "3"}],
                    },
                    {
                        "name": "Clot",
                        "frames": {
                            "1": {
                                "polygon": {
                                    "paths": [[{"x": 1, "y": 1}, {"x": 3, "y": 1}, {"x": 3, "y": 3}]]
                                }
                            }
                        },
                    },
                ]
            },
        )

        self.assertEqual(data["classification"]["thrombosis"], "DVT0")
        self.assertEqual(data["classification"]["compressibility"], "COMP1")
        self.assertTrue(data["classification"]["_reviewed"])
        self.assertEqual(data["classification"]["_reviewed_timestamp"], "2026-03-24T13:00:00")
        self.assertTrue(data["classification"]["protocol_deviation"])
        self.assertEqual(data["classification"]["protocol_deviation_notes"], "wrong probe")
        self.assertEqual(data["frame_grading"]["1"], "Grade 3")
        self.assertEqual(data["frames"]["1"][0]["label"], "Clot")


if __name__ == "__main__":
    unittest.main()
