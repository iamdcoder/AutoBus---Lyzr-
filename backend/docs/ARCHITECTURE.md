# AutoBus Architecture

This is the full technical reference. For the judge-facing summary and rubric mapping, see the root [`README.md`](../../README.md).

## 1. Design goal

AutoBus separates **model capability** from **business authority**. Lyzr agents can propose negotiation moves, but the application — not the LLM — owns the authoritative negotiation state and contract decision.

## 1.1 Engineering-quality controls

The repository also includes development and maintainability controls around the architecture described below:

- **CI/CD:** `.github/workflows/ci-cd.yml` validates pull requests and `main` pushes with linting, Python compilation, tests **with coverage reporting** (uploaded as a downloadable build artifact), Docker builds, and an optional Render deployment hook.
- **Configuration management:** `backend/config.py` centralizes every environment variable the backend reads into a single validated, typed `pydantic-settings` `Settings` model (with defaults matching the previous `os.getenv(...)` call sites exactly, so this is a behavior-preserving refactor). `LyzrGovernance` is wired to it; every value is exposed, secrets masked, at `GET /api/system/config`.
- **Testing:** 162 tests across 26 files (up from 46/15). The additions specifically target previously-thin areas: model validators, the agreement firewall in isolation, convergence/deadlock arithmetic (hand-verified against the documented formula), engine-level accept/walk-away/revision-retry/governance-retry branches, Pareto dominance with a genuinely-dominated point, and — previously entirely untested — audit hash-chain tamper detection and the new configuration module.
- **Version control hygiene:** [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) documents the small-atomic-commit convention this round of changes follows.
- **Environment hygiene:** `.gitignore` excludes real `.env` files and local/runtime artifacts, while `.env.example` documents the expected environment surface without credentials.
- **Business-logic documentation:** this build ships with zero inline `#` comments and zero docstrings anywhere in `agents/` or `backend/` (verified with Python's `tokenize` module). The scoring bands, utility weighting, and normalized risk calculation that would otherwise be explained in comments at the point of implementation are documented in full in section 6.1 below instead.
- **Frontend structure:** `frontend/index.html` uses a centralized React reducer for negotiation-level state and keeps repeated dashboard concerns in reusable components.

## 2. Environment → Agent → Inference

```text
ENVIRONMENT
├── Buyer private policy
└── Supplier private policy
          │
          ▼
AGENT
├── Buyer Lyzr Studio agent
└── Supplier Lyzr Studio agent
          │
          ▼
INFERENCE
├── Lyzr Agent API / SDK transport
├── independent session_id per party
└── model-generated proposal/action
          │
          ▼
GOVERNANCE BOUNDARY
├── optional Lyzr/custom external guardrail
├── deterministic policy validation (PolicyValidator)
├── deterministic legal validation (LegalValidator)
└── negotiation state mutation only after approval
          │
          ├───────────────┐
          ▼               ▼
       Analytics       Deadlock / convergence
          │               │
          └───────┬───────┘
                  ▼
           Agreement firewall (AgreementValidator)
                  │
                  ▼
           Contract compiler
            ├── JSON
            └── PDF + SHA-256 hash
                  │
                  ▼
          Tamper-evident audit chain (AuditLogger)
                  │
                  └── optional authorized AIMS-compatible sink
```

This is implemented in `backend/negotiation/engine.py` (`NegotiationEngine._generate_with_revisions` and `.run`), `backend/guardrails/` (`PolicyValidator`, `LegalValidator`, `GuardrailEngine`, `AgreementValidator`), `backend/contract/generator.py`, and `backend/audit/logger.py`.

## 3. Agent and policy isolation

Buyer and Supplier have distinct Lyzr agent identities (`BUYER_AGENT_ID` / `SUPPLIER_AGENT_ID`) and distinct conversation sessions — `main.py` constructs each with `session_id=f"{negotiation_id}-buyer"` / `f"{negotiation_id}-supplier"`. Private policy values such as reservation prices and BATNA are kept in party-specific application state and are not inserted into the counterparty's context.

The shared negotiation channel contains only information that is safe to expose as part of the bargaining process.

### 3.1 Environment isolation implementation (`governance/environment.py`)

`AgentEnvironment` wraps a party's `actor`, private `PartyPolicy`, `session_id`, and `shared_context`. `private_snapshot()` never returns raw policy values — it returns only presence flags (`{"price": {"target_present": true}, ...}`) via `build_redaction_snapshot()`. `allowed_shared_fields(payload)` and `can_read(field_name)` both check against an explicit forbidden-field blocklist (`batna`, `minimum_price`, `maximum_price`, `reservation_price`, `raw_policy`, `private_policy`, `walk_away_price`) before any dictionary key is allowed to cross into the counterparty's visible context.

### 3.2 Agent transport (`agents/`)

- **`buyer_agent.py` / `supplier_agent.py` — `BuyerAgent` / `SupplierAgent`.** Each builds a full negotiation prompt embedding the party's private policy values, an explicit "NEVER REVEAL: maximum price / reservation price / BATNA / internal policy values" instruction block, the current round number, running negotiation context, and any revision feedback from a prior blocked attempt — then calls `LyzrClient.chat()` and parses the JSON response into a `NegotiationProposal`. The parser strips Markdown code fences (```` ```json ```` / ```` ``` ````) if the model wraps its JSON, and normalizes `accepted_offer` back to `null` if the model set it on a non-`accept` action.
- **`lyzr_client.py` — `LyzrClient`.** The transport-agnostic entry point used by both agents. Prefers the Lyzr SDK/ADK transport when `LYZR_USE_SDK=1` and the SDK import succeeds; on an SDK-path failure it falls back to a direct Agent API call (`POST {LYZR_BASE_URL}/v3/inference/chat/`) when `LYZR_SDK_FALLBACK=1`, otherwise re-raises. Tracks `last_transport` (`"sdk"` or `"agent_api"`) for observability. Raises immediately at construction if `LYZR_API_KEY` is unset.
- **`lyzr_sdk.py` — `LyzrSDKClient`.** A thin wrapper over the `lyzr` package's `Studio` client, exposing `chat()`, `get_agent()`, and `list_agents()`.
- **`lyzr_bootstrap.py`.** Discovery/setup helpers (`list_agents`, `get_agent`, `summarize_features`, `bootstrap_agents`) that find the two Studio agents named `AutoBus Buyer Agent` / `AutoBus Supplier Agent` (or create them if `auto_create=True`) and can persist their IDs into a local `.env` file — used by `POST /api/lyzr/bootstrap` and the `backend/scripts/setup_lyzr*` scripts.
- **`agents/lyzr/environment_manifest.json`** — the static Environment → Agent → Inference mapping document referenced by the Buyer/Supplier Studio agent configuration.

## 4. Governance order

The authoritative path, as implemented in `NegotiationEngine._generate_with_revisions`:

```text
agent proposal
    ↓
optional external Lyzr/custom guardrail (governance.check)
    ↓
PolicyValidator + LegalValidator (GuardrailEngine.validate)
    ↓
state mutation
```

The key invariant:

> **An LLM response cannot directly mutate the authoritative negotiation state.**

If the external guardrail is configured, the application treats its denial/unavailability according to the configured fail-closed behavior. The local deterministic validators remain the business-rule firewall regardless of external guardrail availability.

### 4.1 `LyzrGovernance` implementation (`governance/lyzr_governance.py`)

`check(stage, actor, payload)` always runs `_local_check()` first, regardless of whether an external guardrail is configured:
- **Secret-leakage scan** — the entire payload is serialized to lowercase JSON and scanned for marker phrases (`"reservation price"`, `"walk-away price"`, `"private batna"`, `"supplier minimum"`, `"buyer maximum"`, `"raw_policy"`, `"private_policy"`, `"internal threshold"`, `"secret batna"`, and more); any hit denies with rule `privacy-isolation`.
- **Prompt-injection scan** — a second marker list (`"ignore previous instructions"`, `"system prompt"`, `"reveal your instructions"`, `"reveal your policy"`, `"disregard the policy"`, `"bypass the guardrail"`, `"disable the guardrail"`, `"pretend the rules do not apply"`) denies with rule `prompt-injection`.
- **Proposal schema check** — if a `proposal` key is present, it must be a JSON object containing all five required fields (`price`, `delivery_days`, `payment_days`, `sla_penalty`, `sla_uptime`); missing fields deny with rule `proposal-schema`.
- **Numeric sanity check** — each of those five fields must be a finite, non-boolean number within a broad sanity range (e.g. price `0.01`–`1,000,000,000`, delivery/payment days `0`–`3650`, SLA fields `0`–`100`); anything else denies with rule `numeric-sanity`.

Only if all local checks pass, and only if `LYZR_GUARDRAIL_URL` is configured, does `check()` additionally call the external Lyzr Responsible AI custom-guardrail endpoint (`POST` with `{stage, actor, payload, mode: "validate"}`, bearer-token auth if `LYZR_GUARDRAIL_TOKEN` is set). Any exception calling it (timeout, network error, non-2xx) is treated as a **denial** — this is the fail-closed behavior referenced above.

`publish_event(event)` wraps the event in the `autobus.aims-event.v1` envelope and POSTs it to `LYZR_AIMS_WEBHOOK_URL` if configured; on success it reports `{"published": true, ...}`, and on any failure (or when no webhook is configured at all) it appends the envelope to the local JSONL outbox (`LYZR_AIMS_OUTBOX`, default `data/aims_outbox.jsonl`) instead, so no governance event is ever silently dropped. `outbox_status()` reports how many events are currently queued locally.

## 5. Agreement firewall

An `accept` action is not trusted merely because an agent proposed it. The complete candidate agreement is revalidated by `AgreementValidator.validate()` against both parties' policies and the legal validator before `agreement_reached` and contract generation occur.

## 6. Negotiation intelligence

`backend/negotiation/` tracks:

- proposal history, gap history, and per-round metrics (`state.py`);
- concession movement across rounds (`convergence.py`);
- convergence signals and repeated-offer/deadlock detection (`deadlock.py`);
- party utility (`utility.py`);
- commercial risk (`risk.py`);
- Pareto efficiency (`pareto.py`);
- generic concession/negotiation-pressure helpers (`strategy.py`);
- multi-supplier RFQ ranking (`main.py` `/api/rfq`).

This allows the system to distinguish a policy violation from a commercially weak but still valid deal.

### 6.1 Per-module detail

**`state.py` — `NegotiationState`.** A dataclass holding `current_round`, the full `buyer_proposals`/`supplier_proposals` lists, the per-round `gaps` list, `round_metrics`, and the `consecutive_non_concessions` / `consecutive_repeated_proposals` counters used by deadlock detection. Exposes `initial_gap`, `latest_gap`, `gap_reduction`, and `convergence_ratio` (`(initial_gap - latest_gap) / initial_gap`, clamped to `[0, 1]`) as computed properties.

**`convergence.py`.**
- `calculate_gap(buyer, supplier)` — a single normalized distance between the two sides' current proposals: `0.55 × price_gap + 0.20 × delivery_gap + 0.15 × payment_gap + 0.10 × sla_gap`, where `price_gap` is `|Δprice| / max(|buyer.price|, |supplier.price|, 1.0)`, `delivery_gap`/`payment_gap` are `|Δdays| / 60`, and `sla_gap` is `|Δpenalty| / 10`. Lower is closer to a deal.
- `is_converging(previous_gap, current_gap)` — `True` when the gap shrank round-over-round.
- `calculate_concession(previous, current, role)` — per-field deltas plus role-aware "concession" amounts (a buyer conceding means raising price/payment or lowering its delivery/SLA ask; a supplier conceding means the reverse), each floored at 0 so a party that moved the wrong way shows zero concession rather than a negative one.

**`deadlock.py`.**
- `price_is_feasible(buyer_policy, supplier_policy)` — `True` unless the buyer's price ceiling is strictly below the supplier's price floor (in which case no price exists that satisfies both hard limits).
- `detect_stagnation(gaps, repeated_rounds, threshold=3)` — flags deadlock either when the same proposal has repeated for `threshold` rounds, or when the last three recorded gaps are non-decreasing within a `0.0005` tolerance (the negotiation has stopped closing).

**`utility.py`.**
- `_band_score(value, best, worst, higher_is_better)` — the shared normalization primitive: maps any raw value linearly onto `[0, 1]`, where `best` scores `1.0`, `worst` scores `0.0`, and values beyond `worst` clamp to `0.0`.
- Per-field scorers (`_price_score`, `_delivery_score`, `_payment_score`, `_sla_uptime_score`, `_sla_penalty_score`) each pick that party's own `best`/`worst` reference points from its private policy (e.g. for a buyer, price `best = target`, `worst = maximum or target × 1.25`; for a supplier it's mirrored around the price floor).
- `calculate_utility(proposal, policy, role)` — combines the five component scores into a single weighted total: **price 45%, delivery 20%, payment 15%, SLA uptime 10%, SLA penalty 10%**. It also derives a `risk_score` from how much margin the proposal leaves versus each hard policy limit (price ceiling/floor, delivery max, payment min, uptime min, penalty max — each clamped to `[0, 1]` and averaged, then `risk_score = 100 × (1 − average_margin)`), and buckets the total into a plain-language `rationale` (`≥0.80` strong alignment, `≥0.60` acceptable with trade-offs, `≥0.40` marginal, else close to walk-away).
- `explain_tradeoff(before, after, role, policy)` — utility and risk before/after a proposal change, plus the per-component deltas, used to explain *why* a concession helped or hurt a party.

**`risk.py`.**
- `_hard_limit_checks(...)` — counts how many of the 10 hard policy limits (buyer/supplier price bound, both parties' delivery max, both parties' payment min, both parties' SLA penalty band, both parties' SLA uptime min) a proposal violates.
- `_margin_risk(utility_score)` — `(1 − utility) × 100`, clamped to `[0, 100]`.
- `calculate_risk(proposal, buyer_policy, supplier_policy)` — averages buyer/supplier margin risk into a `commercial_risk` score, and labels the deal **CRITICAL** if any hard limit is violated (regardless of score), otherwise **HIGH** (≥70), **MEDIUM** (≥40), or **LOW**. Returns both utilities, both individual risk scores, the hard-limit-hit count, a `policy_compliance` flag (100 or 0), and a plain-language `interpretation`.

**`pareto.py`.**
- `build_pareto_frontier(proposals, buyer_policy, supplier_policy)` — scores every historical proposal for both parties (via `calculate_utility`) and marks a point `pareto_efficient=False` only if another point is **at least as good for both parties and strictly better for at least one** (classic Pareto dominance). Also reports each point's `joint_utility` (the mean of buyer and supplier utility).

**`strategy.py`** — smaller, standalone helpers not currently wired into `engine.py`'s main loop but available for reuse/testing: `calculate_concession` (raw per-field deltas), `has_meaningful_concession` (`True` if any field moved by more than `0.01`), and `negotiation_pressure(current_round, max_rounds)` (how close the negotiation is to its round limit, as a `0..1` ratio).

**`engine.py` — `NegotiationEngine`.** The orchestrator. `run()` drives the round loop (up to each party's configured `max_rounds`): for every round it calls `_generate_with_revisions()` for both sides, which (a) calls the party's agent (`_call_agent`) for a proposal, (b) runs it through `LyzrGovernance.check()` and `GuardrailEngine.validate()`, (c) if blocked, retries with revision feedback up to `max_revisions_per_round` times before giving up, and (d) audit-logs every attempt, block, and approval. `_project_to_joint_feasible_zone()` is an arbiter step — not a policy concession — that nudges a policy-valid-but-not-yet-overlapping proposal toward the counterparty's boundary when a feasible zone genuinely exists, without ever crossing either party's private hard limit. `proposal_is_acceptable_to_buyer`/`_supplier` and `_is_jointly_feasible` decide when an `accept` action is legitimate. `_update_repeated_proposal_count` and `state_to_rounds` feed the deadlock/stagnation and API-response-serialization paths respectively. `build_negotiation_context`/`build_revision_context` render the running negotiation summary and revision feedback text that gets embedded in the next agent prompt.

## 6.2 Guardrails in detail (`backend/guardrails/`)

- **`policy_validator.py` — `PolicyValidator`.** Enforces each party's own private numeric bounds: for the buyer, proposed price must not exceed `price.maximum` (if set); for the supplier, it must not fall below `price.minimum` (if set). Independent of role, it also enforces `delivery_days ≤ delivery.maximum_days`, `payment_days ≥ payment.minimum_days`, `sla.minimum_penalty ≤ sla_penalty ≤ sla.maximum_penalty`, and `sla_uptime ≥ sla.minimum_uptime`, plus rejects an unsupported `action` value or an unrecognized `role` string. Every failing check appends a specific, human-readable violation message rather than a generic "invalid" result.
- **`legal_validator.py` — `LegalValidator`.** A second, policy-independent firewall of mandatory legal/commercial sanity rules that apply regardless of either party's private preferences, each tagged with a stable rule ID for traceability: `LEGAL-PRICE-001` (price > 0), `LEGAL-DELIVERY-001` (1–3650 days), `LEGAL-PAYMENT-001` (1–365 days), `LEGAL-SLA-001` (95–100% uptime), `LEGAL-SLA-002` (penalty ≥ 0).
- **`guardrail_engine.py` — `GuardrailEngine.validate()`.** The per-round entry point used by `NegotiationEngine`: runs `PolicyValidator` first, then `LegalValidator`, short-circuiting on the first block and tagging the result with which validator caused it (`"policy"` / `"legal"`) and a severity (`"error"` for policy, `"critical"` for legal).
- **`agreement_validator.py` — `AgreementValidator`.** The **agreement firewall**: before any `accept` action is allowed to become `agreement_reached`, the complete candidate package is independently re-checked against *both* parties' `PolicyValidator` rules (not just the accepting party's) and the `LegalValidator`, with violations prefixed `BUYER:` / `SUPPLIER:` / `LEGAL:` so the source is unambiguous. An agent proposing "accept" is never sufficient on its own — this validator is the last gate before contract generation.

## 6.3 Domain models (`backend/models/`)

- **`policy.py`** — `PricePolicy`, `DeliveryPolicy`, `PaymentPolicy`, `SLAPolicy`, and the composite `PartyPolicy` (adds `batna: str` and `max_rounds: int`, default 10, bounded `1–50`). Each sub-model has a `pydantic` cross-field validator enforcing internal consistency at construction time — e.g. `PricePolicy` rejects a `minimum > maximum` or a `target` outside `[minimum, maximum]` before the object can even be built, so an invalid policy can never enter the negotiation.
- **`proposal.py`** — `ProposalAction` enum (`offer` / `counter` / `accept` / `walk_away`) and `NegotiationProposal`, with a validator that ties `accepted_offer` to the `accept` action only (it must be `None` for every other action, and if present for `accept` must be `"buyer"` or `"supplier"`).
- **`contract.py`** — `SLAContract` and `B2BContract`, the structured output schema: buyer/supplier/product/quantity/price/currency/delivery/payment/SLA terms plus `negotiation_id`, `negotiation_rounds`, `status`, `created_at`, a `version` field (currently `1`), and an optional `contract_hash`.
- **`validation.py`** — `ValidationStatus` enum (`allowed` / `blocked`) and `ValidationResult` (`status`, `reason`, `violations: list[str]`, `validator`, `severity`) — the single shared response shape every guardrail (policy, legal, agreement) returns, which is why the frontend and API can render any of them identically.

## 7. Audit and AIMS boundary

Every meaningful state transition is appended to a tamper-evident local hash chain (`backend/audit/logger.py`, SHA-256-linked JSONL). Normalized `autobus.aims-event.v1` records can also be sent to an authorized external sink via `LYZR_AIMS_WEBHOOK_URL`.

**`audit/logger.py` — `AuditLogger`.** `log()` writes one JSON line per event; each record embeds `previous_hash` (the `event_hash` of the prior line, or the literal string `"GENESIS"` for the first event in a file) and its own `event_hash` (SHA-256 of the canonical, sorted-key JSON of everything except the hash itself). `verify()` walks the file from the top, recomputing each hash and confirming it matches both the stored value and the next record's `previous_hash`; it returns `{"valid": bool, "events": <count verified>, "broken_at": <line number or null>}`, so a single edited historical line is detectable and localizable, not just "the file looks wrong."

**`audit/models.py` — `AuditEventType`.** 16 named event types spanning the full negotiation lifecycle: `negotiation_started`, `proposal_generation_attempt`, `proposal_generated`, `proposal_parse_error`, `policy_check`, `legal_check`, `proposal_approved`, `proposal_blocked`, `proposal_revised`, `agreement_validation`, `agreement_reached`, `deadlock`, `contract_generated`, `governance_event` (plus the underlying `AuditEvent` schema: `event_id`, `negotiation_id`, `timestamp`, `round_number`, `event_type`, `actor`, `status`, `details`).

**Native Lyzr AIMS is not claimed when the required subscription/platform access is unavailable.** See [`LYZR_EVIDENCE.md`](LYZR_EVIDENCE.md) for the full boundary.

## 8. Contract integrity

`backend/contract/generator.py` produces structured JSON/PDF output with a deterministic SHA-256 hash and a version field (`version=1`). This lets a downstream consumer verify that the artifact corresponds to the canonical contract payload.

- `create_contract(...)` — builds a `B2BContract` from the negotiation's final agreed proposal, generating a `CTR-XXXXXXXX` contract ID and an ISO-8601 UTC `created_at` timestamp; currency is fixed at `INR` and `status` is set to `"AGREED"`.
- `contract_payload_hash(contract)` — serializes the contract to canonical JSON (sorted keys, no extraneous whitespace) with the `contract_hash` field itself excluded, then returns its SHA-256 hex digest — this is the value stored back into `contract_hash`, so any later mutation of the payload is detectable by recomputing the hash.
- `contract_to_json(contract)` — pretty-printed (`indent=2`) JSON for the `GET /api/negotiations/{id}/contract` response and the dashboard's JSON download.
- `generate_contract_pdf(contract, output_path)` — renders a one-page PDF via ReportLab: a title, a labeled field table (contract ID, buyer, supplier, product, quantity, unit price, delivery, payment, SLA uptime, SLA penalty), a "Negotiation Record" block (negotiation ID, round count, status), and a closing disclaimer line — served by `GET /api/negotiations/{id}/pdf`.

## 9. Configuration reference (`backend/config.py`)

`Settings` (a `pydantic-settings` `BaseSettings`) is the single source of truth for every environment variable the backend reads. Fields, grouped by concern:

| Group | Fields | Notes |
|---|---|---|
| Lyzr transport | `LYZR_API_KEY`, `LYZR_BASE_URL`, `LYZR_CHAT_TIMEOUT`, `LYZR_USE_SDK`, `LYZR_SDK_FALLBACK`, `LYZR_USER_ID` | `LYZR_CHAT_TIMEOUT` must be `> 0` (validated at startup). |
| Studio agents | `BUYER_AGENT_ID`, `SUPPLIER_AGENT_ID` | Identifiers, not credentials; required only for live mode. |
| Responsible AI / governance | `LYZR_GUARDRAIL_URL`, `LYZR_GUARDRAIL_TOKEN`, `LYZR_GOVERNANCE_TIMEOUT`, `LYZR_RAI_POLICY_ID`, `LYZR_RESPONSIBLE_AI_ENABLED`, `LYZR_VERIFY_AGENT_FEATURES` | `LYZR_GOVERNANCE_TIMEOUT` must be `> 0`. |
| AIMS | `LYZR_AIMS_WEBHOOK_URL`, `LYZR_AIMS_TOKEN`, `LYZR_AIMS_OUTBOX` | Falls back to the local outbox path when no webhook is set. |
| Deployment | `CORS_ORIGINS`, `PUBLIC_BASE_URL` | `CORS_ORIGINS` accepts a comma-separated list or `*`. |

Computed, secret-safe properties used throughout the API (`sdk_preferred`, `sdk_fallback_enabled`, `agent_feature_check_enabled`, `cors_origin_list`, `lyzr_api_key_configured`, `studio_agents_configured`, `responsible_ai_endpoint_configured`, `aims_sink_configured`) expose *whether* something is configured as a boolean without ever exposing the underlying secret value — this is exactly what `GET /api/system/config` returns.

## 10. Reference files

- `agents/lyzr/environment_manifest.json` — Environment → Agent → Inference mapping.
- [`LYZR_EVIDENCE.md`](LYZR_EVIDENCE.md) — Lyzr capability evidence, subscription boundaries, and Agent ID setup.
- `../config.py` — centralized, validated environment configuration.
- `../samples/judge_negotiation_input.json` — the reproducible sample negotiation payload.
