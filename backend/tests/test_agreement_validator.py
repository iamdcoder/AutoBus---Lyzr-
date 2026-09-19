
from guardrails.agreement_validator import AgreementValidator
from models.policy import (
    DeliveryPolicy,
    PartyPolicy,
    PaymentPolicy,
    PricePolicy,
    SLAPolicy,
)
from models.proposal import NegotiationProposal, ProposalAction


def make_buyer_policy(**price_overrides):
    price = {"target": 100, "maximum": 110}
    price.update(price_overrides)
    return PartyPolicy(
        price=PricePolicy(**price),
        delivery=DeliveryPolicy(target_days=30, maximum_days=45),
        payment=PaymentPolicy(preferred_days=60, minimum_days=30),
        sla=SLAPolicy(minimum_uptime=98, minimum_penalty=2, maximum_penalty=5),
        batna="Existing supplier",
        max_rounds=10,
    )


def make_supplier_policy(**price_overrides):
    price = {"target": 105, "minimum": 95}
    price.update(price_overrides)
    return PartyPolicy(
        price=PricePolicy(**price),
        delivery=DeliveryPolicy(target_days=30, maximum_days=45),
        payment=PaymentPolicy(preferred_days=30, minimum_days=15),
        sla=SLAPolicy(minimum_uptime=98, minimum_penalty=2, maximum_penalty=5),
        batna="Other customer",
        max_rounds=10,
    )


def make_proposal(**overrides):
    data = {
        "round_number": 1,
        "price": 105,
        "delivery_days": 35,
        "payment_days": 45,
        "sla_penalty": 3,
        "sla_uptime": 98,
        "action": ProposalAction.COUNTER,
    }
    data.update(overrides)
    return NegotiationProposal(**data)


def test_valid_agreement_passes_all_three_layers():
    result = AgreementValidator.validate(
        make_proposal(), make_buyer_policy(), make_supplier_policy()
    )
    assert result.status.value == "allowed"
    assert result.validator == "agreement_firewall"
    assert result.violations == []


def test_buyer_only_violation_is_prefixed_and_reported():
    proposal = make_proposal(price=500)  
    result = AgreementValidator.validate(
        proposal, make_buyer_policy(), make_supplier_policy()
    )
    assert result.status.value == "blocked"
    assert any(v.startswith("BUYER:") for v in result.violations)
    assert not any(v.startswith("SUPPLIER:") for v in result.violations)
    assert not any(v.startswith("LEGAL:") for v in result.violations)


def test_supplier_only_violation_is_prefixed_and_reported():
    proposal = make_proposal(price=50)  
    result = AgreementValidator.validate(
        proposal, make_buyer_policy(), make_supplier_policy()
    )
    assert result.status.value == "blocked"
    assert any(v.startswith("SUPPLIER:") for v in result.violations)
    assert not any(v.startswith("BUYER:") for v in result.violations)


def test_legal_only_violation_is_prefixed_and_reported():
    
    
    
    
    
    
    buyer = make_buyer_policy()
    buyer_lenient = PartyPolicy(
        price=buyer.price,
        delivery=buyer.delivery,
        payment=buyer.payment,
        sla=SLAPolicy(minimum_uptime=80, minimum_penalty=2, maximum_penalty=5),
        batna=buyer.batna,
        max_rounds=buyer.max_rounds,
    )
    supplier = make_supplier_policy()
    supplier_lenient = PartyPolicy(
        price=supplier.price,
        delivery=supplier.delivery,
        payment=supplier.payment,
        sla=SLAPolicy(minimum_uptime=80, minimum_penalty=2, maximum_penalty=5),
        batna=supplier.batna,
        max_rounds=supplier.max_rounds,
    )
    proposal = make_proposal(sla_uptime=90)  
    result = AgreementValidator.validate(proposal, buyer_lenient, supplier_lenient)
    assert result.status.value == "blocked"
    assert any(v.startswith("LEGAL:") for v in result.violations)
    assert not any(v.startswith("BUYER:") for v in result.violations)
    assert not any(v.startswith("SUPPLIER:") for v in result.violations)


def test_combined_violations_from_every_layer_are_all_reported():
    proposal = make_proposal(price=-10, delivery_days=35, payment_days=45)
    result = AgreementValidator.validate(
        proposal, make_buyer_policy(), make_supplier_policy()
    )
    assert result.status.value == "blocked"
    
    
    
    
    prefixes = {v.split(":", 1)[0] for v in result.violations}
    assert "SUPPLIER" in prefixes
    assert "LEGAL" in prefixes
    assert "BUYER" not in prefixes
