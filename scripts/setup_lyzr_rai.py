"""Create a reusable Lyzr Responsible AI policy for AutoBus.

This script creates the policy in Lyzr. Policy assignment to Buyer/Supplier
agents is intentionally left to Lyzr Studio because the current Studio flow
supports assigning the created policy from the agent's Responsible AI feature.
"""
from __future__ import annotations

import json
import os
import sys
import requests

BASE_URL = "https://rai-prod.studio.lyzr.ai"

def main() -> int:
    api_key = os.getenv("LYZR_API_KEY", "").strip()
    user_id = os.getenv("LYZR_USER_ID", "autobus-system").strip()
    if not api_key:
        print("Set LYZR_API_KEY in your environment first.")
        return 2

    policy = {
        "name": "AutoBus Negotiation Safety",
        "description": "Blocks prompt injection and secret leakage around bounded B2B negotiation agents.",
        "allowed_topics": {"enabled": True, "topics": ["B2B procurement", "supplier negotiation", "SLA contracts"]},
        "banned_topics": {"enabled": False, "topics": []},
        "keywords": {"enabled": True, "keywords": ["reservation price", "walk-away price", "private BATNA", "internal policy"]},
        "toxicity_check": {"enabled": True, "threshold": 0.8},
        "prompt_injection": {"enabled": True, "threshold": 0.5},
        "secrets_detection": {"enabled": True, "action": "mask"},
        "pii_detection": {"enabled": False, "types": {}, "custom_pii": []},
        "user_id": user_id,
    }
    r = requests.post(
        f"{BASE_URL}/v1/rai/policies",
        headers={"x-api-key": api_key, "content-type": "application/json", "accept": "application/json"},
        json=policy,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    print(json.dumps(data, indent=2, default=str))
    policy_id = data.get("_id") or data.get("id")
    if policy_id:
        print(f"\\nRAI_POLICY_ID={policy_id}")
        print("Next: open each AutoBus agent in Lyzr Studio → Responsible AI → select this policy → Save Configuration.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
