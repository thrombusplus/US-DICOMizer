import unittest

from anonymized_filename_utils import (
    build_anonymized_filename,
    compressibility_label_to_value,
    compressibility_value_to_label,
    parse_anonymized_filename,
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
                "dvt": "",
                "compressibility": "",
                "reviewed": False,
            },
        )

    def test_parse_expanded_anonymized_filename_with_hyphenated_tag(self):
        parsed = parse_anonymized_filename(
            "anonymized_study_A-01_0_123_FV-D-R-D-PC-R.dcm",
            TAG_VALUES,
        )

        self.assertEqual(
            parsed,
            {
                "patient_id": "study_A-01",
                "file_no": "0_123",
                "tag": "FV-D-R",
                "dvt": "DVT",
                "compressibility": "PC",
                "reviewed": True,
            },
        )

    def test_parse_prefers_longest_matching_tag_for_patient_ids_with_underscores(self):
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
                "dvt": "NO DVT",
                "compressibility": "NC",
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

    def test_build_compact_filename_from_classification_state(self):
        filename = build_anonymized_filename(
            patient_id="P-01",
            file_no=1,
            tag="FV-D-R",
            dvt="DVT",
            compressibility="FC",
            reviewed=True,
            include_classification=True,
        )

        self.assertEqual(filename, "anonymized_P-01_0_001_FV-D-R-D-FC-R.dcm")

    def test_compressibility_value_to_pretty_label(self):
        self.assertEqual(compressibility_value_to_label("FC"), "Full")
        self.assertEqual(compressibility_value_to_label("PC"), "Partial")
        self.assertEqual(compressibility_value_to_label("NC"), "None")

    def test_compressibility_pretty_label_to_value(self):
        self.assertEqual(compressibility_label_to_value("Full"), "FC")
        self.assertEqual(compressibility_label_to_value("Partial"), "PC")
        self.assertEqual(compressibility_label_to_value("None"), "NC")
        self.assertEqual(compressibility_label_to_value("FC"), "FC")


if __name__ == "__main__":
    unittest.main()
