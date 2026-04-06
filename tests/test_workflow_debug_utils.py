import unittest

from workflow_debug_utils import (
    parse_debug_allow_all_steps,
    should_force_annotation_stage,
)


class WorkflowDebugUtilsTests(unittest.TestCase):
    def test_parse_debug_allow_all_steps_accepts_truthy_values(self):
        self.assertTrue(parse_debug_allow_all_steps("yes"))
        self.assertTrue(parse_debug_allow_all_steps("TRUE"))
        self.assertTrue(parse_debug_allow_all_steps("1"))

    def test_parse_debug_allow_all_steps_rejects_falsey_values(self):
        self.assertFalse(parse_debug_allow_all_steps(""))
        self.assertFalse(parse_debug_allow_all_steps("no"))
        self.assertFalse(parse_debug_allow_all_steps(None))

    def test_should_force_annotation_stage_respects_debug_mode(self):
        self.assertTrue(should_force_annotation_stage("Ordered files", True, False))
        self.assertFalse(should_force_annotation_stage("Ordered files", True, True))
        self.assertFalse(should_force_annotation_stage("Anonymized files", True, False))
        self.assertFalse(should_force_annotation_stage("Selected files", False, False))


if __name__ == "__main__":
    unittest.main()
