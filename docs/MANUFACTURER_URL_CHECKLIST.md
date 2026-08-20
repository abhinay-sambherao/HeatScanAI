# Manufacturer Website URL Checklist

Automated link check run on **2026-08-16** against all entries in
`MANUFACTURER_SITES` (`backend/app/services/manufacturer_scraper.py`).

Broken/404 entries were **removed from the crawler config**, and search URLs
with a working replacement were **updated**. robots.txt was checked for every
remaining site.

## How to use

1. Open each **Base URL** in your browser and confirm it loads the correct manufacturer homepage.
2. Open each **Search URL** (replace `{model}` with a real model, e.g. `Vitodens`) and confirm the search works.
3. Tick the **Verified** box on every row you have confirmed manually.

Automated markers: ✅ 2xx · 🛡️ 403 (likely bot-block, not a dead link) · ⚠️ 429 (rate-limited) · ❌ broken/unreachable

**robots.txt** column: ✅ 200 and the search path is crawlable (no `Disallow` match) ·
⚠️ 404 / not served (no restrictions by convention) · 🛡️ 403 (robots.txt itself bot-blocked)

Summary: **37** entries · **36** base URLs reachable (2xx) · **35** search URLs reachable (2xx) ·
**2** bot-blocked (403) · **0** broken/404 remaining. 4 dead entries removed since the last run.

| #   | Manufacturer   | Base URL                                 | Base check            | Search URL                                                                        | Search check          | robots.txt | Verified |
| --- | -------------- | ---------------------------------------- | --------------------- | --------------------------------------------------------------------------------- | --------------------- | ---------- | -------- |
| 1   | viessmann      | `https://www.viessmann.de`               | ✅ 200                 | `https://www.viessmann.de/de/suche.html?q=**{model}**`                            | ✅ 200                 | ✅ 200      | - [ ]    |
| 2   | vaillant       | `https://www.vaillant.de`                | ✅ 200                 | `https://www.vaillant.de/produkte/?q=**{model}**`                                 | ✅ 200                 | ✅ 200      | - [ ]    |
| 3   | bosch          | `https://www.bosch-thermotechnology.com` | ✅ 200                 | `https://www.bosch-thermotechnology.com/de/search/?q=**{model}**`                 | ✅ 200                 | ✅ 200      | - [ ]    |
| 4   | wolf           | `https://www.wolf.eu`                    | ✅ 200                 | `https://www.wolf.eu/de-de/suche?q=**{model}**`                                   | ✅ 200                 | ✅ 200      | - [ ]    |
| 5   | daikin         | `https://www.daikin.de`                  | ✅ 200                 | `https://www.daikin.de/de_de/produkte.html?q=**{model}**`                         | ✅ 200                 | ✅ 200      | - [ ]    |
| 6   | mitsubishi     | `https://www.mitsubishi-les.com`         | ✅ 200                 | `https://www.mitsubishi-les.com/de/produkte/?q=**{model}**`                       | ✅ 200                 | ✅ 200      | - [ ]    |
| 7   | worcester      | `https://www.worcester-bosch.co.uk`      | ✅ 200                 | `https://www.worcester-bosch.co.uk/search?q=**{model}**`                          | ✅ 200                 | ⚠️ 404      | - [ ]    |
| 8   | stiebel eltron | `https://www.stiebel-eltron.de`          | ✅ 200                 | `https://www.stiebel-eltron.de/de/produkte/?q=**{model}**`                        | 🛡️ 403 (bot-blocked) | ✅ 200      | - [ ]    |
| 9   | panasonic      | `https://www.panasonic.com`              | 🛡️ 403 (bot-blocked) | `https://www.panasonic.com/de/consumer/haushalt-heizung/suche.html?q=**{model}**` | 🛡️ 403 (bot-blocked) | 🛡️ 403     | - [ ]    |
| 10  | weishaupt      | `https://www.weishaupt.de`               | ✅ 200                 | `https://www.weishaupt.de/produkte?q=**{model}**`                                 | ✅ 200                 | ✅ 200      | - [ ]    |
| 11  | ferroli        | `https://www.ferroli.com`                | ✅ 200                 | `https://www.ferroli.com/en/produkte?q=**{model}**`                               | ✅ 200                 | ✅ 200      | - [ ]    |
| 12  | ariston        | `https://www.ariston.com`                | ✅ 200                 | `https://www.ariston.com/de/produkte/?q=**{model}**`                              | ✅ 200                 | ✅ 200      | - [ ]    |
| 13  | baxi           | `https://www.baxi.de`                    | ✅ 200                 | `https://www.baxi.de/produkte/?q=**{model}**`                                     | ✅ 200                 | ⚠️ 404      | - [ ]    |
| 14  | glow-worm      | `https://www.glow-worm.co.uk`            | ✅ 200                 | `https://www.glow-worm.co.uk/products?q=**{model}**`                              | ✅ 200                 | ✅ 200      | - [ ]    |
| 15  | ideal          | `https://www.idealheating.com`           | ✅ 200                 | `https://www.idealheating.com/search?q=**{model}**`                               | ✅ 200                 | ✅ 200      | - [ ]    |
| 16  | remeha         | `https://www.remeha.de`                  | ✅ 200                 | `https://www.remeha.de/produkte/?q=**{model}**`                                   | ✅ 200                 | ✅ 200      | - [ ]    |
| 17  | intergas       | `https://www.intergasheating.co.uk`      | ✅ 200                 | `https://www.intergasheating.co.uk/search?q=**{model}**`                          | ✅ 200                 | ✅ 200      | - [ ]    |
| 18  | atag           | `https://www.atagverwarming.nl`          | ✅ 200                 | `https://www.atagverwarming.nl/producten/?q=**{model}**`                          | ✅ 200                 | ✅ 200      | - [ ]    |
| 19  | junkers        | `https://www.junkers.de`                 | ✅ 200                 | `https://www.junkers.de/search?q=**{model}**`                                     | ✅ 200                 | ✅ 200      | - [ ]    |
| 20  | samsung        | `https://www.samsung.com`                | ✅ 200                 | `https://www.samsung.com/de/search/?q=**{model}**`                                | ✅ 200                 | ✅ 200      | - [ ]    |
| 21  | lg             | `https://www.lg.com`                     | ✅ 200                 | `https://www.lg.com/de/search?q=**{model}**`                                      | ✅ 200                 | ✅ 200      | - [ ]    |
| 22  | beretta        | `https://www.beretta.com`                | ✅ 200                 | `https://www.beretta.com/de-de/produkte/?q=**{model}**`                           | ✅ 200                 | ✅ 200      | - [ ]    |
| 23  | biasi          | `https://www.biasi.com`                  | ✅ 200                 | `https://www.biasi.com/de/produkte/?q=**{model}**`                                | ✅ 200                 | ✅ 200      | - [ ]    |
| 24  | nefit          | `https://www.nefit.nl`                   | ✅ 200                 | `https://www.nefit.nl/zoeken/?q=**{model}**`                                      | ✅ 200                 | ⚠️ n/a      | - [ ]    |
| 25  | awb            | `https://www.awb.nl`                     | ✅ 200                 | `https://www.awb.nl/producten?q=**{model}**`                                      | ✅ 200                 | ✅ 200      | - [ ]    |
| 26  | brotje         | `https://www.brotje.de`                  | ✅ 200                 | `https://www.brotje.de/produkte/?q=**{model}**`                                   | ✅ 200                 | ✅ 200      | - [ ]    |
| 27  | brötje         | `https://www.brotje.de`                  | ✅ 200                 | `https://www.brotje.de/produkte/?q=**{model}**`                                   | ✅ 200                 | ✅ 200      | - [ ]    |
| 28  | viadrus        | `https://www.viadrus.cz`                 | ✅ 200                 | `https://www.viadrus.cz/?s=**{model}**`                                           | ✅ 200                 | ✅ 200      | - [ ]    |
| 29  | de dietrich    | `https://www.dedietrich-thermique.com`   | ✅ 200                 | `https://www.dedietrich-thermique.com/de/search?q=**{model}**`                    | ✅ 200                 | ⚠️ n/a      | - [ ]    |
| 30  | saunier duval  | `https://www.saunierduval.com`           | ✅ 200                 | `https://www.saunierduval.com/search/?q=**{model}**`                              | ✅ 200                 | ✅ 200      | - [ ]    |
| 31  | atmos          | `https://www.atmos.eu`                   | ✅ 200                 | `https://www.atmos.eu/?s=**{model}**`                                             | ✅ 200                 | ✅ 200      | - [ ]    |
| 32  | thermia        | `https://www.thermia.com`                | ✅ 200                 | `https://www.thermia.com/de/search?q=**{model}**`                                 | ✅ 200                 | ✅ 200      | - [ ]    |
| 33  | clage          | `https://www.clage.com`                  | ✅ 200                 | `https://www.clage.com/de/produkte?q=**{model}**`                                 | ✅ 200                 | ⚠️ n/a      | - [ ]    |
| 34  | truma          | `https://www.truma.com`                  | ✅ 200                 | `https://www.truma.com/de/produkte?q=**{model}**`                                 | ✅ 200                 | ✅ 200      | - [ ]    |
| 35  | ökofen         | `https://www.oekofen.com`                | ✅ 200                 | `https://www.oekofen.com/de-de/pelletheizung`                                     | ✅ 200                 | ✅ 200      | - [ ]    |
| 36  | ochsner        | `https://www.ochsner.com`                | ✅ 200                 | `https://www.ochsner.com/de-de`                                                   | ✅ 200                 | ✅ 200      | - [ ]    |
| 37  | elco           | `https://www.elco.net`                   | ✅ 200                 | `https://www.elco.net/de/produkte.html`                                           | ✅ 200                 | ✅ 200      | - [ ]    |

## Removed on 2026-08-16 (broken / 404, no working replacement found)

These were **deleted from `MANUFACTURER_SITES`** because their search endpoint 404'd
(every candidate path probed) or the domain was unreachable:

| Manufacturer   | Previous base URL                           | Reason |
| -------------- | ------------------------------------------- | ------ |
| buderus        | `https://www.buderus.com/de/search/?q={model}` | Search endpoint returns 404/500 on all paths (`/de/search/`, `/de/produkte/`, `/de/suche/`); no server-side search found. Base site reachable. |
| nibe           | `https://www.nibe.de/de/produkte/?q={model}` | Search endpoint 404 on all probed paths (`/de/produkte/`, `/de-de/`, `/suche/`, `/search/`). |
| riello         | `https://www.riello.com/de/produkte/?q={model}` | Search endpoint 404 on all probed paths; homepage exposes no server-side search. |
| chaffoteaux    | `https://www.chaffoteaux.com/de-de/search?q={model}` | Domain unreachable (ConnectTimeout). Brand is live at `https://chaffoteaux.fr/` but that site has no working search endpoint either. |

## URLs fixed on 2026-08-16 (search endpoint had changed)

| Manufacturer   | Old search URL                                  | New search URL                                           |
| -------------- | ----------------------------------------------- | -------------------------------------------------------- |
| wolf           | `/de-de/search?q=`                              | `https://www.wolf.eu/de-de/suche?q=`                     |
| weishaupt      | `/de/produkte/?q=`                              | `https://www.weishaupt.de/produkte?q=`                   |
| glow-worm      | `/search?q=`                                    | `https://www.glow-worm.co.uk/products?q=`                |
| junkers        | `/produkte/?q=`                                 | `https://www.junkers.de/search?q=`                       |
| lg             | `/de/suche/?q=`                                 | `https://www.lg.com/de/search?q=`                        |
| awb            | `/zoeken/?q=`                                   | `https://www.awb.nl/producten?q=`                        |
| truma          | `/de/search?q=`                                 | `https://www.truma.com/de/produkte?q=`                   |
| ferroli        | `/de/produkte?q=` (404)                         | `https://www.ferroli.com/en/produkte?q=`                 |
| viadrus        | `/vyrobky/?q=`                                  | `https://www.viadrus.cz/?s=`                             |
| stiebel eltron | `/de/produkte/suche.html?q=` (404)              | `/de/produkte/?q=` (now 🛡️ 403 bot-blocked)              |
| ideal          | `https://www.idealboilers.com/...` (domain dead)| `https://www.idealheating.com/search?q=`                 |
| clage          | `https://www.clage.de/suche?q=`                 | `https://www.clage.com/de/produkte?q=` (domain moved)    |
| saunier duval  | `https://www.saunierduval.de/...` (domain dead) | `https://www.saunierduval.com/search/?q=`                |
| atmos          | `https://www.atmos.cz/vyrobky/?q=` (domain dead)| `https://www.atmos.eu/?s=` (domain moved to atmos.eu)    |

## robots.txt notes

- Every configured search path is **crawlable** (no `Disallow` match for the `*` agent).
- `worcester-bosch.co.uk` and `baxi.de` return **404 for robots.txt** — no restrictions by convention.
- `nefit.nl`, `dedietrich-thermique.com`, `clage.com` respond to `/robots.txt` with an HTML page / empty body (no machine-readable rules).
- `panasonic.com` serves robots.txt itself behind a 403 bot-block.

## Remaining manual confirmations

- **panasonic** / **stiebel eltron** — 403 to our client; usually reachable in a normal browser. Confirm manually.
- **viadrus** / **atmos** — search now uses the site-wide WordPress search (`/?s=`); product-link selectors may need adjusting against real result pages.
- **daikin** — `Crawl-delay: 60` in robots.txt; scraping is allowed but slow, keep request rate low.
