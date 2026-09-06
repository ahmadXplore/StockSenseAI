# Antigravity Build Prompt
## StockSense AI — Phase-by-Phase Agentic Build Instructions
**Use in:** Google Antigravity (Agent Manager / Editor, Plan Mode)
**Version:** 1.0

---

## HOW TO USE THIS PROMPT

1. Create a new Antigravity project rooted in this repo. Place all seven `_DOCUMENT.md` files (listed below) in a `/docs` folder at the project root **before** starting the agent — Antigravity is project-centric and needs these on disk to load as context, not pasted inline each time.
2. Paste the content below **"SYSTEM CONTEXT FOR THE AGENT"** as your first message to the Agent Manager.
3. Work in **Plan Mode**, one milestone at a time. After the agent produces a Plan Artifact for a milestone, review it against that milestone's Exit Criteria below, then explicitly approve before letting it switch to execution/Autopilot.
4. Do not let the agent skip ahead to a later milestone "while it's in there." Each milestone is a hard gate — that's intentional, because this system's entire value depends on data integrity that's invisible in a demo and only shows up as wrong signals later.
5. Re-paste or reference the relevant source doc section when a milestone touches it — the "Reference" line under each milestone tells you which doc/section to point the agent at if it starts guessing instead of reading.

---

## SYSTEM CONTEXT FOR THE AGENT
*(paste everything from here to the end as your opening message)*

You are building **StockSense AI**, a production-grade AI-powered stock analysis platform. This is not a demo or academic exercise — it will inform real investment decisions, so data integrity and honest uncertainty reporting matter more than feature velocity or visual polish.

Your ground-truth specifications are these files in `/docs`, in order of authority when documents conflict:

1. `1_MASTER_PROMPT.md` — product philosophy, module-by-module functional spec, system architecture, build order
2. `2_PRODUCT_REQUIREMENTS_DOCUMENT.md` — user stories, functional requirements (FR-xxx), non-functional requirements, MVP scope
3. `3_TECHNICAL_REQUIREMENTS_DOCUMENT.md` — tech stack, service architecture, API spec, ML performance thresholds, security/testing/deployment requirements
4. `4_APP_FLOW_DOCUMENT.md` — screen-by-screen user flows and navigation
5. `5_UIUX_DESIGN_BRIEF.md` — visual identity, component library, layouts, accessibility
6. `6_BACKEND_SCHEMA_DOCUMENT.md` — the authoritative PostgreSQL/TimescaleDB schema. Do not invent tables or columns that contradict this file — extend it via migration if a genuine gap is found, and flag the gap to me rather than silently diverging.
7. `7_IMPLEMENTATION_PLAN.md` — phase sequencing and per-phase exit criteria (background reference; the milestone list below supersedes its phase numbering for this build)

Read all seven before writing any code. When a requirement is ambiguous across documents, stop and ask me rather than guessing — for a financial system, a wrong assumption compounds silently.

### Non-negotiable constraints (apply to every milestone, no exceptions)

- **No feature is ever used before its `data_available_date`.** Build and reuse a single shared lag-enforcement function for both live inference and backtesting — do not implement this check twice in two places that can drift apart.
- **Backtests must never *claim* to be survivorship-bias-free unless they actually are.** Delisted, bankrupt, and acquired tickers must stay in the historical index-constituent tables (`market_data.index_constituents`) — that membership tracking is required for MVP. However, **for MVP we are not fetching delisted-ticker price history** (no free source — yfinance/Stooq/Alpha Vantage — reliably serves it, and this is a documented, deliberate MVP limitation, not a bug to fix). Every backtest run must therefore set `universe_note = 'current-universe-approximate'` and the UI must show the Data Limitation Badge (UI/UX Brief Section 3.2a) on every backtest view. Do not build delisted-price ingestion in this build — see Master Prompt Part 1.3 and PRD Section 5.
- **Confidence scores are never hand-tuned.** They come only from calibration curves (Platt/isotonic), prediction-interval width, model agreement, and regime match.
- **The Hard Veto Engine runs independently of, and before, the scoring/recommendation engine.** A single triggered veto blocks BUY/STRONG BUY regardless of how good every other score looks. Do not let vetoes become "one more weighted input."
- **Anomaly Type A/B/C classification defaults to Type C whenever evidence is ambiguous.** Never default to Type A. Type A requires ALL listed conditions present; Type C requires only ONE disqualifier present.
- **Every generated report carries a non-removable disclaimer, plus source attribution and a staleness/as-of timestamp on every data point.** This is structural output, not optional UI copy — enforce it in the report-generation code path, not just the frontend template.
- **Never silently fill missing data.** Flag and surface it. Missing data policy is "flag and report," not "interpolate and move on," unless a document explicitly says otherwise for a specific field.

### Operating protocol

For each milestone:
1. Enter Plan Mode. Produce a Plan Artifact listing the files you'll create/modify, the approach, and how you'll verify it against that milestone's Exit Criteria.
2. Wait for my explicit approval of the plan before executing.
3. Execute. Use the terminal to run tests and the browser tool to verify any UI-facing work end-to-end (don't just claim it works — show me it running).
4. Before declaring the milestone done, re-check it against its Exit Criteria line by line and report the result honestly, including anything that didn't pass.
5. Stop and wait for me to say "approved, proceed to Milestone N+1." Do not self-advance.

If you're ever unsure whether something should be a hard rule-based check versus a model-driven judgment, default to hard rule-based — the veto system, the Type A/B/C classifier, and the look-ahead guard should all be deterministic and unit-testable, not left to model discretion.

---

## MILESTONE 0 — Scaffolding & Environment

**Build:** Repo structure, Docker Compose (FastAPI + PostgreSQL 15/TimescaleDB + Redis + Celery worker + Next.js frontend), `.env.example` with no real secrets, lint/format config, CI skeleton (lint + unit test on PR), initial Alembic migration applying the full schema from `6_BACKEND_SCHEMA_DOCUMENT.md`.

**Reference:** TRD Section 1 (architecture + stack) and Section 9 (deployment) for exact service topology; Backend Schema Document in full for the migration.

**Exit criteria:**
- [ ] `docker-compose up` boots API, DB, Redis, Celery, frontend with no errors
- [ ] A health-check endpoint returns 200
- [ ] Migration runs cleanly against an empty database and produces every schema in `market_data`, `fundamentals`, `analysis`, `portfolio`, `ml`, `news`, `macro`, `audit`

---

## MILESTONE 1 — Data Foundation (look-ahead-safe)

**Build:** Price/volume ingestion (yfinance primary, Stooq cross-check, Alpha Vantage free-tier fallback), fundamentals ingestion (SEC EDGAR Company Facts API primary, Financial Modeling Prep free tier for analyst estimates only) with as-reported (not restated) values, corporate-action ingestion and adjustment verification, the shared `feature_date <= prediction_date - required_lag` guard function, data-quality checks (completeness, staleness, corporate-action verification) writing to `audit.data_quality_log`. All sources are free-tier — no paid API keys required for MVP.

**Reference:** Master Prompt Part 1 (Data Layer) for exact source-per-data-type mapping and lag rules (minimum 25-day earnings lag); Backend Schema `fundamentals.income_statements.data_available_date` for the generated-column pattern to reuse elsewhere.

**Exit criteria:**
- [ ] A test that deliberately tries to pull a fundamental value before its `data_available_date` fails/raises as designed
- [ ] Corporate-action-adjusted price series matches a manually verified reference for at least 3 tickers with known historical splits/dividends
- [ ] `audit.data_quality_log` populates on every ingestion run with pass/fail/warning status

---

## MILESTONE 2 — Core Scoring Engines

**Build:** Technical Analysis Engine (TA-Lib/pandas-ta indicators + plain-language translation), Fundamental Health Score (all 9 sub-scores from `analysis.fundamental_health_scores`), Valuation Engine (relative multiples + DCF, minimum 4 methods), baseline ML ensemble (XGBoost/LightGBM/Random Forest) with walk-forward validation stored in `ml.model_metadata`.

**Reference:** Master Prompt Parts 7–9 for scoring formulas; TRD Section 5.1 for the exact minimum performance thresholds a model must clear before `is_deployed = TRUE`.

**Exit criteria:**
- [ ] Fundamental and Valuation scores for 10 known companies are directionally sane on manual review
- [ ] Walk-forward validation covers ≥3 non-overlapping windows before any model is marked deployed
- [ ] Every deployed model passes ALL of: directional accuracy >54%, ROC-AUC >0.58, calibration error <0.08, backtest Sharpe >0.5, win rate >50%, max drawdown <-35%

---

## MILESTONE 3 — Advanced Signals

**Build:** News & Sentiment Engine (FinBERT + source-reliability weighting + materiality filter + event classification + insider 10b5-1 context), Anomaly Detection with explicit Type A/B/C rule logic, Macro Overlay (FRED indicators, VIX, sector/SPY relative performance), Regime Detection (Bull/Bear/High-Vol/Low-Vol/Rate-Rising/Rate-Falling/Recession), Hard Veto Engine as a standalone rule module.

**Reference:** Master Prompt Parts 5–6 and 10, 17 for the exact veto rule list, Type A/B/C condition sets, and regime-mismatch handling — implement these conditions literally, don't paraphrase them into something looser.

**Exit criteria:**
- [ ] Anomaly classifier run against 20 historical drop events correctly separates Type A/B from Type C — any Type C misclassified as Type A is a blocking bug
- [ ] Veto engine unit tests confirm BUY is blocked when any single veto condition is true, regardless of how favorable other test-fixture scores are
- [ ] Regime detector's labels for 2008, 2020, and 2022 spot-check sanely against known market history

---

## MILESTONE 4 — Risk & Backtesting

**Build:** Risk Analysis Engine (volatility, beta, drawdown, VaR/CVaR, Sharpe/Sortino/Calmar), Backtesting Engine that (a) correctly tracks historical index membership including delisted/bankrupt/acquired names via `market_data.index_constituents`, and (b) **explicitly and honestly discloses** — rather than silently corrects — the fact that delisted-ticker price history is not fetched in MVP (documented limitation, not a defect); point-in-time-only data access (reuse the Milestone 1 guard); execution/spread/slippage/commission models; Exit Strategy Module (stop-loss, trailing stop, profit targets, fundamental exit triggers, thesis tracking); confidence-score calibration (Platt/isotonic) with stored reliability diagrams.

**Reference:** Master Prompt Parts 1.3 and 13 (delisted-data known limitation and disclosure requirement) and Parts 11, 15; PRD Section 5; the earlier loophole review's fix on transaction-cost modeling — treat that fix as a requirement, not a suggestion. Do NOT attempt to source delisted-ticker price data in this milestone.

**Exit criteria:**
- [ ] `analysis.backtest_runs.universe_note` is populated as `'current-universe-approximate'` on every run, and `excluded_delisted_tickers` lists any index members from the test period whose price history could not be simulated
- [ ] The Data Limitation Badge (UI/UX Brief Section 3.2a) renders on every backtest view, non-dismissible, whenever `universe_note != 'survivorship-bias-corrected'`
- [ ] Backtest results include transaction costs and report `alpha_vs_buy_hold` and `alpha_vs_spy`
- [ ] At least one deployed model's reliability diagram shows predicted-probability bins tracking observed frequency within a reasonable tolerance
- [ ] Code review confirms no delisted-price fabrication/interpolation was added anywhere in the pipeline

---

## MILESTONE 5 — Recommendation, Report, Calculator

**Build:** Recommendation Engine (aggregates scores, applies veto engine as a hard gate before anything else, produces Short/Medium/Long recommendations with confidence), Investment Calculator (scenario returns in $ and %, annualized returns, position sizing by risk tolerance), Explainability Engine (reasons-for/reasons-against tied to actual data points, not generic text), full Report Generator assembling everything per the report structure.

**Reference:** Master Prompt Parts 14, 16, 19–20; PRD FR-014, FR-015, FR-020–024.

**Exit criteria:**
- [ ] Single-ticker report generation completes in <30 seconds
- [ ] Every field in the report traces to a source and an as-of/freshness timestamp
- [ ] Disclaimer is present and non-removable on every code path that produces a report, including raw API responses

---

## MILESTONE 6 — Frontend & Dashboard

**Build:** Full Next.js 14 application implementing every screen in the App Flow Document, styled per the UI/UX Design Brief (component library, dark/light mode, chart specs using Recharts + TradingView Lightweight Charts).

**Reference:** `4_APP_FLOW_DOCUMENT.md` in full for screen-by-screen flows; `5_UIUX_DESIGN_BRIEF.md` in full for visual/component specs. Use the browser tool to actually click through each flow, not just render it once.

**Exit criteria:**
- [ ] Every journey in the App Flow Document's screen flows is navigable end-to-end with real (or realistic seeded) data
- [ ] Mobile responsive behavior matches Section 3 of the App Flow Document
- [ ] Accessibility requirements from the UI/UX Brief are checked, not assumed

---

## MILESTONE 7 — Hardening & Launch Readiness

**Build:** Input validation and rate limiting on all endpoints, secrets audit, load test at 100 concurrent users, E2E test suite (Playwright) over critical flows, disclaimer/compliance language review against PRD Section 4.6, and a written runbook for vendor outages and failed model retrains.

**Reference:** TRD Sections 7 (Security) and 8 (Testing); PRD Section 4.6 (Compliance).

**Exit criteria:**
- [ ] Load test passes at target latency (p95 API response reasonable, per TRD monitoring targets) with no error-rate spike
- [ ] A deliberately simulated vendor outage produces a graceful "data stale, showing last known values" state — never a silent wrong number, never a crash
- [ ] No secrets present in code, logs, or version control history

---

## FINAL REMINDER TO THE AGENT

Feature velocity is not the goal here. A financial analysis tool that looks complete but silently leaks future data into its backtests, defaults an ambiguous anomaly to "buying opportunity" instead of "danger," or lets a great valuation score paper over an active SEC investigation is worse than no tool at all. When in doubt at any milestone, choose the more conservative, more verifiable implementation — and tell me you did.
