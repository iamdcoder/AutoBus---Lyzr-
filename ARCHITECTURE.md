# AutoBus Architecture

## 1. Design goal

AutoBus separates **model capability** from **business authority**. Lyzr agents can propose negotiation moves, but the application—not the LLM—owns the authoritative negotiation state and contract decision.

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
├── deterministic policy validation
├── deterministic legal validation
└── negotiation state mutation only after approval
          │
          ├───────────────┐
          ▼               ▼
       Analytics       Deadlock / convergence
          │               │
          └───────┬───────┘
                  ▼
           Agreement firewall
                  │
                  ▼
           Contract compiler
            ├── JSON
            └── PDF + SHA-256 hash
                  │
                  ▼
          Tamper-evident audit chain
                  │
                  └── optional authorized AIMS-compatible sink
```

## 3. Agent and policy isolation

Buyer and Supplier have distinct Lyzr agent identities and distinct conversation sessions. Private policy values such as reservation prices and BATNA are kept in party-specific application state and are not inserted into the counterparty's context.

The shared negotiation channel contains only information that is safe to expose as part of the bargaining process.

## 4. Governance order

The authoritative path is:

```text
agent proposal
    ↓
optional external Lyzr/custom guardrail
    ↓
PolicyValidator
    ↓
LegalValidator
    ↓
state mutation
```

The key invariant is:

> **An LLM response cannot directly mutate the authoritative negotiation state.**

If the external guardrail is configured, the application treats its denial/unavailability according to the configured fail-closed behavior. The local deterministic validators remain the business-rule firewall.

## 5. Agreement firewall

An `accept` action is not trusted merely because an agent proposed it. The complete candidate agreement is revalidated against both parties' policies and the legal validator before `agreement_reached` and contract generation occur.

## 6. Negotiation intelligence

The negotiation layer tracks:

- concession movement across rounds;
- convergence signals;
- repeated offers;
- deadlock conditions;
- party utility;
- commercial risk;
- Pareto efficiency; and
- multi-supplier RFQ ranking.

This allows the system to distinguish a policy violation from a commercially weak but still valid deal.

## 7. Audit and AIMS boundary

Every meaningful state transition is appended to a tamper-evident local hash chain. Normalized `autobus.aims-event.v1` records can also be sent to an authorized external sink.

**Native Lyzr AIMS is not claimed when the required subscription/platform access is unavailable.** The local audit chain is an application-level integrity mechanism and export/fallback, not a replacement claim for native AIMS.

## 8. Contract integrity

The contract compiler creates structured JSON/PDF output and includes deterministic SHA-256 integrity metadata plus version information. This lets a downstream consumer verify that the artifact corresponds to the canonical contract payload.

## 9. Reference files

- `agents/lyzr/environment_manifest.json` — Environment → Agent → Inference mapping.
- `LYZR_EVIDENCE.md` — Lyzr capability evidence and subscription boundaries.
- `AGENT_CONFIGURATION.md` — Agent IDs, session separation, and secret handling.
- `JUDGE_GUIDE.md` — rubric mapping and demo proof.
