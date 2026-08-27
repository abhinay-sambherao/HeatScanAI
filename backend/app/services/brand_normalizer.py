"""Brand normalization for EPREL products.

EPREL stores manufacturer names inconsistently:
  - Some use the brand ("Viessmann", 15 products)
  - Others use the legal entity ("Viessmann Climate Solutions SE", 2111 products)
  - Some use the full legal name ("Viessmann Werke GmbH & Co. KG", 1165 products)

This module normalizes all variants to a single canonical brand name at
crawl time, preventing duplicate manufacturer rows and ensuring products
are searchable under the correct brand.

Usage:
    canonical = normalize_brand("Viessmann Werke GmbH & Co. KG")  # -> "Viessmann"
    if is_valid_brand("Wolf Sonnenpaket; COB-15"):  # -> False (composition)
        ...
"""

from __future__ import annotations

import re
from typing import Optional

# ── EPREL manufacturer name → canonical brand ───────────────────────
# Maps the exact strings returned by EPREL's supplierOrTrademark /
# organisation.organisationTitle to the brand that appears on nameplates.
# Keys are LOWERCASE for case-insensitive matching.
EPREL_BRAND_MAP: dict[str, str] = {
    # ── German Big 7 + major brands ──
    "viessmann": "Viessmann",
    "viessmann climate solutions se": "Viessmann",
    "viessmann werke gmbh & co. kg": "Viessmann",
    "viessmann werke gmbh & co kg": "Viessmann",
    "viessmann werke gmbh": "Viessmann",
    "viessmann climate solutions": "Viessmann",
    "bosch": "Bosch",
    "buderus": "Buderus",
    "buderus heiztechnik gmbh": "Buderus",
    "junkers": "Junkers",
    "vaillant": "Vaillant",
    "stiebel eltron": "Stiebel Eltron",
    "stiebel-eltron": "Stiebel Eltron",
    "stiebel eltron gmbh": "Stiebel Eltron",
    "wolf": "Wolf",
    "wolf gmbh": "Wolf",
    "wolf heiztechnik gmbh": "Wolf",
    "weishaupt": "Weishaupt",
    "max weishaupt gmbh": "Weishaupt",
    "brötje": "Brötje",
    "broetje": "Brötje",
    "brotje": "Brötje",
    "brötje gmbh": "Brötje",
    "brotje gmbh": "Brötje",

    # ── KWB (3 variants in DB) ──
    "kwb": "KWB",
    "kwb energiesysteme gmbh": "KWB",
    "kwb energie systeme gmbh": "KWB",
    "kwb - kraft und wärme aus biomasse gmbh": "KWB",
    "kwb kraft und wärme aus biomasse gmbh": "KWB",
    "kwb kraft und wärme aus biomasse": "KWB",
    "kwb - kraft und wärme aus biomasse": "KWB",

    # ── ÖkoFEN ──
    "ökofen": "ÖkoFEN",
    "oekofen": "ÖkoFEN",
    "ökofen heizsysteme gmbh": "ÖkoFEN",

    # ── Ochsner ──
    "ochsner": "Ochsner",
    "ochsner wärmepumpen gmbh": "Ochsner",
    "ochsner warmepumpen gmbh": "Ochsner",

    # ── ELCO ──
    "elco": "ELCO",
    "elco vayonis s.a.": "ELCO",

    # ── Other brands with legal-entity variants ──
    "daikin": "Daikin",
    "daikin europe n.v.": "Daikin",
    "mitsubishi electric": "Mitsubishi Electric",
    "mitsubishi": "Mitsubishi Electric",
    "mitsubishi electric hydronics & it cooling systems s.p.a.": "Mitsubishi Electric",
    "mitsubishi electric hydronics & it cooling systems spa": "Mitsubishi Electric",
    "mitsubishi heavy industries air conditioning europe ltd.": "Mitsubishi Electric",
    "ariston": "Ariston",
    "ariston thermo": "Ariston",
    "ariston thermo groupe": "Ariston",
    "baxi": "Baxi",
    "baxi spa": "Baxi",
    "ferroli": "Ferroli",
    "ferroli spa": "Ferroli",
    "worcester": "Worcester",
    "worcester bosch": "Worcester Bosch",
    "worcester bosch group": "Worcester Bosch",
    "ideal": "Ideal",
    "ideal boiler": "Ideal",
    "ideal heating": "Ideal",
    "chaffoteaux": "Chaffoteaux",
    "chaffoteaux et maury": "Chaffoteaux",
    "de dietrich": "De Dietrich",
    "de dietrich thermique": "De Dietrich",
    "saunier duval": "Saunier Duval",
    "saunier duval sa": "Saunier Duval",
    "atag": "ATAG",
    "atag heating": "ATAG",
    "nefit": "Nefit",
    "nefit b.v.": "Nefit",
    "awb": "AWB",
    "awb b.v.": "AWB",
    "beretta": "Beretta",
    "beretta s.p.a.": "Beretta",
    "rima": "Rima",
    "rima s.p.a.": "Rima",
    "viadrus": "Viadrus",
    "viadrus a.s.": "Viadrus",
    "atmos": "ATMOS",
    "atmos dc spol. s r.o.": "ATMOS",
    "thermia": "Thermia",
    "clage": "CLAGE",
    "truma": "Truma",
    "truma gerätebau gmbh": "Truma",
    "defro": "DEFRO",
    "defro r. dziubeła spółka komandytowa": "DEFRO",
    "defro sp. z o.o.": "DEFRO",
    "dražice": "Dražice",
    "družstevní závody dražice": "Dražice",
    "družstevní závody dražice - strojírna s.r.o.": "Dražice",
    "fröling": "Fröling",
    "froling": "Fröling",
    "fröling heizkessel- und behälterbau ges.m.b.h.": "Fröling",
    "froling heizkessel": "Fröling",
    "aisin": "Aisin",
    "aisin seiki co. ltd.": "Aisin",
    "aisin seiki co. ltd": "Aisin",
    "glen dimplex": "Glen Dimplex",
    "glen dimplex heating & ventilation ireland": "Glen Dimplex",
    "dimplex sdner": "Dimplex",

    # ── Case-only variants ──
    "midea": "Midea",
    "midea inc.": "Midea",
    "centrometal": "Centrometal",
    "kospel": "KOSPEL",
    "kospel sp. z o.o.": "KOSPEL",
    "kalfire": "Kalfire",
    "tiki": "Tiki",
    "tiki d.o.o.": "Tiki",
    "sylber": "SYLBER",
    "sylber s.r.l.": "SYLBER",
    "tekla": "Tekla",
    "expondo": "Expondo",
    "muhler": "MUHLER",
    "thermoflux": "ThermoFlux",
    "fer": "FER",
    "fer s.p.a.": "FER",
    "lg electronics": "LG",
    "lg": "LG",
    "lg electronics inc.": "LG",
    "lg electronics inc": "LG",
    "lg electronic": "LG",
    "jøtul": "Jøtul",
    "jotul": "Jøtul",
    "comfee": "Comfee",
    "comfee mbt": "Comfee",
    "vulcano": "Vulcano",
    "esperia": "Esperia",
    "esperia s.r.l.": "Esperia",
    "nordic fire": "Nordic Fire",
    "solvis": "Solvis",
    "solvis gmbh": "Solvis",
    "well-born": "Well-born",
    "well born": "Well-born",
    "dimplex": "Dimplex",
    "dimplex sdner": "Dimplex",
    "justus": "Justus",
    "justus gmbh": "Justus",
    "blaupunkt": "Blaupunkt",
    "candy": "Candy",
    "grundig": "Grundig",
    "heatstore": "Heatstore",
    "wamsler": "WAMSLER",
    "wam­sl­er": "WAMSLER",
    "haas+sohn ofentechnik": "Haas+Sohn",
    "haas+sohn ofentechnik gmbh": "Haas+Sohn",
    "haas sohn": "Haas+Sohn",
    "austroflamm": "Austroflamm",
    "austroflamm gmbh": "Austroflamm",
    "oranier": "ORANIER",
    "oranier heiztechnik gmbh": "ORANIER",
    "leda werk": "LEDA",
    "leda werk gmbh & co. kg": "LEDA",
    "termet": "Termet",
    "termet s.a.": "Termet",
    "rika": "RIKA",
    "rika innovative ofentechnik gmbh": "RIKA",
    "herz": "HERZ",
    "herz energietechnik gmbh": "HERZ",
    "lohberger": "Lohberger",
    "lohberger gmbh": "Lohberger",
    "hdg bavaria": "HDG Bavaria",
    "hdg bavaria gmbh": "HDG Bavaria",
    "wodtke": "Wodtke",
    "wodtke gmbh": "Wodtke",
    "camina & schmid": "Camina & Schmid",
    "camina & schmid gmbh & co. kg": "Camina & Schmid",
    "hase": "Hase",
    "hase kaminofenbau gmbh": "Hase",
    "solarbayer": "Solarbayer",
    "solarbayer gmbh": "Solarbayer",
    "olsberg": "Olsberg",
    "olsberg gmbh - olsberg": "Olsberg",
    "olsberg gmbH - königshütte": "Olsberg",
    "roth": "Roth",
    "roth werke gmbh": "Roth",
    "spartherm": "Spartherm",
    "spartherm feuerungstechnik gmbh": "Spartherm",
    "max blank": "Max Blank",
    "max blank gmbh": "Max Blank",
    "knv": "KNV",
    "knv energietechnik gmbh": "KNV",
    "robin wood": "Robin Wood",
    "robin wood gmbh": "Robin Wood",
    "rowi": "ROWI",
    "rowi europe gmbh": "ROWI",
    "junker": "Junkers",
    "panasia": "Panasia",
    "panasia co. ltd": "Panasia",
    "gas:": None,  # junk
    "": None,  # empty
}

# ── Brand validation ────────────────────────────────────────────────
# Reject composition strings, trivial codes, and other junk that EPREL
# stores in supplierOrTrademark.

# Strings that indicate a composition / package description
_COMPOSITION_MARKERS = re.compile(r"[;]|paket|sonnenpaket|module|kit\b", re.IGNORECASE)

# Pure numeric or very short codes (1-2 chars) — these are gas/flue codes, not brands
_TRIVIAL_MODEL_RE = re.compile(r"^[0-9]{1,4}$")

# Very short names (1-2 chars) that are codes, not brands ("a", "AC", "10")
_SHORT_NAME_RE = re.compile(r"^[A-Za-z0-9]{1,2}(?:\.|,)?$")

# Postal codes / gas category codes that EPREL sometimes stores
_GAS_POSTAL_RE = re.compile(r"^[GBCHD]-?\d{3,5}$|^[GBC]\d{2,3}\s")


def is_valid_brand(brand: str) -> bool:
    """Return True if the string is a plausible manufacturer brand name.

    Rejects:
    - Composition/package descriptions (contains ';', 'paket', etc.)
    - Strings > 60 chars (legal entities, address strings)
    - Trivially short or numeric codes (gas codes, postal codes)
    - Empty or whitespace-only

    Known canonical brand values (e.g. "LG", "AWB") are exempt from the
    short-name rejection.
    """
    if not brand or not brand.strip():
        return False
    brand = brand.strip()
    if len(brand) > 60:
        return False
    if _COMPOSITION_MARKERS.search(brand):
        return False
    if _TRIVIAL_MODEL_RE.match(brand):
        return False
    if _SHORT_NAME_RE.match(brand):
        # Exempt known canonical brands that are legitimately short
        if brand.lower() not in {v.lower() for v in EPREL_BRAND_MAP.values() if v}:
            return False
    if _GAS_POSTAL_RE.match(brand):
        return False
    return True


def normalize_brand(name: str) -> Optional[str]:
    """Normalize an EPREL manufacturer name to its canonical brand.

    Returns the canonical brand name, or None if the name is invalid/junk.

    Examples:
        normalize_brand("Viessmann Werke GmbH & Co. KG") -> "Viessmann"
        normalize_brand("KWB - Kraft und Wärme aus Biomasse GmbH") -> "KWB"
        normalize_brand("MIDEA") -> "Midea"
        normalize_brand("a") -> None (trivial)
        normalize_brand("") -> None
    """
    if not name or not name.strip():
        return None
    name = name.strip()

    # Check brand validity first
    if not is_valid_brand(name):
        return None

    # Exact match (case-insensitive) in EPREL_BRAND_MAP
    key = name.lower()
    if key in EPREL_BRAND_MAP:
        return EPREL_BRAND_MAP[key]

    # Try with common suffixes stripped
    # "Viessmann Climate Solutions SE" -> try "viessmann climate solutions"
    for suffix in [" gmbh", " gmbh & co. kg", " gmbh & co kg", " spa", " s.a.", " s.r.l.",
                    " b.v.", " a.s.", " ltd", " inc.", " se", " oe", " ab"]:
        if key.endswith(suffix):
            stripped = key[:-len(suffix)].strip()
            if stripped in EPREL_BRAND_MAP:
                return EPREL_BRAND_MAP[stripped]
            break

    # If no mapping found, return the original name (title-cased for consistency)
    # But only if it looks like a real brand (not a legal entity)
    if any(marker in key for marker in ["gmbh", "kg", "s.a.", "s.r.l.", "b.v.", "ltd", "inc.", "spa", "co., ltd"]):
        # Legal entity without a mapping — return as-is but warn
        return name

    # Return as-is for unknown brands (could be a real brand we haven't mapped)
    return name


def extract_brand_from_raw(raw_json: dict) -> Optional[str]:
    """Extract and normalize the brand from an EPREL raw_json hit.

    Uses supplierOrTrademark > trademarkOwner > organisation.organisationTitle,
    then normalizes to canonical brand.

    Returns the canonical brand name, or None if no valid brand found.
    """
    # Priority 1: supplierOrTrademark (nameplate brand)
    brand = raw_json.get("supplierOrTrademark")
    if brand and str(brand).strip():
        normalized = normalize_brand(str(brand).strip())
        if normalized:
            return normalized

    # Priority 2: trademarkOwner
    owner = raw_json.get("trademarkOwner")
    if owner and str(owner).strip():
        normalized = normalize_brand(str(owner).strip())
        if normalized:
            return normalized

    # Priority 3: organisation (registrant) — last resort
    org = raw_json.get("organisation") or {}
    title = org.get("organisationTitle") if isinstance(org, dict) else None
    if title and str(title).strip():
        normalized = normalize_brand(str(title).strip())
        if normalized:
            return normalized

    return None
