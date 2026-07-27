from __future__ import annotations

"""Regex-based cleanup and manufacturer/model extraction from OCR text."""

import re


KNOWN_MANUFACTURERS = [
    "Viessmann", "Vaillant", "Buderus", "Bosch", " Junkers",
    "Wolf", "Weishaupt", "Stiebel Eltron", "Daikin", "Mitsubishi",
    "Samsung", "LG", "NIBE", "Panasonic", "Glow-worn",
    "Ideal", "Worcester", "Baxi", "Ferroli", "Ariston", "Beretta",
    "Biasi", "Glow-worm", "Potterton", "Remeha", "Intergas",
    "Atag", "Nefit", "AWB", "Brotje", "Viadrus", "Dakins",
    "Chaffoteaux", "De Dietrich", "Saunier Duval", "Vailant",
    "ATMOS", "Thermia", "CLAGE", "Stiebel", "Eltron",
]

# Common OCR misspellings mapped to canonical names
MANUFACTURER_ALIASES = {
    "villent": "Vaillant",
    "vaillant": "Vaillant",
    "vaillant": "Vaillant",
    "viessman": "Viessmann",
    "viessman": "Viessmann",
    "buderu": "Buderus",
    "bosCH": "Bosch",
    "bosch": "Bosch",
    "wolF": "Wolf",
    "wolf": "Wolf",
    "daikin": "Daikin",
    "mitsubis": "Mitsubishi",
    "mitsubishi": "Mitsubishi",
    "nibe": "NIBE",
    "panasonic": "Panasonic",
    "ariston": "Ariston",
    "baxi": "Baxi",
    "ferroli": "Ferroli",
    "worcester": "Worcester",
}

ENERGY_CLASS_PATTERN = re.compile(r"(?<![A-Za-z])(A\+{0,3}|[B-G])(?![A-Za-z+])", re.IGNORECASE)

HEAT_OUTPUT_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:kW|kw|KW)", re.IGNORECASE
)

MODEL_PATTERNS = [
    re.compile(r"(?:Model|Modell|Type|Typ)\s*[:\s]*([A-Za-z0-9\-\.\s]+)", re.IGNORECASE),
    re.compile(r"\b([A-Z]{1,3}[\s\-]?\d{2,5}[A-Za-z]?)\b"),
]

FUEL_KEYWORDS = {
    "gas": ["gas", "erdgas", "natural gas", "methane"],
    "oil": ["oil", "öl", "heating oil", "heizöl", "diesel"],
    "electricity": ["electric", "elektrisch", "heat pump", "wärmepumpe", "electricity"],
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


def extract_model(text: str) -> str | None:
    """Extract the most likely model number from OCR text."""
    for pattern in MODEL_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


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
