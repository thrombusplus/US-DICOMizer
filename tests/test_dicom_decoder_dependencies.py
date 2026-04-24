import unittest

from pydicom.pixels.decoders.base import get_decoder
from pydicom.uid import JPEGLosslessSV1


class DicomDecoderDependencyTests(unittest.TestCase):
    def test_jpeg_lossless_sv1_decoder_plugin_is_available(self):
        decoder = get_decoder(JPEGLosslessSV1)
        available_plugins = set(decoder.available_plugins)

        self.assertTrue(
            {"gdcm", "pylibjpeg"} & available_plugins,
            "JPEG Lossless SV1 DICOM files require either gdcm or pylibjpeg "
            f"decoder support; missing dependencies: {decoder.missing_dependencies}",
        )


if __name__ == "__main__":
    unittest.main()
