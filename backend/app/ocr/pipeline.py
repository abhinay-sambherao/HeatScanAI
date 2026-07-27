"""Orchestrates the full OCR pipeline: upload -> preprocess -> read -> parse."""

from app.ocr.preprocessor import preprocess, load_from_bytes, resize_for_ocr
from app.ocr.reader import extract_text
from app.ocr.parser import clean_text, extract_fields


def run_pipeline(image_data: bytes) -> dict:
    """Execute the full OCR pipeline on raw image bytes.

    Steps:
        1. Try preprocessed image first
        2. If OCR returns very little text, fall back to original (resized) image
        3. Clean and parse the extracted text

    Returns:
        Dictionary with: raw_text, cleaned_text, confidence, fields
    """
    preprocessed = preprocess(image_data)
    raw_text, confidence = extract_text(preprocessed)

    # Fallback: try OCR on the original resized image if preprocessed gave poor results
    if len(raw_text.strip()) < 10:
        original = resize_for_ocr(load_from_bytes(image_data))
        orig_text, orig_conf = extract_text(original)
        if len(orig_text.strip()) > len(raw_text.strip()):
            raw_text = orig_text
            confidence = orig_conf

    cleaned = clean_text(raw_text)
    fields = extract_fields(raw_text)

    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned,
        "confidence": round(confidence * 100, 2),
        "manufacturer": fields["manufacturer"],
        "model": fields["model"],
        "energy_class": fields["energy_class"],
        "heat_output": fields["heat_output"],
        "fuel_type": fields["fuel_type"],
    }
