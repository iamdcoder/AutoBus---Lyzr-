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
| **Code Architecture & Testing** | **20%** | Modular backend, deterministic governance, 46 passing tests across 15 files covering negotiation, deadlock, guardrails, legal validation, audit integrity, contract integrity and Lyzr integration |
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
```

These expose architecture/runtime evidence without exposing secrets.

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
├── tests/                15 test files, 46 tests
└── main.py               API entrypoint

Dockerfile                container build
.env.example              environment template (no secrets)
README.md                 this file
```

---

# Testing

```bash
cd backend
pytest -q
```

46 tests across 15 files, all passing at time of writing: `test_negotiation`, `test_deadlock`, `test_guardrails`, `test_policy`, `test_legal_validator`, `test_governance`, `test_audit`, `test_contract`, `test_contract_integrity`, `test_lyzr_client`, `test_lyzr_integration`, `test_lyzr_surfaces`, `test_api_demo`, `test_integration`, `test_winning_features`.

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
