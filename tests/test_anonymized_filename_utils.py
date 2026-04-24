import unittest

from anonymized_filename_utils import (
    build_anonymized_filename,
    compressibility_label_to_value,
    compressibility_value_to_label,
    parse_anonymized_filename,
    tag_value_to_display_label,
    thrombosis_label_to_value,
    thrombosis_value_to_label,
)


TAG_VALUES = [
    "CFV-R",
    "CFVr-R",
    "FV-D-R",
]


class AnonymizedFilenameUtilsTests(unittest.TestCase):
    def test_parse_legacy_anonymized_filename_without_compact_suffix(self):
        parsed = parse_anonymized_filename(
            "anonymized_IT1-0071_0_001_CFV-R.dcm",
            TAG_VALUES,
        )

        self.assertEqual(
            parsed,
            {
                "patient_id": "IT1-0071",
                "file_no": "0_001",
                "tag": "CFV-R",
                "thrombosis": "",
                "dvt": "",
                "compressibility": "",
                "reviewed": False,
            },
        )

    def test_parse_expanded_anonymized_filename_with_new_values(self):
        parsed = parse_anonymized_filename(
            "anonymized_study_A-01_0_123_FV-D-R-DVT1-COMP1-R.dcm",
            TAG_VALUES,
        )

        self.assertEqual(
            parsed,
            {
                "patient_id": "study_A-01",
                "file_no": "0_123",
                "tag": "FV-D-R",
                "thrombosis": "DVT1",
                "dvt": "DVT1",
                "compressibility": "COMP1",
                "reviewed": True,
            },
        )

    def test_parse_prefers_longest_matching_tag_with_legacy_suffix_values(self):
        parsed = parse_anonymized_filename(
            "anonymized_patient_alpha-beta_1_001_CFVr-R-N-NC-U.dcm",
            TAG_VALUES,
        )

        self.assertEqual(
            parsed,
            {
                "patient_id": "patient_alpha-beta",
                "file_no": "1_001",
                "tag": "CFVr-R",
                "thrombosis": "DVT0",
                "dvt": "DVT0",
                "compressibility": "COMP0",
                "reviewed": False,
            },
        )

    def test_parse_supports_legacy_none_tag(self):
        parsed = parse_anonymized_filename(
            "anonymized_case_42_0_001_none.dcm",
            ["none"],
        )

        self.assertEqual(
            parsed,
            {
                "patient_id": "case_42",
                "file_no": "0_001",
                "tag": "none",
                "thrombosis": "",
                "dvt": "",
                "compressibility": "",
                "reviewed": False,
            },
        )

    def test_build_preserves_existing_file_number_format(self):
        filename = build_anonymized_filename(
            patient_id="P_01",
            file_no="0_001",
            tag="CFV-R",
        )

        self.assertEqual(filename, "anonymized_P_01_0_001_CFV-R.dcm")

    def test_build_ignores_annotation_classification_suffixes(self):
        filename = build_anonymized_filename(
            patient_id="P-01",
            file_no=1,
            tag="FV-D-R",
            thrombosis="DVT1",
            compressibility="COMP2",
            reviewed=True,
            include_classification=True,
        )

        self.assertEqual(filename, "anonymized_P-01_0_001_FV-D-R.dcm")

    def test_thrombosis_value_to_pretty_label(self):
        self.assertEqual(thrombosis_value_to_label("DVT1"), "Yes")
        self.assertEqual(thrombosis_value_to_label("DVT0"), "No")
        self.assertEqual(thrombosis_value_to_label("DVT"), "Yes")

    def test_thrombosis_pretty_label_to_value(self):
        self.assertEqual(thrombosis_label_to_value("Yes"), "DVT1")
        self.assertEqual(thrombosis_label_to_value("No"), "DVT0")
        self.assertEqual(thrombosis_label_to_value("DVT1"), "DVT1")

    def test_compressibility_value_to_pretty_label(self):
        self.assertEqual(compressibility_value_to_label("COMP2"), "Yes")
        self.assertEqual(compressibility_value_to_label("PC"), "Partial")
        self.assertEqual(compressibility_value_to_label("NC"), "No")

    def test_compressibility_pretty_label_to_value(self):
        self.assertEqual(compressibility_label_to_value("Yes"), "COMP2")
        self.assertEqual(compressibility_label_to_value("Partial"), "COMP1")
        self.assertEqual(compressibility_label_to_value("No"), "COMP0")
        self.assertEqual(compressibility_label_to_value("FC"), "COMP2")

    def test_tag_value_to_display_label_uses_human_readable_description(self):
        self.assertEqual(
            tag_value_to_display_label("CFVr-R"),
            "Common Femoral Vein Random Image(Right)",
        )


if __name__ == "__main__":
    unittest.main()
