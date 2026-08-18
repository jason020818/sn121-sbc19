"""Invariant and controlled-flip transformations over structured deal facts."""

from __future__ import annotations

from random import Random

from eval_lab.holdout_generator import COMPANIES, PEOPLE
from eval_lab.models import HoldoutRecord
from eval_lab.policy_engine import apply_policy
from eval_lab.policy_manifests import load_policy
from eval_lab.policy_models import DealFact

INVARIANT_TRANSFORMS = [
    "rename_entities",
    "reorder_rows",
    "scale_amounts",
    "swap_amounts",
    "add_monitor_deal",
    "quota_context",
    "nonmaterial_close_dates",
    "paraphrase",
    "reorder_notes",
    "name_shape",
    "drop_irrelevant_amounts",
    "mixed_currency",
]

CONTROLLED_FLIPS = [
    "wait_to_seller_deliverable",
    "checkpoint_passed",
    "add_meeting_today",
    "add_do_not_contact",
    "human_correction",
    "unnamed_to_named_owner",
    "automated_to_human_reply",
]


def clone_record(record: HoldoutRecord) -> HoldoutRecord:
    return HoldoutRecord.model_validate(record.model_dump())


def deals_of(record: HoldoutRecord) -> list[DealFact]:
    return [DealFact.model_validate(item) for item in record.deals]


def _refresh(record: HoldoutRecord, deals: list[DealFact], production=None) -> HoldoutRecord:
    policy = production or load_policy("production")
    decision = apply_policy(deals, policy)
    record.deals = [item.model_dump() for item in deals]
    record.expected_dispositions = dict(decision.dispositions)
    record.hidden_expectations.allowed_action_deals = list(decision.action_set)
    record.hidden_expectations.required_monitor_deals = list(decision.monitor_set)
    record.hidden_expectations.meeting_deals = list(decision.meeting_set)
    record.hidden_expectations.record_only_deals = list(decision.record_set)
    record.hidden_expectations.source_entities = [item.name for item in deals]
    record.hidden_expectations.source_people = [item.contact for item in deals if item.contact]
    record.hidden_expectations.source_amounts = [item.amount for item in deals if item.amount]
    record.scenario = record.scenario  # caller may rewrite
    return record


def apply_invariant(record: HoldoutRecord, transform: str, rng: Random) -> HoldoutRecord:
    out = clone_record(record)
    out.variant_kind = "invariant"
    out.parent_id = record.id
    out.transform = transform
    deals = deals_of(out)
    if transform == "rename_entities":
        mapping: dict[str, str] = {}
        used = set()
        extras = [f"{name} Partners" for name in COMPANIES] + [f"{name} Group" for name in COMPANIES]
        pool = [name for name in extras if name not in {d.name for d in deals}]
        rng.shuffle(pool)
        for deal in deals:
            new = pool.pop() if pool else f"{deal.name} Holdings"
            while new in used:
                new = f"{new} II"
            mapping[deal.name] = new
            used.add(new)
            deal.name = new
        people = list(PEOPLE)
        rng.shuffle(people)
        for index, deal in enumerate(deals):
            if deal.contact:
                deal.contact = people[index % len(people)]
        out.name_map = mapping
        out.expected_dispositions = {
            mapping.get(name, name): disp for name, disp in record.expected_dispositions.items()
        }
        out.deals = [item.model_dump() for item in deals]
        out.hidden_expectations.source_entities = [item.name for item in deals]
        out.hidden_expectations.allowed_action_deals = [
            mapping.get(name, name) for name in record.hidden_expectations.allowed_action_deals
        ]
        out.hidden_expectations.required_monitor_deals = [
            mapping.get(name, name) for name in record.hidden_expectations.required_monitor_deals
        ]
        out.hidden_expectations.meeting_deals = [
            mapping.get(name, name) for name in record.hidden_expectations.meeting_deals
        ]
        out.hidden_expectations.record_only_deals = [
            mapping.get(name, name) for name in record.hidden_expectations.record_only_deals
        ]
        out.scenario = "Renamed entities.\n" + out.scenario
        return out
    if transform == "reorder_rows":
        rng.shuffle(deals)
    elif transform == "scale_amounts":
        factor = rng.choice([2, 3, 5])
        for deal in deals:
            deal.amount = _scale(deal.amount, factor)
    elif transform == "swap_amounts":
        if len(deals) >= 2:
            deals[0].amount, deals[-1].amount = deals[-1].amount, deals[0].amount
    elif transform == "add_monitor_deal":
        deals.append(
            DealFact(
                name=f"FillerMonitor-{record.id}",
                amount="$12K",
                state="customer_legal",
                checkpoint="present",
            )
        )
    elif transform == "quota_context":
        out.dimensions = dict(out.dimensions)
        out.dimensions["quota"] = "95%" if out.dimensions.get("commercial") != "quota_pressure" else "38%"
    elif transform == "nonmaterial_close_dates":
        for deal in deals:
            if deal.state in {"customer_legal", "procurement", "board", "evaluation"} and not deal.seller_owns_next:
                deal.close_offset_days += rng.choice([-3, 4, 11])
    elif transform == "paraphrase":
        out.scenario = "Paraphrased notes. " + " ".join(reversed(out.scenario.splitlines()))
        out.deals = [item.model_dump() for item in deals]
        return out
    elif transform == "reorder_notes":
        lines = out.scenario.splitlines()
        rng.shuffle(lines)
        out.scenario = "\n".join(lines)
        out.deals = [item.model_dump() for item in deals]
        return out
    elif transform == "name_shape":
        mapping = {}
        for deal in deals:
            new = deal.name.replace(" ", "") + " LLC"
            mapping[deal.name] = new
            deal.name = new
        out.name_map = mapping
        out.expected_dispositions = {
            mapping.get(name, name): disp for name, disp in record.expected_dispositions.items()
        }
        out.deals = [item.model_dump() for item in deals]
        out.hidden_expectations.allowed_action_deals = [
            mapping.get(name, name) for name in record.hidden_expectations.allowed_action_deals
        ]
        out.hidden_expectations.required_monitor_deals = [
            mapping.get(name, name) for name in record.hidden_expectations.required_monitor_deals
        ]
        out.hidden_expectations.meeting_deals = [
            mapping.get(name, name) for name in record.hidden_expectations.meeting_deals
        ]
        out.hidden_expectations.record_only_deals = [
            mapping.get(name, name) for name in record.hidden_expectations.record_only_deals
        ]
        out.hidden_expectations.source_entities = [item.name for item in deals]
        return out
    elif transform == "drop_irrelevant_amounts":
        for deal in deals:
            if not deal.seller_owns_next and not deal.meeting_today:
                deal.amount = None
    elif transform == "mixed_currency":
        currencies = ["EUR ", "GBP ", "JPY "]
        for index, deal in enumerate(deals):
            if deal.amount and deal.amount.startswith("$"):
                deal.amount = currencies[index % 3] + deal.amount[1:]
    production = load_policy("production")
    if transform in {"add_monitor_deal"}:
        return _refresh(out, deals, production)
    out.deals = [item.model_dump() for item in deals]
    return out


def apply_controlled_flip(record: HoldoutRecord, transform: str) -> HoldoutRecord:
    out = clone_record(record)
    out.variant_kind = "controlled_flip"
    out.parent_id = record.id
    out.transform = transform
    out.expected_before = dict(record.expected_dispositions)
    deals = deals_of(out)
    production = load_policy("production")
    target = None
    if transform == "wait_to_seller_deliverable":
        target = next(
            (d for d in deals if out.expected_before.get(d.name) == "MONITOR" and not d.meeting_today and not d.record_kind),
            None,
        )
        if target:
            target.state = "seller_owned_deliverable"
            target.seller_owns_next = True
            target.constraint = None
    elif transform == "checkpoint_passed":
        target = next(
            (
                d
                for d in deals
                if out.expected_before.get(d.name) == "MONITOR"
                and not d.meeting_today
                and not d.record_kind
                and d.constraint not in {"do_not_contact", "wait_until"}
            ),
            None,
        )
        if target:
            target.timing_material = True
            target.checkpoint = "passed"
            target.uncertainty_reduction = True
            target.seller_owns_next = False
            target.state = "missed_checkpoint"
    elif transform == "add_meeting_today":
        target = next(
            (d for d in deals if out.expected_before.get(d.name) in {"ACTION", "MONITOR"} and not d.record_kind),
            None,
        )
        if target:
            target.meeting_today = True
    elif transform == "add_do_not_contact":
        target = next((d for d in deals if out.expected_before.get(d.name) == "ACTION" and not d.meeting_today), None)
        if target:
            target.constraint = "do_not_contact"
            target.seller_owns_next = False
    elif transform == "human_correction":
        target = next(
            (d for d in deals if out.expected_before.get(d.name) == "MONITOR" and not d.meeting_today),
            None,
        )
        if target:
            target.record_kind = "human_correction"
            target.decision_blocking_record_problem = True
    elif transform == "unnamed_to_named_owner":
        target = next(
            (
                d
                for d in deals
                if out.expected_before.get(d.name) == "ACTION"
                and d.state in {"unknown_owner", "champion_left"}
                and not d.owner_named
            ),
            None,
        )
        if target:
            target.owner_named = True
            target.state = "customer_legal"
            target.seller_owns_next = False
            target.checkpoint = "present"
    elif transform == "automated_to_human_reply":
        target = next((d for d in deals if out.expected_before.get(d.name) == "ACTION"), None)
        if target:
            target.state = "customer_legal"
            target.seller_owns_next = False
            target.checkpoint = "present"
            target.timing_material = False
            target.uncertainty_reduction = False
            target.meeting_today = False
    if target is None:
        # Fall back so every base still has a flip: add a seller-owned deal.
        target = DealFact(name="Keel Pavilion Extra", state="seller_owned_deliverable", seller_owns_next=True)
        deals.append(target)
        transform = "wait_to_seller_deliverable"
        out.transform = transform
    _refresh(out, deals, production)
    out.flip_deals = [target.name]
    out.expected_after = dict(out.expected_dispositions)
    return out


def _scale(amount: str | None, factor: int) -> str | None:
    if not amount:
        return amount
    digits = "".join(ch for ch in amount if ch.isdigit())
    if not digits:
        return amount
    scaled = int(digits) * factor
    prefix = "".join(ch for ch in amount if not ch.isdigit() and ch not in ",.")
    suffix = "K" if "K" in amount else ("M" if "M" in amount else "")
    return f"{prefix}{scaled}{suffix}"
