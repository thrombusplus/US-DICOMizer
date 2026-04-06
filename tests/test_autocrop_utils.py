import unittest

import numpy as np

from autocrop_utils import (
    box_area_ratio,
    build_frame_sample_indices,
    combine_crop_boxes,
    detect_crop_box,
)


class AutoCropUtilsTests(unittest.TestCase):
    def test_threshold_method_can_lock_onto_central_island(self):
        image = np.zeros((300, 300), dtype=np.uint8)
        image[60:220, 40:125] = 140
        image[100:170, 135:165] = 220
        image[60:220, 175:260] = 160

        threshold_box = detect_crop_box(image, method="threshold")
        hybrid_box = detect_crop_box(image, method="hybrid")

        self.assertIsNotNone(threshold_box)
        self.assertIsNotNone(hybrid_box)
        self.assertLess(box_area_ratio(threshold_box, image.shape), 0.10)
        self.assertGreater(box_area_ratio(hybrid_box, image.shape), 0.40)
        self.assertLessEqual(hybrid_box[0], 55)
        self.assertGreaterEqual(hybrid_box[2], 245)

    def test_gray_background_breaks_simple_threshold_but_not_hybrid(self):
        rng = np.random.default_rng(7)
        image = np.full((300, 300), 20, dtype=np.uint8)
        image[35:245, 45:255] = rng.integers(60, 170, size=(210, 210), dtype=np.uint8)
        image[255:265, 30:270:20] = 240

        threshold_box = detect_crop_box(image, method="threshold")
        hybrid_box = detect_crop_box(image, method="hybrid")

        self.assertEqual(threshold_box, (0, 0, 300, 300))
        self.assertIsNotNone(hybrid_box)
        self.assertLess(box_area_ratio(hybrid_box, image.shape), 0.80)
        self.assertGreater(box_area_ratio(hybrid_box, image.shape), 0.40)
        self.assertLessEqual(hybrid_box[0], 55)
        self.assertGreaterEqual(hybrid_box[2], 245)

    def test_build_frame_sample_indices_prefers_requested_frame_without_duplicates(self):
        self.assertEqual(build_frame_sample_indices(8, preferred_index=6), [6, 4, 2, 0, 7])

    def test_combine_crop_boxes_uses_union_of_valid_boxes(self):
        combined = combine_crop_boxes(
            [
                None,
                (10, 20, 110, 180),
                (14, 18, 108, 190),
            ],
            image_shape=(240, 320),
        )

        self.assertEqual(combined, (10, 18, 110, 190))


if __name__ == "__main__":
    unittest.main()
