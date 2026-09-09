# Judge Execution Guide — AutoBus

This is the fastest reproducible path for evaluating AutoBus.

The project can be judged in two ways:

1. **Live demo:** open the deployed dashboard and run a negotiation.
2. **API execution:** use the included sample JSON and Swagger/OpenAPI to reproduce the same workflow without relying on the visual dashboard.

## 1. Start with the live application

**Live application**

https://autobus-lyzr.onrender.com/

Useful endpoints:

| Purpose | URL |
|---|---|
| Application | https://autobus-lyzr.onrender.com/ |
| Dashboard | https://autobus-lyzr.onrender.com/ui |
| Health | https://autobus-lyzr.onrender.com/health |
| Swagger / API docs | https://autobus-lyzr.onrender.com/docs |

No API key is required from the judge for the public deployment.

> The deployed service chooses live Lyzr mode when the server has its Lyzr credentials and Agent IDs configured. Otherwise, the application supports deterministic simulation mode for reproducible evaluation.

## 2. Recommended 3-minute judge path

### Step 1 — Open the dashboard

Open:

https://autobus-lyzr.onrender.com/ui

The dashboard presents the Buyer and Supplier sides, their guardrails, the negotiation arena, analytics, governance checks, audit information, and contract output.

### Step 2 — Run a normal negotiation

Use the default/example policies already available in the UI.

Click the action that starts the negotiation.

Watch for:

- multiple negotiation rounds;
- price, delivery, payment, and SLA terms;
- concessions between Buyer and Supplier;
- convergence/deadlock information;
- policy/governance status.

The important architecture point is:

> **A Lyzr agent generates a proposal; the proposal is validated before it can change authoritative negotiation state.**

Sample initiation JSON:
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

### Step 3 — Inspect the final agreement

When the negotiation reaches `agreed`, note the returned `negotiation_id`.

The result contains:

- final proposal;
- contract data;
- negotiation rounds;
- convergence/analytics;
- risk;
- Pareto information;
- policy-integrity status;
- audit-integrity status;
- runtime governance mode.

### Step 4 — Get the contract JSON

Open:

```text
https://autobus-lyzr.onrender.com/api/negotiations/<NEGOTIATION_ID>/contract
```

Replace `<NEGOTIATION_ID>` with the ID returned by the negotiation.

This returns the structured contract representation.

### Step 5 — Get the contract PDF

Open:

```text
https://autobus-lyzr.onrender.com/api/negotiations/<NEGOTIATION_ID>/pdf
```

The endpoint returns the generated PDF contract.

### Step 6 — Verify the audit chain

Open:

```text
https://autobus-lyzr.onrender.com/api/negotiations/<NEGOTIATION_ID>/audit/verify
```

A successful verification demonstrates that the recorded audit events form a valid tamper-evident chain.

## 3. Reproduce the workflow through Swagger

Open:

https://autobus-lyzr.onrender.com/docs

Find:

```text
POST /api/negotiations
```

Click **Try it out**.

Use the sample payload from:

```text
samples/judge_negotiation_input.json
```

Paste the JSON into the request body and execute it.

A successful response contains a field similar to:

```json
{
  "negotiation_id": "NEG-XXXXXXXX",
  "status": "agreed"
}
```

Copy that `negotiation_id`.

Then use it with:

```text
GET /api/negotiations/{negotiation_id}/contract
GET /api/negotiations/{negotiation_id}/pdf
GET /api/negotiations/{negotiation_id}/audit/verify
GET /api/negotiations/{negotiation_id}/analytics
```

Swagger is the recommended route for a technically oriented judge because it exposes the complete API contract without requiring any local setup.

## 4. Sample negotiation scenario

The included example models a realistic B2B purchase:

- Buyer target: ₹100,000
- Buyer maximum: ₹110,000
- Supplier target: ₹120,000
- Supplier minimum: ₹110,000
- Delivery target: 30 days
- Maximum delivery: 31 days
- Net payment target: 60 days
- Minimum SLA uptime: 98%
- SLA penalty bounded by each party's policy

The intended simulation outcome converges to the shared feasible boundary around:

**₹110,000 · 31 days · Net 60 · 98% uptime · 2% SLA penalty**

Exact output can vary in live Lyzr mode because model-generated proposals can differ; the deterministic simulation path is the reproducible benchmark path.

## 5. Proving the guardrails

For the rubric's governance/guardrail proof, use:

```text
POST /api/stress-test
```

The same negotiation payload can be supplied.

The endpoint generates deliberately invalid cases such as:

- buyer over budget;
- supplier below price floor;
- delivery violation;
- payment violation;
- SLA penalty violation;
- uptime violation.

The expected behavior is that invalid proposals are **blocked**, not committed to negotiation state.

This provides a compact way to demonstrate the hard-boundary principle:

> **The model may propose; the governance layer decides whether the proposal is admissible.**

## 6. Proving the Lyzr architecture

Useful inspection endpoints:

```text
GET /api/architecture
GET /api/lyzr/evidence
GET /api/lyzr/status
GET /api/system/governance
```

These expose the architecture and runtime configuration without exposing secrets.

For repository-level inspection, see:

- `ARCHITECTURE.md`
- `LYZR_EVIDENCE.md`
- `AGENT_CONFIGURATION.md`
- `JUDGE_GUIDE.md`

## 7. AIMS and Responsible AI disclosure

AutoBus does **not** claim that native Lyzr AIMS or Lyzr Responsible AI was activated when the required subscription/platform access was unavailable on the quest account.

The repository instead contains:

- deterministic application-side policy and legal validation;
- a tamper-evident local audit chain;
- optional AIMS-compatible export/sink support;
- optional external/custom guardrail integration.

The local audit chain is **not** represented as native Lyzr AIMS.

## 8. Local execution by a technical judge

Clone the repository and install the backend dependencies according to the project setup instructions.

For a no-credential demonstration, use the deterministic simulation path. It does not require a Lyzr API key or Agent IDs.

For live Lyzr inference, configure:

```text
LYZR_API_KEY=<private credential>
BUYER_AGENT_ID=<Buyer Studio agent id>
SUPPLIER_AGENT_ID=<Supplier Studio agent id>
```

Never commit the API key.

## 9. What to evaluate

For the quest rubric, the most useful evidence is:

| Rubric pillar | Judge evidence |
|---|---|
| Lyzr Multi-Agent Depth | Two agents, isolated sessions, Environment → Agent → Inference mapping, Lyzr API/SDK integration |
| Negotiation Logic & Guardrails | Multi-round bargaining, concessions, policy/legal firewall, stress-test blocking |
| Code Architecture & Testing | Modular backend, deterministic governance, focused unit/integration tests |
| Visual Dashboard & UX | Live negotiation arena, analytics, governance/security views, audit and contract output |

## 10. Fastest possible evaluation

If time is extremely limited:

1. Open the live dashboard.
2. Run one negotiation.
3. Open the returned contract.
4. Open the PDF endpoint.
5. Run the stress test.
6. Verify the audit chain.
7. Open `/api/architecture`.

That path demonstrates the core product and the core judging evidence without requiring repository setup.
