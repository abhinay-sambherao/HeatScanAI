# Manufacturer Website URL Checklist

Automated link check run on **2026-08-13** against all entries in
`MANUFACTURER_SITES` (`backend/app/services/manufacturer_scraper.py`).

## How to use

1. Open each **Base URL** in your browser and confirm it loads the correct manufacturer homepage.
2. Open each **Search URL** (replace `{model}` with a real model, e.g. `Vitodens`) and confirm the search works.
3. Tick the **Verified** box on every row you have confirmed manually.

Automated markers: ✅ 2xx · 🛡️ 403 (likely bot-block, not a dead link) · ⚠️ 429 (rate-limited) · ❌ broken/unreachable

Summary: **37** reachable (2xx) · **2** bot-blocked (403/429) · **2** unreachable.

| # | Manufacturer | Base URL | Base check | Search URL | Search check | Verified |
|---|---|---|---|---|---|---|
| 1 | viessmann | `https://www.viessmann.de` | ✅ 200 | `https://www.viessmann.de/de/suche.html?q=**{model}**` | ✅ 200 | - [ ] |
| 2 | vaillant | `https://www.vaillant.de` | ✅ 200 | `https://www.vaillant.de/produkte/?q=**{model}**` | ✅ 200 | - [ ] |
| 3 | bosch | `https://www.bosch-thermotechnology.com` | ✅ 200 | `https://www.bosch-thermotechnology.com/de/search/?q=**{model}**` | ✅ 200 | - [ ] |
| 4 | buderus | `https://www.buderus.com` | ✅ 200 | `https://www.buderus.com/de/search/?q=**{model}**` | ❌ 404 | - [ ] |
| 5 | wolf | `https://www.wolf.eu` | ✅ 200 | `https://www.wolf.eu/de-de/search?q=**{model}**` | ❌ 404 | - [ ] |
| 6 | daikin | `https://www.daikin.de` | ✅ 200 | `https://www.daikin.de/de_de/produkte.html?q=**{model}**` | ✅ 200 | - [ ] |
| 7 | mitsubishi | `https://www.mitsubishi-les.com` | ✅ 200 | `https://www.mitsubishi-les.com/de/produkte/?q=**{model}**` | ✅ 200 | - [ ] |
| 8 | worcester | `https://www.worcester-bosch.co.uk` | ✅ 200 | `https://www.worcester-bosch.co.uk/search?q=**{model}**` | ✅ 200 | - [ ] |
| 9 | stiebel eltron | `https://www.stiebel-eltron.de` | ✅ 200 | `https://www.stiebel-eltron.de/de/produkte/suche.html?q=**{model}**` | ❌ 404 | - [ ] |
| 10 | nibe | `https://www.nibe.de` | ✅ 200 | `https://www.nibe.de/de/produkte/?q=**{model}**` | ❌ 404 | - [ ] |
| 11 | panasonic | `https://www.panasonic.com` | 🛡️ 403 (bot-blocked) | `https://www.panasonic.com/de/consumer/haushalt-heizung/suche.html?q=**{model}**` | 🛡️ 403 (bot-blocked) | - [ ] |
| 12 | riello | `https://www.riello.com` | ✅ 200 | `https://www.riello.com/de/produkte/?q=**{model}**` | ❌ 404 | - [ ] |
| 13 | weishaupt | `https://www.weishaupt.de` | ✅ 200 | `https://www.weishaupt.de/de/produkte/?q=**{model}**` | ❌ 404 | - [ ] |
| 14 | ferroli | `https://www.ferroli.com` | ✅ 200 | `https://www.ferroli.com/de/produkte?q=**{model}**` | ❌ 404 | - [ ] |
| 15 | ariston | `https://www.ariston.com` | ✅ 200 | `https://www.ariston.com/de/produkte/?q=**{model}**` | ✅ 200 | - [ ] |
| 16 | baxi | `https://www.baxi.de` | ✅ 200 | `https://www.baxi.de/produkte/?q=**{model}**` | ✅ 200 | - [ ] |
| 17 | glow-worm | `https://www.glow-worm.co.uk` | ✅ 200 | `https://www.glow-worm.co.uk/search?q=**{model}**` | ❌ 404 | - [ ] |
| 18 | ideal | `https://www.idealboilers.com` | ✅ 200 | `https://www.idealboilers.com/search?q=**{model}**` | ✅ 200 | - [ ] |
| 19 | remeha | `https://www.remeha.de` | ✅ 200 | `https://www.remeha.de/produkte/?q=**{model}**` | ✅ 200 | - [ ] |
| 20 | intergas | `https://www.intergasheating.co.uk` | 🛡️ 403 (bot-blocked) | `https://www.intergasheating.co.uk/search?q=**{model}**` | 🛡️ 403 (bot-blocked) | - [ ] |
| 21 | atag | `https://www.atagverwarming.nl` | ✅ 200 | `https://www.atagverwarming.nl/producten/?q=**{model}**` | ✅ 200 | - [ ] |
| 22 | junkers | `https://www.junkers.de` | ✅ 200 | `https://www.junkers.de/produkte/?q=**{model}**` | ❌ 404 | - [ ] |
| 23 | samsung | `https://www.samsung.com` | ✅ 200 | `https://www.samsung.com/de/search/?q=**{model}**` | ✅ 200 | - [ ] |
| 24 | lg | `https://www.lg.com` | ✅ 200 | `https://www.lg.com/de/suche/?q=**{model}**` | ❌ 404 | - [ ] |
| 25 | beretta | `https://www.beretta.com` | ✅ 200 | `https://www.beretta.com/de-de/produkte/?q=**{model}**` | ✅ 200 | - [ ] |
| 26 | biasi | `https://www.biasi.com` | ✅ 200 | `https://www.biasi.com/de/produkte/?q=**{model}**` | ✅ 200 | - [ ] |
| 27 | nefit | `https://www.nefit.nl` | ✅ 200 | `https://www.nefit.nl/zoeken/?q=**{model}**` | ✅ 200 | - [ ] |
| 28 | awb | `https://www.awb.nl` | ✅ 200 | `https://www.awb.nl/zoeken/?q=**{model}**` | ❌ 404 | - [ ] |
| 29 | brotje | `https://www.brotje.de` | ✅ 200 | `https://www.brotje.de/produkte/?q=**{model}**` | ✅ 200 | - [ ] |
| 30 | brötje | `https://www.brotje.de` | ✅ 200 | `https://www.brotje.de/produkte/?q=**{model}**` | ✅ 200 | - [ ] |
| 31 | viadrus | `https://www.viadrus.cz` | ✅ 200 | `https://www.viadrus.cz/vyrobky/?q=**{model}**` | ❌ 404 | - [ ] |
| 32 | chaffoteaux | `https://www.chaffoteaux.com` | ❌ unreachable | `https://www.chaffoteaux.com/de-de/search?q=**{model}**` | ❌ unreachable | - [ ] |
| 33 | de dietrich | `https://www.dedietrich-thermique.com` | ✅ 200 | `https://www.dedietrich-thermique.com/de/search?q=**{model}**` | ✅ 200 | - [ ] |
| 34 | saunier duval | `https://www.saunierduval.de` | ❌ unreachable | `https://www.saunierduval.de/produkte/?q=**{model}**` | ❌ unreachable | - [ ] |
| 35 | atmos | `https://www.atmos.cz` | ✅ 200 | `https://www.atmos.cz/vyrobky/?q=**{model}**` | ❌ 404 | - [ ] |
| 36 | thermia | `https://www.thermia.com` | ✅ 200 | `https://www.thermia.com/de/search?q=**{model}**` | ✅ 200 | - [ ] |
| 37 | clage | `https://www.clage.de` | ✅ 200 | `https://www.clage.de/suche?q=**{model}**` | ❌ 404 | - [ ] |
| 38 | truma | `https://www.truma.com` | ✅ 200 | `https://www.truma.com/de/search?q=**{model}**` | ❌ 404 | - [ ] |
| 39 | ökofen | `https://www.oekofen.com` | ✅ 200 | `https://www.oekofen.com/de-de/pelletheizung` | ✅ 200 | - [ ] |
| 40 | ochsner | `https://www.ochsner.com` | ✅ 200 | `https://www.ochsner.com/de-de` | ✅ 200 | - [ ] |
| 41 | elco | `https://www.elco.net` | ✅ 200 | `https://www.elco.net/de/produkte.html` | ✅ 200 | - [ ] |

## Known dead configs (from automated check)

- **chaffoteaux** — `chaffoteaux.com` unreachable (ConnectTimeout). Brand is live at `https://chaffoteaux.fr/`.
- **saunier duval** — `saunierduval.de` unreachable (ConnectError). Brand exited Germany; live at `https://www.saunierduval.com/`.
- **panasonic** / **intergas** — 403 to our client; usually reachable in a normal browser. Confirm manually.
- Several **search URLs** return 404 with `?q=200` — the search page path may have changed, or search requires real query terms. Confirm manually.

