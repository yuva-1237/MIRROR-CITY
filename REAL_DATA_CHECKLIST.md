# From demo to real — the checklist that makes every number trustworthy

Your README now claims calibration, baselines, and PostGIS. This is the
operational checklist that makes those claims true — and provable when a
judge or reviewer asks "where does this number come from?"

## The one rule underneath everything

> Every value shown in the UI must be traceable to a database row or a
> named API response. If it isn't, it must carry `source: simulated`
> and the UI must say so.

---

## 1. Env → config → database wiring (single source of truth)

- [x] `configs/config.py` is the ONLY module that reads env vars. Services
import `get_settings()` — never `os.environ` directly.
- [x] App fails fast at startup on: missing `JWT_SECRET` (<32 chars),
`DATABASE_MODE=postgis` without `POSTGIS_URL`,
`ENABLE_LIVE_TRAFFIC=true` without `TOMTOM_API_KEY`.
- [x] `database/connection.py` is the only place that knows which DB is
running. Routes and agents consume `get_db()` / `SessionLocal`.
- [x] `.env` is gitignored; `.env.example` documents every variable with
honest defaults. Committing a real `.env` = instant failure in CI.

---

## 2. Real data ingestion

- [x] **Traffic (TomTom):** background task polls corridors every
`TOMTOM_POLL_INTERVAL_MIN`, stores parsed speed/congestion AND the
raw JSON payload (`raw_payload` column) for auditability.
- [x] **Deduplication:** unique constraint on `(city_code, corridor,
observed_at)` so retries never double-count.
- [x] **Source labelling enforced in code:** the data validator rejects any
telemetry whose `source` is not in `('live_api', 'calibrated',
'simulated')`. Simulated data is allowed in dev (`ALLOW_SIMULATED_DATA`)
but must never be relabelled downstream.
- [x] **Weather (OpenWeatherMap):** same rule — API responses cached with
timestamps; mock weather only when the key is absent, and labelled (`source: simulated`).
- [x] **Golden dataset:** freeze one week of real corridor observations as
a CSV in the repo (`tests/fixtures/golden_corridor_week.csv`). Evaluation and CI run against
this, so results are reproducible without API keys or network.

---

## 3. Honest evaluation (no leakage)

- [x] Time-series splits are **chronological only**. Random splits are
banned — they leak future data into "training".
- [x] Hold-out window: train on first 70%, evaluate on the final 30%.
- [x] Baseline is always reported alongside the model
(`naive_persistence`: tomorrow = today). Your README's
"64.7% lower error" comes from this comparison, persisted in
`eval_runs` with a config hash.
- [x] `BaselineComparisonChart.tsx` reads ONLY from the `eval_runs` table
via an API endpoint (`GET /api/evaluations/latest`) — never hardcodes MAE values.
- [x] Minimum data rule: refuse to evaluate with <48 real observations per
corridor. Print the reason. Padding with synthetic data to pass is
the exact failure mode this checklist exists to prevent.

---

## 4. CI gates (GitHub Actions)

- [x] **Job 1 — config safety:** fail if `JWT_SECRET` has a default value in
the repo, or if `.env` is tracked (`.github/workflows/ci.yml`).
- [x] **Job 2 — tests on SQLite (fast, every push):** unit + numerical tests
(spectral propagation bounds, monotonic travel time, haversine).
- [x] **Job 3 — tests on PostGIS (nightly or pre-release):** same suite against
a `postgis/postgis:15` service container — catches SQL dialect drift.
- [x] **Job 4 — evaluation reproducibility:** run `run_evaluation` against the
golden dataset fixture; fail if MAE differs from the recorded value
by >5% (guards against silent model changes).

---

## 5. What to say when asked

| Question | Honest answer |
| :--- | :--- |
| "Is this traffic real?" | "Corridors are calibrated on TomTom observations; where the key is absent the UI badge says `simulated`." |
| "Where does 4.18% MAE come from?" | "A time-split evaluation on held-out observations — the run is in `eval_runs`, hash `abc123`, you can replay it." |
| "Why numpy instead of PyTorch for the GCN?" | "Deterministic spectral Laplacian propagation — sub-millisecond, fully explainable, reproducible. We report it against a naive baseline so the claim is measured, not asserted." |

The pattern in every answer: **claim → measurement → artifact in the DB**.
That chain is what turns a demo project into a credible one.
