"""Additional coverage for contract/generator.py, complementing
test_contract.py (creation + PDF) and test_contract_integrity.py (hash
stability). test_contract_integrity.py proves the hash is *stable* when
recomputed; this file proves the reverse — that it actually changes when
the contract's terms change, which is the property that makes it useful
as a tamper-evidence check in the first place.
"""

import json

from contract.generator import contract_payload_hash, contract_to_json, create_contract
from models.proposal import NegotiationProposal, ProposalAction


def make_proposal(**overrides):
    data = dict(
        round_number=6, price=52500, delivery_days=32, payment_days=45,
        sla_penalty=3, sla_uptime=98, action=ProposalAction.ACCEPT,
    )
    data.update(overrides)
    return NegotiationProposal(**data)


def make_contract(**proposal_overrides):
    proposal = make_proposal(**proposal_overrides)
    return create_contract(
        final_proposal=proposal,
        buyer_name="Buyer Corp",
        supplier_name="Supplier Corp",
        product_name="Industrial Motor",
        quantity=500,
        negotiation_id="NEG-001",
        negotiation_rounds=6,
    )


def test_hash_changes_when_a_contract_term_is_mutated():
    contract = make_contract()
    original_hash = contract_payload_hash(contract)

    contract.unit_price = contract.unit_price + 1

    assert contract_payload_hash(contract) != original_hash


def test_hash_changes_when_sla_terms_differ():
    contract = make_contract()
    original_hash = contract_payload_hash(contract)

    contract.sla.penalty_percent = contract.sla.penalty_percent + 1

    assert contract_payload_hash(contract) != original_hash


def test_hash_is_unaffected_by_the_contract_hash_field_itself():
    contract = make_contract()
    baseline = contract_payload_hash(contract)

    contract.contract_hash = "not-a-real-hash"
    assert contract_payload_hash(contract) == baseline

    contract.contract_hash = baseline
    assert contract_payload_hash(contract) == baseline


def test_contract_to_json_round_trips_every_field():
    contract = make_contract()
    parsed = json.loads(contract_to_json(contract))

    assert parsed["contract_id"] == contract.contract_id
    assert parsed["buyer_name"] == "Buyer Corp"
    assert parsed["supplier_name"] == "Supplier Corp"
    assert parsed["unit_price"] == contract.unit_price
    assert parsed["delivery_days"] == 32
    assert parsed["payment_days"] == 45
    assert parsed["sla"]["minimum_uptime"] == 98
    assert parsed["sla"]["penalty_percent"] == 3
    assert parsed["status"] == "AGREED"
    assert parsed["version"] == 1


def test_two_contracts_from_identical_terms_still_get_distinct_ids():
    # contract_id is generated fresh (uuid4-based) on every call, so two
    # contracts negotiated with identical commercial terms must not be
    # confusable with one another.
    first = make_contract()
    second = make_contract()
    assert first.contract_id != second.contract_id
    assert first.contract_id.startswith("CTR-")
