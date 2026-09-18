"""Direct, arithmetic-level tests for the negotiation-support modules that
previously had no dedicated coverage: negotiation/convergence.py,
negotiation/deadlock.py, and the NegotiationState properties in
negotiation/state.py. These are pure functions/dataclasses with no I/O,
so every assertion below is computed by hand against the documented
formula rather than merely checked for "did not raise".
"""

from models.proposal import NegotiationProposal, ProposalAction
from negotiation.convergence import calculate_concession, calculate_gap, is_converging
from negotiation.deadlock import detect_stagnation, price_is_feasible
from negotiation.state import NegotiationState


def proposal(**overrides):
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
    return NegotiationProposal(**data)


class DummyPolicy:
    def __init__(self, maximum=None, minimum=None):
        self.price = type("P", (), {"maximum": maximum, "minimum": minimum})()


# --- calculate_gap -----------------------------------------------------


def test_calculate_gap_is_zero_for_identical_proposals():
    p = proposal(price=100, delivery_days=30, payment_days=45, sla_penalty=2)
    assert calculate_gap(p, p) == 0.0


def test_calculate_gap_matches_hand_computed_weighted_formula():
    buyer = proposal(price=100, delivery_days=30, payment_days=60, sla_penalty=2)
    supplier = proposal(price=110, delivery_days=40, payment_days=30, sla_penalty=4)

    price_gap = abs(100 - 110) / max(100, 110, 1.0)  # 10/110
    delivery_gap = abs(30 - 40) / 60.0
    payment_gap = abs(60 - 30) / 60.0
    sla_gap = abs(2 - 4) / 10.0
    expected = price_gap * 0.55 + delivery_gap * 0.20 + payment_gap * 0.15 + sla_gap * 0.10

    assert calculate_gap(buyer, supplier) == expected


def test_calculate_gap_price_scale_floor_prevents_division_by_zero():
    # Both prices at 0 would otherwise divide by zero; the function floors
    # the scale at 1.0.
    buyer = proposal(price=0, delivery_days=30, payment_days=45, sla_penalty=2)
    supplier = proposal(price=0, delivery_days=30, payment_days=45, sla_penalty=2)
    assert calculate_gap(buyer, supplier) == 0.0


# --- is_converging -------------------------------------------------------


def test_is_converging_true_when_gap_shrinks():
    assert is_converging(previous_gap=0.5, current_gap=0.3) is True


def test_is_converging_false_when_gap_grows_or_stays_flat():
    assert is_converging(previous_gap=0.3, current_gap=0.5) is False
    assert is_converging(previous_gap=0.3, current_gap=0.3) is False


# --- calculate_concession --------------------------------------------------


def test_buyer_concession_counts_only_favorable_movement():
    previous = proposal(price=100, delivery_days=30, payment_days=45, sla_penalty=2)
    current = proposal(price=95, delivery_days=32, payment_days=50, sla_penalty=1)
    concession = calculate_concession(previous, current, role="buyer")
    # Buyer concedes by paying *more* (price up is not a concession for
    # buyer; price down toward supplier is), accepting later delivery,
    # paying sooner (more days-until-payment is *not* a buyer concession —
    # buyer concedes by shortening its own payment window), or lowering
    # its own SLA penalty ask.
    assert concession["price_concession"] == max(100 - 95, 0)
    assert concession["delivery_concession"] == max(32 - 30, 0)
    assert concession["payment_concession"] == max(50 - 45, 0)
    assert concession["sla_concession"] == max(2 - 1, 0)


def test_supplier_concession_is_the_mirror_of_buyer():
    previous = proposal(price=110, delivery_days=40, payment_days=30, sla_penalty=5)
    current = proposal(price=115, delivery_days=35, payment_days=25, sla_penalty=3)
    concession = calculate_concession(previous, current, role="supplier")
    assert concession["price_concession"] == max(115 - 110, 0)
    assert concession["delivery_concession"] == max(40 - 35, 0)
    assert concession["payment_concession"] == max(30 - 25, 0)
    # Supplier's SLA-penalty concession is current - previous (offering a
    # *higher* penalty is the supplier's concession); here the penalty
    # dropped (5 -> 3), which is unfavorable to the buyer, so the
    # supplier's own concession on this dimension is floored at 0.
    assert concession["sla_concession"] == max(3 - 5, 0) == 0


def test_concession_is_never_negative_when_the_party_moves_unfavorably():
    previous = proposal(price=100, delivery_days=30, payment_days=45, sla_penalty=2)
    current = proposal(price=105, delivery_days=25, payment_days=40, sla_penalty=4)
    concession = calculate_concession(previous, current, role="buyer")
    assert concession["price_concession"] == 0
    assert concession["delivery_concession"] == 0
    assert concession["payment_concession"] == 0
    assert concession["sla_concession"] == 0


def test_concession_deltas_are_signed_regardless_of_role():
    previous = proposal(price=100, delivery_days=30, payment_days=45, sla_penalty=2)
    current = proposal(price=90, delivery_days=28, payment_days=40, sla_penalty=1)
    concession = calculate_concession(previous, current, role="buyer")
    assert concession["price_delta"] == -10
    assert concession["delivery_delta"] == -2
    assert concession["payment_delta"] == -5
    assert concession["sla_delta"] == -1


# --- price_is_feasible ----------------------------------------------------


def test_price_feasible_when_either_bound_is_unset():
    assert price_is_feasible(DummyPolicy(maximum=None), DummyPolicy(minimum=100)) is True
    assert price_is_feasible(DummyPolicy(maximum=100), DummyPolicy(minimum=None)) is True
    assert price_is_feasible(DummyPolicy(maximum=None), DummyPolicy(minimum=None)) is True


def test_price_feasible_when_ranges_overlap():
    assert price_is_feasible(DummyPolicy(maximum=110), DummyPolicy(minimum=100)) is True


def test_price_feasible_boundary_equal_is_feasible():
    assert price_is_feasible(DummyPolicy(maximum=100), DummyPolicy(minimum=100)) is True


def test_price_infeasible_when_buyer_ceiling_below_supplier_floor():
    assert price_is_feasible(DummyPolicy(maximum=90), DummyPolicy(minimum=100)) is False


# --- detect_stagnation ------------------------------------------------------


def test_stagnation_true_when_repeated_rounds_hit_threshold():
    assert detect_stagnation(gaps=[0.5], repeated_rounds=3) is True


def test_stagnation_false_with_fewer_than_three_gaps_and_no_repeats():
    assert detect_stagnation(gaps=[0.5, 0.4], repeated_rounds=0) is False


def test_stagnation_false_when_gap_is_steadily_shrinking():
    assert detect_stagnation(gaps=[0.5, 0.4, 0.3], repeated_rounds=0) is False


def test_stagnation_true_when_gap_plateaus_across_three_rounds():
    assert detect_stagnation(gaps=[0.30, 0.31, 0.31], repeated_rounds=0) is True


def test_stagnation_respects_custom_threshold():
    assert detect_stagnation(gaps=[0.5], repeated_rounds=2, threshold=2) is True
    assert detect_stagnation(gaps=[0.5], repeated_rounds=1, threshold=2) is False


# --- NegotiationState properties --------------------------------------------


def test_state_gap_properties_are_none_with_no_rounds():
    state = NegotiationState()
    assert state.initial_gap is None
    assert state.latest_gap is None
    assert state.gap_reduction is None
    assert state.convergence_ratio == 0.0


def test_state_tracks_gap_reduction_across_rounds():
    state = NegotiationState()
    p1 = proposal(round_number=1)
    p2 = proposal(round_number=2)
    state.record_round(p1, p1, gap=0.5)
    state.record_round(p2, p2, gap=0.2)
    assert state.initial_gap == 0.5
    assert state.latest_gap == 0.2
    assert state.gap_reduction == 0.3
    assert state.convergence_ratio == 0.6


def test_state_convergence_ratio_is_clamped_between_zero_and_one():
    state = NegotiationState()
    p1 = proposal(round_number=1)
    p2 = proposal(round_number=2)
    # Gap *growing* would otherwise produce a negative ratio; it is
    # clamped to 0.0 so callers can treat this as a simple percentage.
    state.record_round(p1, p1, gap=0.2)
    state.record_round(p2, p2, gap=0.5)
    assert state.convergence_ratio == 0.0


def test_state_convergence_ratio_is_one_when_initial_gap_is_zero():
    state = NegotiationState()
    p1 = proposal(round_number=1)
    state.record_round(p1, p1, gap=0.0)
    assert state.convergence_ratio == 1.0


def test_state_current_round_tracks_the_latest_buyer_round_number():
    state = NegotiationState()
    state.record_round(proposal(round_number=1), proposal(round_number=1), gap=0.3)
    state.record_round(proposal(round_number=2), proposal(round_number=2), gap=0.1)
    assert state.current_round == 2
    assert len(state.buyer_proposals) == 2
    assert len(state.supplier_proposals) == 2
