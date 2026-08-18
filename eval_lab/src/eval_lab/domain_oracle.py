"""Independent domain oracle. Expected labels are generator contracts, not policy output.

This module must not import candidate/production policy loaders or apply_policy.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path
from random import Random

from eval_lab.config import lab_root
from eval_lab.holdout_generator import COMPANIES
from eval_lab.models import HiddenExpectations, HoldoutRecord
from eval_lab.policy_models import DealFact, Disposition

WAIT_PROCESSES = ["customer_legal", "procurement", "board", "signature", "evaluation"]
INVARIANT_TRANSFORMS = [
    "rename_entities",
    "reorder_rows",
    "swap_amounts",
    "quota_context",
    "add_monitor_deal",
    "age_change",
    "stage_swap",
    "name_shape",
]


def domain_oracle_path() -> Path:
    return lab_root() / "generated" / "domain_oracle.jsonl"


def domain_metamorphic_path() -> Path:
    return lab_root() / "generated" / "domain_metamorphic.jsonl"


def domain_pairwise_path() -> Path:
    return lab_root() / "generated" / "domain_pairwise.jsonl"


def domain_label(deal: DealFact) -> tuple[Disposition, str]:
    """Independent sales-ops contract. Not derived from any candidate engine."""
    if deal.meeting_today:
        return "MEETING", "todays_customer_meeting"
    if deal.decision_blocking_record_problem:
        return "RECORD", "decision_blocking_record"
    if not deal.constraint_expired and deal.constraint in {"do_not_contact", "wait_until"}:
        return "MONITOR", "explicit_contact_wait"
    if (
        deal.seller_deliverable_due
        or deal.seller_owns_next
        or deal.state
        in {
            "seller_owned_deliverable",
            "seller_answer_due",
            "schedule_needed_interaction",
            "correct_operational_blocker",
        }
    ):
        return "ACTION", "seller_owned_due_move"
    if deal.state == "champion_left" and not deal.owner_named:
        return "ACTION", "champion_left_identify_owner"
    if deal.state in {"unknown_owner", "unknown_decision_owner"} and deal.owner_identification_needed_now:
        return "ACTION", "unknown_owner_needed_now"
    if (
        deal.timing_material
        and deal.checkpoint in {"missing", "passed"}
        and deal.uncertainty_reduction
        and deal.state in WAIT_PROCESSES + ["explicit_wait_date", "no_checkpoint", "missed_checkpoint"]
    ):
        return "ACTION", "external_wait_three_part_escalation"
    if deal.state in WAIT_PROCESSES + ["explicit_wait_date", "verbal_paperwork", "future_meeting", "newly_qualified"]:
        return "MONITOR", "credible_customer_owned_wait"
    return "MONITOR", "default_monitor_non_trigger"


def _pack(deals: list[DealFact], case_id: str, seed: int, family: str, extra: dict | None = None) -> HoldoutRecord:
    expected = {}
    rules = {}
    for deal in deals:
        disp, rule = domain_label(deal)
        expected[deal.name] = disp
        rules[deal.name] = rule
    dims = {"family": family, **(extra or {})}
    return HoldoutRecord(
        id=case_id,
        seed=seed,
        scenario=f"family={family}",
        hidden_expectations=HiddenExpectations(
            allowed_action_deals=[n for n, d in expected.items() if d == "ACTION"],
            required_monitor_deals=[n for n, d in expected.items() if d == "MONITOR"],
            meeting_deals=[n for n, d in expected.items() if d == "MEETING"],
            record_only_deals=[n for n, d in expected.items() if d == "RECORD"],
            explicit_constraints=[f"{d.name}:{d.constraint}" for d in deals if d.constraint and not d.constraint_expired],
            source_entities=[d.name for d in deals],
        ),
        dimensions=dims,
        deals=[d.model_dump() for d in deals],
        expected_dispositions=expected,
        oracle_rules=rules,
    )


def _name(rng: Random, index: int, suffix: str = "") -> str:
    base = COMPANIES[index % len(COMPANIES)]
    return f"{base} {index:04d}{suffix}"


def generate_wait_boundary(rng: Random, start: int) -> list[HoldoutRecord]:
    records = []
    combos = list(
        product(
            [True, False],
            ["present", "missing", "passed"],
            [True, False],
            WAIT_PROCESSES,
            [True, False],
            ["$50K", "$900K"],
        )
    )
    for offset, (timing, checkpoint, uncertainty, process, close_near, amount) in enumerate(combos):
        idx = start + offset
        close = 3 if close_near else 60
        state = process if checkpoint != "passed" else "missed_checkpoint"
        if checkpoint == "missing":
            state = "no_checkpoint"
        deal = DealFact(
            name=_name(rng, idx, "-W"),
            amount=amount,
            state=state,
            timing_material=timing,
            checkpoint=checkpoint,  # type: ignore[arg-type]
            uncertainty_reduction=uncertainty,
            close_offset_days=close,
            stage="Negotiation" if close_near else "Proposal",
        )
        records.append(
            _pack(
                [deal],
                f"D-WAIT-{offset + 1:04d}",
                121190200 + idx,
                "external_wait",
                {
                    "timing_near": timing,
                    "checkpoint": checkpoint,
                    "uncertainty": uncertainty,
                    "process": process,
                    "close_near": close_near,
                    "amount": amount,
                },
            )
        )
    # Repeat the matrix until at least 500.
    needed = 500 - len(records)
    extra = []
    for i in range(max(0, needed)):
        src = records[i % len(records)]
        cloned = HoldoutRecord.model_validate(src.model_dump())
        cloned.id = f"D-WAIT-R{i + 1:04d}"
        cloned.seed = src.seed + 10_000 + i
        deal = DealFact.model_validate(cloned.deals[0])
        deal.name = _name(rng, start + 10_000 + i, "-WR")
        cloned.deals = [deal.model_dump()]
        cloned.expected_dispositions = {deal.name: next(iter(src.expected_dispositions.values()))}
        cloned.oracle_rules = {deal.name: next(iter(src.oracle_rules.values()))}
        extra.append(cloned)
    return records + extra


def generate_seller_matrix(rng: Random, start: int) -> list[HoldoutRecord]:
    specs = [
        ("seller_owned_deliverable", True, False, False, False, False),
        ("seller_answer_due", True, False, False, False, False),
        ("schedule_needed_interaction", True, False, False, False, False),
        ("unknown_owner", False, True, True, False, False),
        ("unknown_owner", False, False, False, False, False),
        ("correct_operational_blocker", True, False, False, False, False),
        ("seller_owned_deliverable", True, False, False, True, False),
        ("champion_left", False, False, False, False, True),
        ("customer_legal", False, False, False, True, False),
        ("seller_answer_due", False, False, False, False, False),
    ]
    records = []
    n = 0
    while len(records) < 400:
        state, owns, needed, unnamed, meeting, champion = specs[n % len(specs)]
        idx = start + n
        deal = DealFact(
            name=_name(rng, idx, "-S"),
            state=state,
            seller_owns_next=owns,
            seller_deliverable_due=owns and state == "seller_owned_deliverable",
            owner_identification_needed_now=needed,
            owner_named=not unnamed and not champion,
            meeting_today=meeting,
            checkpoint="present",
        )
        records.append(_pack([deal], f"D-SELL-{n + 1:04d}", 121190200 + idx, "seller_owned", {"state": state}))
        n += 1
    return records


def generate_record_matrix(rng: Random, start: int) -> list[HoldoutRecord]:
    kinds = [
        ("human_correction", False),
        ("contradiction", True),
        ("missing_amount", False),
        ("missing_contact", True),
        ("missing_contact", False),
        ("stale_automated", False),
        ("conflicting_close", True),
    ]
    records = []
    n = 0
    while len(records) < 300:
        kind, blocking = kinds[n % len(kinds)]
        idx = start + n
        deal = DealFact(
            name=_name(rng, idx, "-R"),
            state="customer_legal",
            record_kind=kind,
            decision_blocking_record_problem=blocking,
            checkpoint="present",
        )
        records.append(_pack([deal], f"D-REC-{n + 1:04d}", 121190200 + idx, "record", {"record_kind": kind}))
        n += 1
    return records


def generate_communication_matrix(rng: Random, start: int) -> list[HoldoutRecord]:
    specs = [
        ("do_not_contact", False, "seller_owned_deliverable", True),
        ("do_not_contact", True, "seller_owned_deliverable", True),
        ("wait_until", False, "seller_answer_due", True),
        ("wait_until", True, "seller_answer_due", True),
        ("email_only", False, "seller_owned_deliverable", True),
        ("call_requested", False, "schedule_needed_interaction", True),
        ("no_channel", False, "customer_legal", False),
        ("second_hand", False, "customer_legal", False),
    ]
    records = []
    n = 0
    while len(records) < 300:
        constraint, expired, state, owns = specs[n % len(specs)]
        idx = start + n
        deal = DealFact(
            name=_name(rng, idx, "-C"),
            state=state,
            seller_owns_next=owns,
            constraint=constraint if constraint not in {"no_channel", "second_hand"} else None,
            constraint_expired=expired,
            channel="email" if constraint == "email_only" else ("call" if constraint == "call_requested" else None),
            checkpoint="present",
        )
        records.append(
            _pack(
                [deal],
                f"D-COM-{n + 1:04d}",
                121190200 + idx,
                "communication",
                {"constraint": constraint, "expired": expired},
            )
        )
        n += 1
    return records


def generate_mixed_books(rng: Random, start: int, count: int) -> list[HoldoutRecord]:
    records = []
    for n in range(count):
        idx = start + n
        size = [3, 5, 8, 12][n % 4]
        deals = []
        for i in range(size):
            kind = i % 5
            name = _name(rng, idx * 20 + i, f"-M{i}")
            if kind == 0:
                deals.append(
                    DealFact(
                        name=name,
                        state="seller_owned_deliverable",
                        seller_owns_next=True,
                        seller_deliverable_due=True,
                    )
                )
            elif kind == 1:
                deals.append(DealFact(name=name, state="customer_legal", checkpoint="present", amount="$120K"))
            elif kind == 2:
                deals.append(
                    DealFact(
                        name=name,
                        state="no_checkpoint",
                        checkpoint="missing",
                        timing_material=True,
                        uncertainty_reduction=True,
                    )
                )
            elif kind == 3:
                deals.append(DealFact(name=name, meeting_today=True, state="future_meeting"))
            else:
                deals.append(
                    DealFact(
                        name=name,
                        state="unknown_owner",
                        owner_named=False,
                        owner_identification_needed_now=True,
                    )
                )
        records.append(_pack(deals, f"D-MIX-{n + 1:04d}", 121190200 + idx, "mixed", {"book_size": size}))
    return records


def generate_domain_oracle(count: int = 3000, seed: int = 121190200) -> list[HoldoutRecord]:
    rng = Random(seed)
    wait = generate_wait_boundary(rng, 0)
    seller = generate_seller_matrix(rng, 20_000)
    record = generate_record_matrix(rng, 30_000)
    comm = generate_communication_matrix(rng, 40_000)
    records = wait + seller + record + comm
    if len(records) < count:
        records.extend(generate_mixed_books(rng, 50_000, count - len(records)))
    elif len(records) > count:
        records = records[:count]
    for item in records:
        if not item.expected_dispositions:
            raise RuntimeError("domain oracle produced a case without expected labels")
    return records


def apply_invariant_domain(record: HoldoutRecord, transform: str, rng: Random) -> HoldoutRecord:
    out = HoldoutRecord.model_validate(record.model_dump())
    out.variant_kind = "invariant"
    out.parent_id = record.id
    out.transform = transform
    deals = [DealFact.model_validate(item) for item in out.deals]
    if transform == "rename_entities":
        mapping = {}
        for deal in deals:
            new = f"{deal.name} Partners"
            mapping[deal.name] = new
            deal.name = new
        out.name_map = mapping
        out.expected_dispositions = {mapping[k]: v for k, v in record.expected_dispositions.items()}
        out.oracle_rules = {mapping.get(k, k): v for k, v in record.oracle_rules.items()}
        out.deals = [d.model_dump() for d in deals]
        return out
    if transform == "reorder_rows":
        rng.shuffle(deals)
    elif transform == "swap_amounts" and len(deals) >= 2:
        deals[0].amount, deals[-1].amount = deals[-1].amount, deals[0].amount
    elif transform == "quota_context":
        out.dimensions = dict(out.dimensions)
        out.dimensions["quota"] = "95%"
    elif transform == "add_monitor_deal":
        extra = DealFact(name=f"FillerMonitor-{record.id}", state="customer_legal", checkpoint="present", amount="$11K")
        deals.append(extra)
        disp, rule = domain_label(extra)
        out.expected_dispositions = dict(record.expected_dispositions)
        out.expected_dispositions[extra.name] = disp
        out.oracle_rules = dict(record.oracle_rules)
        out.oracle_rules[extra.name] = rule
        out.deals = [d.model_dump() for d in deals]
        return out
    elif transform == "age_change":
        for deal in deals:
            deal.last_offset_days += 17
    elif transform == "stage_swap":
        for deal in deals:
            deal.stage = "Discovery" if deal.stage != "Discovery" else "Negotiation"
    elif transform == "name_shape":
        mapping = {deal.name: deal.name.replace(" ", "") + " LLC" for deal in deals}
        for deal in deals:
            deal.name = mapping[deal.name]
        out.name_map = mapping
        out.expected_dispositions = {mapping[k]: v for k, v in record.expected_dispositions.items()}
        out.oracle_rules = {mapping.get(k, k): v for k, v in record.oracle_rules.items()}
        out.deals = [d.model_dump() for d in deals]
        return out
    out.deals = [d.model_dump() for d in deals]
    return out


def apply_controlled_flip_domain(record: HoldoutRecord, kind: str) -> HoldoutRecord:
    """Apply the requested mutation. If the base cannot support it, synthesize a valid target."""
    out = HoldoutRecord.model_validate(record.model_dump())
    out.variant_kind = "controlled_flip"
    out.parent_id = record.id
    out.transform = kind
    out.mutation_kind = kind
    deals = [DealFact.model_validate(item) for item in out.deals]
    before = {deal.name: domain_label(deal)[0] for deal in deals}

    def _relabel() -> dict[str, str]:
        return {deal.name: domain_label(deal)[0] for deal in deals}

    if kind == "wait_to_seller_deliverable":
        target = next(
            (
                d
                for d in deals
                if before.get(d.name) == "MONITOR"
                and not d.meeting_today
                and not d.decision_blocking_record_problem
            ),
            None,
        )
        if target is None:
            target = DealFact(name=f"WaitSeed-{record.id}", state="customer_legal", checkpoint="present")
            deals.append(target)
            before[target.name] = domain_label(target)[0]
        target.state = "seller_owned_deliverable"
        target.seller_owns_next = True
        target.seller_deliverable_due = True
        target.constraint = None
        target.constraint_expired = True
        target.meeting_today = False
        target.decision_blocking_record_problem = False
    elif kind == "checkpoint_passed":
        target = next(
            (
                d
                for d in deals
                if before.get(d.name) == "MONITOR"
                and not d.meeting_today
                and d.constraint not in {"do_not_contact", "wait_until"}
            ),
            None,
        )
        if target is None:
            target = DealFact(name=f"WaitSeed-{record.id}", state="customer_legal", checkpoint="present")
            deals.append(target)
            before[target.name] = domain_label(target)[0]
        target.timing_material = True
        target.checkpoint = "passed"
        target.uncertainty_reduction = True
        target.state = "missed_checkpoint"
        target.meeting_today = False
        target.decision_blocking_record_problem = False
        target.constraint = None
    elif kind == "add_meeting_today":
        target = next((d for d in deals if before.get(d.name) in {"ACTION", "MONITOR"} and not d.meeting_today), None)
        if target is None:
            target = DealFact(name=f"MeetSeed-{record.id}", state="customer_legal", checkpoint="present")
            deals.append(target)
            before[target.name] = domain_label(target)[0]
        target.meeting_today = True
        target.decision_blocking_record_problem = False
        target.constraint = None
    elif kind == "add_do_not_contact":
        target = next((d for d in deals if before.get(d.name) == "ACTION" and not d.meeting_today), None)
        if target is None:
            target = DealFact(
                name=f"ActionSeed-{record.id}",
                state="seller_owned_deliverable",
                seller_owns_next=True,
                seller_deliverable_due=True,
            )
            deals.append(target)
            before[target.name] = domain_label(target)[0]
        target.constraint = "do_not_contact"
        target.constraint_expired = False
        target.meeting_today = False
    else:
        raise ValueError(f"Unknown controlled-flip kind: {kind}")

    after = _relabel()
    if after.get(target.name) == before.get(target.name):
        raise RuntimeError(f"controlled flip {kind} did not change {target.name}")
    out.deals = [item.model_dump() for item in deals]
    out.expected_before = before
    out.expected_after = after
    out.expected_dispositions = after
    out.oracle_rules = {deal.name: domain_label(deal)[1] for deal in deals}
    out.flip_deals = [target.name]
    out.target_deal = target.name
    out.target_before = before[target.name]
    out.target_after = after[target.name]
    out.allowed_changed_deals = [target.name]
    return out


def generate_domain_metamorphic(bases: list[HoldoutRecord], variants_per_base: int = 4, seed: int = 121190200) -> list[HoldoutRecord]:
    rng = Random(seed)
    invariant_n = max(3, variants_per_base - 1)
    flips = ["wait_to_seller_deliverable", "checkpoint_passed", "add_meeting_today", "add_do_not_contact"]
    out = []
    for index, base in enumerate(bases):
        for offset in range(invariant_n):
            transform = INVARIANT_TRANSFORMS[(index + offset) % len(INVARIANT_TRANSFORMS)]
            variant = apply_invariant_domain(base, transform, Random(rng.randint(0, 10**9)))
            variant.id = f"{base.id}-INV-{offset + 1}"
            out.append(variant)
        controlled = apply_controlled_flip_domain(base, flips[index % len(flips)])
        controlled.id = f"{base.id}-FLIP-1"
        out.append(controlled)
    return out


def generate_domain_pairwise(count: int = 1000, seed: int = 121190200) -> list[HoldoutRecord]:
    rng = Random(seed)
    families = ["amount_bias", "stage_bias", "age_bias", "quota_bias", "deal_order_bias", "company_name_bias", "add_monitor"]
    records = []
    for index in range(count):
        family = families[index % len(families)]
        left = [
            DealFact(name="Ambergris Quorum", amount="$50K", state="customer_legal", checkpoint="present"),
            DealFact(
                name="Basalt Cask",
                amount="$900K",
                state="seller_owned_deliverable",
                seller_owns_next=True,
                seller_deliverable_due=True,
                stage="Negotiation",
            ),
        ]
        right = [DealFact.model_validate(item.model_dump()) for item in left]
        if family == "amount_bias":
            right[0].amount, right[1].amount = right[1].amount, right[0].amount
        elif family == "stage_bias":
            right[1].stage = "Proposal" if right[1].stage != "Proposal" else "Negotiation"
        elif family == "age_bias":
            right[0].last_offset_days = 40
        elif family == "quota_bias":
            pass
        elif family == "deal_order_bias":
            rng.shuffle(right)
        elif family == "company_name_bias":
            right[0].name = "Zed Short"
            right[1].name = "The Extraordinarily Long Fictional Cooperative"
        elif family == "add_monitor":
            right.append(DealFact(name="Internal Standup Filler", state="customer_legal", checkpoint="present", amount="$1K"))
        left_exp = {d.name: domain_label(d)[0] for d in left}
        right_exp = {d.name: domain_label(d)[0] for d in right}
        records.append(
            HoldoutRecord(
                id=f"DP-{index + 1:04d}",
                seed=seed + index,
                scenario=family,
                hidden_expectations=HiddenExpectations(),
                dimensions={"family": "bias", "bias_kind": family},
                deals=[d.model_dump() for d in left] + [{"_right": True, **d.model_dump()} for d in right],
                expected_dispositions=left_exp,
                expected_before=left_exp,
                expected_after=right_exp,
                variant_kind="pairwise",
                transform=family,
                oracle_rules={d.name: domain_label(d)[1] for d in left},
            )
        )
    return records


def write_jsonl(records: list[HoldoutRecord], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")
    return path


def load_jsonl(path: Path) -> list[HoldoutRecord]:
    return [HoldoutRecord.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
