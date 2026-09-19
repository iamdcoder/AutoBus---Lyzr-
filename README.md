# AutoBus — Autonomous B2B Supply Chain & SLA Contract Negotiator

> **Two agents. One governed negotiation.**
>
> **The agent proposes. Governance decides. The contract is emitted only after validation.**

AutoBus is a governed B2B procurement negotiation arena. A Buyer agent and a Supplier agent negotiate price, delivery, payment, and SLA terms while private policy envelopes, legal checks, risk scoring, convergence/deadlock handling, contract compilation, and audit integrity remain outside the LLM's authority.

The project is designed around the quest rubric:

| Quest pillar | Weight | AutoBus demonstrates |
|---|---:|---|
| **Lyzr Multi-Agent Depth** | **30%** | Two Lyzr agents, isolated Buyer/Supplier sessions, Studio configuration, Lyzr Agent API/SDK transport, Environment → Agent → Inference separation |
| **Negotiation Logic & Guardrails** | **30%** | Multi-round bargaining, concessions, convergence/deadlock, utility/risk/Pareto analysis, policy/legal firewall, final agreement firewall |
| **Code Architecture & Testing** | **20%** | Modular backend, deterministic governance, centralized/validated configuration, 162 passing tests across 26 files covering negotiation, deadlock, guardrails, legal validation, audit tamper-detection, contract integrity, configuration, and Lyzr integration |
| **Visual Dashboard & UX** | **20%** | Live negotiation arena, concession analytics, security/red-team views, audit verification, RFQ/Pareto views and contract output |

Full architecture detail: [`backend/docs/ARCHITECTURE.md`](backend/docs/ARCHITECTURE.md).
Full Lyzr integration and subscription-boundary detail: [`backend/docs/LYZR_EVIDENCE.md`](backend/docs/LYZR_EVIDENCE.md).

---

# Judge First: Live Demo

**Live application:** https://autobus-lyzr.onrender.com/

**Dashboard:** https://autobus-lyzr.onrender.com/ui

**Health:** https://autobus-lyzr.onrender.com/health

**Swagger / API docs:** https://autobus-lyzr.onrender.com/docs

No API key is required from the judge for the public deployment.

### Fastest judging path

**Live Dashboard → Run Negotiation → Inspect governance → Open Contract JSON → Open PDF → Verify Audit → Run Stress Test → Inspect Architecture**

---

# Judge Execution — Reproducible Path

## 1. Open the live dashboard

Open the dashboard URL above. It exposes the business outcome first while the deeper Lyzr architecture is available through the API and repository.

## 2. Run a normal negotiation

Use the default/demo configuration and click the button that starts the negotiation directly in the dashboard.

- **Buyer:** private procurement policy.
- **Supplier:** private commercial policy.

Look for multiple negotiation rounds, price/delivery/payment/SLA proposals, concessions, utility and risk, convergence or deadlock status, and policy/guardrail decisions.

The key sequence is:

```text
Agent proposal
    ↓
Guardrail / governance validation
    ↓
Authoritative state update
    ↓
Next negotiation round
```

A Lyzr agent does not directly write the authoritative deal state.

## 3. Inspect the final agreement

When the negotiation reaches `agreed`, note the returned `negotiation_id`. The result contains the final proposal, contract data, negotiation rounds, convergence/analytics, risk, Pareto information, and audit-integrity state.

## 4–6. Retrieve contract, PDF, and audit verification

```text
GET /api/negotiations/{negotiation_id}/contract
GET /api/negotiations/{negotiation_id}/pdf
GET /api/negotiations/{negotiation_id}/audit/verify
```

The generated contract includes a deterministic SHA-256 hash and a version number. A successful `/audit/verify` call confirms the recorded local audit events form a valid tamper-evident hash chain.

## 7. Run the guardrail stress test

```text
POST /api/stress-test
```

This runs six deliberately invalid cases — buyer over budget, supplier below price floor, delivery-window violation, payment-term violation, SLA penalty violation, uptime violation — and every one of them is **blocked rather than committed** to authoritative negotiation state (verified: 6/6 blocked against the sample payload below).

> **The model may propose; the governance layer decides whether the proposal is admissible.**

## 8. Inspect the Lyzr architecture

```text
GET /api/architecture
GET /api/lyzr/evidence
GET /api/lyzr/status
GET /api/system/governance
GET /api/system/config
```

These expose architecture/runtime evidence without exposing secrets. `/api/system/config` reports the validated, typed configuration state (which subsystems are configured) with every secret reduced to a boolean "configured" flag — never the value.

---

# Swagger / JSON Execution

Open `/docs` on the live deployment (or `http://localhost:8000/docs` locally), find `POST /api/negotiations`, click **Try it out**, and paste the sample payload from [`backend/samples/judge_negotiation_input.json`](backend/samples/judge_negotiation_input.json):

```json
{
  "buyer": {
    "price": { "target": 100000, "minimum": 95000, "maximum": 110000 },
    "delivery": { "target_days": 30, "maximum_days": 31 },
    "payment": { "preferred_days": 60, "minimum_days": 45 },
    "sla": { "minimum_uptime": 98, "minimum_penalty": 2, "maximum_penalty": 5 },
    "batna": "Purchase from alternate supplier at a 10% higher total cost with 45-day delivery.",
    "max_rounds": 10
  },
  "supplier": {
    "price": { "target": 120000, "minimum": 110000, "maximum": 125000 },
    "delivery": { "target_days": 28, "maximum_days": 31 },
    "payment": { "preferred_days": 60, "minimum_days": 60 },
    "sla": { "minimum_uptime": 98, "minimum_penalty": 2, "maximum_penalty": 4 },
    "batna": "Sell to another qualified buyer at a 110000 minimum price with Net 45 terms.",
    "max_rounds": 10
  },
  "buyer_name": "Apex Industrial Procurement",
  "supplier_name": "Vertex Components Ltd.",
  "product_name": "Industrial Components",
  "quantity": 1000
}
```

A successful response returns a negotiation identifier similar to:

```json
{ "negotiation_id": "NEG-XXXXXXXX", "status": "agreed" }
```

Use that identifier with:

```text
GET /api/negotiations/{negotiation_id}/contract
GET /api/negotiations/{negotiation_id}/pdf
GET /api/negotiations/{negotiation_id}/audit/verify
GET /api/negotiations/{negotiation_id}/analytics
```

### Verified sample outcome

Run directly against the deterministic simulation path (no Lyzr credentials required), this exact payload converges — reproducibly, in round 1 — to:

**₹110,000 · 30 days delivery · Net 60 · 98% uptime · 2% SLA penalty**

Live Lyzr inference can differ from this because model-generated proposals may vary; the deterministic simulation path is the reproducible benchmark path.

---

# Architecture: Environment → Agent → Inference (summary)

AutoBus separates **model capability** from **business authority**. Lyzr agents can propose negotiation moves, but the application owns the authoritative negotiation state and contract decision.

```text
ENVIRONMENT (Buyer/Supplier private policy)
        ↓
AGENT (Buyer/Supplier Lyzr Studio agent)
        ↓
INFERENCE (Lyzr Agent API/SDK, per-party session_id)
        ↓
GOVERNANCE BOUNDARY (optional external guardrail → PolicyValidator → LegalValidator)
        ↓
state mutation → analytics / deadlock-convergence → agreement firewall
        ↓
contract compiler (JSON + PDF, SHA-256) → tamper-evident audit chain
```

An `accept` action is not trusted merely because an agent proposed it — the complete candidate agreement is independently revalidated by `AgreementValidator` before `agreement_reached` and contract generation occur.

See [`backend/docs/ARCHITECTURE.md`](backend/docs/ARCHITECTURE.md) for the full governance ordering, isolation guarantees, and negotiation-intelligence detail.

---

# Guardrails and Security

The system treats LLM output as untrusted proposal data. `PolicyValidator` and `LegalValidator` (`backend/guardrails/`) check numeric bounds, procurement policy constraints, and legal constraints before a proposal can affect negotiation state; `AgreementValidator` re-checks the final package before contract generation.

The recommended security demo: run a normal negotiation, then run `POST /api/stress-test` and show that all 6 deliberately invalid cases are rejected before they can mutate negotiation state.

---

# Lyzr Integration and AIMS/Responsible AI (summary)

AutoBus uses the **Lyzr Agent API** (`agent_id` + per-party `session_id`) and the **Lyzr SDK/ADK** as a second transport path, with Buyer and Supplier configured as separate Lyzr Studio agents (`agents/lyzr/environment_manifest.json`).

`BUYER_AGENT_ID` and `SUPPLIER_AGENT_ID` are **identifiers, not credentials** — required for live Lyzr mode, not required for deterministic simulation mode. The sensitive value is `LYZR_API_KEY`.

**Native Lyzr Responsible AI and native Lyzr AIMS were not exposed on the quest submission account**, so AutoBus does not claim either was activated. It instead ships deterministic application-side policy/legal enforcement and a tamper-evident local audit chain (normalized `autobus.aims-event.v1` records, forwardable to an authorized external sink via `LYZR_AIMS_WEBHOOK_URL`).

See [`backend/docs/LYZR_EVIDENCE.md`](backend/docs/LYZR_EVIDENCE.md) for the full capability boundary, Agent ID setup, and exact judge wording for this distinction.

---

# Recommended 3-Minute Demo Script

1. **Guardrails (20s)** — Show Buyer ceiling, Supplier floor, delivery window, payment terms, SLA bounds. *"These values are private policy — reservation values are never exposed to the other agent."*
2. **Normal negotiation (50s)** — Run it; point to proposal history, concessions, utility, risk, convergence. *"The Lyzr agent generates a proposal. It crosses the governance boundary before it can mutate authoritative state."*
3. **Bounded attack surface (35s)** — Run the stress test; show a blocked out-of-policy value. *"Even an invalid proposal doesn't get write access to the deal state."*
4. **Multi-vendor decision quality (30s)** — Run the 3-supplier RFQ; show utility/risk/Pareto ranking. *"The system compares commercial trade-offs, not just price."*
5. **Auditability (25s)** — Open Audit, verify the hash chain. *"Every meaningful state transition is recorded and verifiable."*
6. **Contract integrity (20s)** — Generate the contract, show the SHA-256 hash and version. *"The output of the governed state machine is the contract — not the agent."*

If asked about AIMS/Responsible AI, use the exact wording in `backend/docs/LYZR_EVIDENCE.md` — do not call the local JSONL audit chain "AIMS."

---

# Local Execution

## No-credential simulation

Deterministic simulation mode requires no Lyzr credentials and reproduces the verified sample outcome above.

### Windows

```text
setup.bat
run_backend.bat
```

### Manual

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Then open `http://localhost:8000/ui` or `http://localhost:8000/docs`.

## Live Lyzr mode

```text
LYZR_API_KEY=<private credential>
BUYER_AGENT_ID=<Buyer Studio agent id>
SUPPLIER_AGENT_ID=<Supplier Studio agent id>
LYZR_USER_ID=<deployment/user configuration>
```

Never place the API key in source control.

---

# Complete Feature Reference

This section catalogs every endpoint and every dashboard capability in the current build. For the *why* behind each negotiation/guardrail formula, see [`backend/docs/ARCHITECTURE.md`](backend/docs/ARCHITECTURE.md#6-negotiation-intelligence).

## API endpoints

| Method & path | Purpose |
|---|---|
| `GET /` | Serves the dashboard (`frontend/index.html`). |
| `GET /health` | Liveness/version check (`status`, `service`, `version`). |
| `GET /ui` | Same dashboard as `/`, hidden from the OpenAPI schema. |
| `POST /api/negotiations` | Runs a full Buyer-vs-Supplier negotiation to completion (or deadlock/walk-away) and returns the negotiation ID, status, rounds, final proposal, contract, analytics, and audit-integrity summary. |
| `GET /api/negotiations/{id}/contract` | The generated `B2BContract` as JSON (404 if the negotiation never reached agreement). |
| `GET /api/negotiations/{id}/audit` | The raw list of audit events recorded for a negotiation. |
| `GET /api/negotiations/{id}/audit/verify` | Recomputes the SHA-256 hash chain and reports `{valid, events, broken_at}`. |
| `GET /api/negotiations/{id}/pdf` | Downloads the contract as a generated PDF. |
| `GET /api/negotiations/{id}/analytics` | Convergence, utility, risk, and Pareto-frontier analytics for a completed negotiation. |
| `POST /api/stress-test` | Runs 6 deliberately invalid proposals (buyer-over-budget, supplier-below-floor, delivery/payment/SLA-penalty/uptime violations) through the guardrails and reports how many were blocked. |
| `POST /api/rfq` | Runs one buyer policy against N supplier policies, ranks the outcomes by joint utility, and returns a winner. |
| `GET /api/architecture` | Environment → Agent → Inference → Governance → Contract → Audit layer status. |
| `GET /api/lyzr/evidence` | Lyzr capability/configuration evidence (API, SDK, Studio agents, RAI, AIMS) with all secrets masked. |
| `GET /api/lyzr/status` | Live Lyzr connectivity check: agent count, agent feature flags (when `LYZR_VERIFY_AGENT_FEATURES=1`), and `live_mode_ready`. |
| `POST /api/lyzr/bootstrap` | Discovers the `AutoBus Buyer Agent` / `AutoBus Supplier Agent` Studio agents and returns their IDs. |
| `POST /api/governance/lyzr-custom-guardrail` | The adapter endpoint Lyzr Responsible AI can call as a custom guardrail; returns `{verdict: allow|deny, reason, rule}`. |
| `GET /api/system/governance` | Governance subsystem status: mode, whether RAI/AIMS are configured, the local-fallback check list, and fail-closed behavior. |
| `GET /api/system/config` | The full validated `Settings` snapshot, secrets reduced to booleans. |
| `GET /api/aims/outbox` | Count and path of AIMS-envelope events currently queued in the local outbox. |

## Negotiation engine

- Multi-round bargaining (`NegotiationEngine.run`) with a configurable `max_rounds` per party (default 10, capped at 50).
- Per-proposal revision retries (`max_revisions_per_round`, default 2) — a guardrail-blocked proposal gets specific revision feedback and another attempt before the round is abandoned, rather than failing the whole negotiation on the first miss.
- Deterministic **or** live-Lyzr agent generation — `SimulationBuyerAgent`/`SimulationSupplierAgent` (`backend/main.py`) reproduce the verified sample outcome with zero external calls; `BuyerAgent`/`SupplierAgent` (`agents/`) drive the same interface against real Lyzr Studio agents.
- Convergence tracking (weighted price/delivery/payment/SLA gap every round) and deadlock/stagnation detection (repeated-offer threshold or a non-decreasing 3-round gap trend).
- Joint-feasible-zone projection — an arbiter step that nudges an already policy-valid proposal toward a genuine overlap between both parties' hard limits, without ever crossing either one.
- Independent per-party utility scoring (5 weighted components) and a 0–100 commercial risk score with CRITICAL/HIGH/MEDIUM/LOW labeling.
- Pareto-efficiency analysis across every proposal made during a negotiation.
- Multi-supplier RFQ mode — one buyer policy evaluated against several supplier policies in one call, ranked by joint utility.

## Guardrails & governance

- **`PolicyValidator`** — enforces each party's private numeric bounds (price ceiling/floor, delivery max, payment min, SLA penalty band, SLA uptime min).
- **`LegalValidator`** — five mandatory, policy-independent legal/commercial sanity rules, each with a stable rule ID.
- **`GuardrailEngine`** — the per-round guardrail pipeline (policy → legal, first-block-wins).
- **`AgreementValidator`** — the agreement firewall: re-validates the full candidate deal against *both* parties plus legal rules before it can become a contract.
- **`LyzrGovernance`** — local deterministic checks (private-data-leakage scan, prompt-injection scan, proposal-schema check, numeric-sanity check) that run unconditionally, plus an optional external Lyzr Responsible AI guardrail call that fails closed on error.
- **AIMS-compatible audit export** — normalized `autobus.aims-event.v1` events, sent to an authorized external sink when configured or queued in a local JSONL outbox otherwise.
- **Environment isolation** (`AgentEnvironment`) — a forbidden-field blocklist (BATNA, min/max price, reservation/walk-away price, raw policy) that nothing can bypass on the way into the shared negotiation channel.

## Contract & audit

- Structured `B2BContract` generation (JSON) with a canonical, sorted-key SHA-256 payload hash and a `version` field.
- One-page PDF contract rendering (ReportLab) with the same fields plus a negotiation-record summary, downloadable per negotiation.
- Tamper-evident local audit chain — every meaningful transition is SHA-256-hash-linked to the previous event; `verify()` recomputes the whole chain and reports exactly where it breaks, if anywhere.
- 16 distinct audit event types spanning negotiation start through contract generation and governance events.

## Configuration & deployment

- Centralized, validated `pydantic-settings` configuration (`backend/config.py`) covering Lyzr transport, Studio agent IDs, Responsible AI/governance, AIMS, and deployment (CORS, public URL) — with startup-time validation (e.g. timeouts must be positive) instead of silent misconfiguration.
- Deterministic **no-credential simulation mode** for local/offline running and judging.
- Live Lyzr mode via four environment variables (`LYZR_API_KEY`, `BUYER_AGENT_ID`, `SUPPLIER_AGENT_ID`, `LYZR_USER_ID`).
- Docker build (`Dockerfile`) and a GitHub Actions CI/CD pipeline (lint, compile, test-with-coverage, Docker build, optional Render deploy hook).
- Windows setup/run scripts and cross-platform Lyzr Studio agent bootstrap scripts (`backend/scripts/`).

## Frontend dashboard (`frontend/index.html`, single-file React, zero build step)

- Editable Buyer/Supplier policy forms (price, delivery, payment, SLA, BATNA, max rounds) with an "Advanced" toggle for raw JSON editing.
- One-click negotiation run against `POST /api/negotiations`, with loading and error states managed by a centralized `useReducer`.
- Deal-outcome header (agreed / no-agreement / partial) with live status and audit-event count.
- Tabbed results: **Deal path** (price-convergence chart across rounds), **Round history** (per-round buyer/supplier price, gap, and action table), **Trust & audit** (event stream plus a hash-chain-verified badge).
- Contract card with one-click **PDF** and **JSON** downloads.
- **Adversarial Guardrail Lab** — runs the 6-attack stress test from the UI and shows attempts/blocked/enforcement-rate plus a per-attack pass/fail indicator.
- **Pareto frontier panel** — table of every historical proposal's buyer/supplier/joint utility with a PARETO/dominated tag.
- **Multi-vendor RFQ panel** — runs the buyer against three predefined supplier policies and highlights the recommended winner.
- **Lyzr control-plane strip** — "Powered by Lyzr" status badges (SDK active, both Studio agents configured) sourced live from `/api/architecture` and `/api/lyzr/evidence`.
- Header **LIVE / DEMO READY** badge driven by `/api/lyzr/status.live_mode_ready`.

## Testing

162 tests across 26 files — see the [Testing](#testing) section below for the full file list and how to run them.

---

# Repository Structure

```text
agents/
└── lyzr/                Buyer/Supplier Lyzr integration and configuration

frontend/                 zero-build dashboard / negotiation arena (single index.html)

backend/
├── audit/                tamper-evident audit chain
├── contract/             contract compilation / integrity
├── docs/                 ARCHITECTURE.md, LYZR_EVIDENCE.md
├── governance/           policy/legal governance boundary
├── guardrails/           deterministic guardrail validators
├── models/               structured domain models
├── negotiation/          rounds, concessions, convergence, deadlock, utility
├── samples/              judge_negotiation_input.json
├── scripts/              setup/bootstrap helpers
├── tests/                26 test files, 162 tests
├── config.py             centralized, validated environment configuration (pydantic Settings)
└── main.py               API entrypoint

Dockerfile                container build
.env.example              environment template (no secrets)
CONTRIBUTING.md            commit hygiene and PR conventions
README.md                 this file
```

---

# Engineering Improvements Completed

The following development-quality improvements are included in the current repository baseline without changing the negotiation or application behavior:

| Improvement area | Completed implementation | Where to see it |
|---|---|---|
| **CI/CD automation** | GitHub Actions runs Python linting, source compilation, the backend test suite **with coverage reporting** (`pytest-cov`, uploaded as a build artifact on every run), Docker image builds, and an optional Render deployment trigger on pushes to `main`. Pull requests run the validation stages without deploying. | [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) |
| **Testing coverage** | 116 new tests added on top of the previous 46 (162 total, across 26 files), targeting the areas that previously had the thinnest coverage: policy/proposal model validators, the agreement firewall, convergence/deadlock math, engine-level accept/walk-away/revision-retry/governance-retry branches, Pareto dominance (a proposal genuinely worse for both sides), risk's CRITICAL label, contract hash *sensitivity* (not just stability), and — previously untested entirely — audit hash-chain tamper detection and the centralized configuration module. | [`backend/tests/`](backend/tests/) |
| **Configuration management** | A centralized, validated `Settings` model (`pydantic-settings`) declares every environment variable the backend reads, with explicit types, defaults, and descriptions, so a misconfigured deployment fails fast and legibly instead of silently reaching a request handler as an empty string. Wired into `LyzrGovernance` (replacing scattered `os.getenv` calls one-for-one, with identical defaults). The one deliberate behavior change: the two timeout fields now reject a zero or negative value at startup instead of silently accepting a value that could never have worked; every other field's parsing is unchanged. Exposed read-only, secrets-masked, at a new `GET /api/system/config` endpoint. | [`backend/config.py`](backend/config.py), [`backend/tests/test_config.py`](backend/tests/test_config.py) |
| **Version control hygiene** | [`CONTRIBUTING.md`](CONTRIBUTING.md) documents the small-atomic-commit and conventional-commit-message convention this round of changes follows going forward, plus PR expectations (tests for new logic, `ruff`/`pytest` passing locally before pushing). | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| **Environment & secret hygiene** | A repository `.gitignore` excludes real environment files, local credentials/artifacts, Python caches, virtual environments, IDE files, generated runtime data, and frontend dependencies/build output. `.env.example` provides the environment configuration template without secrets. | [`.gitignore`](.gitignore), [`.env.example`](.env.example) |
| **Maintainability documentation** | This build intentionally ships with zero inline `#` comments and zero docstrings anywhere in `agents/` or `backend/` — every file was verified comment-free with Python's `tokenize` module, not a text search. Business-logic reasoning that would otherwise live in a comment (preference-band normalization, utility weighting, risk calculation near hard policy boundaries) is instead written out in full in [`backend/docs/ARCHITECTURE.md`](backend/docs/ARCHITECTURE.md) and the [Complete Feature Reference](#complete-feature-reference) below. | [`backend/negotiation/utility.py`](backend/negotiation/utility.py), [`backend/docs/ARCHITECTURE.md`](backend/docs/ARCHITECTURE.md) |
| **Frontend state & component structure** | The dashboard uses centralized `useReducer` state for negotiation results, audit data, security data, integrity status, loading, and errors, while reusable React components keep policy forms, statistics, utility displays, and dashboard sections separated. | [`frontend/index.html`](frontend/index.html) |

These items directly address the previously identified improvement areas: automated quality gates with visible coverage, materially deeper test coverage of the negotiation/guardrail/audit core, type-safe and validated configuration, a documented commit convention, safer deployment configuration, clearer business-logic maintainability, and a more structured frontend state model. None of them change negotiation, guardrail, contract, or audit *behavior*. The `config.py` wiring into `LyzrGovernance` preserves every previous default and parsing rule, with one narrow, deliberate exception noted above (rejecting non-positive timeouts) — everything else is covered by tests that pin the preserved behavior down.

---

# Testing

```bash
cd backend
pip install -r requirements.txt pytest-cov
pytest -q --cov=. --cov-report=term-missing
```

162 tests across 26 files, all passing at time of writing. In addition to the original `test_negotiation`, `test_deadlock`, `test_guardrails`, `test_policy`, `test_legal_validator`, `test_governance`, `test_audit`, `test_contract`, `test_contract_integrity`, `test_lyzr_client`, `test_lyzr_integration`, `test_lyzr_surfaces`, `test_api_demo`, `test_integration`, `test_winning_features`, the suite now also includes `test_config`, `test_policy_validation_edge_cases`, `test_proposal_model`, `test_agreement_validator`, `test_negotiation_math`, `test_utility_and_pareto_extra`, `test_engine_edge_cases`, `test_contract_extra`, `test_audit_tamper_detection`, `test_governance_extra`, and `test_policy_and_legal_supplement`.

---

# Documentation Structure

This README is the primary judge entry point. Two supporting files hold detail that doesn't belong in a top-level README:

- [`backend/docs/ARCHITECTURE.md`](backend/docs/ARCHITECTURE.md) — full governance ordering, isolation guarantees, negotiation-intelligence detail.
- [`backend/docs/LYZR_EVIDENCE.md`](backend/docs/LYZR_EVIDENCE.md) — full Lyzr capability boundary, Agent ID setup and secret handling, and exact AIMS/Responsible AI judge wording.

Earlier drafts of this repository also carried `JUDGE_EXECUTION.md`, `JUDGE_GUIDE.md`, `LIVE_DEMO.md`, `DEMO_SCRIPT.md`, and `AGENT_CONFIGURATION.md` — these were near-duplicates of this README with drifting numbers (a stale sample-negotiation JSON, an inconsistent path to the sample file) and have been removed so there is one accurate version of each fact instead of five.

---

# Final submission checklist

- keep `LYZR_API_KEY` only in deployment secrets;
- provide Buyer/Supplier Agent IDs through environment configuration;
- verify no real `.env` or secret-bearing credential file is committed;
- keep the deterministic simulation path available for reproducibility;
- verify `backend/samples/judge_negotiation_input.json` is present;
- do not describe the local audit chain as native Lyzr AIMS;
- do not describe application-side guardrails as native Lyzr Responsible AI when that subscription access is unavailable.

---

# Important Links

- **Live AutoBus:** https://autobus-lyzr.onrender.com/
- **Dashboard:** https://autobus-lyzr.onrender.com/ui
- **Health:** https://autobus-lyzr.onrender.com/health
- **Swagger:** https://autobus-lyzr.onrender.com/docs
- **Lyzr Agent API reference:** https://docs.lyzr.ai/agent-api/inferences/chat
- **Lyzr Responsible AI reference:** https://docs.lyzr.ai/enterprise/agent-studio/responsible-safe-ai/Responsible

---

## One sentence for the judge

> **AutoBus uses two Lyzr agents to negotiate, but keeps policy, legal validation, state mutation, contract creation, and audit integrity outside the LLM's authority.**
