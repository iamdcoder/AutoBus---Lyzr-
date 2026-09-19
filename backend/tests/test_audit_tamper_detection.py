
import json

from audit.logger import AuditLogger
from audit.models import AuditEventType


def log_two_events(path):
    logger = AuditLogger(path=str(path))
    logger.log(
        negotiation_id="NEG-TAMPER",
        event_type=AuditEventType.NEGOTIATION_STARTED,
        actor="negotiation_engine",
        status="success",
        details={"buyer": "Buyer Corp"},
    )
    logger.log(
        negotiation_id="NEG-TAMPER",
        event_type=AuditEventType.PROPOSAL_GENERATED,
        actor="buyer_agent",
        status="success",
        details={"price": 50000},
        round_number=1,
    )
    return logger


def test_verify_on_a_log_that_was_never_written_is_valid(tmp_path):
    logger = AuditLogger(path=str(tmp_path / "never-written-audit.jsonl"))
    result = logger.verify()
    assert result == {"valid": True, "events": 0, "broken_at": None}


def test_verify_passes_on_an_untampered_chain(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    logger = log_two_events(log_path)
    logger.log(
        negotiation_id="NEG-TAMPER",
        event_type=AuditEventType.AGREEMENT_REACHED,
        actor="buyer_agent",
        status="success",
        details={},
        round_number=1,
    )

    result = logger.verify()
    assert result == {"valid": True, "events": 3, "broken_at": None}


def test_verify_detects_a_record_whose_content_no_longer_matches_its_hash(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    logger = log_two_events(log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    
    
    first["actor"] = "attacker_controlled_actor"
    lines[0] = json.dumps(first, sort_keys=True)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = logger.verify()
    assert result["valid"] is False
    assert result["broken_at"] == 1
    assert result["events"] == 0


def test_verify_detects_a_broken_chain_link_between_records(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    logger = log_two_events(log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    
    
    
    
    first["actor"] = "attacker_controlled_actor"
    payload = dict(first)
    payload.pop("event_hash", None)
    first["event_hash"] = AuditLogger._hash_event(payload)
    lines[0] = json.dumps(first, sort_keys=True)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = logger.verify()
    assert result["valid"] is False
    assert result["events"] == 1  
    assert result["broken_at"] == 2


def test_verify_detects_truncation_style_hash_corruption(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    logger = log_two_events(log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    second = json.loads(lines[1])
    second["event_hash"] = "0" * 64
    lines[1] = json.dumps(second, sort_keys=True)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = logger.verify()
    assert result["valid"] is False
    assert result["broken_at"] == 2
    assert result["events"] == 1
