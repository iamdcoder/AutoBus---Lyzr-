"""Additional coverage for governance/lyzr_governance.py and
governance/environment.py, complementing test_governance.py.

test_governance.py already covers the local-fallback check paths and the
"external endpoint unreachable -> fail closed" behavior. This file adds:
  * the `mode` property's four combinations,
  * a mocked *successful* external guardrail response (the "allow" path,
    which nothing previously exercised — only the unreachable-endpoint
    fail-closed path was tested),
  * both branches of `publish_event` (external sink success, and falling
    back to the local outbox when the sink call raises),
  * `build_redaction_snapshot` directly, and
  * `AgentEnvironment.allowed_shared_fields`, which had no test at all.

Every test that touches `requests.post` monkeypatches it rather than
making a real network call, matching the pattern already used in
test_lyzr_client.py.
"""

import json

from governance.environment import AgentEnvironment
from governance.lyzr_governance import LyzrGovernance, build_redaction_snapshot
from models.policy import PartyPolicy


def policy():
    return PartyPolicy(
        price={"target": 100, "maximum": 120},
        delivery={"target_days": 30, "maximum_days": 45},
        payment={"preferred_days": 60, "minimum_days": 30},
        sla={"minimum_uptime": 98, "minimum_penalty": 1, "maximum_penalty": 5},
        batna="secret-batna",
        max_rounds=6,
    )


# --- mode property -------------------------------------------------------


def test_mode_is_deterministic_fallback_with_nothing_configured(monkeypatch):
    monkeypatch.delenv("LYZR_GUARDRAIL_URL", raising=False)
    monkeypatch.delenv("LYZR_AIMS_WEBHOOK_URL", raising=False)
    assert LyzrGovernance().mode == "deterministic_fallback"


def test_mode_reports_responsible_ai_only(monkeypatch):
    monkeypatch.setenv("LYZR_GUARDRAIL_URL", "https://guardrail.example")
    monkeypatch.delenv("LYZR_AIMS_WEBHOOK_URL", raising=False)
    assert LyzrGovernance().mode == "lyzr_responsible_ai"


def test_mode_reports_aims_sink_only(monkeypatch):
    monkeypatch.delenv("LYZR_GUARDRAIL_URL", raising=False)
    monkeypatch.setenv("LYZR_AIMS_WEBHOOK_URL", "https://aims.example")
    assert LyzrGovernance().mode == "lyzr_aims_sink"


def test_mode_reports_both_when_fully_configured(monkeypatch):
    monkeypatch.setenv("LYZR_GUARDRAIL_URL", "https://guardrail.example")
    monkeypatch.setenv("LYZR_AIMS_WEBHOOK_URL", "https://aims.example")
    assert LyzrGovernance().mode == "lyzr_responsible_ai+lyzr_aims_sink"


# --- external guardrail: the "allow" path -----------------------------------


def test_configured_governance_allows_when_external_endpoint_approves(monkeypatch):
    monkeypatch.setenv("LYZR_GUARDRAIL_URL", "https://guardrail.example")
    monkeypatch.delenv("LYZR_GUARDRAIL_TOKEN", raising=False)

    class Response:
        status_code = 200
        content = b'{"verdict": "allow", "reason": "looks fine"}'

        def raise_for_status(self):
            pass

        def json(self):
            return {"verdict": "allow", "reason": "looks fine"}

    calls = {}

    def fake_post(url, headers, json, timeout):
        calls.update(url=url, headers=headers, json=json, timeout=timeout)
        return Response()

    monkeypatch.setattr("governance.lyzr_governance.requests.post", fake_post)

    g = LyzrGovernance()
    decision = g.check(stage="agent_output", actor="buyer_agent", payload={"x": 1})

    assert decision.allowed is True
    assert decision.source == "lyzr_responsible_ai"
    assert calls["url"] == "https://guardrail.example"
    assert "authorization" not in calls["headers"]


def test_configured_governance_includes_bearer_token_when_set(monkeypatch):
    monkeypatch.setenv("LYZR_GUARDRAIL_URL", "https://guardrail.example")
    monkeypatch.setenv("LYZR_GUARDRAIL_TOKEN", "secret-token")

    class Response:
        status_code = 200
        content = b'{"verdict": "deny", "reason": "blocked", "rule": "custom-rule"}'

        def raise_for_status(self):
            pass

        def json(self):
            return {"verdict": "deny", "reason": "blocked", "rule": "custom-rule"}

    calls = {}

    def fake_post(url, headers, json, timeout):
        calls.update(headers=headers)
        return Response()

    monkeypatch.setattr("governance.lyzr_governance.requests.post", fake_post)

    g = LyzrGovernance()
    decision = g.check(stage="agent_output", actor="buyer_agent", payload={"x": 1})

    assert decision.allowed is False
    assert decision.rule == "custom-rule"
    assert calls["headers"]["authorization"] == "Bearer secret-token"


# --- publish_event: external sink vs local outbox fallback ------------------


def test_publish_event_succeeds_against_a_configured_sink(monkeypatch, tmp_path):
    monkeypatch.setenv("LYZR_AIMS_WEBHOOK_URL", "https://aims.example")
    monkeypatch.setenv("LYZR_AIMS_OUTBOX", str(tmp_path / "unused_outbox.jsonl"))

    class Response:
        status_code = 202

        def raise_for_status(self):
            pass

    monkeypatch.setattr("governance.lyzr_governance.requests.post", lambda *a, **k: Response())

    g = LyzrGovernance()
    result = g.publish_event({"event_type": "agreement_reached", "negotiation_id": "NEG-1"})

    assert result == {"published": True, "source": "lyzr_aims_sink", "status_code": 202}
    # Nothing should have been queued locally on a successful publish.
    assert not (tmp_path / "unused_outbox.jsonl").exists()


def test_publish_event_falls_back_to_local_outbox_when_sink_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("LYZR_AIMS_WEBHOOK_URL", "https://aims.example")
    outbox_path = tmp_path / "aims.jsonl"
    monkeypatch.setenv("LYZR_AIMS_OUTBOX", str(outbox_path))

    def raising_post(*args, **kwargs):
        raise ConnectionError("no route to host")

    monkeypatch.setattr("governance.lyzr_governance.requests.post", raising_post)

    g = LyzrGovernance()
    result = g.publish_event({"event_type": "agreement_reached", "negotiation_id": "NEG-1"})

    assert result["published"] is False
    assert result["source"] == "lyzr_aims_sink"
    assert result["queued"] is True
    assert outbox_path.exists()

    queued = json.loads(outbox_path.read_text(encoding="utf-8").splitlines()[0])
    assert queued["schema_version"] == "autobus.aims-event.v1"
    assert queued["event"]["negotiation_id"] == "NEG-1"


# --- build_redaction_snapshot -------------------------------------------------


def test_build_redaction_snapshot_never_exposes_reservation_data():
    snapshot = build_redaction_snapshot(policy())
    assert snapshot["private_fields_redacted"] is True
    assert snapshot["price"] == {"target_present": True}
    assert "batna" not in snapshot
    assert "minimum" not in snapshot["price"]
    assert "maximum" not in snapshot["price"]


# --- AgentEnvironment.allowed_shared_fields -----------------------------------


def test_allowed_shared_fields_strips_every_forbidden_key():
    env = AgentEnvironment(actor="buyer", private_policy=policy(), session_id="NEG-1-buyer")
    payload = {
        "price": 100,
        "batna": "secret-batna",
        "minimum_price": 90,
        "maximum_price": 110,
        "reservation_price": 95,
        "raw_policy": {"everything": True},
        "private_policy": {"everything": True},
        "walk_away_price": 80,
        "note": "keep me",
    }
    result = env.allowed_shared_fields(payload)
    assert result == {"price": 100, "note": "keep me"}
