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
| **Code Architecture & Testing** | **20%** | Modular backend, deterministic governance, focused tests for negotiation, deadlock, guardrails, legal validation, audit integrity, contract integrity and Lyzr integration |
| **Visual Dashboard & UX** | **20%** | Live negotiation arena, concession analytics, security/red-team views, audit verification, RFQ/Pareto views and contract output |

---

# Judge First: Live Demo

**Live application:** https://autobus-lyzr.onrender.com/

**Dashboard:** https://autobus-lyzr.onrender.com/ui

**Health:** https://autobus-lyzr.onrender.com/health

**Swagger / API docs:** https://autobus-lyzr.onrender.com/docs

No API key is required from the judge for the public deployment.

### Fastest judging path

**Live Dashboard → Run Negotiation → Inspect governance → Open Contract JSON → Open PDF → Verify Audit → Run Stress Test → Inspect Architecture**

If the dashboard feels too technical, use the exact reproducible execution path in the next section.

---

# Judge Execution — Reproducible Path

## 1. Open the live dashboard

Open:

https://autobus-lyzr.onrender.com/ui

The dashboard is the governed negotiation arena. It exposes the business outcome first while the deeper Lyzr architecture is available through the API and repository.

## 2. Run a normal negotiation

Use the default/demo configuration and start the negotiation.
  For steps, refer to **line 180 - Swagger / JSON Execution**

The Buyer and Supplier are bounded participants:

- **Buyer:** private procurement policy.
- **Supplier:** private commercial policy.

Look for:

- multiple negotiation rounds;
- price, delivery, payment and SLA proposals;
- concessions and counter-proposals;
- utility and risk;
- convergence or deadlock status;
- policy/guardrail decisions.

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

**Please wait for some time for the execution to complete.**

When the negotiation reaches `agreed`, note the returned `negotiation_id`.

The result can contain:

- final proposal;
- contract data;
- negotiation rounds;
- convergence/analytics;
- risk;
- Pareto information;
- policy-integrity state;
- audit-integrity state;
- runtime governance mode.

## 4. Retrieve the contract JSON

Use:

```text
GET /api/negotiations/{negotiation_id}/contract
```

For example:

```text
https://autobus-lyzr.onrender.com/api/negotiations/<NEGOTIATION_ID>/contract
```

## 5. Retrieve the PDF contract

Use:

```text
GET /api/negotiations/{negotiation_id}/pdf
```

For example:

```text
https://autobus-lyzr.onrender.com/api/negotiations/<NEGOTIATION_ID>/pdf
```

The generated contract contains integrity metadata including a deterministic SHA-256 hash and version information.

## 6. Verify the audit chain

Use:

```text
GET /api/negotiations/{negotiation_id}/audit/verify
```

A successful verification demonstrates that the recorded local audit events form a valid tamper-evident hash chain.

## 7. Run the guardrail stress test

Use:

```text
POST /api/stress-test
```

The test intentionally exercises invalid cases such as:

- Buyer over budget;
- Supplier below price floor;
- delivery-window violation;
- payment-term violation;
- SLA penalty violation;
- uptime violation.

The expected behavior is that invalid proposals are **blocked rather than committed** to authoritative negotiation state.

This demonstrates the central boundary:

> **The model may propose; the governance layer decides whether the proposal is admissible.**

## 8. Inspect the Lyzr architecture

Useful live inspection endpoints:

```text
GET /api/architecture
GET /api/lyzr/evidence
GET /api/lyzr/status
GET /api/system/governance
```

These expose architecture/runtime evidence without exposing secrets.

---

# Swagger / JSON Execution

A technically oriented judge can reproduce the negotiation without relying on the dashboard.

Open:

https://autobus-lyzr.onrender.com/docs

Find:

```text
POST /api/negotiations
```

Click **Try it out** and paste the ready-made payload from:

Sample JSON for negotiation:
{
  "buyer": {
    "price": {
      "target": 110000,
      "minimum": 95000,
      "maximum": 120000
    },
    "delivery": {
      "target_days": 30,
      "maximum_days": 35
    },
    "payment": {
      "preferred_days": 60,
      "minimum_days": 30
    },
    "sla": {
      "minimum_uptime": 98,
      "minimum_penalty": 1,
      "maximum_penalty": 3
    },
    "batna": "Switch to alternate supplier at ₹125000 with 40-day delivery",
    "max_rounds": 10
  },
  "supplier": {
    "price": {
      "target": 115000,
      "minimum": 105000,
      "maximum": 130000
    },
    "delivery": {
      "target_days": 28,
      "maximum_days": 35
    },
    "payment": {
      "preferred_days": 45,
      "minimum_days": 30
    },
    "sla": {
      "minimum_uptime": 97,
      "minimum_penalty": 1,
      "maximum_penalty": 2
    },
    "batna": "Accept another buyer at ₹125000 with 35-day delivery",
    "max_rounds": 10
  },
  "buyer_name": "Acme Manufacturing",
  "supplier_name": "Industrial Components Ltd",
  "product_name": "Industrial Components",
  "quantity": 1000
}

```text
samples/judge_negotiation_input.json
```

A successful response returns a negotiation identifier similar to:

```json
{
  "negotiation_id": "NEG-XXXXXXXX",
  "status": "agreed"
}
```

Use that identifier with:

```text
GET /api/negotiations/{negotiation_id}/contract
GET /api/negotiations/{negotiation_id}/pdf
GET /api/negotiations/{negotiation_id}/audit/verify
GET /api/negotiations/{negotiation_id}/analytics
```

### Included sample scenario

The sample models a realistic B2B purchase with a feasible shared agreement around:

**₹110,000 · 31 days · Net 60 · 98% uptime · 2% SLA penalty**

The example policy envelope includes:

- Buyer target ₹100,000; maximum ₹110,000;
- Supplier target ₹120,000; minimum ₹110,000;
- delivery target 30 days; maximum 31 days;
- Net 60 payment preference;
- minimum SLA uptime 98%;
- bounded SLA penalty;
- BATNA information kept private to each side;
- multi-round negotiation limits.

The deterministic simulation path is the reproducible benchmark path. Live Lyzr inference can vary because model-generated proposals may differ.

---

# Architecture: Environment → Agent → Inference

AutoBus separates **model capability** from **business authority**. Lyzr agents can propose negotiation moves, but the application owns the authoritative negotiation state and contract decision.

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
└── state mutation only after approval
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
            └── PDF + SHA-256
                  │
                  ▼
          Tamper-evident audit chain
                  │
                  └── optional authorized AIMS-compatible sink
```

## Agent and policy isolation

Buyer and Supplier have distinct Lyzr agent identities and distinct conversation sessions.

Private values such as reservation prices and BATNA remain in party-specific application state and are not copied into the counterparty's context.

The shared negotiation channel contains only information that is safe to expose as part of bargaining.

The intended boundary is:

```text
Buyer policy → Buyer agent → Buyer session
Supplier policy → Supplier agent → Supplier session
```

Only approved negotiation information crosses between the two sides.

## Governance ordering

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

The invariant is:

> **An LLM response cannot directly mutate the authoritative negotiation state.**

If an external guardrail is configured, its result participates in the governance path according to the configured fail-closed behavior. Local deterministic validators remain the application-side business-rule firewall.

## Agreement firewall

An `accept` action is not trusted merely because an agent proposed it. The complete candidate agreement is independently revalidated against both parties' policy envelopes and the legal validator before `agreement_reached` and contract generation occur.

---

# Negotiation Intelligence

AutoBus tracks:

- concession movement across rounds;
- convergence signals;
- repeated offers;
- deadlock conditions;
- party utility;
- commercial risk;
- Pareto efficiency;
- three-supplier RFQ ranking.

This lets the system distinguish a hard policy violation from a commercially weak but still valid deal.

For multi-vendor decision quality, the system does not simply choose the cheapest supplier. It compares commercial trade-offs under the applicable constraints using utility, risk and Pareto signals.

---

# Guardrails and Security

The system treats LLM output as untrusted proposal data.

Application-side checks cover:

- prompt-injection indicators;
- private-policy leakage;
- malformed proposals;
- non-finite values;
- numeric bounds;
- procurement policy constraints;
- legal constraints;
- final-agreement validity.

A persuasive or malicious LLM output does not receive direct write access to the authoritative negotiation state.

The recommended security demo is:

1. Run a normal negotiation.
2. Run deliberately invalid/red-team cases.
3. Show that invalid proposals are rejected.
4. Explain that governance occurs before state mutation.

---

# Contract and Audit Integrity

A completed negotiation is independently validated before `agreement_reached` and contract generation.

The contract compiler creates structured JSON/PDF output with deterministic SHA-256 integrity metadata and version information.

Every meaningful state transition is appended to a tamper-evident local hash chain. This makes the negotiation history reconstructable and verifiable.

Normalized `autobus.aims-event.v1` event records can be forwarded to an authorized external sink when configured.

**The local audit chain is not represented as native Lyzr AIMS.**

---

# Lyzr Integration and Capability Boundaries

## Lyzr Agent API

The live path identifies a Lyzr agent with `agent_id` and maintains its conversation with a per-party `session_id`.

Official reference:

https://docs.lyzr.ai/agent-api/inferences/chat

## Lyzr SDK / ADK

The runtime includes the Lyzr SDK/ADK transport and retains the Agent API HTTP client as an additional transport path. This makes the platform boundary explicit while allowing an alternative transport path when needed.

## Lyzr Agent Studio

Buyer and Supplier configurations are intended to live in Lyzr Studio. The repository maps them to the Environment → Agent → Inference model and includes setup/bootstrap material for the two named AutoBus agents.

## Environment separation

Buyer and Supplier have distinct application-side environment/policy objects. Their private policy values are not copied into the counterparty's prompt.

---

# Agent IDs — are they necessary?

**Yes, for live Lyzr mode.**

`BUYER_AGENT_ID` and `SUPPLIER_AGENT_ID` tell AutoBus which two Lyzr Studio agents to invoke.

They are **identifiers, not API credentials**. The sensitive value is the Lyzr API key.

The live configuration is conceptually:

```text
LYZR_API_KEY=<private credential>
BUYER_AGENT_ID=<Buyer Studio agent id>
SUPPLIER_AGENT_ID=<Supplier Studio agent id>
LYZR_USER_ID=<deployment/user configuration>
```

Agent IDs are not required for deterministic simulation mode.

The two IDs identify different Studio agent configurations while independent `session_id` values keep the Buyer and Supplier conversations separate.

The included setup scripts can discover agents named:

```text
AutoBus Buyer Agent
AutoBus Supplier Agent
```

and write only their IDs into local environment configuration.

Never commit:

- a real `LYZR_API_KEY`;
- access tokens;
- a secret-bearing `.env` file.

A useful judge explanation is:

> “The Agent IDs select the two Lyzr Studio agents; the session IDs keep their conversations separate; the governance layer outside the model decides whether a proposal is allowed to change the deal.”

---

# AIMS and Responsible AI — Explicit Subscription Boundary

AutoBus deliberately distinguishes platform features that were available from application-side governance implemented in this submission.

### Native Lyzr Responsible AI

Native Lyzr Responsible/Safe AI platform features can provide configurable safety/compliance policies and custom guardrails.

The quest account used for this submission did **not** expose the additional native subscription-level Responsible AI access required to demonstrate those features end-to-end.

Therefore, AutoBus **does not claim native Lyzr Responsible AI activation** in the shipped demo.

The repository still contains:

- deterministic application-side policy/legal enforcement;
- local defense-in-depth against malformed, out-of-policy, prompt-injection and policy-leakage attempts;
- an adapter path for an authorized Lyzr custom guardrail endpoint.

### Lyzr AIMS

Native Lyzr AIMS console/API access was also **not exposed on the quest submission account**.

Therefore, AutoBus **does not claim the local audit implementation is native Lyzr AIMS**.

The distinction is:

```text
Native Lyzr AIMS
    = Lyzr platform capability, subscription/access dependent

AutoBus local audit
    = application-controlled tamper-evident audit chain

AIMS-compatible sink
    = optional integration when an authorized endpoint is available
```

When configured, normalized events can be forwarded using:

```text
LYZR_AIMS_WEBHOOK_URL
LYZR_AIMS_TOKEN
```

Without an authorized sink, AutoBus keeps the normalized events in its local outbox and maintains the local hash chain.

**We do not describe the local outbox/hash chain as AIMS.**

Recommended judge wording:

> “The Lyzr agent integration is real and the Buyer/Supplier sessions are isolated. Native Responsible AI and AIMS are subscription-gated capabilities that were not exposed on this quest account, so we did not fabricate those integrations. Instead, the application has deterministic enforcement and a tamper-evident audit fallback, with optional adapters for an authorized deployment.”

---

# Recommended 3-Minute Demo Script

## Opening — 20 seconds

Say:

> “This is not an LLM that negotiates without limits. It is a governed procurement negotiation where two Lyzr agents can bargain, but neither can break the policy envelope.”

## 1. Show guardrails

Set/show Buyer ceiling, Supplier floor, delivery window, payment terms and SLA bounds.

Say:

> “These values are private policy. They control what each side is willing to accept, but reservation values are never exposed to the other agent.”

## 2. Run normal negotiation

Point to:

- proposal history;
- round number;
- concessions;
- utility;
- risk;
- convergence.

Say:

> “The Lyzr agent generates a proposal. The proposal then crosses the governance boundary before it can mutate the authoritative negotiation state.”

## 3. Prove the attack surface is bounded

Run red-team/security examples.

Show a blocked out-of-policy value and, where available, a prompt-injection or policy-leakage attempt.

Say:

> “Even when the model produces an invalid or unsafe proposal, the model does not get write access to the deal state. The deterministic firewall blocks it.”

## 4. Show multi-vendor decision quality

Run the three-supplier RFQ and show utility, risk and Pareto efficiency.

Say:

> “The system does not simply choose the cheapest supplier. It compares the commercial trade-off under the policy constraints.”

## 5. Prove auditability

Open Audit and verify the hash chain.

Say:

> “Every meaningful state transition is recorded in a tamper-evident chain, so the negotiation can be reconstructed and verified.”

## 6. Prove contract integrity

Generate the JSON/PDF contract and show the SHA-256 hash/version metadata.

Close with:

> **“The output of the agent is not the contract. The output of the governed state machine is the contract.”**

### AIMS / Responsible AI question

Use the explicit wording from the subscription section above. Do not call the local JSONL audit chain “AIMS”.

---

# Local Execution

## No-credential simulation

Deterministic simulation mode is intended for reproducible local evaluation when live Lyzr credentials are unavailable.

### Windows

Run:

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

Then open:

```text
http://localhost:8000/ui
```

or:

```text
http://localhost:8000/docs
```

## Live Lyzr mode

Configure deployment environment variables:

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
backend/
├── agents/          Buyer/Supplier agent integration
├── audit/           tamper-evident audit chain
├── contract/        contract compilation / integrity
├── governance/      policy/legal governance boundary
├── guardrails/      deterministic and external guardrail integration
├── models/          structured domain models
├── negotiation/     rounds, concessions, convergence, deadlock, utility
├── tests/            unit/integration coverage
└── main.py          API entrypoint

frontend/             zero-build dashboard / negotiation arena
data/                 project data/configuration
scripts/              setup/bootstrap helpers
agents/lyzr/
└── environment_manifest.json   Environment → Agent → Inference mapping

samples/
└── judge_negotiation_input.json   ready-made judge payload
```

---

# Testing

Run:

```bash
cd backend
pytest -q
```

The test suite covers negotiation behavior, guardrails, governance ordering, deadlock, legal validation, contract integrity, audit integrity, Lyzr integration, and API/demo behavior.

The judge-ready build has been validated with the project's automated test suite.

---

# What each documentation file contains

Everything needed for judging is summarized here, so judges **do not need to read the whole repository**.

### `JUDGE_EXECUTION.md`
Exact reproducible judge workflow:

- live deployment links;
- dashboard flow;
- Swagger execution;
- sample JSON input;
- contract JSON retrieval;
- PDF retrieval;
- audit verification;
- guardrail stress test;
- Lyzr evidence endpoints;
- local simulation/live-mode distinction.

### `JUDGE_GUIDE.md`
Rubric-oriented judging guide with:

- 20-second project explanation;
- 30/30/20/20 rubric mapping;
- what to inspect for every pillar;
- recommended three-minute demo;
- deliberate governance boundaries;
- Agent ID explanation;
- verification endpoints;
- submission checklist.

### `LIVE_DEMO.md`
Live deployment walkthrough with:

- public URL;
- dashboard instructions;
- what to watch during negotiation;
- governance panels;
- contract/audit inspection;
- rubric interpretation;
- subscription disclosure;
- recommended judging order.

### `DEMO_SCRIPT.md`
The concise presenter script with exact judge-facing language for:

- guardrails;
- normal negotiation;
- red-team/security proof;
- three-supplier RFQ;
- auditability;
- contract integrity;
- AIMS/Responsible AI questions.

### `ARCHITECTURE.md`
The formal technical architecture:

- Environment → Agent → Inference;
- policy/session isolation;
- governance ordering;
- agreement firewall;
- negotiation intelligence;
- audit/AIMS boundary;
- contract integrity.

### `LYZR_EVIDENCE.md`
The precise capability boundary for:

- Lyzr Agent API;
- Lyzr SDK/ADK;
- Lyzr Agent Studio;
- environment separation;
- Responsible AI subscription boundary;
- AIMS subscription boundary;
- runtime evidence endpoints;
- non-overclaiming judge language.

### `AGENT_CONFIGURATION.md`
Explains:

- why Buyer/Supplier Agent IDs exist;
- why they are needed in live mode;
- why they are not secrets;
- how they relate to separate sessions;
- how setup scripts discover them;
- what must never be published.

### `backend/docs/*.md`
These are intentionally short pointers to the root documents so documentation cannot drift into conflicting duplicate versions.

---

# What makes AutoBus different

The core architectural choice is deliberately enterprise-oriented:

```text
LLM proposal
    ≠
authorized business decision
```

Instead:

```text
Lyzr agent proposes
        ↓
Governance validates
        ↓
Legal validates
        ↓
State may change
        ↓
Agreement is revalidated
        ↓
Contract is compiled
        ↓
Audit is recorded
```

This makes the LLM useful for negotiation strategy while preventing it from becoming the final authority over procurement commitments.

---

# Final submission checklist

Before publishing/submitting:

- confirm the live URL works;
- keep `LYZR_API_KEY` only in deployment secrets;
- provide Buyer/Supplier Agent IDs through environment configuration;
- verify no real `.env` or secret-bearing credential file is committed;
- keep the deterministic simulation path available for reproducibility;
- verify `JUDGE_EXECUTION.md` and `samples/judge_negotiation_input.json` are present;
- verify the README remains the primary judge entry point;
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
For output testing, please go to the link pointed by the heading **Swagger**.
---

## One sentence for the judge

> **AutoBus uses two Lyzr agents to negotiate, but keeps policy, legal validation, state mutation, contract creation, and audit integrity outside the LLM's authority.**
