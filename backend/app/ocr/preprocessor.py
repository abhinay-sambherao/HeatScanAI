"""Image preprocessing for OCR: perspective correction, noise removal,
contrast enhancement, and rotation correction."""

import cv2
import numpy as np


def load_from_bytes(data: bytes) -> np.ndarray:
    """Load an image from raw bytes (e.g. uploaded file)."""
    nparr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image from bytes")
    return img


def resize_for_ocr(img: np.ndarray, max_side: int = 1500) -> np.ndarray:
    """Resize image if too large, preserving aspect ratio."""
    h, w = img.shape[:2]
    if max(h, w) <= max_side:
        return img
    scale = max_side / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def upscale_for_ocr(img: np.ndarray, factor: float = 2.0, max_side: int = 3200) -> np.ndarray:
    """Upscale small images so small nameplate text becomes readable.

    PaddleOCR struggles with text under ~10px; a 2x upscale is a standard
    remedy. The result is clamped to ``max_side`` to bound worker memory.
    """
    h, w = img.shape[:2]
    nh, nw = int(h * factor), int(w * factor)
    if max(nh, nw) > max_side:
        scale = max_side / max(nh, nw)
        nh, nw = int(nh * scale), int(nw * scale)
    return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_CUBIC)


def correct_perspective(img: np.ndarray) -> np.ndarray:
    """Detect the largest rectangular contour and apply perspective transform.
    Only applies if a clear rectangle is found covering >30% of the image.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 200)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)

    if area < img.shape[0] * img.shape[1] * 0.3:
        return img

    peri = cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, 0.02 * peri, True)

    if len(approx) == 4:
        pts = approx.reshape(4, 2).astype(np.float32)
        rect = _order_points(pts)
        w = max(np.linalg.norm(rect[0] - rect[1]), np.linalg.norm(rect[2] - rect[3]))
        h = max(np.linalg.norm(rect[0] - rect[3]), np.linalg.norm(rect[1] - rect[2]))
        if w < 50 or h < 50:
            return img
        dst = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
        matrix = cv2.getPerspectiveTransform(rect, dst)
        return cv2.warpPerspective(img, matrix, (int(w), int(h)))

    return img


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Order 4 points as: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]
    rect[3] = pts[np.argmax(d)]
    return rect


def enhance_contrast(img: np.ndarray) -> np.ndarray:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) on L channel."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l_channel)
    enhanced = cv2.merge([l_enhanced, a, b])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def correct_rotation(img: np.ndarray) -> np.ndarray:
    """Detect dominant text angle and rotate to make text horizontal.
    Only applies rotation if angle is clearly > 2 degrees.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 200, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)

    if lines is None:
        return img

    angles = []
    for line in lines:
        coords = np.array(line).flatten()
        x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if abs(angle) < 45:
            angles.append(angle)

    if not angles:
        return img

    median_angle = float(np.median(angles))

    if abs(median_angle) < 2.0:
        return img

    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    return cv2.warpAffine(img, matrix, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def preprocess(image_data: bytes) -> np.ndarray:
    """Run preprocessing pipeline on raw image bytes.

    Pipeline: load → resize → perspective correction → contrast enhancement → rotation correction
    Noise removal is skipped as PaddleOCR v3.7 handles denoising internally.
    """
    img = load_from_bytes(image_data)
    img = resize_for_ocr(img)
    img = correct_perspective(img)
    img = enhance_contrast(img)
    img = correct_rotation(img)
    return img
