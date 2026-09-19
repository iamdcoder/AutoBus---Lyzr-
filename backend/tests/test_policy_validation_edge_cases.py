
import pytest

from models.policy import (
    DeliveryPolicy,
    PartyPolicy,
    PaymentPolicy,
    PricePolicy,
    SLAPolicy,
)


def make_full_policy(**overrides):
    data = {
        "price": PricePolicy(target=100, minimum=90, maximum=110),
        "delivery": DeliveryPolicy(target_days=30, maximum_days=45),
        "payment": PaymentPolicy(preferred_days=60, minimum_days=30),
        "sla": SLAPolicy(minimum_uptime=98, minimum_penalty=1, maximum_penalty=5),
        "batna": "Existing supplier",
        "max_rounds": 10,
    }
    data.update(overrides)
    return PartyPolicy(**data)





def test_price_minimum_cannot_exceed_maximum():
    with pytest.raises(ValueError):
        PricePolicy(target=100, minimum=120, maximum=110)


def test_price_target_cannot_be_below_minimum():
    with pytest.raises(ValueError):
        PricePolicy(target=80, minimum=90, maximum=110)


def test_price_target_cannot_exceed_maximum():
    with pytest.raises(ValueError):
        PricePolicy(target=120, minimum=90, maximum=110)


def test_price_policy_without_bounds_is_valid():
    
    
    policy = PricePolicy(target=100)
    assert policy.minimum is None
    assert policy.maximum is None





def test_delivery_target_cannot_exceed_maximum():
    with pytest.raises(ValueError):
        DeliveryPolicy(target_days=50, maximum_days=45)


def test_delivery_target_equal_to_maximum_is_valid():
    policy = DeliveryPolicy(target_days=45, maximum_days=45)
    assert policy.target_days == policy.maximum_days == 45


def test_delivery_days_must_be_positive():
    with pytest.raises(ValueError):
        DeliveryPolicy(target_days=0, maximum_days=45)





def test_preferred_payment_days_cannot_be_below_minimum():
    with pytest.raises(ValueError):
        PaymentPolicy(preferred_days=20, minimum_days=30)


def test_preferred_payment_days_equal_to_minimum_is_valid():
    policy = PaymentPolicy(preferred_days=30, minimum_days=30)
    assert policy.preferred_days == policy.minimum_days == 30





def test_sla_minimum_penalty_cannot_exceed_maximum_penalty():
    with pytest.raises(ValueError):
        SLAPolicy(minimum_uptime=98, minimum_penalty=6, maximum_penalty=5)


def test_sla_uptime_must_be_between_zero_and_hundred():
    with pytest.raises(ValueError):
        SLAPolicy(minimum_uptime=101, minimum_penalty=1, maximum_penalty=5)
    with pytest.raises(ValueError):
        SLAPolicy(minimum_uptime=-1, minimum_penalty=1, maximum_penalty=5)





def test_max_rounds_defaults_to_ten():
    policy = make_full_policy(max_rounds=10)
    assert policy.max_rounds == 10


def test_max_rounds_must_be_positive():
    with pytest.raises(ValueError):
        make_full_policy(max_rounds=0)


def test_max_rounds_has_an_upper_bound():
    with pytest.raises(ValueError):
        make_full_policy(max_rounds=51)


def test_max_rounds_upper_bound_is_inclusive():
    policy = make_full_policy(max_rounds=50)
    assert policy.max_rounds == 50
