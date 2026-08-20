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
    # Brand often missing from nameplates; detect via distinctive signals:
    # "Pellematic" is ÖkoFEN's pellet boiler product line, "Niederkappel"
    # (A-4133, Austria) is ÖkoFEN Heizsysteme's registered HQ address.
    "pellematic": "ÖkoFEN",
    "niederkappel": "ÖkoFEN",
    "ochsner": "Ochsner",
    "elco": "ELCO",
    "sieger": "Sieger",
}

# Energy class letter must not be followed by a digit: boiler plates print
# gas-category codes like "G20", "G31", "B23", "C13(X)" whose leading letter
# would otherwise be read as a class ("G").
ENERGY_CLASS_PATTERN = re.compile(
    r"(?<![A-Za-z0-9)\]\-])(A\+{0,3}|[B-G])(?![A-Za-z+0-9\-])", re.IGNORECASE
)

HEAT_OUTPUT_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:kW|kw|KW)", re.IGNORECASE
)

MODEL_PATTERNS = [
    # Explicit labels at start of line / after punctuation, plus word-boundary
    # Model/Modell anywhere. A trailing letter guard keeps "Typenschild",
    # "Modellnummer", "Heater type:" from matching.
    re.compile(
        r"(?:(?:^|[.\n\r])\s*(?:Model|Modell|Mod|Type|Typ)(?![A-Za-z])"
        r"|(?<!\w)(?:Model|Modell|Mod)(?![A-Za-z]))"
        r"\s*[:\s.]*([A-Za-z0-9][A-Za-z0-9\-\.\s]{1,50}?)"
        r"(?=\s*(?:Serial|S\/N|No\.?\s*[:.]|Pin|\n|$)|\s+[A-Z][a-z])",
        re.IGNORECASE,
    ),
    # Mid-line "Type"/"Typ" followed by a single token that contains a digit
    # (e.g. nameplate "Fax: DW 10 Type Pellematic08"). Requiring a digit in the
    # immediate token means "Heater type: Condensing" never matches.
    re.compile(
        r"(?<![A-Za-z])(?:Type|Typ)(?![A-Za-z])\s*[:\s.]*"
        r"([A-Z][A-Za-z0-9]*[0-9][A-Za-z0-9]*)"
        r"(?=\s|$|[.,;:])",
        re.IGNORECASE,
    ),
]

MODEL_GENERIC = re.compile(r"\b([A-Z]{1,3}[\s\-]?\d{2,5}[A-Za-z]?(?:[\s\-]\d{2,4}[A-Za-z]?)?)\b")

# Gas/flue-category codes printed on every gas boiler plate (G20/G25/G31 gas
# groups, C13-C93 flue systems, B23/B33 appliance categories). Letter + 2-3
# digits like "G20 20", "C930" or "C980X" are not models.
GAS_CODE_RE = re.compile(r"^[GBC]\d{2,3}(?:[\s\-/]\d{2,4})?[A-Za-z]?$")

# OCR artifact: a letter directly followed by a leading zero then digits
# (e.g. "L0330" read from "C33X") -- never a real model, but pattern-matches
# the generic model rule and serial-like codes.
LEADING_ZERO_CODE_RE = re.compile(r"^[A-Z]0\d{2,4}$")

# Postal codes on nameplate addresses ("D-88475 Schwendi", "A-4133
# Niederkappel", "CH-9466 Sennwald") pattern-match the generic model rule.
POSTAL_CODE_RE = re.compile(r"^[A-Za-z]{1,2}-\d{4,5}$")

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


def _clean_model_candidate(candidate: str) -> str | None:
    """Trim noise that OCR merges onto the end of a labeled model.

    Merged lines like "Mod.: WTC-GB 90-A 0063 BS 3948 CE 0085" capture
    trailing certificate/article codes; leading-zero codes ("0063",
    "0085") mark the field boundary. Returns None if nothing real remains.
    """
    candidate = candidate.strip(" .:-–-|/\\")
    tokens = re.split(r"\s+", candidate)
    for i, tok in enumerate(tokens):
        if re.match(r"^0\d{3,}$", tok):
            tokens = tokens[:i]
            break
    trimmed = " ".join(tokens).strip(" .:-–-|/\\")
    return trimmed if len(trimmed) >= 3 else None


def extract_model(text: str) -> str | None:
    """Extract the most likely model number from OCR text."""
    # First pass: explicit model labels
    for pattern in MODEL_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = _clean_model_candidate(match.group(1))
            if candidate and len(candidate) <= 40:
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
        # Skip pure years, short numeric codes, gas/flue-category codes, and
        # known non-model patterns
        if re.match(r"^\d{4}$", val):
            continue
        if GAS_CODE_RE.match(val):
            continue  # G20 20 / C930 / B23-style appliance codes
        if LEADING_ZERO_CODE_RE.match(val):
            continue  # "L0330" OCR garble of a flue-code line
        if POSTAL_CODE_RE.match(val):
            continue  # "D-88475" address postcode, not a model
        if re.search(r"(?:^|\s)0\d{3,}(?=\s|$)", val):
            continue  # trailing certificate codes like "CE 0085"
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
