# AutoBus — Lyzr Evidence

This file is intentionally precise about what is connected to Lyzr, what is implemented as application-side governance, and what depends on additional platform access.

## Lyzr capabilities used by the build

### Lyzr Agent API

The live path identifies a Lyzr agent with `agent_id` and maintains its conversation with a per-party `session_id`. AutoBus uses separate Buyer and Supplier sessions so their private negotiation contexts do not collapse into one shared conversation.

Official reference: https://docs.lyzr.ai/agent-api/inferences/chat

### Lyzr SDK / ADK

The runtime includes the Lyzr SDK/ADK transport and retains the Agent API HTTP client as an additional transport path. This keeps the platform boundary explicit while allowing the application to remain operational if one transport path is unavailable.

### Lyzr Agent Studio

The Buyer and Supplier agent configurations are intended to live in Lyzr Studio. The repository documents their Environment → Agent → Inference relationship and includes bootstrap/setup material for the two named AutoBus agents.

### Environment separation

The application maintains distinct Buyer and Supplier environment/policy objects. Their private policy values are not copied into the counterparty's prompt.

## Responsible AI boundary

Lyzr Responsible AI supports configurable safety/compliance policies and custom guardrails. The current Lyzr documentation describes Responsible AI policies and custom HTTP guardrails that can allow/deny interactions.

Official reference: https://docs.lyzr.ai/enterprise/agent-studio/responsible-safe-ai/Responsible

**Subscription note:** Native Lyzr Responsible AI features required for this workflow were not exposed on the quest submission account. AutoBus therefore does not claim native RAI activation in the shipped demo.

The repository does, however, contain an adapter for an authorized Lyzr custom guardrail endpoint and also enforces deterministic application-side checks before negotiation state can change.

## AIMS boundary

AutoBus emits normalized audit records in the `autobus.aims-event.v1` shape and supports an optional external sink through environment configuration.

**Subscription note:** Native Lyzr AIMS console/API access was not exposed on the quest submission account. The local JSONL outbox and hash chain are therefore explicitly **not** called AIMS.

The distinction is:

```text
Native Lyzr AIMS
    = platform capability, subscription/access dependent

AutoBus local audit
    = application-controlled, tamper-evident fallback/export

AIMS-compatible sink
    = optional integration when an authorized endpoint is available
```

## Why this still satisfies the governance intent

The application does not rely on an LLM to enforce its hard procurement rules. Policy, legal, numeric, and agreement checks remain deterministic and outside model authority.

The live Lyzr agents therefore operate inside a bounded workflow:

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

- `/api/architecture` — Environment → Agent → Inference separation.
- `/api/lyzr/evidence` — platform/integration readiness without exposing secrets.
- `/api/lyzr/status` — deployment and agent-configuration status.

## Judge wording

Use this wording rather than over-claiming:

> “The Lyzr agent integration is real and the Buyer/Supplier sessions are isolated. Native Responsible AI and AIMS are subscription-gated capabilities that were not exposed on this quest account, so we did not fabricate those integrations. Instead, the application has deterministic enforcement and a tamper-evident audit fallback, with optional adapters for an authorized deployment.”
