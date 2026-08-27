# Heizungscheck — Dokumentation

Der **Heizungscheck** identifiziert Heizungsanlagen anhand eines Fotos ihres
**Typenschilds**. Er liest die wichtigsten Daten per OCR aus, gleicht sie gegen
die EU-EPREL-Produktdatenbank und die Kataloge der Hersteller ab und liefert
dem Anwender passende Produkttreffer — auch wenn das Typenschild nur schwer
lesbar ist oder die Marke gar nicht abgedruckt wurde.

> Zielgruppe: Energieberater, Schornsteinfeger und SHK-Installateure, die
> Heizungsanlagen für Fernwärme-Kampagnen, Sanierungsberatung oder
> Altbau-Erfassung erfassen.

---

## Inhaltsverzeichnis

1. [Funktionsweise](#funktionsweise)
2. [Ablauf einer Erfassung](#ablauf-einer-erfassung)
3. [Was erkannt wird](#was-erkannt-wird)
4. [Wie die Treffer entstehen (Matching)](#wie-die-treffer-entstehen)
5. [Beispiele](#beispiele)
6. [Grenzen](#grenzen)
7. [Technischer Überblick](#technischer-überblick)
8. [API](#api)
9. [Weitere Unterlagen](#weitere-unterlagen)

---

## Funktionsweise

```
Foto vom Typenschild
   │
   ▼
OCR-Pipeline (3 Lesepfade, isolierter Worker)
   │  Preprocessing   → Perspektive, Kontrast, OCR-Bildqualität
   │  Lesen           → PaddleOCR (robuster, crash-sicherer Subprozess)
   │  Parser          → Hersteller, Modell, Energieklasse, Brennstoff,
   │                    Nennwärmeleistung, Baujahr
   ▼
Matching (3-stufige Fallback-Kette)
   │  1. Lokale Produktdatenbank (132.000+ Produkte)
   │  2. Live-EPREL-API (on-demand)
   │  3. Hersteller-Website (Scraper)
   ▼
Ergebnis mit Konfidenz, Treffern und Begründung
```

Jedes **gültige Feld** wird mit einer **Konfidenz** ausgegeben. Die Treffer
zeigen, wie sicher die Zuordnung ist und **welche Merkmale übereinstimmen**
(Hersteller, Modell, Energieklasse, Brennstoff, Leistung).

---

## Ablauf einer Erfassung

1. **Foto aufnehmen oder hochladen** (JPG, PNG, WebP, PDF; bis 20 MB; auch
   mehrere Bilder möglich — die besten Einzelergebnisse werden zusammengeführt).
2. **Standort angeben** (GPS oder manuell; optional). Der Standort hilft bei der
   regionalen Identifikation und der Erfassung von Fernwärme-Potenzial.
3. **Baujahr**: Wird automatisch vom Typenschild gelesen (z. B. `Baujahr:`).
   Nur wenn auf dem Schild **kein** Jahr steht, fragt das System nach.
4. **Ergebnis**: Die erkannten Daten, der Standort und die passenden
   Produkttreffer (Konfidenz + Übereinstimmungsmerkmale) werden angezeigt.
   Daten lassen sich bei Bedarf manuell korrigieren.

---

## Was erkannt wird

| Feld | Quellen am Typenschild | Hinweis |
|---|---|---|
| **Hersteller** | Markenname, Alias, Produktlinie, Firmensitz | Auch wenn die Marke fehlt (z. B. `Niederkappel` → ÖkoFEN) |
| **Modell** | `Typ:`/`Mod.`-Label, direkt hinter der Marke | Störende Codes (PLZ, CE-Kennzeichen, Seriennummern) werden entfernt |
| **Energieklasse** | `A+++` … `G` | Verwechselt nie Gaskategorien (`G20`) mit Klassen |
| **Brennstoff** | `Erdgas`, `Öl`, `Strom`, `Holz` … | Auch Tippfehler wie `Stom` werden erkannt |
| **Nennwärmeleistung** | `14,4 kW` | Für die Leistungsfilterung beim Abgleich |
| **Baujahr** | `Baujahr:`, `Errichtung`, `Herstelldatum:` | Nur wenn vorhanden; sonst Abfrage |

---

## Wie die Treffer entstehen (Matching)

Der Abgleich bewertet jedes Produkt der Datenbank mit einer gewichteten
Punktzahl:

- Hersteller 35 %, Modell 35 %, Energieklasse 10 %, Brennstoff 10 %,
  Nennwärmeleistung 10 %.

**Qualitätsfilter** verhindern falsche Treffer:

- **P0 — Mindest-Modellwert:** Ist ein Modell vorhanden, muss es einen
  Mindest-Übereinstimmungswert erreichen. Ein nur-markenbasierter Treffer
  reicht nicht mehr aus.
- **P1 — Leistungsfilter:** Ein Produkt, dessen Nennleistung nicht in die
  ±25 %-/±2-kW-Bandbreite des abgelesenen Werts fällt, wird ausgeschlossen.
- **P2 — Baujahr-Filter:** Produkte, die deutlich **nach** dem abgelesenen
  Baujahr registriert wurden, werden ausgeblendet.

Fallen keine lokalen Treffer aus, wird automatisch die EPREL-API und — wenn
nötig — die Hersteller-Website abgefragt.

---

## Beispiele

| Typenschild | Ergebnis |
|---|---|
| `Vaillant auroCOMPACT VSC S 146/4-5` · Baujahr 2014 | Vaillant, Modell gefunden, Baujahr 2014 direkt gelesen |
| `… Niederkappel … Type Pellematic08` | ÖkoFEN `Pellematic08`, Holz, 8,2 kW (Marke fehlte auf dem Schild) |
| `… Mod.: WTC-GB 90-A 0063 BS 3948 …` | Weishaupt `WTC-GB 90-A`, Gas (Störcodes entfernt) |
| `Stiebel Eltron WPL 18` | Stiebel Eltron `WPL 18`, Strom, 97,9 % Konfidenz |
| `Truma S 3004` | **0 Treffer** — bewusst kein falscher Treffer (`TERMIA`/`TRANE` werden abgelehnt) |

Siehe auch: [`PRESENTATION_EXAMPLES.md`](./PRESENTATION_EXAMPLES.md).

---

## Grenzen

- **Namenssysteme weichen ab:** EPREL führt den Handelsnamen, nicht die
  Typenschild-Bezeichnung (`Ochsner Europa MINI EW P` ≠ `AIR 80 C13A`). Der
  Abgleich ist fuzzy und wird durch die Qualitätsfilter auf ein Minimum an
  Fehltreffern begrenzt.
- **Anlagen vor 2014 sind nicht in EPREL:** Aufgrund der
  Energielabel-Verordnung sind ältere Anlagen gesetzlich nicht registriert.
  Dann liefert die Hersteller-Website-Fallback oder ein ehrliches
  „Keine Treffer“.
- **OCR-Qualität:** Abgenutzte, verwinkelte oder überbelichtete Schilder können
  zu falschen Feldern führen. Mehrere Lesepfade und Stör-Muster-Filter
  minimieren dies, garantieren es aber nicht.
- **Die Leistungsangabe stammt vom Schild:** Die Filterbandbreite ist nur so
  gut wie der abgelesene kW-Wert.

---

## Technischer Überblick

| Komponente | Technologie |
|---|---|
| Backend | FastAPI (Python 3.12, asynchron) |
| Datenbank | PostgreSQL 16 (Produktion) / SQLite (Entwicklung) |
| OCR | PaddleOCR in isoliertem Worker-Subprozess |
| Bildverarbeitung | OpenCV (Perspektive, Kontrast, Rotation, Upscaling) |
| Fuzzy-Matching | RapidFuzz |
| Crawler | httpx + BeautifulSoup |
| Frontend | Statisches HTML/JS/CSS (vanilla, i18n DE/EN) |
| Bereitstellung | Docker Compose (PostgreSQL + Backend + Nginx) |

**Datenbestand:** ~132.000 Produkte, 2.500+ Hersteller (Quelle: EPREL).

---

## API

Die REST-API ist unter `GET /docs` (Swagger) dokumentiert. Wichtigste
Endpunkte:

| Methode | Pfad | Beschreibung |
|---|---|---|
| POST | `/ocr` | Bild hochladen, analysieren, Treffer liefern |
| POST | `/ocr/{id}/rematch` | Erfassung mit Baujahr neu abgleichen |
| GET | `/products` | Produkte suchen / listen |
| GET | `/manufacturers` | Hersteller mit Produktanzahl |
| POST | `/crawler/run` | EPREL-Crawler anstoßen |
| GET | `/health` | Health-Check |

---

## Weitere Unterlagen

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — technische Architektur
- [`API.md`](./API.md) — vollständige API-Referenz
- [`DEPLOYMENT.md`](./DEPLOYMENT.md) — lokale & Docker-Bereitstellung
- [`DEPLOYMENT_AWS.md`](./DEPLOYMENT_AWS.md) — AWS-Bereitstellung
- [`PRESENTATION_EXAMPLES.md`](./PRESENTATION_EXAMPLES.md) — Beispiele & Grenzen
- [`MATCHING_LIMITATIONS.md`](./MATCHING_LIMITATIONS.md) — Matching & Qualitätsfilter
- [`WORK_PROGRESS.md`](./WORK_PROGRESS.md) — Arbeitsfortschritt
