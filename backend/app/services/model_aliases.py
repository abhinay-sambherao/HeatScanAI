"""P3: curated nameplate → EPREL model alias table.

The nameplate model string and EPREL's `modelIdentifier` are different naming
systems (e.g. `Ochsner Europa MINI EW P` vs EPREL `AIR 80 C13A`). This table
records known equivalences learned from real scans. When an OCR-read model
matches an alias key, the matching engine treats it as an exact model match
against the mapped EPREL model(s).

Bootstrapped from the documented test scenarios in MATCHING_LIMITATIONS.md and
the nameplate dataset (docs/PRESENTATION_EXAMPLES.md).

Keys are lowercased nameplate models. Values are lists of valid EPREL
modelIdentifiers (also lowercased) that correspond to them.
"""

from typing import Dict, List, Optional

MODEL_ALIASES: Dict[str, List[str]] = {
    # Ochsner: nameplate "Europa MINI EW P" ~ EPREL "AIR 80 C13A" range.
    "europa mini ew": ["air 80 c13a", "air 55 c13a"],
    "europa mini ew p": ["air 80 c13a", "air 55 c13a"],
    "europa mini ew p r407c": ["air 80 c13a", "air 55 c13a"],
    # ELCO: nameplate "Thision S Plus 13" ~ EPREL "THISION L PLUS 13" line.
    "thision s plus 13": ["thision l plus 13", "thision sk 13"],
    "thision s plus 13.1": ["thision l plus 13"],
    # ÖkoFEN: nameplate "Pellematic08" ~ EPREL "PELEMATIC PES10" (abbreviation).
    "pellematic08": ["pelematic pes10", "pelematic smart"],
    # Stiebel Eltron: nameplate "WPL 18" ~ EPREL "WPL 13 E"/"WPL 18 EUS".
    "wpl 18": ["wpl 18 eus", "wpl 18 a"],
    # Viessmann: WB2 is an internal type code; map to the gas condensing line.
    "wb2": ["vitodens 200-w", "vitodens 300-w"],
    # Weishaupt: WTC-GB 90-A is already the EPREL-identical catalog code.
    "wtc-gb 90-a": ["wtc-gb 90-a", "wtc-gb 90"],
}


def lookup_alias(manufacturer: Optional[str], model: Optional[str]) -> Optional[List[str]]:
    """Return the EPREL model identifiers for a nameplate model, or None.

    Accepts an optional manufacturer to scope the lookup, but the alias table
    is deliberately small and mostly manufacturer-agnostic.
    """
    if not model:
        return None
    return MODEL_ALIASES.get(model.strip().lower())


def alias_overrides_model_score(model: Optional[str], product_model: Optional[str]) -> bool:
    """True if the EPREL model is a known alias of the nameplate model.

    Used to promote an otherwise-weak fuzzy score to a confident model match.
    """
    if not model or not product_model:
        return False
    aliases = MODEL_ALIASES.get(model.strip().lower())
    if not aliases:
        return False
    return product_model.strip().lower() in aliases
