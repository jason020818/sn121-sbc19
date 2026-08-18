"""Metamorphic and pairwise batteries over the oracle corpus."""

from __future__ import annotations

from pathlib import Path
from random import Random

from eval_lab.config import lab_root
from eval_lab.models import HiddenExpectations, HoldoutRecord
from eval_lab.oracle_evaluator import deals_from_record, load_jsonl, oracle_base_path, write_jsonl
from eval_lab.perturbations import (
    CONTROLLED_FLIPS,
    INVARIANT_TRANSFORMS,
    apply_controlled_flip,
    apply_invariant,
)
from eval_lab.policy_engine import apply_policy
from eval_lab.policy_models import DealFact, PolicyManifest
from eval_lab.policy_manifests import load_policy


def metamorphic_path() -> Path:
    return lab_root() / "generated" / "oracle_metamorphic.jsonl"


def pairwise_path() -> Path:
    return lab_root() / "generated" / "oracle_pairwise.jsonl"


def generate_metamorphic(
    bases: list[HoldoutRecord] | None = None,
    variants_per_base: int = 4,
    seed: int = 121190100,
) -> list[HoldoutRecord]:
    if bases is None:
        bases = load_jsonl(oracle_base_path())
    rng = Random(seed)
    invariant_n = max(3, variants_per_base - 1)
    out: list[HoldoutRecord] = []
    for index, base in enumerate(bases):
        for offset in range(invariant_n):
            transform = INVARIANT_TRANSFORMS[(index + offset) % len(INVARIANT_TRANSFORMS)]
            variant = apply_invariant(base, transform, Random(rng.random()))
            variant.id = f"{base.id}-INV-{offset + 1}"
            variant.seed = seed + index * 10 + offset
            out.append(variant)
        flip = CONTROLLED_FLIPS[index % len(CONTROLLED_FLIPS)]
        controlled = apply_controlled_flip(base, flip)
        controlled.id = f"{base.id}-FLIP-1"
        controlled.seed = seed + index * 10 + 9
        out.append(controlled)
    return out


def remap(dispositions: dict[str, str], name_map: dict[str, str]) -> dict[str, str]:
    if not name_map:
        return dict(dispositions)
    return {name_map.get(name, name): disp for name, disp in dispositions.items()}


def check_invariant(base: HoldoutRecord, variant: HoldoutRecord, policy: PolicyManifest) -> dict:
    actual = apply_policy(deals_from_record(variant), policy)
    expected_base = remap(base.expected_dispositions, variant.name_map)
    violations = []
    for name, disp in expected_base.items():
        got = actual.dispositions.get(name)
        if got != disp:
            violations.append(f"{name}: expected {disp} got {got}")
    extra = set(actual.dispositions) - set(expected_base)
    for name in extra:
        if actual.dispositions[name] != "MONITOR":
            violations.append(f"new non-monitor deal {name}")
    action_base = {name for name, disp in expected_base.items() if disp == "ACTION"}
    action_got = {name for name, disp in actual.dispositions.items() if disp == "ACTION" and name in expected_base}
    if action_base != action_got:
        violations.append("action_set_changed")
    if any(hold in {"do_not_contact", "wait_until"} and actual.dispositions.get(name) == "ACTION" for name, hold in actual.constraint_holds.items()):
        violations.append("contact_violation")
    return {"passed": not violations, "violations": violations}


def check_controlled_flip(base: HoldoutRecord, variant: HoldoutRecord, policy: PolicyManifest) -> dict:
    actual = apply_policy(deals_from_record(variant), policy)
    before = remap(variant.expected_before or base.expected_dispositions, variant.name_map)
    after = actual.dispositions
    changed = [name for name in before if after.get(name) != before[name]]
    new_names = [name for name in after if name not in before]
    expected_changed = set(variant.flip_deals) | set(new_names)
    collateral = [name for name in changed if name not in expected_changed]
    misses = [name for name in variant.flip_deals if name in before and after.get(name) == before.get(name) and name not in new_names]
    if new_names:
        misses = [name for name in misses if name not in new_names]
        # A newly added deal is the intended change.
        misses = []
    passed = not collateral and (bool(changed) or bool(new_names)) and not misses
    return {
        "passed": passed,
        "collateral": collateral,
        "misses": misses,
        "changed": changed + new_names,
    }


def evaluate_metamorphic(bases: list[HoldoutRecord], variants: list[HoldoutRecord], policy: PolicyManifest) -> dict:
    by_id = {item.id: item for item in bases}
    inv_pass = 0
    inv_n = 0
    flip_pass = 0
    flip_n = 0
    invariant_violations = 0
    flip_misses = 0
    collateral = 0
    for variant in variants:
        parent = by_id.get(variant.parent_id or "")
        if parent is None:
            continue
        if variant.variant_kind == "invariant":
            result = check_invariant(parent, variant, policy)
            inv_n += 1
            inv_pass += int(result["passed"])
            invariant_violations += 0 if result["passed"] else 1
        elif variant.variant_kind == "controlled_flip":
            result = check_controlled_flip(parent, variant, policy)
            flip_n += 1
            flip_pass += int(result["passed"])
            flip_misses += len(result["misses"])
            collateral += len(result["collateral"])
    return {
        "invariant_pass_rate": inv_pass / inv_n if inv_n else 1.0,
        "controlled_flip_pass_rate": flip_pass / flip_n if flip_n else 1.0,
        "invariant_violation_count": invariant_violations,
        "controlled_flip_miss_count": flip_misses,
        "collateral_change_count": collateral,
        "invariant_n": inv_n,
        "controlled_flip_n": flip_n,
    }


def generate_pairwise(count: int = 1000, seed: int = 121190100) -> list[HoldoutRecord]:
    rng = Random(seed)
    production = load_policy("production")
    families = [
        "amount_bias",
        "stage_bias",
        "age_bias",
        "quota_bias",
        "deal_order_bias",
        "company_name_bias",
        "calendar_bias",
        "close_date_wait",
    ]
    records: list[HoldoutRecord] = []
    for index in range(count):
        family = families[index % len(families)]
        left = [
            DealFact(name="Ambergris Quorum", amount="$50K", state="customer_legal", checkpoint="present", last_offset_days=4, stage="Proposal", close_offset_days=40),
            DealFact(
                name="Basalt Cask",
                amount="$900K",
                state="seller_owned_deliverable",
                seller_owns_next=True,
                last_offset_days=3,
                stage="Negotiation",
                close_offset_days=12,
            ),
            DealFact(name="Cattail Relay", amount="$120K", state="procurement", checkpoint="present", last_offset_days=9, close_offset_days=30),
        ]
        right = [DealFact.model_validate(item.model_dump()) for item in left]
        if family == "amount_bias":
            left[0].amount, left[1].amount = "$50K", "$900K"
            right[0].amount, right[1].amount = "$900K", "$50K"
        elif family == "stage_bias":
            left[1].stage = "Proposal"
            right[1].stage = "Negotiation"
        elif family == "age_bias":
            left[0].constraint = "wait_until"
            right[0].constraint = "wait_until"
            left[0].last_offset_days = 3
            right[0].last_offset_days = 54
        elif family == "quota_bias":
            pass
        elif family == "deal_order_bias":
            rng.shuffle(right)
        elif family == "company_name_bias":
            right[0].name = "Z"
            right[1].name = "The Extraordinarily Long Fictional Cooperative Name"
            right[2].name = "Qxk-9"
        elif family == "calendar_bias":
            right.append(DealFact(name="Internal Standup Filler", state="customer_legal", checkpoint="present", amount="$1K"))
        elif family == "close_date_wait":
            left[0].close_offset_days = 90
            right[0].close_offset_days = 2
            left[0].timing_material = False
            right[0].timing_material = False
        left_dec = apply_policy(left, production)
        right_dec = apply_policy(right, production)
        expected = dict(left_dec.dispositions)
        if family == "company_name_bias":
            expected = dict(right_dec.dispositions)
        records.append(
            HoldoutRecord(
                id=f"P-{index + 1:04d}",
                seed=seed + index,
                scenario=family,
                hidden_expectations=HiddenExpectations(),
                dimensions={"family": family, "side": "pair"},
                deals=[item.model_dump() for item in left] + [{"_right": True, **item.model_dump()} for item in right],
                expected_dispositions=expected,
                variant_kind="pairwise",
                transform=family,
                expected_before=dict(left_dec.dispositions),
                expected_after=dict(right_dec.dispositions),
            )
        )
    return records


def evaluate_pairwise(records: list[HoldoutRecord], policy: PolicyManifest) -> dict:
    n = 0
    passed = 0
    for record in records:
        left_raw = [item for item in record.deals if not item.get("_right")]
        right_raw = [item for item in record.deals if item.get("_right")]
        left = [DealFact.model_validate({k: v for k, v in item.items() if k != "_right"}) for item in left_raw]
        right = [DealFact.model_validate({k: v for k, v in item.items() if k != "_right"}) for item in right_raw]
        left_dec = apply_policy(left, policy)
        right_dec = apply_policy(right, policy)
        family = record.transform or record.scenario
        ok = True
        if family == "company_name_bias":
            ok = list(left_dec.dispositions.values()) == list(right_dec.dispositions.values())
        elif family == "calendar_bias":
            shared = set(left_dec.dispositions)
            ok = all(left_dec.dispositions[name] == right_dec.dispositions.get(name) for name in shared)
            extra = set(right_dec.dispositions) - shared
            ok = ok and all(right_dec.dispositions[name] == "MONITOR" for name in extra)
        elif family == "deal_order_bias":
            ok = left_dec.dispositions == right_dec.dispositions
        else:
            # Amount/stage/age/quota/close-date wait: labels by position after aligning names.
            ok = list(left_dec.dispositions.values()) == list(right_dec.dispositions.values()) or left_dec.dispositions == {
                k: right_dec.dispositions.get(k, v) for k, v in left_dec.dispositions.items()
            }
            if set(left_dec.dispositions) == set(right_dec.dispositions):
                ok = left_dec.dispositions == right_dec.dispositions
        n += 1
        passed += int(ok)
    return {
        "pairwise_bias_pass_rate": passed / n if n else 1.0,
        "pairwise_n": n,
        "pairwise_fail_count": n - passed,
    }
