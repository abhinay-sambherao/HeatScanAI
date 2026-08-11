from __future__ import annotations

"""Regex-based cleanup and manufacturer/model extraction from OCR text."""

import re


# German market majors (~90% of installed heating systems: Bosch Group,
# Vaillant, Viessmann, Stiebel Eltron, Wolf, Weishaupt, Brötje) are checked
# first. Umlaut/hyphen variants are included so German nameplate spellings
# ("Brötje", "STIEBEL-ELTRON") resolve to the same brand.
KNOWN_MANUFACTURERS = [
    "Bosch", "Buderus", "Junkers",
    "Vaillant", "Viessmann",
    "Stiebel Eltron", "Stiebel-Eltron",
    "Wolf", "Weishaupt",
    "Brötje", "Broetje", "Brotje",
    "Daikin", "Mitsubishi", "Samsung", "LG", "NIBE", "Panasonic",
    "Glow-worn", "Ideal", "Worcester", "Baxi", "Ferroli", "Ariston",
    "Beretta", "Biasi", "Glow-worm", "Potterton", "Remeha", "Intergas",
    "Atag", "Nefit", "AWB", "Viadrus", "Dakins", "Chaffoteaux",
    "De Dietrich", "Saunier Duval", "Vailant", "ATMOS", "Thermia",
    "CLAGE", "Stiebel", "Eltron", "Truma",
    "ÖkoFEN", "OekoFEN", "Ochsner", "Ochsner Wärmepumpen", "ELCO",
    "Sieger",
]

# Common OCR misspellings mapped to canonical names
MANUFACTURER_ALIASES = {
    "villent": "Vaillant",
    "vaillant": "Vaillant",
    "vailant": "Vaillant",
    "valiant": "Vaillant",
    "vaillat": "Vaillant",
    "viessman": "Viessmann",
    "viessmann": "Viessmann",
    "viesman": "Viessmann",
    "viesmann": "Viessmann",
    "vissmann": "Viessmann",
    "buderu": "Buderus",
    "bosch": "Bosch",
    "wolf": "Wolf",
    "weishaupt": "Weishaupt",
    "stiebel-eltron": "Stiebel Eltron",
    "stiebeleltron": "Stiebel Eltron",
    "brötje": "Brötje",
    "broetje": "Brötje",
    "brotje": "Brötje",
    "daikin": "Daikin",
    "mitsubis": "Mitsubishi",
    "mitsubishi": "Mitsubishi",
    "nibe": "NIBE",
    "panasonic": "Panasonic",
    "ariston": "Ariston",
    "baxi": "Baxi",
    "ferroli": "Ferroli",
    "worcester": "Worcester",
    "ökofen": "ÖkoFEN",
    "oekofen": "ÖkoFEN",
    "ochsner": "Ochsner",
    "elco": "ELCO",
    "sieger": "Sieger",
}

ENERGY_CLASS_PATTERN = re.compile(r"(?<![A-Za-z])(A\+{0,3}|[B-G])(?![A-Za-z+])", re.IGNORECASE)

HEAT_OUTPUT_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:kW|kw|KW)", re.IGNORECASE
)

MODEL_PATTERNS = [
    re.compile(
        r"(?:(?:^|[.\n\r])\s*(?:Model|Modell|Type|Typ)|(?<!\w)(?:Model|Modell))"
        r"\s*[:\s]*([A-Za-z0-9][A-Za-z0-9\-\.\s]{1,50}?)"
        r"(?=\s*(?:Serial|S\/N|No\.?\s*[:.]|Pin|\n|$)|\s+[A-Z][a-z])",
        re.IGNORECASE,
    ),
]

MODEL_GENERIC = re.compile(r"\b([A-Z]{1,3}[\s\-]?\d{2,5}[A-Za-z]?(?:[\s\-]\d{2,4}[A-Za-z]?)?)\b")

# Tokens that end a manufacturer-anchored model phrase (German field headers,
# legal forms, common connectors). Models are typically Title/ALL-CAPS token
# runs ending in digits, so these delimiters keep the phrase tight.
_MODEL_STOPWORDS = {
    "brennstoff", "brenner", "brennerart", "leistung", "leistungsbereich",
    "nennwärmeleistung", "nennwärme", "art", "kategorie", "gas", "gasversorgung",
    "typ", "serial", "s/n", "s/n:", "nr", "nr.", "hersteller", "model", "modell",
    "type", "energy", "effizienz", "effizienzklasse", "warmetauscher", "heizung",
    "feverstätte", "feverstattenart", "befeuerung", "messergebnis", "abgas",
    "abgasleitung", "verbrennungsluft", "lufttemperatur", "druckdifferenz",
    "abgasklappe", "flammenbild", "verbindungsstück", "max", "min",
    "gmbh", "ag", "co", "ltd", "llc", "group", "werke", "sa", "inc", "kg",
    "und", "&", "mit", "bei", "der", "die", "das", "eine", "ein", "nicht",
    "für", "fur", "an", "auf", "zu", "im", "am", "des", "den",
}

FUEL_KEYWORDS = {
    "gas": ["gas", "erdgas", "natural gas", "methane", "butane", "propane", "lpg"],
    "oil": ["oil", "öl", "heating oil", "heizöl", "diesel"],
    "electricity": ["electric", "elektrisch", "heat pump", "wärmepumpe", "electricity", "strom", "heizstrom"],
    "wood": ["wood", "holz", "pellet", "biomass", "biomasse"],
    "solar": ["solar", "photovoltaic", "pv"],
    "district_heating": ["district heating", "fernwärme", "blockheizkraftwerk"],
}


def clean_text(raw_text: str) -> str:
    """Clean OCR artifacts and normalize text."""
    text = raw_text
    text = re.sub(r"[^\w\s\-\.\+\/,():]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?<=[a-zA-Z])0(?=[a-zA-Z])", "O", text)
    text = re.sub(r"(?<!\w)l(?=\d)", "1", text)
    return text


def extract_manufacturer(text: str) -> str | None:
    """Extract the most likely manufacturer name from OCR text.
    Checks aliases first for common OCR misspellings, then known names.
    """
    text_lower = text.lower()
    for alias, canonical in MANUFACTURER_ALIASES.items():
        if alias in text_lower:
            return canonical
    for mfr in KNOWN_MANUFACTURERS:
        if mfr.lower().strip() in text_lower:
            return mfr.strip()
    return None


def _extract_model_after_manufacturer(text: str, manufacturer: str | None) -> str | None:
    """Extract the model phrase that follows the detected manufacturer name.

    Handles nameplates/inspection reports that list the brand and model
    together ("ELCO, Thision S Plus 13.1") and short models the generic
    pattern deliberately filters ("STIEBEL ELTRON WPL 18"). Stops at known
    field headers and legal forms; requires a digit + uppercase letter so
    it never returns bare company suffixes ("GmbH & Co.").
    """
    if not manufacturer:
        return None
    idx = text.lower().find(manufacturer.lower())
    if idx == -1:
        return None
    idx += len(manufacturer)
    seg = re.sub(r"^[\s,.:;|/\-]+", "", text[idx : idx + 100])
    parts = []
    for tok in re.findall(r"[A-Za-z0-9][A-Za-z0-9.\-]*", seg):
        if tok.lower().strip(".-") in _MODEL_STOPWORDS:
            break
        parts.append(tok)
    phrase = " ".join(parts).strip()
    if len(phrase) < 3 or len(phrase) > 40:
        return None
    if not re.search(r"\d", phrase):
        return None
    if not re.search(r"[A-Z]", phrase):
        return None
    return phrase


def extract_model(text: str) -> str | None:
    """Extract the most likely model number from OCR text."""
    # First pass: explicit model labels
    for pattern in MODEL_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = match.group(1).strip()
            if len(candidate) >= 3 and len(candidate) <= 40:
                return candidate

    # Second pass: the model often directly follows the manufacturer name
    manufacturer = extract_manufacturer(text)
    anchored = _extract_model_after_manufacturer(text, manufacturer)
    if anchored:
        return anchored

    # Third pass: collect all generic model-like candidates, pick best
    candidates = []
    for m in MODEL_GENERIC.finditer(text):
        val = m.group(1).strip()
        parts = re.findall(r"\d+", val)
        num_digits = sum(len(p) for p in parts)
        # Skip pure years, short numeric codes, and known non-model patterns
        if re.match(r"^\d{4}$", val):
            continue
        if num_digits < 3:
            continue  # not enough digit content to be a model
        if num_digits > 12:
            continue  # too long (serial numbers)
        candidates.append(val)

    if not candidates:
        return None

    # Prefer candidates with more digits (more likely real model numbers)
    candidates.sort(key=lambda v: sum(len(p) for p in re.findall(r"\d+", v)), reverse=True)
    return candidates[0]


def extract_energy_class(text: str) -> str | None:
    """Extract the energy efficiency class from OCR text."""
    match = ENERGY_CLASS_PATTERN.search(text)
    return match.group(1).upper() if match else None


def extract_heat_output(text: str) -> str | None:
    """Extract heat output in kW from OCR text."""
    match = HEAT_OUTPUT_PATTERN.search(text)
    return f"{match.group(1)} kW" if match else None


def extract_fuel_type(text: str) -> str | None:
    """Detect fuel type from keywords in OCR text."""
    text_lower = text.lower()
    for fuel_type, keywords in FUEL_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return fuel_type
    return None


def extract_fields(text: str) -> dict:
    """Extract all relevant fields from OCR text in a single pass.

    Returns:
        Dictionary with keys: manufacturer, model, energy_class, heat_output, fuel_type
    """
    cleaned = clean_text(text)
    return {
        "manufacturer": extract_manufacturer(cleaned),
        "model": extract_model(cleaned),
        "energy_class": extract_energy_class(cleaned),
        "heat_output": extract_heat_output(cleaned),
        "fuel_type": extract_fuel_type(cleaned),
    }
