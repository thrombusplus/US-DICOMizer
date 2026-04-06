from __future__ import annotations

from typing import Literal

import cv2 as cv
import numpy as np
from pydicom.pixels.utils import get_nr_frames, pixel_array

CropBox = tuple[int, int, int, int]
CropMethod = Literal["threshold", "mode", "edge", "hybrid"]

_MIN_AREA_RATIO = 0.08
_MAX_REASONABLE_AREA_RATIO = 0.98
_BACKGROUND_TOLERANCE = 2


def build_frame_sample_indices(num_frames: int, preferred_index: int | None = None) -> list[int]:
    if num_frames <= 1:
        return [0]

    candidates = [
        preferred_index,
        num_frames // 2,
        num_frames // 4,
        (3 * num_frames) // 4,
        0,
        num_frames - 1,
    ]

    indices: list[int] = []
    for index in candidates:
        if index is None:
            continue
        index = int(index)
        if 0 <= index < num_frames and index not in indices:
            indices.append(index)
    return indices or [0]


def detect_crop_box(image: np.ndarray, method: CropMethod = "hybrid") -> CropBox | None:
    gray = _to_grayscale(image)
    if gray.size == 0:
        return None

    if method == "threshold":
        return _detect_threshold_box(gray)
    if method == "mode":
        return _detect_mode_box(gray)
    if method == "edge":
        return _detect_edge_box(gray)
    if method == "hybrid":
        return _detect_hybrid_box(gray)
    raise ValueError(f"Unsupported crop method: {method}")


def detect_dicom_autocrop_box(ds, preferred_frame_index: int = 0, method: CropMethod = "hybrid") -> CropBox:
    num_frames = get_nr_frames(ds)
    frame_indices = build_frame_sample_indices(num_frames, preferred_index=preferred_frame_index)

    detections: list[CropBox | None] = []
    fallback_box: CropBox | None = None
    frame_shape = None

    for frame_index in frame_indices:
        frame = pixel_array(ds, index=frame_index)
        frame_shape = frame.shape
        height, width = frame_shape[:2]
        full_box = (0, 0, width, height)
        search_box = read_ultrasound_region_box(ds, frame_shape) or full_box
        fallback_box = search_box

        search_x0, search_y0, search_x1, search_y1 = search_box
        roi = frame[search_y0:search_y1, search_x0:search_x1]
        detected_box = detect_crop_box(roi, method=method)
        detections.append(offset_crop_box(detected_box, search_x0, search_y0))

    if frame_shape is None:
        width = int(ds.get((0x0028, 0x0011), 0).value) if (0x0028, 0x0011) in ds else 0
        height = int(ds.get((0x0028, 0x0010), 0).value) if (0x0028, 0x0010) in ds else 0
        if width > 0 and height > 0:
            return (0, 0, width, height)
        return (0, 0, 1, 1)

    return combine_crop_boxes(detections, frame_shape, fallback_box=fallback_box)


def combine_crop_boxes(
    boxes: list[CropBox | None],
    image_shape: tuple[int, int] | tuple[int, int, int],
    fallback_box: CropBox | None = None,
) -> CropBox:
    height, width = image_shape[:2]
    valid_boxes = [clamp_crop_box(box, width, height) for box in boxes if box is not None]
    valid_boxes = [box for box in valid_boxes if is_valid_crop_box(box, width, height)]

    if not valid_boxes:
        if fallback_box is not None:
            return clamp_crop_box(fallback_box, width, height)
        return (0, 0, width, height)

    x0 = min(box[0] for box in valid_boxes)
    y0 = min(box[1] for box in valid_boxes)
    x1 = max(box[2] for box in valid_boxes)
    y1 = max(box[3] for box in valid_boxes)
    return clamp_crop_box((x0, y0, x1, y1), width, height)


def offset_crop_box(box: CropBox | None, offset_x: int = 0, offset_y: int = 0) -> CropBox | None:
    if box is None:
        return None
    x0, y0, x1, y1 = box
    return (x0 + offset_x, y0 + offset_y, x1 + offset_x, y1 + offset_y)


def clamp_crop_box(box: CropBox, width: int, height: int) -> CropBox:
    x0, y0, x1, y1 = (int(value) for value in box)
    x0 = min(max(0, x0), max(0, width - 1))
    y0 = min(max(0, y0), max(0, height - 1))
    x1 = min(max(x0 + 1, x1), width)
    y1 = min(max(y0 + 1, y1), height)
    return (x0, y0, x1, y1)


def is_valid_crop_box(
    box: CropBox | None,
    width: int,
    height: int,
    min_area_ratio: float = _MIN_AREA_RATIO,
    max_area_ratio: float = _MAX_REASONABLE_AREA_RATIO,
) -> bool:
    if box is None:
        return False

    x0, y0, x1, y1 = clamp_crop_box(box, width, height)
    area = max(0, x1 - x0) * max(0, y1 - y0)
    if area == 0 or width == 0 or height == 0:
        return False

    area_ratio = area / float(width * height)
    return min_area_ratio <= area_ratio <= max_area_ratio


def box_area_ratio(box: CropBox, image_shape: tuple[int, int] | tuple[int, int, int]) -> float:
    height, width = image_shape[:2]
    if width == 0 or height == 0:
        return 0.0
    x0, y0, x1, y1 = clamp_crop_box(box, width, height)
    return max(0, x1 - x0) * max(0, y1 - y0) / float(width * height)


def read_ultrasound_region_box(ds, frame_shape: tuple[int, int] | tuple[int, int, int]) -> CropBox | None:
    height, width = frame_shape[:2]

    try:
        sequence = ds[0x0018, 0x6011].value
        item = sequence[0]
        crop_box = (
            int(item[0x0018, 0x6018].value),
            int(item[0x0018, 0x601a].value),
            int(item[0x0018, 0x601c].value),
            int(item[0x0018, 0x601e].value),
        )
    except Exception:
        return None

    x0, y0, x1, y1 = crop_box
    if x1 <= x0 or y1 <= y0:
        return None

    x0 = min(max(0, x0), max(0, width - 1))
    y0 = min(max(0, y0), max(0, height - 1))
    x1 = min(max(x0 + 1, x1), width)
    y1 = min(max(y0 + 1, y1), height)
    return (x0, y0, x1, y1)


def _detect_hybrid_box(gray: np.ndarray) -> CropBox | None:
    height, width = gray.shape[:2]

    edge_box = _detect_edge_box(gray)
    mode_box = _detect_mode_box(gray)
    threshold_box = _detect_threshold_box(gray)

    if is_valid_crop_box(edge_box, width, height):
        if is_valid_crop_box(mode_box, width, height):
            return _shrink_edge_box_towards_mode(gray, edge_box, mode_box)
        return edge_box

    if is_valid_crop_box(mode_box, width, height):
        return mode_box

    if is_valid_crop_box(threshold_box, width, height):
        return threshold_box

    return edge_box or mode_box or threshold_box


def _detect_threshold_box(gray: np.ndarray) -> CropBox | None:
    _, thresholded = cv.threshold(gray, 1, 255, cv.THRESH_BINARY)
    return _find_center_weighted_contour_box(thresholded)


def _detect_mode_box(gray: np.ndarray) -> CropBox | None:
    background_mode = _dominant_background_value(gray)
    clean_image = gray.copy()

    lower_bound = max(0, background_mode - _BACKGROUND_TOLERANCE)
    upper_bound = min(255, background_mode + _BACKGROUND_TOLERANCE)

    mask = ((clean_image >= lower_bound) & (clean_image <= upper_bound)).astype(np.uint8) * 255
    kernel = np.ones((5, 5), np.uint8)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=3)
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel, iterations=6)
    clean_image[mask.astype(bool)] = 0

    _, thresholded = cv.threshold(clean_image, 1, 255, cv.THRESH_BINARY)
    return _find_center_weighted_contour_box(thresholded)


def _detect_edge_box(gray: np.ndarray) -> CropBox | None:
    edges = cv.Canny(gray, threshold1=30, threshold2=100)

    kernel_size = max(5, int(round(min(gray.shape[:2]) * 0.04)))
    if kernel_size % 2 == 0:
        kernel_size += 1

    kernel = cv.getStructuringElement(cv.MORPH_RECT, (kernel_size, kernel_size))
    closed = cv.morphologyEx(edges, cv.MORPH_CLOSE, kernel)
    closed = cv.dilate(closed, kernel, iterations=1)

    contours, _ = cv.findContours(closed, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest_contour = max(contours, key=cv.contourArea)
    x, y, w, h = cv.boundingRect(largest_contour)
    return (x, y, x + w, y + h)


def _find_center_weighted_contour_box(binary_image: np.ndarray) -> CropBox | None:
    contours, _ = cv.findContours(binary_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    image_center = np.array([binary_image.shape[1] / 2, binary_image.shape[0] / 2], dtype=np.float32)
    areas = [cv.contourArea(contour) for contour in contours]
    sorted_indices = np.argsort(areas)[::-1]
    top_contours = [contours[index] for index in sorted_indices[:3]]

    min_distance = float("inf")
    closest_contour = None

    for contour in top_contours:
        moments = cv.moments(contour)
        if moments["m00"] == 0:
            continue

        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]
        distance = np.linalg.norm(np.array([cx, cy], dtype=np.float32) - image_center)
        if distance < min_distance:
            min_distance = distance
            closest_contour = contour

    if closest_contour is None:
        return None

    x, y, w, h = cv.boundingRect(closest_contour)
    return (x, y, x + w, y + h)


def _shrink_edge_box_towards_mode(gray: np.ndarray, edge_box: CropBox, mode_box: CropBox) -> CropBox:
    background_mode = _dominant_background_value(gray)
    edge_x0, edge_y0, edge_x1, edge_y1 = edge_box
    mode_x0, mode_y0, mode_x1, mode_y1 = mode_box

    x0, y0, x1, y1 = edge_box

    if mode_x0 > edge_x0 and _foreground_ratio(gray[edge_y0:edge_y1, edge_x0:mode_x0], background_mode) < 0.08:
        x0 = mode_x0
    if mode_y0 > edge_y0 and _foreground_ratio(gray[edge_y0:mode_y0, x0:x1], background_mode) < 0.08:
        y0 = mode_y0
    if mode_x1 < edge_x1 and _foreground_ratio(gray[y0:y1, mode_x1:edge_x1], background_mode) < 0.08:
        x1 = mode_x1
    if mode_y1 < edge_y1 and _foreground_ratio(gray[mode_y1:edge_y1, x0:x1], background_mode) < 0.08:
        y1 = mode_y1

    return clamp_crop_box((x0, y0, x1, y1), gray.shape[1], gray.shape[0])


def _foreground_ratio(region: np.ndarray, background_mode: int) -> float:
    if region.size == 0:
        return 0.0
    lower_bound = max(0, background_mode - _BACKGROUND_TOLERANCE)
    upper_bound = min(255, background_mode + _BACKGROUND_TOLERANCE)
    background_mask = (region >= lower_bound) & (region <= upper_bound)
    return float((~background_mask).mean())


def _dominant_background_value(gray: np.ndarray) -> int:
    counts = np.bincount(gray.flatten(), minlength=256)
    return int(np.argmax(counts))


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    return cv.cvtColor(image, cv.COLOR_BGR2GRAY)
