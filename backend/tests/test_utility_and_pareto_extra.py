
from models.policy import (
    DeliveryPolicy,
    PartyPolicy,
    PaymentPolicy,
    PricePolicy,
    SLAPolicy,
)
from models.proposal import NegotiationProposal, ProposalAction
from negotiation.pareto import build_pareto_frontier
from negotiation.risk import calculate_risk
from negotiation.utility import calculate_utility, explain_tradeoff


def buyer_policy():
    return PartyPolicy(
        price=PricePolicy(target=100, maximum=120),
        delivery=DeliveryPolicy(target_days=30, maximum_days=45),
        payment=PaymentPolicy(preferred_days=60, minimum_days=30),
        sla=SLAPolicy(minimum_uptime=98, minimum_penalty=1, maximum_penalty=5),
        batna="Existing supplier",
        max_rounds=10,
    )


def supplier_policy():
    return PartyPolicy(
        price=PricePolicy(target=110, minimum=95),
        delivery=DeliveryPolicy(target_days=25, maximum_days=45),
        payment=PaymentPolicy(preferred_days=30, minimum_days=15),
        sla=SLAPolicy(minimum_uptime=97, minimum_penalty=1, maximum_penalty=5),
        batna="Other customer",
        max_rounds=10,
    )


def make_proposal(price, delivery_days, payment_days, sla_penalty, sla_uptime, round_number=1):
    return NegotiationProposal(
        round_number=round_number,
        price=price,
        delivery_days=delivery_days,
        payment_days=payment_days,
        sla_penalty=sla_penalty,
        sla_uptime=sla_uptime,
        action=ProposalAction.COUNTER,
    )





def test_explain_tradeoff_reports_full_negative_delta_for_buyer_worst_case():
    policy = buyer_policy()
    
    
    
    best = make_proposal(price=100, delivery_days=30, payment_days=60, sla_penalty=1, sla_uptime=100)
    
    
    worst = make_proposal(price=120, delivery_days=45, payment_days=30, sla_penalty=5, sla_uptime=98)

    before_u = calculate_utility(best, policy, "buyer")
    after_u = calculate_utility(worst, policy, "buyer")
    assert before_u.total == 1.0
    assert after_u.total == 0.0

    tradeoff = explain_tradeoff(best, worst, "buyer", policy)
    assert tradeoff["utility_before"] == 1.0
    assert tradeoff["utility_after"] == 0.0
    assert tradeoff["utility_delta"] == -1.0
    assert set(tradeoff["component_deltas"]) == {"price", "delivery", "payment", "sla_uptime", "sla_penalty"}
    assert all(delta == -1.0 for delta in tradeoff["component_deltas"].values())
    
    assert tradeoff["risk_after"] >= tradeoff["risk_before"]


def test_explain_tradeoff_is_zero_when_nothing_changes():
    policy = supplier_policy()
    proposal = make_proposal(price=105, delivery_days=30, payment_days=25, sla_penalty=2, sla_uptime=98)
    tradeoff = explain_tradeoff(proposal, proposal, "supplier", policy)
    assert tradeoff["utility_delta"] == 0.0
    assert all(delta == 0.0 for delta in tradeoff["component_deltas"].values())





def test_dominated_proposal_is_excluded_from_the_efficient_set():
    buyer, supplier = buyer_policy(), supplier_policy()

    p1 = make_proposal(100, 30, 45, 2, 98)  
    p2 = make_proposal(108, 32, 40, 3, 98)  
    p3 = make_proposal(115, 28, 35, 2, 99)  
    
    
    
    
    p4_dominated = make_proposal(100, 30, 45, 5, 97)

    points = build_pareto_frontier([p1, p2, p3, p4_dominated], buyer, supplier)
    by_index = {point.index: point for point in points}

    assert by_index[0].pareto_efficient is True
    assert by_index[1].pareto_efficient is True
    assert by_index[2].pareto_efficient is True
    assert by_index[3].pareto_efficient is False

    dominated_point = by_index[3]
    dominating_point = by_index[0]
    assert dominating_point.buyer_utility >= dominated_point.buyer_utility
    assert dominating_point.supplier_utility >= dominated_point.supplier_utility
    assert (
        dominating_point.buyer_utility > dominated_point.buyer_utility
        or dominating_point.supplier_utility > dominated_point.supplier_utility
    )


def test_pareto_frontier_preserves_input_order_and_count():
    buyer, supplier = buyer_policy(), supplier_policy()
    proposals = [
        make_proposal(100, 30, 45, 2, 98),
        make_proposal(108, 32, 40, 3, 98),
    ]
    points = build_pareto_frontier(proposals, buyer, supplier)
    assert [p.index for p in points] == [0, 1]
    assert all(p.proposal is proposals[p.index] for p in points)





def test_risk_label_is_critical_when_a_hard_policy_limit_is_breached():
    buyer, supplier = buyer_policy(), supplier_policy()
    
    
    proposal = make_proposal(130, 30, 45, 2, 98)

    risk = calculate_risk(proposal, buyer, supplier)

    assert risk["hard_limit_hits"] >= 1
    assert risk["label"] == "CRITICAL"
    assert risk["policy_compliance"] == 0.0
    assert "must be blocked" in risk["interpretation"]


def test_risk_label_is_not_critical_when_no_hard_limit_is_breached():
    buyer, supplier = buyer_policy(), supplier_policy()
    proposal = make_proposal(105, 30, 45, 2, 98)

    risk = calculate_risk(proposal, buyer, supplier)

    assert risk["hard_limit_hits"] == 0
    assert risk["label"] != "CRITICAL"
    assert risk["policy_compliance"] == 100.0
