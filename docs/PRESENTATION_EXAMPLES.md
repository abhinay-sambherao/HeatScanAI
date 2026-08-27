# Heizungscheck — Working Examples & Limits (for Presentations)

This document collects **verified, real-world examples** of the Heizungscheck in
action — what it identifies correctly and where its limits are. Use these to
illustrate the system in presentations, demos, and sales conversations.

Each example is derived from actual scans in the project's test data
(`docs/Kopie von Testdata_images_checked.xlsx - Tabelle1.csv`), the OCR test
suite (`backend/tests/`), and the documented "Verified" results in `AGENTS.md`.

---

## Working Examples (5+)

### ✅ Example 1 — Vaillant combo boiler with readable year

**Nameplate:** `Vaillant auroCOMPACT VSC S 146/4-5 150` · Baujahr **2014** · Gas · 14 kW  
**Result:** Identified Vaillant, model `auroCOMPACT VSC S 146/4-5`, fuel gas,
installation year **2014** read directly off the plate. Year is used to filter
the product set (products released years later are excluded). *(Real scan, test dataset)*

**Why it works:** clear `Baujahr:` label + exact-on-plate model string + year filter.

---

### ✅ Example 2 — ÖkoFEN pellet boiler, brand never printed

**Nameplate:** `… Niederkappel … Type Pellematic08`  
**Result:** manufacturer **ÖkoFEN**, model **Pellematic08**, fuel `wood`,
heat output **8,2 kW**. *(Verified output, AGENTS.md §9)*

**Why it works:** the plate only printed the product line (`Pellematic`) and the
registered HQ address (`Niederkappel`) — never the word "ÖkoFEN". The parser maps
both aliases to the manufacturer, so the plate is still attributed correctly.
This is a case other tools would miss entirely.

---

### ✅ Example 3 — Weishaupt gas boiler, noisy plate

**Nameplate:** `… Mod.: WTC-GB 90-A 0063 BS 3948 CE 0085 …`  
**Result:** manufacturer **Weishaupt**, model **WTC-GB 90-A**, fuel `gas`.
The trailing codes (`0063 BS 3948`, `CE 0085` — a postal-like / CE code) are
deliberately stripped. *(Verified output, AGENTS.md §10)*

**Why it works:** multi-variant OCR (preprocessed + original + 2× upscale) + a
"model cleaner" that truncates at noise codes.

---

### ✅ Example 4 — Stiebel Eltron WPL 18 heat pump, live OCR

**Nameplate:** `Stiebel Eltron WPL 18`  
**Result:** manufacturer **Stiebel Eltron**, model **WPL 18**, electricity,
extracted at **97.9 % OCR confidence** in ~3.3 s. *(Verified live, AGENTS.md)*

**Why it works:** brand alias + manufacturer-anchored model pass; OCR runs in an
isolated, crash-safe subprocess.

---

### ✅ Example 5 — Truma generic-match suppression (honest "no match")

**Nameplate:** `Truma S 3004` (gas water heater)  
**Result:** **0 matches** — the system correctly refuses the old behaviour of
surfacing 5 junk hits (`TERMIA`, `TRANE`, `Terma`). *(Verified, 12-product sweep 12/12)*

**Why it works / why it matters:** rather than guess, the Heizungscheck reports
"Keine Treffer" and falls through to manufacturer-website search. **Saying no is
a feature** — it protects the user from wrong recommendations and build trust.

---

### ✅ Example 6 — ELCO boiler, partial-name worst case

**Nameplate:** `ELCO Thision S Plus 13`, Gas, 14.4 kW, **2019**  
**Result:** model `Thision S Plus 13.1` extracted via the manufacturer-anchored
pass; fuel `Erdgas` displayed. EPREL only lists the `Thision L PLUS` line, so the
system reports the closest match *with an explicit "limits" notice* (see below).
*(Real scan, test dataset)*

---

## Honest Limits (present in the "limits" slide)

No tool is perfect. These are the documented, deliberate boundaries — present
them as transparency and proof of rigor:

| Limit | Explanation | Mitigation |
|---|---|---|
| **Nameplate vs EPREL naming mismatch** | EPREL's `modelIdentifier` is a commercial catalog code, not what's printed on the plate. `Ochsner Europa MINI EW P` ≠ `AIR 80 C13A`. | Fuzzy scoring + P0 minimum-model threshold; attribute lookup (P5); growing alias table (P3) |
| **Pre-2014 units legally absent from EPREL** | EPREL only registers products after the energy-labelling regulation. Older plates have no matched entry. | Fallback chain: local DB → EPREL API → manufacturer website; explicit "no match" |
| **OCR noise** | Flue-gas tables (`G20 20`, `C13(X)`), postal codes (`D-88475`), serials can masquerade as model/energy fields. | Multiple OCR passes, rejection regexes, model cleaner |
| **Similar-looking wrong models** | `WPL 18` could fuzzy-match a `WPF 13` *water* heater at ~72 %. | Heat-output hard filter (P1) + model threshold (P0) keep it honest |
| **Heat-output relies on the plate value** | The kW band is only as good as the OCR value read off the plate. | ±25 % or ±2 kW band; falls back sensibly |
| **Installation year** | If the plate has no readable year (or none at all), the year is only as good as what the user enters. | OCR year extraction first; inline prompt only if absent; `P2` release-date filter |

---

## What to say (a 20-second elevator pitch)

> "Point your phone at your heating system's nameplate. The Heizungscheck reads
> manufacturer, model, energy class, fuel, heat output and installation year —
> even when the brand word is missing — and matches it against the EU EPREL
> database plus manufacturer catalogs. It knows when it can't find the exact
> product and tells you instead of guessing, so you never get a wrong
> recommendation."
