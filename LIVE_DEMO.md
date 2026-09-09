# AutoBus Live Judge Guide

## Live deployment

**Open:** https://autobus-lyzr.onrender.com/

The deployed application is the fastest way to evaluate AutoBus. No repository setup or local credentials are required for the public demo.

## What to do

### 1. Open the live app

Open the URL above and wait for the dashboard to finish loading.

The main screen is the **governed negotiation arena**. It is designed to show the business workflow first, while the underlying Lyzr Environment → Agent → Inference architecture remains documented separately in `ARCHITECTURE.md`.

### 2. Start a negotiation

Use the primary negotiation action on the dashboard.

Choose the default/demo configuration unless you want to test a different scenario. The demo is designed to show two bounded participants:

- **Buyer** — operates under a private procurement policy.
- **Supplier** — operates under a private commercial policy.

Private reservation prices and internal policy values are not exposed to the opposing agent.

### 3. Watch the rounds

Follow the negotiation as proposals and counter-proposals are exchanged.

The important sequence to look for is:

`Agent proposal → Guardrail validation → State update → Next round`

The LLM does not directly write the final contract. A proposal must pass the application's deterministic policy/legal validation before it can affect negotiation state.

### 4. Look at the governance panels

During or after negotiation, inspect the dashboard sections for:

- policy/guardrail status
- negotiation rounds and concessions
- convergence/deadlock information
- risk and utility information
- audit events
- final agreement validation

These panels correspond to the project's core design: agents are allowed to negotiate, but they are not allowed to bypass hard business constraints.

### 5. Verify the final agreement

When the negotiation reaches agreement, inspect the final terms and validation status.

The resulting agreement should contain the negotiated commercial terms while remaining inside both parties' policy envelopes.

### 6. Inspect the contract and audit trail

Use the contract/audit actions to inspect the structured agreement and the recorded negotiation history.

The application also computes integrity metadata for the generated contract/audit artifacts. See `LYZR_EVIDENCE.md` for the precise distinction between the local audit implementation and native Lyzr AIMS.

## What this demo is proving

A judge can evaluate the core quest pillars from the live deployment:

| Quest pillar | What to inspect in the live demo |
|---|---|
| **Lyzr Multi-Agent Depth — 30 pts** | Buyer/Supplier agent flow, isolated policies/sessions, Lyzr-backed inference configuration |
| **Negotiation Logic & Guardrails — 30 pts** | Multi-round bargaining, concessions, policy enforcement, legal validation, deadlock/convergence |
| **Code Architecture & Testing — 20 pts** | Repository architecture, unit/integration tests, governance modules, validators |
| **Visual Dashboard & UX — 20 pts** | Live negotiation arena, round history, concessions, guardrail and audit visibility |

## Lyzr subscription note

AutoBus documents the Lyzr platform boundary accurately.

**Lyzr AIMS and Lyzr Responsible/Safe AI platform capabilities may require additional subscription/access.** They are therefore not represented as active native services in this public demo unless the relevant Lyzr account entitlement is enabled.

AutoBus still provides application-side deterministic guardrails, legal validation, agreement validation, and a tamper-evident local audit chain so the governance behavior can be demonstrated without misrepresenting subscription-only platform features.

See `LYZR_EVIDENCE.md` for the detailed evidence and capability boundary.

## Live Lyzr agents

The live deployment uses configured Lyzr agent identifiers for Buyer and Supplier inference. Agent IDs identify the configured agents; they are not API secrets.

The Lyzr API key is kept as a deployment secret and is **not** exposed through this guide or the repository.

## Optional repository verification

For a deeper technical evaluation, start with:

1. `README.md` — project overview and setup
2. `ARCHITECTURE.md` — Environment / Agent / Inference architecture
3. `JUDGE_GUIDE.md` — rubric-oriented evaluation path
4. `LYZR_EVIDENCE.md` — Lyzr integration and subscription boundary
5. `AGENT_CONFIGURATION.md` — agent ID and environment configuration

The repository also contains a deterministic simulation mode for local evaluation when live Lyzr credentials are unavailable.

## Recommended judging order

**Live demo first → governance/guardrails → final contract → repository architecture → tests → Lyzr evidence.**

That order shows the product outcome first, then the engineering and governance mechanisms that make the outcome trustworthy.
