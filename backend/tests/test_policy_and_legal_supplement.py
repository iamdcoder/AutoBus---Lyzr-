"""Supplements test_guardrails.py and test_legal_validator.py:

  * PolicyValidator is thoroughly tested for role="buyer" already, but had
    zero tests exercising the role="supplier" branch (the price-floor
    check, and confirming the shared delivery/payment/SLA checks apply to
    the supplier's own policy).
  * GuardrailEngine's policy-before-legal precedence, and the case where
    policy allows a proposal but the legal firewall still blocks it
    independently, had no direct test.
  * LegalValidator's exact boundary values (95% uptime, 3650-day delivery,
    365-day payment) and the negative-SLA-penalty rule were untested.
"""

from guardrails.guardrail_engine import GuardrailEngine
from guardrails.legal_validator import LegalValidator
from guardrails.policy_validator import PolicyValidator
from models.policy import (
    DeliveryPolicy,
    PartyPolicy,
    PaymentPolicy,
    PricePolicy,
    SLAPolicy,
)
from models.proposal import NegotiationProposal, ProposalAction


def make_supplier_policy(**overrides):
    data = dict(
        price=PricePolicy(target=115, minimum=100),
        delivery=DeliveryPolicy(target_days=30, maximum_days=45),
        payment=PaymentPolicy(preferred_days=30, minimum_days=15),
        sla=SLAPolicy(minimum_uptime=98, minimum_penalty=2, maximum_penalty=5),
        batna="Other customer",
        max_rounds=10,
    )
    data.update(overrides)
    return PartyPolicy(**data)


def make_proposal(**overrides):
    data = dict(
        round_number=1, price=105, delivery_days=35, payment_days=20,
        sla_penalty=3, sla_uptime=98, action=ProposalAction.COUNTER,
    )
    data.update(overrides)
    return NegotiationProposal(**data)


# --- PolicyValidator: supplier role ----------------------------------------


def test_supplier_price_below_minimum_is_blocked():
    policy = make_supplier_policy()
    result = PolicyValidator.validate(make_proposal(price=90), policy, "supplier")
    assert result.status.value == "blocked"
    assert any("below" in v and "supplier minimum" in v for v in result.violations)


def test_supplier_price_at_minimum_is_allowed():
    policy = make_supplier_policy()
    result = PolicyValidator.validate(make_proposal(price=100), policy, "supplier")
    assert result.status.value == "allowed"


def test_supplier_price_has_no_ceiling_check():
    # Unlike the buyer branch, the supplier branch never checks a price
    # *maximum* — a supplier is free to ask for as much as it likes; only
    # the buyer's own policy (checked separately, under role="buyer")
    # constrains the ceiling.
    policy = make_supplier_policy()
    result = PolicyValidator.validate(make_proposal(price=1_000_000), policy, "supplier")
    assert result.status.value == "allowed"


def test_supplier_delivery_payment_and_sla_checks_use_the_supplier_policy():
    policy = make_supplier_policy()
    proposal = make_proposal(delivery_days=50, payment_days=5, sla_penalty=10, sla_uptime=80)
    result = PolicyValidator.validate(proposal, policy, "supplier")
    assert result.status.value == "blocked"
    assert len(result.violations) >= 3


def test_valid_supplier_proposal_passes():
    policy = make_supplier_policy()
    result = PolicyValidator.validate(make_proposal(price=110), policy, "supplier")
    assert result.status.value == "allowed"


# --- GuardrailEngine precedence ------------------------------------------------


def test_guardrail_engine_reports_policy_when_both_layers_would_block():
    policy = make_supplier_policy()
    # price=50 fails the supplier's own policy floor (100) *and* would
    # otherwise be a perfectly legal positive price — policy should be
    # reported first, per GuardrailEngine's own precedence.
    result = GuardrailEngine.validate(make_proposal(price=50), policy, "supplier")
    assert result.status.value == "blocked"
    assert result.validator == "policy"


def test_guardrail_engine_reports_legal_when_only_legal_layer_blocks():
    # A generous supplier policy (payment window up to 4000 days) allows
    # a 3700-day payment term at the *policy* layer, but the legal
    # firewall's hard 365-day cap still blocks it independently.
    policy = make_supplier_policy(payment=PaymentPolicy(preferred_days=30, minimum_days=15))
    policy_lenient_delivery = policy.model_copy(
        update={"delivery": DeliveryPolicy(target_days=30, maximum_days=4000)}
    )
    proposal = make_proposal(delivery_days=3700, payment_days=20)

    policy_layer = PolicyValidator.validate(proposal, policy_lenient_delivery, "supplier")
    assert policy_layer.status.value == "allowed"  # sanity: policy alone would allow this

    result = GuardrailEngine.validate(proposal, policy_lenient_delivery, "supplier")
    assert result.status.value == "blocked"
    assert result.validator == "legal"
    assert any("LEGAL-DELIVERY-001" in v for v in result.violations)


# --- LegalValidator boundaries -------------------------------------------------


def test_legal_delivery_boundary_3650_is_allowed_3651_is_blocked():
    assert LegalValidator.validate(make_proposal(delivery_days=3650)).status.value == "allowed"
    assert LegalValidator.validate(make_proposal(delivery_days=3651)).status.value == "blocked"


def test_legal_delivery_zero_days_is_blocked():
    assert LegalValidator.validate(make_proposal(delivery_days=0)).status.value == "blocked"


def test_legal_payment_boundary_365_is_allowed_366_is_blocked():
    assert LegalValidator.validate(make_proposal(payment_days=365)).status.value == "allowed"
    assert LegalValidator.validate(make_proposal(payment_days=366)).status.value == "blocked"


def test_legal_payment_zero_days_is_blocked():
    assert LegalValidator.validate(make_proposal(payment_days=0)).status.value == "blocked"


def test_legal_sla_uptime_boundary_95_is_allowed_below_is_blocked():
    assert LegalValidator.validate(make_proposal(sla_uptime=95)).status.value == "allowed"
    assert LegalValidator.validate(make_proposal(sla_uptime=94.99)).status.value == "blocked"


def test_legal_negative_sla_penalty_is_blocked():
    result = LegalValidator.validate(make_proposal(sla_penalty=-1))
    assert result.status.value == "blocked"
    assert any("LEGAL-SLA-002" in v for v in result.violations)


def test_legal_violation_messages_are_tagged_with_their_rule_id():
    result = LegalValidator.validate(make_proposal(price=-5))
    assert any(v.startswith("LEGAL-PRICE-001:") for v in result.violations)


def test_legal_reports_every_violated_rule_at_once():
    proposal = make_proposal(price=-5, delivery_days=0, payment_days=0, sla_penalty=-1, sla_uptime=10)
    result = LegalValidator.validate(proposal)
    assert result.status.value == "blocked"
    assert len(result.violations) == 5
