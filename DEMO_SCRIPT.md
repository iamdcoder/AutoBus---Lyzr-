# AutoBus — Winning Demo Script

## Opening

> “This is not an LLM that negotiates without limits. It is a governed procurement negotiation where two Lyzr agents can bargain, but neither can break the policy envelope.”

## 1. Show the guardrails

Set the Buyer ceiling, Supplier floor, delivery window, payment terms, and SLA bounds.

Say:

> “These values are private policy. They control what each side is willing to accept, but reservation values are never exposed to the other agent.”

## 2. Run the normal negotiation

Start the negotiation and point to:

- proposal history;
- round number;
- concessions;
- utility;
- risk;
- convergence.

Say:

> “The Lyzr agent generates a proposal. The proposal then crosses the governance boundary before it can mutate the authoritative negotiation state.”

## 3. Prove the attack surface is bounded

Run the red-team/security examples.

Show a blocked out-of-policy value and, where available in the UI, a prompt-injection or private-policy leakage attempt.

Say:

> “Even when the model produces an invalid or unsafe proposal, the model does not get write access to the deal state. The deterministic firewall blocks it.”

## 4. Show multi-vendor decision quality

Run the three-supplier RFQ and show utility, risk, and Pareto efficiency.

Say:

> “The system does not simply choose the cheapest supplier. It compares the commercial trade-off under the policy constraints.”

## 5. Prove auditability

Open Audit and verify the hash chain.

Say:

> “Every meaningful state transition is recorded in a tamper-evident chain, so the negotiation can be reconstructed and verified.”

## 6. Prove contract integrity

Generate the JSON/PDF contract and show the SHA-256 hash and version metadata.

Close with:

> **“The output of the agent is not the contract. The output of the governed state machine is the contract.”**

## If the judge asks about AIMS or Responsible AI

Say this exactly:

> “Native Lyzr Responsible AI and AIMS are subscription-gated capabilities that were not exposed on the account used for this quest. We did not fake those integrations. The Lyzr agent integration is real, while the application provides deterministic governance and a tamper-evident audit fallback, with optional adapters for an authorized deployment.”

Do not call the local JSONL audit chain “AIMS”.

## Live links

- Application: https://autobus-lyzr.onrender.com/
- Dashboard: https://autobus-lyzr.onrender.com/ui
- Health: https://autobus-lyzr.onrender.com/health
- API docs: https://autobus-lyzr.onrender.com/docs
