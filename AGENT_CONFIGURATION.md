# Agent Configuration — AutoBus

## Why Agent IDs exist

AutoBus uses two Lyzr Studio agents in live mode:

- **Buyer Agent** — the procurement-side negotiator.
- **Supplier Agent** — the vendor-side negotiator.

Each agent has a unique Lyzr `agent_id`. The application needs those identifiers so it knows which Studio agent to invoke.

For the current Lyzr Agent API, a chat request identifies the target agent with `agent_id` and keeps conversation state with a `session_id`. See the official Lyzr Agent API documentation: https://docs.lyzr.ai/agent-api/inferences/chat

## Required only for live Lyzr inference

```text
BUYER_AGENT_ID=...
SUPPLIER_AGENT_ID=...
```

These values are **required for the live Lyzr path**. They are not required for deterministic simulation mode.

An Agent ID is an identifier, not an API credential. It is still best practice to keep deployment-specific IDs in environment configuration so the same repository can be used with different Studio agents.

The sensitive value in this configuration is the **Lyzr API key**, not the Agent ID:

```text
LYZR_API_KEY=...
```

Never commit the real API key.

## How the IDs relate to isolation

The two IDs identify different Lyzr agent configurations, while the application also creates independent sessions for Buyer and Supplier. The private policy envelopes remain application-side state and are not copied into the counterparty's shared context.

The important boundary is:

```text
Buyer policy → Buyer agent → Buyer session
Supplier policy → Supplier agent → Supplier session
```

Only the approved negotiation information crosses between the two sides.

## How the repository obtains the IDs

The included setup scripts can discover existing Studio agents named:

- `AutoBus Buyer Agent`
- `AutoBus Supplier Agent`

and write only their IDs into the local environment.

If the agents do not exist, the repository includes the bootstrap material needed to create/configure them in Lyzr Studio.

## What should not be published

Do not publish:

- `LYZR_API_KEY` values;
- access tokens;
- `.env` files containing secrets.

Publishing the opaque Agent IDs themselves is not equivalent to publishing an API key, but there is normally no reason to hard-code them into the source repository. Environment configuration keeps deployments portable and avoids coupling the repository to one Studio workspace.

## Judge explanation

A useful one-sentence explanation is:

> **“The Agent IDs select the two Lyzr Studio agents; the session IDs keep their conversations separate; the governance layer outside the model decides whether a proposal is allowed to change the deal.”**
