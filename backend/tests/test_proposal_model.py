
import pytest

from models.proposal import NegotiationProposal, ProposalAction
from models.validation import ValidationResult, ValidationStatus


def base_kwargs(**overrides):
    data = {
        "round_number": 1,
        "price": 100,
        "delivery_days": 30,
        "payment_days": 45,
        "sla_penalty": 2,
        "sla_uptime": 98,
        "action": ProposalAction.COUNTER,
    }
    data.update(overrides)
    return data


def test_offer_with_no_accepted_offer_is_valid():
    proposal = NegotiationProposal(**base_kwargs(action=ProposalAction.OFFER))
    assert proposal.accepted_offer is None


def test_accept_with_buyer_accepted_offer_is_valid():
    proposal = NegotiationProposal(
        **base_kwargs(action=ProposalAction.ACCEPT, accepted_offer="buyer")
    )
    assert proposal.accepted_offer == "buyer"


def test_accept_with_supplier_accepted_offer_is_valid():
    proposal = NegotiationProposal(
        **base_kwargs(action=ProposalAction.ACCEPT, accepted_offer="supplier")
    )
    assert proposal.accepted_offer == "supplier"


def test_accept_with_null_accepted_offer_is_valid():
    proposal = NegotiationProposal(
        **base_kwargs(action=ProposalAction.ACCEPT, accepted_offer=None)
    )
    assert proposal.accepted_offer is None


def test_accept_with_invalid_accepted_offer_value_is_rejected():
    with pytest.raises(ValueError):
        NegotiationProposal(
            **base_kwargs(action=ProposalAction.ACCEPT, accepted_offer="both")
        )


def test_accepted_offer_is_rejected_on_non_accept_actions():
    for action in (ProposalAction.OFFER, ProposalAction.COUNTER, ProposalAction.WALK_AWAY):
        with pytest.raises(ValueError):
            NegotiationProposal(**base_kwargs(action=action, accepted_offer="buyer"))


def test_round_number_must_be_positive():
    with pytest.raises(ValueError):
        NegotiationProposal(**base_kwargs(round_number=0))


def test_walk_away_action_round_trips():
    proposal = NegotiationProposal(**base_kwargs(action=ProposalAction.WALK_AWAY))
    assert proposal.action == ProposalAction.WALK_AWAY
    assert proposal.action.value == "walk_away"


def test_validation_result_defaults():
    result = ValidationResult(status=ValidationStatus.ALLOWED, reason="ok")
    assert result.violations == []
    assert result.validator == "unknown"
    assert result.severity == "error"


def test_validation_result_violations_default_is_not_shared_between_instances():
    first = ValidationResult(status=ValidationStatus.BLOCKED, reason="x")
    first.violations.append("oops")
    second = ValidationResult(status=ValidationStatus.BLOCKED, reason="y")
    
    
    assert second.violations == []
