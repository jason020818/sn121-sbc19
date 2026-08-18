"""Metamorphic variant tests."""

from random import Random

from eval_lab.metamorphic import check_controlled_flip, check_invariant, generate_metamorphic
from eval_lab.oracle_evaluator import generate_oracle_corpus
from eval_lab.perturbations import apply_controlled_flip, apply_invariant
from eval_lab.policy_manifests import load_policy
from eval_lab.policy_models import DealFact
from eval_lab.models import HiddenExpectations, HoldoutRecord
from eval_lab.policy_engine import apply_policy


def _base() -> HoldoutRecord:
    deals = [
        DealFact(name="Alpha Co", state="customer_legal", checkpoint="present"),
        DealFact(name="Beta Co", state="seller_owned_deliverable", seller_owns_next=True),
        DealFact(name="Gamma Co", state="unknown_owner", owner_named=False),
    ]
    policy = load_policy("production")
    decision = apply_policy(deals, policy)
    return HoldoutRecord(
        id="O-0001",
        seed=1,
        scenario="base",
        hidden_expectations=HiddenExpectations(
            allowed_action_deals=decision.action_set,
            required_monitor_deals=decision.monitor_set,
            source_entities=[d.name for d in deals],
        ),
        deals=[d.model_dump() for d in deals],
        expected_dispositions=dict(decision.dispositions),
    )


def test_rename_row_order_amount_quota_meeting_invariance() -> None:
    policy = load_policy("production")
    base = _base()
    rng = Random(0)
    for transform in (
        "rename_entities",
        "reorder_rows",
        "swap_amounts",
        "quota_context",
        "add_monitor_deal",
    ):
        variant = apply_invariant(base, transform, rng)
        assert check_invariant(base, variant, policy)["passed"]


def test_controlled_flips_and_no_collateral() -> None:
    policy = load_policy("production")
    base = _base()
    for transform in (
        "wait_to_seller_deliverable",
        "checkpoint_passed",
        "add_meeting_today",
        "add_do_not_contact",
        "human_correction",
        "unnamed_to_named_owner",
        "automated_to_human_reply",
    ):
        variant = apply_controlled_flip(base, transform)
        result = check_controlled_flip(base, variant, policy)
        assert result["passed"], (transform, result)
        assert result["collateral"] == []


def test_metamorphic_count_from_1200_bases() -> None:
    bases = generate_oracle_corpus(count=1200, seed=121190100)
    variants = generate_metamorphic(bases, variants_per_base=4)
    assert len(bases) == 1200
    assert len(variants) == 4800
    assert len(bases) + len(variants) == 6000
    assert sum(1 for item in variants if item.variant_kind == "invariant") == 3600
    assert sum(1 for item in variants if item.variant_kind == "controlled_flip") == 1200
