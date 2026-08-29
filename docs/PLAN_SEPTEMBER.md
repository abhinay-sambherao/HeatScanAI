# September Plan 2026 — Heizungscheck (HeatScan AI)

**Period:** September 1–30, 2026
**Hour cap:** **20 hours/week incl. all meetings** (= **80 h total** for 4 weeks, hard cap — do not exceed)
**Basis:** Anika Fuchs (client) task list of 2026-08-28 — finalize/open points
from Package 1 + implementation in AWS test environment + documentation.
**Developer:** Abhinay Sambherao

> Related docs: `HOURS.md` (July–Aug lifetime = 417 h, a SEPARATE figure to the
> 80 h September cap), `PENDING_ITEMS.md`, `DEPLOYMENT_AWS.md`, `API.md`,
> `AGENTS.md`. This is the work plan; hours are logged into `HOURS.md` under the
> September bucket (not into the 417 h figure).

---

## 1. Reference to the client task list

Anika's 8 named packages, and where each one stands:

| # | Client task | Status entering Sept | September effort |
|---|-------------|----------------------|------------------|
| 1 | EPREL crawler (all categories) | Mostly done (132 078 products, all heating groups) | Finalization + acceptance sweep |
| 2 | Category-specific structures & edge cases | Largely done (heater-only scope, flue/gas/postcode rejection, variant grouping) | Residual edge-case hardening |
| 3 | Data validation & quality assurance | Done (brand normalization, matching gates) | Formal QA report + migration on target DB |
| 4 | Image dataset feasibility analysis & collection | **Feasibility only (partial)** | **Full feasibility doc + collection = main open gap** |
| 5 | OCR pipeline implementation | Done (multi-variant PaddleOCR subprocess) | Optimization + edge eval |
| 6 | Database matching & search logic | Done (P0–P5, retail enrichment) | Tuning + regression |
| 7 | Testing, evaluation & optimization | Done (207 tests) | Evaluation pass against test dataset |
| 8 | Documentation & final delivery | In progress | Consolidate + client-ready delivery |
| — | Implementation in AWS (test env) + docs | Doc drafted (`DEPLOYMENT_AWS.md`) | **Deploy actual test env = open gap** |

**Two clear open gaps:** (4) systematic image-dataset collection, and the
AWS test-environment *deployment* (doc exists, env not stood up).

---

## 2. Milestones & weekly schedule

**Each week is capped at 20 h (incl. meetings).** Milestones below are assigned to
weeks; meeting hours are called out separately so scope vs. overhead stays
visible.

| Week | Dates | Milestones | Work h | Mtg h | Weekly total | Deliverables |
|------|-------|-----------|--------|-------|--------------|--------------|
| W1 | Sep 1–5 (Tue–Sat) | M0 Kickoff & scope lock · M1 EPREL crawler finalization | 17 | 3 | **20** | Confirmed scope, migrations applied, all-category crawl verified |
| W2 | Sep 7–12 (Mon–Sat) | M2 Data validation & QA · M3 image dataset feasibility | 18 | 2 | **20** | QA report; feasibility doc + dataset ingestion plan |
| W3 | Sep 14–19 (Mon–Sat) | M3 image dataset collection · M4 OCR optimization · M5 matching | 19 | 1 | **20** | Curated nameplate eval dataset; OCR + matching eval |
| W4 | Sep 21–30 (Mon–Wed) | M6 Testing/eval · M7 Documentation & delivery · M8 AWS test env | 15 | 5 | **20** | Green suite, client-ready docs, running AWS test env, delivery |

**Milestone ↔ week mapping (detail in §4):**

| # | Milestone | Week | Work h | Mtg h | Total | Deliverable |
|---|-----------|------|--------|-------|-------|-------------|
| M0 | Kickoff & scope lock | W1 | 2 | 2 | 4 | Confirmed scope, this plan approved, DB migration applied |
| M1 | EPREL crawler finalization | W1 | 7 | 1 | 8 | All-category crawl verified, edge-case fixes in |
| M2 | Data validation & QA hardening | W2 | 7 | 1 | 8 | QA report; brand/model QC across full DB |
| M3 | Image dataset feasibility + collection | W2–W3 | 11 | 1 | 12 | Feasibility doc + curated nameplate dataset |
| M4 | OCR pipeline optimization | W3 | 7 | 1 | 8 | Accuracy/regression report, Eval metric |
| M5 | Matching & search logic | W3 | 8 | 0 | 8 | Tuned thresholds, edge cases covered |
| M6 | Testing, evaluation & optimization | W4 | 9 | 1 | 10 | Full test suite + eval results + fixes |
| M7 | Documentation & final delivery | W4 | 6 | 0 | 6 | Client-ready docs + handoff |
| M8 | AWS test environment + docs | W4 | 8 | 2 | 10 | Running AWS test env + deployed guide |
| — | **Buffer / slippage** | throughout | — | — | 6 | Reallocation pool across M1–M8 |
| — | **TOTAL** | | **65** | **9** | **80** | |

> **Buffer note:** 6 h kept in reserve for day-1 surprises or meeting
> overruns. If it is consumed and the 20 h/week cap is at risk, we **stop and
> ask** before adding hours (consistent with Aug practice).

---

## 3. Meeting plan (9 h total, ~2 h/week)

| # | Meeting | When | Length | Attendees | Purpose |
|---|---------|------|--------|-----------|---------|
| 1 | Kickoff with Anika | Sep 2 (W1) | 1 h | Anika + me | Lock scope for the month, confirm open gaps (image dataset, AWS) |
| 2 | Internal design check | Sep 7 (W2) | 0.5 h | Me | Crawler finalization review |
| 3 | Data/QA checkpoint | Sep 9 (W2) | 0.5 h | Anika + me | Validate QA approach + criteria sign-off |
| 4 | Internal dataset review | Sep 12 (W2) | 0.5 h | Me | Image dataset feasibility decisions |
| 5 | Progress sync | Sep 17 (W3) | 0.5 h | Anika + me | Mid-month status, buffer decisions |
| 6 | Internal eval review | Sep 23 (W4) | 0.5 h | Me | Evaluation results vs. open gaps |
| 7 | Final delivery review | Sep 26 (W4) | 1 h | Anika + me | Walk through docs + demo readiness |
| 8 | Demo / delivery | Sep 30 (W4) | 1 h | Anika + team | Final delivery + AWS test env walkthrough |
| — | Ad-hoc clarifications (email/chat) | throughout | ~2 h | Anika + me | Short clarifications, not counted as formal meetings |

---

## 4. Detailed task breakdown

### M0 — Kickoff & scope lock (4 h)
- Confirm September scope with Anika; agree the 20 h/week (80 h month) cap and the two open gaps.
- Re-read `PENDING_ITEMS.md`; re-confirm each item's status.
- **Apply `products.source` DB migration on the target (test) DB**:
  ```sql
  ALTER TABLE products ADD COLUMN source VARCHAR(50) DEFAULT 'EPREL';
  UPDATE products SET source='EPREL' WHERE source IS NULL;
  ```
- Verify `retail_products` table auto-creates; smoke-test `POST /crawler/retail`.

### M1 — EPREL crawler finalization (8 h)
- Verify all requested categories are represented in DB (space/oil/gas, heat
  pumps, water heaters, solid fuel, storage, controls, solar).
- Confirm no pure-AC/cooling contamination (`HEATING_ONLY_GROUP_SLUGS` +
  `HEATING_ONLY_CATEGORIES`).
- Residual edge cases: composition/paket strings, sparse groups
  (controls/solar), non-model records (null `modelIdentifier`).
- Idempotency re-check (daily scheduler vs. manual crawl both safe).

### M2 — Data validation & QA hardening (8 h)
- Full-DB QC: zero `;`/`Paket` composition brands, `COUNT(*) =
  COUNT(DISTINCT eprel_id)`, no `WEB-` garbled brands.
- Validity sweep with `brand_normalizer.is_valid_brand()` on any new crawl data.
- Formal QA report for client (counts, rule checks, sample checks).

### M3 — Image dataset feasibility + collection (12 h) ← main open gap
- **Feasibility analysis:** nameplate image sources (EPREL product images,
  manufacturer photo archives, public nameplate repositories), licensing/IP
  constraints, annotation cost, target size (e.g. 200–500 curated plates for
  eval, larger for any retraining), train/val/test split.
- **Collection:** gather a feasible, license-clean sample (esp. the German
  majors: Vaillant, Viessmann, Bosch/Buderus/Junkers, Stiebel Eltron, Wolf,
  Brötje, ÖkoFEN, Ochsner, ELCO).
- Ground-truth CSV (mirroring `Kopie von Testdata_images_checked…csv`) with
  brand / model / fuel / heat output / year.

### M4 — OCR pipeline optimization (8 h)
- Multi-variant OCR (preprocessed / original / 2× upscale) tuning.
- Accuracy eval on the collected dataset → per-field (brand/model/fuel/kW/year)
  metric.
- Address residual false positives (flue tables, postal codes, year/power
  tokens) if they reappear on new real plates.

### M5 — Matching & search logic (8 h)
- P0–P5 re-verification; retail enrichment thresholds sanity-check.
- Edge cases: 2-digit German models (label path works by design), variant
  grouping (slash-code guard), fuel-window gating (`_kw_in_range`).
- Optimization: query latency on the growing DB (indexes, full-text).

### M6 — Testing, evaluation & optimization (10 h)
- Full suite green (currently 207) + new tests for any M1–M5 changes.
- 12-day/product regression sweep + the German nameplate test cases.
- Freeze scope; capture metrics report.

### M7 — Documentation & final delivery (6 h)
- Consolidate `ARCHITECTURE.md`, `API.md`, `AGENTS.md`, `HOURS.md` (September
  bucket), `PLAN_SEPTEMBER.md` outcomes.
- Client-facing delivery summary mapped 1:1 to Anika's 8 points.

### M8 — AWS test environment + docs (10 h) ← second open gap
- Stand up the test env per `DEPLOYMENT_AWS.md` / `DEPLOYMENT.md`: EC2
  (backend + Nginx), RDS PostgreSQL, S3 for images, optional ALB/ACM.
- **DB migration on the AWS test DB** (same `products.source` SQL as M0).
- Verify end-to-end scan + retail match + full crawl on the test env.
- Update `DEPLOYMENT_AWS.md` with real, run-tested steps + any deviations.

---

## 5. Risks, problems & mitigation ("all possible problems")

| # | Risk / problem | Likelihood | Impact | Mitigation |
|---|----------------|-----------|--------|------------|
| 1 | **Image dataset licensing** — EPREL/manufacturer images may not be redistributable | Med | High | Only use license-clean sources; treat dataset as internal eval set, not shipped; document provenance |
| 2 | **Image dataset size/time** — collection skews over budget | High | Med | Keep eval set targeted (200–500 plates, German majors first); feasibility-first, don't build a training pipeline unless required |
| 3 | **AWS cost / account access** — no AWS access or cost ceiling | Med | High | Request access + budget early in M0; use free/trial tier; RDS `db.t3.micro`, single AZ |
| 4 | **AWS environment instability** — tunnel/CDN vs direct IP, security groups block 5432 | Med | Med | Follow `DEPLOYMENT_AWS.md`; test from EC2 first, then externally; document every open port |
| 5 | **DB migration not applied** on a deployment → `products.source` / retail queries fail | High (on any un-migrated DB) | Med | Apply SQL in M0 and M8; add a startup/CI check that logs a warning if the column is missing |
| 6 | **Meeting overruns eat the 20 h/week cap** | Med | Med | Meetings capped to the 9 h above; ad-hoc clarifications via email; use the buffer before adding hours |
| 7 | **OCR accuracy floor on real photos** — new plates fail (blur, glare, perspective) | Med | Med | Extend multi-variant OCR; collect failures into the metric; honest "no match" over wrong guess |
| 8 | **Retail crawl rate/site changes** — heizungsdiscount24 sitemap/charset/schema changes | Low | Low | Crawler is additive; keep `_extract_model`/JSON-LD parsing resilient; re-run smoke test |
| 9 | **EPREL export format drift** — daily scheduler pulls a changed schema | Low | Med | Idempotent upsert + per-group commit; validate X rows/group; 0-dup assertion in QA |
| 10 | **Deadline slip** if gaps (image dataset, AWS) prove larger than planned | Med | Medium-High | Front-load both; use 6 h buffer; report scope risk at mid-month sync (Sep 17) |
| 11 | **Hours bookkeeping confusion** — 417 h (Jul–Aug) vs 20 h/wk (Sep) mixed up | Low | Low | Separate September bucket in `HOURS.md`; explicit "do not exceed 20 h/week, 80 h/month" note |
| 12 | **Frontend stale-cache** feedback loop reappears | Low | Low | Serve via backend at `:8000`; hard-refresh instructions; verify `/js/app.js` |

---

## 6. Definition of done (September)

1. Both open gaps closed: image dataset feasibility + a collected (license-clean,
   documented) nameplate eval dataset; and a **running AWS test environment**
   deployed from `DEPLOYMENT_AWS.md`.
2. All 8 of Anika's Package-1 points mapped to either "done" or "done + verified
   in September" with a client-facing one-pager.
3. `products.source` + `retail_products` migration verified on every target DB.
4. Full backend test suite green (≥ 207) with new tests covering September
   changes; evaluation report generated.
5. Documentation consolidated and delivery meeting held.
6. **September hours ≤ 20/week and ≤ 80/month** (recorded in the separate September bucket).

---

## 7. Hours budget reconciliation

- Work effort: **65 h**
- Meetings: **9 h**
- Reserve/buffer: **6 h**
- **Total: 80 h** = **4 weeks × 20 h/week** (hard cap; confirm before exceeding)

> Methodology per `HOURS.md`: hours reflect actual engineering time
> (implementation, debugging, research, tests, docs, deployment meetings).
> Long-running automated processes (crawls, benchmark OCR) are not counted on
> their own.
