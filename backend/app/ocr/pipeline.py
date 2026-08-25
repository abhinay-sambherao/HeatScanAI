"""Orchestrates the full OCR pipeline: upload -> preprocess -> read -> parse."""

from app.ocr.preprocessor import (
    preprocess,
    load_from_bytes,
    resize_for_ocr,
    upscale_for_ocr,
)
from app.ocr.reader import extract_text
from app.ocr.parser import clean_text, extract_fields


def _build_variants(image_data: bytes) -> list:
    """Return the image variants to OCR, most reliable first.

    The preprocessed view runs perspective correction + contrast + rotation,
    but the perspective crop can slice the nameplate away (leaving only e.g.
    the gas/flue table). The unmodified resized view and a 2x upscale recover
    the nameplate in those cases, so every scan tries all three.
    """
    original = None
    try:
        original = load_from_bytes(image_data)
    except ValueError:
        pass

    variants = []
    try:
        variants.append(preprocess(image_data))
    except Exception:
        pass
    if original is not None:
        try:
            variants.append(resize_for_ocr(original))
        except Exception:
            pass
        try:
            variants.append(upscale_for_ocr(original))
        except Exception:
            pass
    return variants


def _merge_ocr_results(results: list) -> tuple:
    """Merge (text, confidence) results from all variants.

    Lines are unioned (exact duplicates removed, best-confidence variants
    first) and the overall confidence is the max across variants.
    """
    if not results:
        return "", 0.0
    seen = set()
    lines = []
    best_conf = 0.0
    for text, conf in sorted(results, key=lambda r: r[1], reverse=True):
        if conf > best_conf:
            best_conf = conf
        for line in text.splitlines():
            norm = " ".join(line.split()).strip()
            if not norm:
                continue
            key = norm.lower()
            if key in seen:
                continue
            seen.add(key)
            lines.append(norm)
    return "\n".join(lines), best_conf


def _parse_sufficient(text: str) -> bool:
    """True if the text already yields a confident brand + model parse.

    Used to skip the extra OCR variants (and their latency) when the first
    view read the nameplate cleanly.
    """
    fields = extract_fields(text)
    return bool(fields.get("manufacturer") and fields.get("model"))


def run_pipeline(image_data: bytes) -> dict:
    """Execute the full OCR pipeline on raw image bytes.

    Steps:
        1. OCR the preprocessed view; if it already yields brand + model,
           stop (fast path)
        2. Otherwise OCR the remaining variants (original resized, upscaled)
        3. Merge the raw texts (dedup) and take the best confidence
        4. Clean and parse the extracted text

    Returns:
        Dictionary with: raw_text, cleaned_text, confidence, fields
    """
    variants = _build_variants(image_data)
    results = []
    for i, img in enumerate(variants):
        try:
            text, conf = extract_text(img)
        except Exception:
            continue
        results.append((text, conf))
        if i == 0 and text.strip() and _parse_sufficient(text):
            break

    raw_text, confidence = _merge_ocr_results(results)
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
        "installation_year": fields.get("installation_year"),
    }
