"""Zero-cost oracle corpus and behavioral scoring. No model calls."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from random import Random

from eval_lab.config import lab_root
from eval_lab.models import HiddenExpectations, HoldoutRecord
from eval_lab.policy_engine import apply_policy
from eval_lab.policy_manifests import load_policy
from eval_lab.policy_models import DealFact, PolicyManifest
from eval_lab.holdout_generator import COMPANIES, PEOPLE

BOOK_SIZES = [5, 8, 12, 18, 30, 40, 60]
ACTION_COUNTS = [0, 1, 2, 3, 4, 6]
CALENDARS = ["none", "internal-only", "one-customer", "multi-customer", "imminent"]
OWNERSHIP = [
    "seller_owned_deliverable",
    "seller_answer_due",
    "customer_legal",
    "procurement",
    "board",
    "signature",
    "evaluation",
    "explicit_wait_date",
    "no_checkpoint",
    "missed_checkpoint",
    "future_meeting",
    "verbal_paperwork",
    "champion_left",
    "unknown_owner",
    "newly_qualified",
]
DATA = [
    "human_correction",
    "automated_touch",
    "stale_timestamp",
    "missing_next_step",
    "missing_contact",
    "missing_amount",
    "mixed_currency",
    "contradiction",
    "near_duplicate",
]
CONSTRAINTS = [
    "do_not_contact",
    "wait_until",
    "email_only",
    "call_requested",
    "no_channel",
    "second_hand",
]
COMMERCIAL = [
    "quarter_near",
    "quarter_far",
    "quota_pressure",
    "quota_none",
    "large_waiting_small_urgent",
    "late_low_early_high",
    "renewal",
    "new_logo",
    "no_amounts",
]


def oracle_base_path() -> Path:
    return lab_root() / "generated" / "oracle_base.jsonl"


def generate_oracle_corpus(count: int = 1200, seed: int = 121190100) -> list[HoldoutRecord]:
    rng = Random(seed)
    names = list(COMPANIES)
    people = list(PEOPLE)
    rng.shuffle(names)
    rng.shuffle(people)
    production = load_policy("production")
    records: list[HoldoutRecord] = []
    ni = 0
    pi = 0
    for index in range(count):
        book = BOOK_SIZES[index % len(BOOK_SIZES)]
        requested_actions = ACTION_COUNTS[index % len(ACTION_COUNTS)]
        n_action = requested_actions
        calendar = CALENDARS[index % len(CALENDARS)]
        ownership = OWNERSHIP[index % len(OWNERSHIP)]
        data = DATA[index % len(DATA)]
        constraint = CONSTRAINTS[index % len(CONSTRAINTS)]
        commercial = COMMERCIAL[index % len(COMMERCIAL)]
        wanted_meetings = {"none": 0, "internal-only": 0, "one-customer": 1, "multi-customer": 3, "imminent": 1}[
            calendar
        ]
        n_record = 1 if data in {"human_correction", "contradiction"} else 0
        n_meetings = min(wanted_meetings, max(0, book - n_record - (6 if n_action >= 6 else n_action)))
        n_action = min(max(n_action, 6) if n_action >= 6 else n_action, max(0, book - n_meetings - n_record))
        deals: list[DealFact] = []
        for i in range(book + (1 if data == "near_duplicate" else 0)):
            name = f"{names[ni % len(names)]} {index:04d}-{i:02d}"
            ni += 1
            contact = people[pi % len(people)]
            pi += 1
            deals.append(
                DealFact(
                    name=name if i < book else f"{names[(ni - 1) % len(names)]} Holdings {index:04d}",
                    amount=None if commercial == "no_amounts" else f"${40 + (i * 17) % 900}K",
                    stage=["Discovery", "Demo", "Proposal", "Negotiation"][i % 4],
                    close_offset_days=20 + i,
                    last_offset_days=2 + (i % 8),
                    contact=None if data == "missing_contact" and i == book - 1 else contact,
                    state="customer_legal",
                    checkpoint="present",
                )
            )
        cursor = 0
        for _ in range(n_meetings):
            deals[cursor].meeting_today = True
            deals[cursor].state = "future_meeting"
            cursor += 1
        action_states = [
            "seller_owned_deliverable",
            "seller_answer_due",
            "schedule_needed_interaction",
            "correct_operational_blocker",
            "champion_left",
            "unknown_owner",
        ]
        for j in range(n_action):
            deal = deals[cursor]
            deal.seller_owns_next = True
            deal.state = action_states[j % len(action_states)]
            if deal.state in {"champion_left", "unknown_owner"}:
                deal.owner_named = False
                deal.seller_owns_next = False
            cursor += 1
        if n_record and cursor < len(deals):
            deals[cursor].record_kind = "human_correction" if data == "human_correction" else "contradiction"
            cursor += 1
        featured = deals[min(cursor, len(deals) - 1)]
        if ownership in ACTION_STATES_SAFE():
            if featured.meeting_today or featured.record_kind:
                featured = next((d for d in deals if not d.meeting_today and not d.record_kind), featured)
            featured.state = ownership
            if ownership in {"seller_owned_deliverable", "seller_answer_due"}:
                featured.seller_owns_next = True
            if ownership in {"no_checkpoint", "missed_checkpoint"}:
                featured.timing_material = True
                featured.checkpoint = "passed" if ownership == "missed_checkpoint" else "missing"
                featured.uncertainty_reduction = True
                featured.seller_owns_next = False
            if ownership == "champion_left":
                featured.owner_named = False
                featured.seller_owns_next = False
        constraint_target = next((d for d in deals if not d.meeting_today and not d.seller_owns_next), deals[-1])
        if constraint in {"do_not_contact", "wait_until"}:
            constraint_target.constraint = constraint
            constraint_target.seller_owns_next = False
        elif constraint in {"email_only", "call_requested"}:
            constraint_target.constraint = constraint
            constraint_target.channel = "email" if constraint == "email_only" else "call"
        if commercial == "large_waiting_small_urgent":
            waiting = next((d for d in deals if not d.seller_owns_next and not d.meeting_today), None)
            urgent = next((d for d in deals if d.seller_owns_next), None)
            if waiting:
                waiting.amount = "$900K"
                waiting.state = "customer_legal"
            if urgent:
                urgent.amount = "$50K"
        decision = apply_policy(deals, production)
        expected = dict(decision.dispositions)
        hidden = HiddenExpectations(
            allowed_action_deals=[n for n, d in expected.items() if d == "ACTION"],
            required_monitor_deals=[n for n, d in expected.items() if d == "MONITOR"],
            meeting_deals=[n for n, d in expected.items() if d == "MEETING"],
            record_only_deals=[n for n, d in expected.items() if d == "RECORD"],
            explicit_constraints=[f"{d.name}:{d.constraint}" for d in deals if d.constraint],
            source_entities=[d.name for d in deals],
            source_people=[d.contact for d in deals if d.contact],
            source_amounts=[d.amount for d in deals if d.amount],
        )
        records.append(
            HoldoutRecord(
                id=f"O-{index + 1:04d}",
                seed=seed + index,
                scenario=_render(deals, calendar, commercial),
                hidden_expectations=hidden,
                dimensions={
                    "book_size": book,
                    "action_count": requested_actions,
                    "calendar": calendar,
                    "ownership": ownership,
                    "data": data,
                    "constraint": constraint,
                    "commercial": commercial,
                },
                deals=[d.model_dump() for d in deals],
                expected_dispositions=expected,
            )
        )
    return records


def ACTION_STATES_SAFE() -> set[str]:
    return set(OWNERSHIP)


def _render(deals: list[DealFact], calendar: str, commercial: str) -> str:
    lines = [f"Calendar={calendar} commercial={commercial}", "OPEN DEALS"]
    for deal in deals:
        lines.append(
            f"- {deal.name} | {deal.amount or 'amount omitted'} | {deal.state} | "
            f"meeting={deal.meeting_today} record={deal.record_kind} constraint={deal.constraint}"
        )
    return "\n".join(lines) + "\n"


def write_jsonl(records: list[HoldoutRecord], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")
    return path


def load_jsonl(path: Path) -> list[HoldoutRecord]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(HoldoutRecord.model_validate_json(line))
    return records


def deals_from_record(record: HoldoutRecord) -> list[DealFact]:
    return [DealFact.model_validate(item) for item in record.deals]


def score_decision(expected: dict[str, str], actual) -> dict:
    names = list(expected)
    correct = sum(1 for name in names if actual.dispositions.get(name) == expected[name])
    exp_actions = {name for name, disp in expected.items() if disp == "ACTION"}
    got_actions = set(actual.action_set)
    tp = len(exp_actions & got_actions)
    fp = len(got_actions - exp_actions)
    fn = len(exp_actions - got_actions)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 1.0

    def acc(label: str) -> float:
        exp = {name for name, disp in expected.items() if disp == label}
        got = {name for name, disp in actual.dispositions.items() if disp == label}
        union = exp | got
        if not union:
            return 1.0
        return len(exp & got) / len(union)

    constraint_ok = 1.0
    for name, disp in actual.dispositions.items():
        hold = actual.constraint_holds.get(name)
        if hold in {"do_not_contact", "wait_until"} and disp == "ACTION":
            constraint_ok = 0.0
    return {
        "disposition_accuracy": correct / len(names) if names else 1.0,
        "action_precision": precision,
        "action_recall": recall,
        "action_f1": f1,
        "meeting_accuracy": acc("MEETING"),
        "monitor_accuracy": acc("MONITOR"),
        "record_accuracy": acc("RECORD"),
        "constraint_accuracy": constraint_ok,
        "catastrophic_logic_failures": len(actual.catastrophic),
    }


def evaluate_oracle(records: list[HoldoutRecord], policy: PolicyManifest) -> dict:
    sums: Counter[str] = Counter()
    n = 0
    catastrophic = 0
    constraint_fail = 0
    for record in records:
        deals = deals_from_record(record)
        actual = apply_policy(deals, policy)
        metrics = score_decision(record.expected_dispositions, actual)
        for key, value in metrics.items():
            if key == "catastrophic_logic_failures":
                catastrophic += int(value)
            elif key == "constraint_accuracy":
                constraint_fail += 0 if value == 1.0 else 1
                sums[key] += value
            else:
                sums[key] += value
        n += 1
    means = {key: (sums[key] / n if n else 1.0) for key in sums}
    means["catastrophic_logic_failures"] = catastrophic
    means["constraint_fail_count"] = constraint_fail
    means["n"] = n
    return means


def coverage_summary(records: list[HoldoutRecord]) -> dict:
    keys = ["book_size", "action_count", "calendar", "ownership", "data", "constraint", "commercial"]
    out = {}
    for key in keys:
        counts = Counter(str(record.dimensions.get(key)) for record in records)
        out[key] = dict(counts)
        out[f"{key}_min"] = min(counts.values()) if counts else 0
    return out
