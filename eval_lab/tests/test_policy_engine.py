"""Deterministic policy engine tests."""

from eval_lab.policy_engine import apply_policy, classify_deal
from eval_lab.policy_manifests import load_policy
from eval_lab.policy_models import DealFact


def test_meeting_outranks_action() -> None:
    policy = load_policy("production")
    deal = DealFact(name="A", meeting_today=True, seller_owns_next=True, state="seller_owned_deliverable")
    assert classify_deal(deal, policy)[0] == "MEETING"


def test_record_outranks_action() -> None:
    policy = load_policy("production")
    deal = DealFact(name="A", record_kind="human_correction", seller_owns_next=True, state="seller_owned_deliverable")
    assert classify_deal(deal, policy)[0] == "RECORD"


def test_do_not_contact_blocks_action() -> None:
    policy = load_policy("production")
    deals = [
        DealFact(
            name="A",
            seller_owns_next=True,
            state="seller_owned_deliverable",
            constraint="do_not_contact",
        )
    ]
    decision = apply_policy(deals, policy)
    assert decision.dispositions["A"] == "MONITOR"
    assert "do_not_contact_action:A" not in decision.catastrophic


def test_amount_alone_is_not_action() -> None:
    policy = load_policy("production")
    deal = DealFact(name="A", amount="$900K", stage="Negotiation", last_offset_days=90, close_offset_days=1)
    assert classify_deal(deal, policy)[0] == "MONITOR"


def test_three_part_wait_escalation() -> None:
    policy = load_policy("production")
    waiting = DealFact(name="A", state="customer_legal", checkpoint="present")
    escalated = DealFact(
        name="B",
        state="missed_checkpoint",
        checkpoint="passed",
        timing_material=True,
        uncertainty_reduction=True,
    )
    decision = apply_policy([waiting, escalated], policy)
    assert decision.dispositions["A"] == "MONITOR"
    assert decision.dispositions["B"] == "ACTION"


def test_unknown_owner_is_action_when_unnamed() -> None:
    policy = load_policy("candidate-b")
    deal = DealFact(name="A", state="unknown_owner", owner_named=False)
    assert classify_deal(deal, policy)[0] == "ACTION"


def test_unique_dispositions() -> None:
    policy = load_policy("production")
    deals = [DealFact(name="A", seller_owns_next=True, state="seller_owned_deliverable"), DealFact(name="B")]
    decision = apply_policy(deals, policy)
    assert set(decision.dispositions) == {"A", "B"}
    assert decision.action_set == ["A"]
