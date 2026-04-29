from __future__ import annotations

from pydicom.uid import JPEGBaseline8Bit


def apply_jpeg_baseline_pixel_metadata(ds):
    transfer_syntax_uid = getattr(getattr(ds, "file_meta", None), "TransferSyntaxUID", None)
    if (
        str(transfer_syntax_uid) == str(JPEGBaseline8Bit)
        and int(getattr(ds, "SamplesPerPixel", 1) or 1) > 1
    ):
        ds.PhotometricInterpretation = "YBR_FULL_422"
        ds.PlanarConfiguration = 0
    return ds
