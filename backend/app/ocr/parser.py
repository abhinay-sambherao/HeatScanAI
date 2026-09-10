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
    r"(?<![A-Za-z0-9)\]\-])(A\+{0,3}|[B-G])(?![A-Za-z+0-9\-])"
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
    # Mid-line "Type"/"Typ" followed by a two-part model code: a short ALL-CAPS
    # prefix then digits, e.g. "TYP:WPL 18". Case-sensitive so lowercase prose
    # ("type: Condensing") never matches, and short codes that sort-of look
    # like words are allowed. Handles nameplates that print the label mid-line
    # with the model split over a space.
    re.compile(
        r"(?<![A-Za-z])(?:[Tt][Yy][Pp][Ee]?)(?![A-Za-z])\s*[:\s.]*"
        r"([A-Z]{1,6}(?:[\s\-]\d{2,5}[A-Za-z]?|\d[A-Za-z0-9\-]*))"
        r"(?=\s|$|[.,;:])",
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

# Serial / certificate codes printed all-caps and jammed into one token
# ("1312CO5870", "21142500100156093100005485N5", "074411"). These begin with
# digits and continue into uppercase letters, or are long pure-digit runs —
# never a model designation.
SERIAL_LIKE_TOKEN_RE = re.compile(
    r"^(\d{2,}[A-Z]{2,}|[0-9A-Z]{9,})$"
)

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
    "ohne", "gebläse", "erdgas", "feuerstättenart", "anlage", "ja", "nein",
    "keine", "angabe", "mangel", "festgestellt", "gemäss", "entspricht",
    "verordnung", "grenzwert", "messunsicherheit", "betreiber", "verpflichtet",
    "messung", "wiederholung", "überprüfung", "ergebnis",
}

# Regex matching power-value tokens like "7,8kW", "0-0kW", "7,80 kW" — these
# are measurement values on chimney sweep reports, not model identifiers.
_POWER_VALUE_RE = re.compile(r"^\d[\d,.\-]*\s*kW$", re.IGNORECASE)

# 4-digit years (2006, 1998, …) appear after models on chimney sweep reports
# ("Junkers /ZSR / 2006") and should stop the model collection.
_YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")

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
        if _YEAR_RE.match(tok):
            break
        if _POWER_VALUE_RE.match(tok):
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


def _extract_product_designation(text: str) -> str | None:
    """Extract a multi-token product designation from OCR text.

    Modern German boiler plates (e.g. Vaillant) print the model as a Title-case
    product-name run followed by an ALL-CAPS type code and digit-bearing tokens:
        "auroCOMPACT VSC S 146/4-5 150 Gas-Kompaktgerät"
    The generic single-token rule would only catch the last fragment
    ("S 146"). This scans the whole text for such a run — a capitalized
    product-name leader, an ALL-CAPS type code, ending in a digit token — and
    preserves the original separators (/ -). Field-label / spec lines
    ("Code 141 230V 50", "bar PMS PMW 10") never qualify because they lack the
    product-name-leader + ALL-CAPS-code structure.

    Returns None if no qualifying run is found.
    """
    best = None  # (start, end, quality_tuple)

    i = 0
    n = len(text)
    while i < n:
        # Locate start of an alphabetic token. Product names may begin with a
        # lowercase letter when OCR keeps the brand casing ("auroCOMPACT",
        # "ecoTEC"), so accept any letter as a potential run start.
        if not text[i].isalpha():
            i += 1
            continue
        j = i
        while j < n and text[j].isalnum():
            j += 1
        if j - i > 14:
            i = j
            continue
        start = i
        prev_end = j
        tokens = [text[i:j]]

        # Extend over separator + next token, while next token is a DENSE
        # ALL-CAPS code, a digit-bearing token, or — for the very next word —
        # a short capitalized stub. This lets "auroCOMPACT VSC S 146/4-5 150"
        # build up, while Title-case descriptor words ("Gas-Kompaktgerät",
        # "Brennwerttechnik") stop it dead.
        cursor = j
        while cursor < n and text[cursor] in " /-.":
            k = cursor + 1
            while k < n and text[k].isalnum():
                k += 1
            if k >= n or k == cursor + 1:
                break
            tok = text[cursor + 1 : k]
            is_digit_tok = bool(re.match(r"^[0-9][0-9A-Za-z.\-]*$", tok))
            is_allcaps_code = (
                tok.isupper() and 2 <= len(tok) <= 6 and tok.isalpha()
            )
            is_single_caps = tok.isalpha() and tok.isupper() and len(tok) == 1
            is_short_stub = len(tokens) == 1 and tok[0].isupper() and len(tok) <= 4
            if is_digit_tok or is_allcaps_code or is_single_caps:
                tokens.append(tok)
                prev_end = k
                cursor = k
                continue
            if is_short_stub:
                tokens.append(tok)
                prev_end = k
                cursor = k
                continue
            # Non-model boundary (Title-case prose / descriptor) — stop.
            break

        end = prev_end
        run_text = text[start:end]
        last = tokens[-1]
        if re.search(r"\d", last) and len(tokens) >= 2:
            first = tokens[0]
            # A Title/Camel-case product-name leader ("auroCOMPACT", "Vitodens",
            # "ecoTEC") must contain at least one uppercase letter, so pure
            # lowercase unit words ("bar", "mit") can never be a leader.
            title_leading = first.isalpha() and any(c.isupper() for c in first)
            has_allcaps_code = any(
                t.isalpha() and t.isupper() and 2 <= len(t) <= 6 for t in tokens
            )
            # A genuine product designation is "auroCOMPACT VSC S 146/4-5 150":
            # a capitalized product-name leader immediately followed by an
            # ALL-CAPS type code, ending in a digit. Field-label / spec lines
            # ("Code 141 230V 50", "bar PMS PMW 10", "Hz 105") never have both,
            # so they never qualify here.
            title_followed_by_code = (
                title_leading and len(tokens) >= 3 and has_allcaps_code
            )
            if title_followed_by_code:
                digit_content = len(re.findall(r"\d", run_text))
                if not any(
                    GAS_CODE_RE.match(t) or POSTAL_CODE_RE.match(t)
                    or LEADING_ZERO_CODE_RE.match(t)
                    or SERIAL_LIKE_TOKEN_RE.match(t)
                    for t in tokens
                ):
                    quality = (digit_content, -start)  # more digits, earlier wins
                    if best is None or quality > best[2]:
                        best = (start, end, quality)
        i = cursor if cursor > end else end

    if best is None:
        return None
    result = text[best[0] : best[1]].strip(" /-.,;:")
    if len(result) > 40 or len(result) < 3:
        return None
    return result




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
            if not candidate or len(candidate) > 40:
                continue
            # Reject label values that are actually flue/category codes, gas
            # groups, postcodes or OCR garble — not models. Every modern gas
            # boiler nameplate prints "Type : C13x, C33x, C43x ..." for its
            # flue-system categories; without this guard that line hijacks the
            # model (e.g. Vaillant auroCOMPACT plate → "C13x").
            if (
                GAS_CODE_RE.match(candidate)
                or LEADING_ZERO_CODE_RE.match(candidate)
                or POSTAL_CODE_RE.match(candidate)
                or re.search(r"(?:^|\s)0\d{3,}(?=\s|$)", candidate)
            ):
                continue
            return candidate

    # Second pass: the model often directly follows the manufacturer name
    # Pass 2.5: multi-token product designation (e.g. "auroCOMPACT VSC S
    # 146/4-5 150"). Runs before the manufacturer-anchored pass because it
    # preserves dash/slash type codes ("146/4-5") the anchored tokenizer
    # drops. It only fires on a Title-case product-name leader followed by an
    # ALL-CAPS type code, so it never matches all-caps models like "WPL 18"
    # (those still fall through to the anchored pass).
    designation = _extract_product_designation(text)
    if designation:
        return designation

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
    for match in ENERGY_CLASS_PATTERN.finditer(text):
        value = match.group(1).upper()
        # Reject temperature units: "62 C", "19,0 C" (from °C after cleaning)
        start = match.start()
        if start > 0:
            prefix = text[:start].rstrip()
            if prefix and prefix[-1].isdigit():
                continue
        return value
    return None


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


# Patterns for installation/manufacture year extraction from nameplates.
# Ordered by specificity: explicit labels first, then context-proximity.
_YEAR_LABEL_RE = re.compile(
    r"(?:Baujahr|Bau\s*jahr|Errichtung|Herstelldatum|Herstellungsdatum|"
    r"Jahr|Jahr\s*der|Year|Installation\s*year|Manufactured|Built)"
    r"\s*[:\s.]*(?:im\s+Jahre\s+)?(\d{4})",
    re.IGNORECASE,
)

# MM/YYYY or MM.YYYY date formats (e.g. "02/2024", "03.2019")
_DATE_MONTH_YEAR_RE = re.compile(r"\b(\d{1,2})[/.](\d{4})\b")

# Vaillant-style document revision stamp (e.g. "01-03/14" → March 2014).
_DOC_REV_DATE_RE = re.compile(r"(?<![\d])(\d{2})[-./](\d{2})[-./](\d{2})(?![\d])")

# Standalone 4-digit year in valid range
_STANDALONE_YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")


def _two_digit_year_to_full(two_digit: int) -> int:
    """Convert a 2-digit year to a 4-digit year in the 1980–2030 window."""
    if two_digit <= 30:
        return 2000 + two_digit
    return 1900 + two_digit


def extract_installation_year(text: str) -> int | None:
    """Extract installation or manufacture year from OCR text.

    Searches for:
    - Labeled years: "Baujahr: 2006", "Errichtung 2015", "Herstelldatum: 02/2024"
    - Date formats: "02/2024", "03.2019"
    - Standalone years (1980-2030) near manufacturer/model context lines

    Returns:
        Year as int, or None if not found.
    """
    # Pass 1: explicit labels (highest confidence)
    match = _YEAR_LABEL_RE.search(text)
    if match:
        year = int(match.group(1))
        if 1980 <= year <= 2030:
            return year

    # Pass 2: date formats (MM/YYYY, MM.YYYY)
    match = _DATE_MONTH_YEAR_RE.search(text)
    if match:
        year = int(match.group(2))
        if 1980 <= year <= 2030:
            return year

    # Pass 2b: document revision stamps (Vaillant "01-03/14", "01.03.14")
    match = _DOC_REV_DATE_RE.search(text)
    if match:
        year = _two_digit_year_to_full(int(match.group(3)))
        if 1980 <= year <= 2030:
            return year

    # Pass 3: standalone year near manufacturer context
    manufacturer = extract_manufacturer(text)
    if manufacturer:
        idx = text.lower().find(manufacturer.lower())
        if idx != -1:
            # Search within ±300 chars of the manufacturer mention
            start = max(0, idx - 300)
            end = min(len(text), idx + len(manufacturer) + 300)
            segment = text[start:end]
            for m in _STANDALONE_YEAR_RE.finditer(segment):
                year = int(m.group(1))
                if 1980 <= year <= 2030:
                    return year

    # Pass 4: any standalone year in valid range (last resort)
    for m in _STANDALONE_YEAR_RE.finditer(text):
        year = int(m.group(1))
        if 1980 <= year <= 2030:
            return year

    return None


def extract_fields(text: str) -> dict:
    """Extract all relevant fields from OCR text in a single pass.

    Returns:
        Dictionary with keys: manufacturer, model, energy_class, heat_output,
        fuel_type, installation_year
    """
    cleaned = clean_text(text)
    return {
        "manufacturer": extract_manufacturer(cleaned),
        "model": extract_model(cleaned),
        "energy_class": extract_energy_class(cleaned),
        "heat_output": extract_heat_output(cleaned),
        "fuel_type": extract_fuel_type(cleaned),
        "installation_year": extract_installation_year(cleaned),
    }
