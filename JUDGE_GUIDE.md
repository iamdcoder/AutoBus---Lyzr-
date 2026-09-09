# AutoBus — Judge Guide

## The 20-second explanation

> **AutoBus is a governed two-agent procurement negotiation. Lyzr agents propose deals, but private policy boundaries and deterministic governance decide what can actually change the negotiation or become a contract.**

## What to evaluate

The project is designed around the four quest pillars:

| Rubric pillar | What AutoBus demonstrates | Where to inspect |
|---|---|---|
| **Lyzr Multi-Agent Depth — 30%** | Two Lyzr agents, private per-party sessions, Studio configuration, SDK/API transport, Environment → Agent → Inference separation | `agents/`, `backend/governance/`, `agents/lyzr/environment_manifest.json`, `/api/architecture` |
| **Negotiation Logic & Guardrails — 30%** | Multi-round bargaining, concessions, convergence/deadlock, utility/risk/Pareto analysis, policy/legal firewall, final agreement firewall | `backend/negotiation/`, `backend/guardrails/`, `backend/governance/` |
| **Code Architecture & Testing — 20%** | Modular backend plus focused tests for deadlock, governance, guardrails, legal validation, audit and Lyzr integration | `backend/tests/` |
| **Visual Dashboard & UX — 20%** | Live negotiation arena, concession analytics, security/red-team view, audit verification, Pareto/RFQ views, contract output | `frontend/index.html`, dashboard panels |

## Architecture in one picture

```text
 Buyer private policy                 Supplier private policy
          │                                      │
          ▼                                      ▼
   Buyer Lyzr agent                         Supplier Lyzr agent
   + private session                        + private session
          │                                      │
          └──────────── approved proposals ─────┘
                            │
                            ▼
                 optional external guardrail
                            │
                            ▼
              deterministic policy firewall
                            │
                            ▼
                 deterministic legal checks
                            │
                            ▼
                     state mutation
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
             analytics            deadlock/convergence
                 └──────────┬──────────┘
                            ▼
                  agreement firewall
                            │
                            ▼
                  contract + SHA-256
                            │
                            ▼
               tamper-evident audit chain
                            │
                            └── optional AIMS-compatible sink
```

## Recommended 3-minute demo

### 0:00–0:30 — establish the problem

Open the dashboard and show the Buyer and Supplier guardrails. Say:

> “These agents can negotiate, but neither agent owns the authority to change the deal outside the policy envelope.”

### 0:30–1:20 — run the normal negotiation

Start the negotiation. Show:

- round number;
- price/delivery/payment/SLA proposals;
- concession movement;
- utility and risk;
- convergence.

Then point out that each proposal passes through the governance boundary before state changes.

### 1:20–1:55 — prove the guardrails

Run the red-team/security checks. Show blocked examples such as:

- out-of-policy price;
- invalid SLA/payment combination;
- private-policy leakage attempt;
- prompt-injection or malformed proposal.

The key explanation is:

> **“A persuasive model output is still only a proposal. It cannot directly commit an invalid deal.”**

### 1:55–2:25 — show decision quality

Open Analytics and show utility, risk, convergence, Pareto results, then the three-supplier RFQ ranking.

The useful distinction is:

> “Policy compliance is a hard boundary. Commercial preference is a separate optimization problem.”

### 2:25–2:50 — show audit and contract integrity

Open Audit, verify the hash chain, generate the contract, and show the contract hash/version metadata.

### 2:50–3:00 — Lyzr transparency close

Show the Lyzr agent configuration and the Environment → Agent → Inference proof.

If asked about Responsible AI or AIMS, say exactly:

> “Native Lyzr Responsible AI and AIMS are subscription-gated capabilities that were not exposed on the account used for this quest. We did not fake those integrations. The Lyzr agent integration is real, while the application supplies deterministic governance and a tamper-evident audit fallback, with optional adapters for an authorized deployment.”

## What is deliberately bounded

- Buyer and Supplier do not receive each other's reservation price or BATNA.
- The LLM cannot directly mutate authoritative negotiation state.
- Final agreement is independently revalidated before contract generation.
- Hard numeric and legal constraints are enforced deterministically.
- The local audit chain is never presented as native Lyzr AIMS.
- Missing subscription-level Lyzr RAI/AIMS access is disclosed rather than fabricated.

## Agent IDs: what the judge needs to know

The deployed live mode uses:

```text
BUYER_AGENT_ID
SUPPLIER_AGENT_ID
```

These are identifiers for the two Lyzr Studio agents. They are required to address the live agents but are not equivalent to the API key and should not be hard-coded into the repository.

The dashboard may display the configured IDs as deployment diagnostics. Never display the Lyzr API key.

See `AGENT_CONFIGURATION.md` for the full explanation.

## Verification endpoints

- `/health` — deployment health.
- `/docs` — FastAPI/Swagger documentation.
- `/api/architecture` — Environment → Agent → Inference proof.
- `/api/lyzr/evidence` — Lyzr integration/readiness evidence without secrets.
- `/api/lyzr/status` — runtime agent/configuration status.

## Repository checklist

Before submission, verify that:

- no real `.env` file is committed;
- no API key appears in source control;
- the two Agent IDs are provided through deployment environment variables;
- the README, judge guide, architecture notes, and Lyzr evidence use the same subscription limitation wording;
- the local audit chain is not described as native AIMS.
