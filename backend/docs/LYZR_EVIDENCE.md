# AutoBus — Lyzr Evidence & Agent Configuration

This file is intentionally precise about what is connected to Lyzr, what is implemented as application-side governance, what depends on additional platform access, and how the two Studio agents are configured. For the judge-facing summary, see the root [`README.md`](../../README.md).

## Lyzr capabilities used by the build

### Lyzr Agent API

The live path identifies a Lyzr agent with `agent_id` and maintains its conversation with a per-party `session_id`. AutoBus uses separate Buyer and Supplier sessions (`{negotiation_id}-buyer` / `{negotiation_id}-supplier`, set in `main.py`) so their private negotiation contexts do not collapse into one shared conversation.

Official reference: https://docs.lyzr.ai/agent-api/inferences/chat

### Lyzr SDK / ADK

The runtime includes the Lyzr SDK/ADK transport (`agents/lyzr_sdk.py`) and retains the Agent API HTTP client (`agents/lyzr_client.py`) as an additional transport path. This keeps the platform boundary explicit while allowing the application to remain operational if one transport path is unavailable.

### Lyzr Agent Studio

The Buyer and Supplier agent configurations are intended to live in Lyzr Studio. `agents/lyzr/environment_manifest.json` documents their Environment → Agent → Inference relationship, and `agents/lyzr_bootstrap.py` contains bootstrap/setup material for the two named AutoBus agents.

### Environment separation

The application maintains distinct Buyer and Supplier environment/policy objects. Their private policy values are not copied into the counterparty's prompt.

---

## Agent Configuration

### Why Agent IDs exist

AutoBus uses two Lyzr Studio agents in live mode — a **Buyer Agent** (procurement-side negotiator) and a **Supplier Agent** (vendor-side negotiator). Each has a unique Lyzr `agent_id`; the application needs those identifiers to know which Studio agent to invoke.

```text
BUYER_AGENT_ID=...
SUPPLIER_AGENT_ID=...
```

These are **required for the live Lyzr path only** — not required for deterministic simulation mode.

An Agent ID is an identifier, not an API credential. The sensitive value in this configuration is the **Lyzr API key**:

```text
LYZR_API_KEY=...
```

Never commit the real API key. Publishing the opaque Agent IDs themselves is not equivalent to publishing an API key, but there is normally no reason to hard-code them into the source repository — environment configuration keeps deployments portable.

### How the IDs relate to isolation

The two IDs identify different Lyzr agent configurations, while the application also creates independent sessions for Buyer and Supplier (see "Lyzr Agent API" above). The private policy envelopes remain application-side state and are not copied into the counterparty's shared context:

```text
Buyer policy → Buyer agent → Buyer session
Supplier policy → Supplier agent → Supplier session
```

Only the approved negotiation information crosses between the two sides.

### How the repository obtains the IDs

The included setup scripts (`backend/scripts/setup_lyzr*.{bat,ps1,py}`, `agents/lyzr_bootstrap.py`) can discover existing Studio agents named `AutoBus Buyer Agent` and `AutoBus Supplier Agent`, and write only their IDs into the local environment. If the agents don't exist, the bootstrap material creates/configures them.

### What should not be published

Do not publish `LYZR_API_KEY` values, access tokens, or `.env` files containing secrets.

---

## Responsible AI boundary

Lyzr Responsible AI supports configurable safety/compliance policies and custom guardrails (`docs.lyzr.ai/enterprise/agent-studio/responsible-safe-ai/Responsible`).

**Subscription note:** native Lyzr Responsible AI features required for this workflow were not exposed on the quest submission account. AutoBus therefore does not claim native RAI activation in the shipped demo.

The repository does, however, contain an adapter for an authorized Lyzr custom guardrail endpoint (`POST /api/governance/lyzr-custom-guardrail`) and enforces deterministic application-side checks (`PolicyValidator`, `LegalValidator`) before negotiation state can change.

## AIMS boundary

AutoBus emits normalized audit records in the `autobus.aims-event.v1` shape (`backend/governance/lyzr_governance.py`) and supports an optional external sink via `LYZR_AIMS_WEBHOOK_URL` / `LYZR_AIMS_TOKEN`.

**Subscription note:** native Lyzr AIMS console/API access was not exposed on the quest submission account. The local JSONL outbox and hash chain are therefore explicitly **not** called AIMS.

```text
Native Lyzr AIMS
    = platform capability, subscription/access dependent

AutoBus local audit
    = application-controlled, tamper-evident fallback/export

AIMS-compatible sink
    = optional integration when an authorized endpoint is available
```

## Why this still satisfies the governance intent

The application does not rely on an LLM to enforce its hard procurement rules. Policy, legal, numeric, and agreement checks remain deterministic and outside model authority:

```text
Lyzr agent proposes
        ↓
optional platform/custom guardrail
        ↓
application policy + legal firewall
        ↓
negotiation state
        ↓
contract + audit
```

## Runtime proof endpoints

- `GET /api/architecture` — Environment → Agent → Inference separation.
- `GET /api/lyzr/evidence` — platform/integration readiness without exposing secrets.
- `GET /api/lyzr/status` — deployment and agent-configuration status.

## Judge wording

Use this wording rather than over-claiming:

> "The Lyzr agent integration is real and the Buyer/Supplier sessions are isolated. Native Responsible AI and AIMS are subscription-gated capabilities that were not exposed on this quest account, so we did not fabricate those integrations. Instead, the application has deterministic enforcement and a tamper-evident audit fallback, with optional adapters for an authorized deployment."

Do not call the local JSONL audit chain "AIMS."
