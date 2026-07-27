"""PaddleOCR wrapper for text extraction from preprocessed images."""

import numpy as np

_ocr_instance = None


def _get_ocr():
    """Lazy-initialize PaddleOCR singleton."""
    global _ocr_instance
    if _ocr_instance is None:
        import os
        os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(lang="en")
    return _ocr_instance


def extract_text(img: np.ndarray) -> tuple:
    """Run PaddleOCR on a preprocessed image.

    Returns:
        Tuple of (full extracted text, average confidence score).
    """
    ocr = _get_ocr()
    results = ocr.predict(img)

    if not results:
        return "", 0.0

    texts = []
    confidences = []

    for result in results:
        rec_texts = result.get("rec_texts", [])
        rec_scores = result.get("rec_scores", [])
        for text, score in zip(rec_texts, rec_scores):
            texts.append(text)
            confidences.append(float(score))

    full_text = " ".join(texts)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return full_text, avg_confidence
