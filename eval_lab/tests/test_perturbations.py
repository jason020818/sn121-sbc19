"""Perturbation helper tests."""

from random import Random

from eval_lab.models import HiddenExpectations, HoldoutRecord
from eval_lab.perturbations import apply_controlled_flip, apply_invariant
from eval_lab.policy_engine import apply_policy
from eval_lab.policy_manifests import load_policy
from eval_lab.policy_models import DealFact


def test_amount_swap_does_not_change_names() -> None:
    policy = load_policy("production")
    deals = [
        DealFact(name="A", amount="$50K", state="customer_legal"),
        DealFact(name="B", amount="$900K", seller_owns_next=True, state="seller_owned_deliverable"),
    ]
    decision = apply_policy(deals, policy)
    record = HoldoutRecord(
        id="t",
        seed=1,
        scenario="s",
        hidden_expectations=HiddenExpectations(),
        deals=[d.model_dump() for d in deals],
        expected_dispositions=dict(decision.dispositions),
    )
    variant = apply_invariant(record, "swap_amounts", Random(1))
    assert {d["name"] for d in variant.deals} == {"A", "B"}
    assert {d["amount"] for d in variant.deals} == {"$50K", "$900K"}


def test_seller_deliverable_flip_changes_only_target() -> None:
    policy = load_policy("production")
    deals = [
        DealFact(name="Wait", state="customer_legal", checkpoint="present"),
        DealFact(name="Act", seller_owns_next=True, state="seller_owned_deliverable"),
    ]
    decision = apply_policy(deals, policy)
    record = HoldoutRecord(
        id="t",
        seed=1,
        scenario="s",
        hidden_expectations=HiddenExpectations(),
        deals=[d.model_dump() for d in deals],
        expected_dispositions=dict(decision.dispositions),
    )
    variant = apply_controlled_flip(record, "wait_to_seller_deliverable")
    assert variant.expected_after["Wait"] == "ACTION"
    assert variant.expected_after["Act"] == "ACTION"
    assert variant.flip_deals == ["Wait"]
