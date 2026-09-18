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
- **Business-logic documentation:** `backend/negotiation/utility.py` explains the scoring bands, utility weighting, and normalized risk calculation at the point where those decisions are implemented.
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

## 5. Agreement firewall

An `accept` action is not trusted merely because an agent proposed it. The complete candidate agreement is revalidated by `AgreementValidator.validate()` against both parties' policies and the legal validator before `agreement_reached` and contract generation occur.

## 6. Negotiation intelligence

`backend/negotiation/` tracks:

- concession movement across rounds (`convergence.py`);
- convergence signals and repeated-offer/deadlock detection (`deadlock.py`);
- party utility (`utility.py`);
- commercial risk (`risk.py`);
- Pareto efficiency (`pareto.py`);
- multi-supplier RFQ ranking (`main.py` `/api/rfq`).

This allows the system to distinguish a policy violation from a commercially weak but still valid deal.

## 7. Audit and AIMS boundary

Every meaningful state transition is appended to a tamper-evident local hash chain (`backend/audit/logger.py`, SHA-256-linked JSONL). Normalized `autobus.aims-event.v1` records can also be sent to an authorized external sink via `LYZR_AIMS_WEBHOOK_URL`.

**Native Lyzr AIMS is not claimed when the required subscription/platform access is unavailable.** See [`LYZR_EVIDENCE.md`](LYZR_EVIDENCE.md) for the full boundary.

## 8. Contract integrity

`backend/contract/generator.py` produces structured JSON/PDF output with a deterministic SHA-256 hash and a version field (`version=1`). This lets a downstream consumer verify that the artifact corresponds to the canonical contract payload.

## 9. Reference files

- `agents/lyzr/environment_manifest.json` — Environment → Agent → Inference mapping.
- [`LYZR_EVIDENCE.md`](LYZR_EVIDENCE.md) — Lyzr capability evidence, subscription boundaries, and Agent ID setup.
- `../config.py` — centralized, validated environment configuration.
- `../samples/judge_negotiation_input.json` — the reproducible sample negotiation payload.
