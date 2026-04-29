import io
import unittest

import numpy as np
import pydicom
from PIL import Image
from pydicom.encaps import encapsulate
from pydicom.pixels.utils import pixel_array
from pydicom.uid import JPEGBaseline8Bit

from dicom_pixel_utils import apply_jpeg_baseline_pixel_metadata


def _jpeg_encoded_dataset(planar_configuration=1):
    image = np.zeros((16, 18, 3), dtype=np.uint8)
    image[:, :, 0] = np.arange(18, dtype=np.uint8)
    image[:, :, 1] = np.arange(16, dtype=np.uint8).reshape(16, 1) * 4
    image[:, :, 2] = 80

    buffer = io.BytesIO()
    Image.fromarray(image).save(buffer, format="JPEG", quality=95, subsampling=1)

    ds = pydicom.Dataset()
    ds.file_meta = pydicom.Dataset()
    ds.file_meta.TransferSyntaxUID = JPEGBaseline8Bit
    ds.Rows = image.shape[0]
    ds.Columns = image.shape[1]
    ds.SamplesPerPixel = 3
    ds.PhotometricInterpretation = "YBR_FULL_422"
    ds.PlanarConfiguration = planar_configuration
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0
    ds.PixelData = encapsulate([buffer.getvalue()])

    return ds


class DicomPixelUtilsTests(unittest.TestCase):
    def test_jpeg_baseline_color_metadata_uses_interleaved_planar_configuration(self):
        ds = _jpeg_encoded_dataset(planar_configuration=1)

        apply_jpeg_baseline_pixel_metadata(ds)

        self.assertEqual(ds.PhotometricInterpretation, "YBR_FULL_422")
        self.assertEqual(ds.PlanarConfiguration, 0)
        decoded = pixel_array(ds, index=0)
        self.assertLess(decoded[:, :, 1].mean(), 40)


if __name__ == "__main__":
    unittest.main()
