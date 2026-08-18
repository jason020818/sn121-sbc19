"""Compositional synthetic holdout generator.

Holdouts are built from general sales-ops dimensions. They are not derived by
copying public benchmark scenarios, company names, or grader answers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from random import Random

from eval_lab.config import lab_root
from eval_lab.models import HiddenExpectations, HoldoutRecord

BOOK_SIZES = [5, 8, 12, 18, 30, 40]
CALENDARS = ["none", "one_internal", "one_customer", "multi_customer", "imminent"]
ACTION_DENSITIES = [0, 1, 2, 3, 4]
OWNERSHIP_STATES = [
    "seller_owned_deliverable",
    "customer_legal_review",
    "procurement_review",
    "board_approval",
    "explicit_waiting_date",
    "no_dated_checkpoint",
    "missed_checkpoint",
    "newly_qualified",
    "scheduled_future_meeting",
    "verbal_paperwork_in_motion",
    "champion_left",
    "unknown_decision_owner",
]
DATA_QUALITY = [
    "stale_system_timestamp",
    "automated_workflow_vs_human",
    "explicit_human_correction",
    "missing_next_step",
    "contradictory_note_table",
    "missing_contact",
    "missing_amount",
    "mixed_currencies",
    "near_duplicate_names",
]
COMMUNICATION = [
    "do_not_contact_until_date",
    "email_only",
    "call_requested",
    "no_explicit_channel",
    "second_hand_information",
]
COMMERCIAL = [
    "quarter_end_near",
    "quarter_end_far",
    "quota_pressure",
    "small_urgent_vs_large_waiting",
    "renewal_vs_new_logo",
    "late_stage_low_vs_early_high",
]
EXTRA_REQUESTS = [
    "forecast_insufficient_assumptions",
    "none",
    "summary_requested",
    "risk_question",
]

COMPANIES = [
    "Quill Cooperative",
    "Emberwick Labs",
    "Nautilus Outfit",
    "Bramble Works",
    "Helix Bureau",
    "Cobblestone Atelier",
    "Ivory Foundry",
    "Juniper Guild",
    "Kite Collective",
    "Lumen Outfitters",
    "Moss Harbor",
    "Nimbus Kiln",
    "Orchard Relay",
    "Pebble Circuit",
    "Quartz Lantern",
    "Riven Compass",
    "Saffron Pier",
    "Tidal Loom",
    "Umber Pavilion",
    "Vellum Forge",
    "Wicker Beacon",
    "Yarrow Transit",
    "Zephyr Orchard",
    "Alder Quorum",
    "Boreal Cask",
    "Cinder Relay",
    "Drift Lantern",
    "Elmwood Spindle",
    "Fjord Archive",
    "Gable Mariner",
    "Hazel Circuit",
    "Inkwell Harbor",
    "Jasper Loom",
    "Keel Pavilion",
    "Larkspur Kiln",
    "Marrow Beacon",
    "Northwind Cask",
    "Oxbow Guild",
    "Pinecroft Atelier",
    "Quay Foundry",
    "Redfern Cooperative",
    "Saltwick Labs",
    "Thornless Outfit",
    "Upland Works",
    "Vesper Bureau",
    "Willowmist Collective",
    "Xylem Harbor",
    "Yellowdock Transit",
    "Zinc Orchard",
    "Ashen Quorum",
    "Briar Cask",
    "Caldera Relay",
    "Dusk Lantern",
    "Eider Spindle",
    "Flint Archive",
    "Granum Mariner",
    "Hollow Kiln",
    "Islet Circuit",
    "Junco Loom",
    "Kelp Pavilion",
    "Linden Beacon",
    "Mica Guild",
    "Nettle Atelier",
    "Oatgrass Foundry",
    "Plumose Cooperative",
    "Rookery Labs",
    "Silt Outfit",
    "Tarn Works",
    "Ulex Bureau",
    "Vireo Collective",
    "Weld Harbor",
    "Yew Transit",
    "Zostera Orchard",
    "Ambergris Quorum",
    "Basalt Cask",
    "Cattail Relay",
    "Dewpond Lantern",
    "Eyrie Spindle",
    "Fenland Archive",
    "Gorse Mariner",
]

PEOPLE = [
    "Ira Calder",
    "Noemi Voss",
    "Soren Pike",
    "Hana Quill",
    "Leif Bram",
    "Odette Marsh",
    "Yuri Kelp",
    "Tamsin Roe",
    "Nico Vale",
    "Esme Flint",
    "Rafi Dune",
    "Pilar Moss",
    "Jonah Reed",
    "Willa Frost",
    "Kaspar Holm",
    "Ines Birch",
    "Tobin Gale",
    "Mira Solace",
    "Edwin Lark",
    "Selene Quinn",
    "Hugo Nettle",
    "Freya Dusk",
    "Arlo Finch",
    "Cora Vellum",
    "Idris Thorn",
    "Maeve Quay",
    "Niels Amber",
    "Petra Linden",
    "Quentin Ash",
    "Rhea Gable",
    "Silas Wren",
    "Tova Keel",
    "Ulric Moss",
    "Vera Pike",
    "Wren Calder",
    "Yasmin Holm",
    "Zeke Birch",
    "Amina Roe",
    "Bram Voss",
    "Celia Dune",
    "Dorian Vale",
    "Elena Flint",
    "Felix Marsh",
    "Greta Quill",
    "Harun Bram",
    "Ivy Kelp",
    "Jules Reed",
    "Kira Frost",
    "Lars Gale",
    "Mina Lark",
]


@dataclass
class Deal:
    name: str
    amount: str
    stage: str
    close: str
    last_activity: str
    contact: str | None
    note: str
    state: str
    action: bool = False
    monitor: bool = False
    record_only: bool = False
    meeting: bool = False
    internal_meeting: bool = False
    constraint: str | None = None
    extras: dict = field(default_factory=dict)


def generated_dir() -> Path:
    path = lab_root() / "generated"
    path.mkdir(parents=True, exist_ok=True)
    return path


def holdouts_path() -> Path:
    return generated_dir() / "holdouts.jsonl"


def generate_holdouts(count: int = 60, seed: int = 1211901) -> list[HoldoutRecord]:
    rng = Random(seed)
    records: list[HoldoutRecord] = []
    used_companies = list(COMPANIES)
    rng.shuffle(used_companies)
    company_cursor = 0
    people = list(PEOPLE)
    rng.shuffle(people)
    person_cursor = 0

    def take_companies(n: int) -> list[str]:
        nonlocal company_cursor
        out = []
        for _ in range(n):
            out.append(used_companies[company_cursor % len(used_companies)])
            company_cursor += 1
        return out

    def take_people(n: int) -> list[str]:
        nonlocal person_cursor
        out = []
        for _ in range(n):
            out.append(people[person_cursor % len(people)])
            person_cursor += 1
        return out

    for index in range(count):
        book = BOOK_SIZES[index % len(BOOK_SIZES)]
        calendar = CALENDARS[index % len(CALENDARS)]
        density = ACTION_DENSITIES[index % len(ACTION_DENSITIES)]
        ownership = OWNERSHIP_STATES[index % len(OWNERSHIP_STATES)]
        quality = DATA_QUALITY[index % len(DATA_QUALITY)]
        communication = COMMUNICATION[index % len(COMMUNICATION)]
        commercial = COMMERCIAL[index % len(COMMERCIAL)]
        extra = EXTRA_REQUESTS[index % len(EXTRA_REQUESTS)]
        names = take_companies(book + (1 if quality == "near_duplicate_names" else 0))
        contacts = take_people(book)
        record = _build_record(
            rng=rng,
            index=index,
            seed=seed,
            book=book,
            calendar=calendar,
            density=density,
            ownership=ownership,
            quality=quality,
            communication=communication,
            commercial=commercial,
            extra=extra,
            names=names,
            contacts=contacts,
        )
        records.append(record)
    return records


def write_holdouts(records: list[HoldoutRecord], path: Path | None = None) -> Path:
    dest = path or holdouts_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")
    return dest


def load_holdouts(path: Path | None = None) -> list[HoldoutRecord]:
    dest = path or holdouts_path()
    if not dest.exists():
        raise FileNotFoundError(f"Holdout file not found: {dest}")
    records: list[HoldoutRecord] = []
    for line in dest.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(HoldoutRecord.model_validate_json(line))
    return records


def _build_record(
    rng: Random,
    index: int,
    seed: int,
    book: int,
    calendar: str,
    density: int,
    ownership: str,
    quality: str,
    communication: str,
    commercial: str,
    extra: str,
    names: list[str],
    contacts: list[str],
) -> HoldoutRecord:
    weekday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"][index % 5]
    month = ["January", "March", "May", "July", "September", "November"][index % 6]
    day = 3 + (index % 24)
    briefing_date = f"{weekday}, {month} {day}"
    close_month = ["January", "February", "March", "April", "May", "June"][index % 6]

    stages = ["Discovery", "Demo", "Proposal", "Negotiation", "Verbal", "Renewal"]
    deals: list[Deal] = []
    for i, name in enumerate(names[:book]):
        amount_n = 40 + ((seed + index * 17 + i * 13) % 860)
        currency = "$"
        if quality == "mixed_currencies" and i % 3 == 0:
            currency = "€" if i % 2 == 0 else "£"
        amount = f"{currency}{amount_n}K"
        stage = stages[i % len(stages)]
        close = f"{close_month} {10 + (i % 18)}"
        last = f"{month} {max(1, day - 2 - (i % 9))}"
        contact = contacts[i]
        state = OWNERSHIP_STATES[(i + index) % len(OWNERSHIP_STATES)]
        note = _state_note(state, contact, last)
        deals.append(
            Deal(
                name=name,
                amount=amount,
                stage=stage,
                close=close,
                last_activity=last,
                contact=contact,
                note=note,
                state=state,
            )
        )

    if quality == "near_duplicate_names" and len(names) > book:
        twin = names[book]
        base = deals[0]
        deals.append(
            Deal(
                name=twin,
                amount="€90K" if base.amount.startswith("$") else "$90K",
                stage="Discovery",
                close=base.close,
                last_activity=base.last_activity,
                contact=contacts[0],
                note="Separate legal entity; do not merge with similarly named account.",
                state="newly_qualified",
                monitor=True,
            )
        )

    _apply_density(deals, density, ownership)
    _apply_calendar(deals, calendar, rng)
    _apply_communication(deals, communication)
    _apply_quality(deals, quality)
    _apply_commercial(deals, commercial)

    allowed_actions = [d.name for d in deals if d.action]
    required_monitor = [d.name for d in deals if d.monitor]
    meeting_deals = [d.name for d in deals if d.meeting and not d.internal_meeting]
    record_only = [d.name for d in deals if d.record_only]
    constraints = [d.constraint for d in deals if d.constraint]
    source_entities = [d.name for d in deals]
    source_people = [d.contact for d in deals if d.contact]
    source_amounts = [d.amount for d in deals if d.amount and "missing" not in (d.extras.get("flags") or [])]

    scenario = _render_scenario(
        briefing_date=briefing_date,
        deals=deals,
        calendar=calendar,
        extra=extra,
        commercial=commercial,
        labeled_total=None,
    )
    return HoldoutRecord(
        id=f"H-{index + 1:04d}",
        seed=seed + index,
        scenario=scenario,
        hidden_expectations=HiddenExpectations(
            allowed_action_deals=allowed_actions,
            required_monitor_deals=required_monitor,
            meeting_deals=meeting_deals,
            record_only_deals=record_only,
            explicit_constraints=[c for c in constraints if c],
            source_entities=source_entities,
            source_people=source_people,
            source_amounts=source_amounts,
        ),
        dimensions={
            "book_size": book,
            "calendar": calendar,
            "action_density": density,
            "ownership": ownership,
            "data_quality": quality,
            "communication": communication,
            "commercial": commercial,
            "extra_request": extra,
        },
    )


def _state_note(state: str, contact: str, last: str) -> str:
    mapping = {
        "seller_owned_deliverable": f"Seller still owes {contact} a revised scope document.",
        "customer_legal_review": f"Contract is with their legal team since {last}; no seller deliverable.",
        "procurement_review": f"Procurement is evaluating pricing. Ball is not with the seller.",
        "board_approval": f"Commercial terms agreed; waiting on their board packet.",
        "explicit_waiting_date": f"{contact} asked the seller to wait until a dated checkpoint already on the calendar.",
        "no_dated_checkpoint": f"Proposal sent {last}. No return date was given.",
        "missed_checkpoint": f"They promised a decision last week and missed it. No new date exists.",
        "newly_qualified": "Qualified yesterday. Discovery is not yet scheduled.",
        "scheduled_future_meeting": f"Next conversation is already scheduled after today with {contact}.",
        "verbal_paperwork_in_motion": f"Verbal agreement is in place; paperwork is moving through their process.",
        "champion_left": f"Named champion {contact} has left. No successor is identified.",
        "unknown_decision_owner": "Next step exists but the decision owner is not named.",
    }
    return mapping[state]


def _apply_density(deals: list[Deal], density: int, featured_state: str) -> None:
    featured = next((d for d in deals if d.state == featured_state), deals[0])
    action_states = {
        "seller_owned_deliverable",
        "champion_left",
        "missed_checkpoint",
        "no_dated_checkpoint",
        "unknown_decision_owner",
    }
    monitor_states = {
        "customer_legal_review",
        "procurement_review",
        "board_approval",
        "explicit_waiting_date",
        "verbal_paperwork_in_motion",
        "scheduled_future_meeting",
        "newly_qualified",
    }
    for deal in deals:
        if deal.state in monitor_states:
            deal.monitor = True
        elif deal.state in action_states:
            deal.action = True
        else:
            deal.monitor = True
    if density == 0:
        for deal in deals:
            deal.action = False
            deal.monitor = True
        return
    actionable = [d for d in deals if d.action]
    if featured not in actionable:
        featured.action = True
        featured.monitor = False
        actionable.append(featured)
    if density >= 4:
        needed = 4
    else:
        needed = density
    for deal in deals:
        if deal is featured:
            continue
        if len([d for d in deals if d.action]) >= needed:
            if deal.action and deal is not featured and len([d for d in deals if d.action]) > needed:
                deal.action = False
                deal.monitor = True
        elif not deal.action and deal.state in action_states:
            deal.action = True
            deal.monitor = False
    # Force exact density when possible.
    current = [d for d in deals if d.action]
    while len(current) > needed:
        extra = current.pop()
        if extra is featured and len(current) >= needed:
            extra.action = False
            extra.monitor = True
        elif extra is not featured:
            extra.action = False
            extra.monitor = True
    while len([d for d in deals if d.action]) < needed:
        idle = next((d for d in deals if not d.action and not d.meeting), None)
        if idle is None:
            break
        idle.action = True
        idle.monitor = False
        idle.state = "seller_owned_deliverable"
        idle.note = f"Seller still owes {idle.contact} a revised scope document."


def _apply_calendar(deals: list[Deal], calendar: str, rng: Random) -> None:
    if calendar == "none":
        return
    if calendar == "one_internal":
        deals[0].internal_meeting = True
        deals[0].meeting = True
        deals[0].action = False
        deals[0].extras["meeting_time"] = "9:00 AM"
        deals[0].extras["meeting_label"] = "internal forecast review"
        return
    customer_slots = {
        "one_customer": 1,
        "multi_customer": 3 + (rng.randint(0, 2)),
        "imminent": 1,
    }[calendar]
    times = ["8:30 AM", "10:00 AM", "1:00 PM", "2:30 PM", "4:00 PM"]
    chosen = deals[:customer_slots]
    for i, deal in enumerate(chosen):
        deal.meeting = True
        deal.action = False
        deal.monitor = False
        deal.extras["meeting_time"] = times[i % len(times)]
        if calendar == "imminent":
            deal.extras["meeting_time"] = "in 40 minutes"
            deal.extras["meeting_label"] = "customer working session"


def _apply_communication(deals: list[Deal], communication: str) -> None:
    if not deals:
        return
    target = deals[-1]
    if communication == "do_not_contact_until_date":
        target.action = False
        target.monitor = True
        target.constraint = f"Do not contact {target.name} until September 30."
        target.note += f" {target.constraint}"
    elif communication == "email_only":
        target.constraint = f"Email only for {target.name}; {target.contact} requested no calls."
        target.note += f" {target.constraint}"
    elif communication == "call_requested":
        target.constraint = f"{target.contact} at {target.name} asked for a phone call, not email."
        target.note += f" {target.constraint}"
        if not target.meeting:
            target.action = True
            target.monitor = False
    elif communication == "second_hand_information":
        target.note += f" Second-hand note from customer success: {target.contact} may be evaluating alternatives. Treat as unconfirmed."
    else:
        target.note += " No channel is specified."


def _apply_quality(deals: list[Deal], quality: str) -> None:
    if not deals:
        return
    deal = deals[min(1, len(deals) - 1)]
    if quality == "stale_system_timestamp":
        deal.note += f" CRM last activity shows {deal.last_activity}, but that stamp is a system sync, not a human touch."
        deal.extras["true_last"] = "a human meeting two weeks earlier"
    elif quality == "automated_workflow_vs_human":
        deal.note += " Last activity is an automated CRM workflow email, not a seller-initiated touch."
    elif quality == "explicit_human_correction":
        wrong = deal.last_activity
        deal.extras["superseded_last"] = wrong
        deal.extras["true_last"] = "April 2"
        deal.note += f" Human correction: CRM last activity shows {wrong}; actual last human touch is April 2."
        deal.record_only = True
        deal.action = False
    elif quality == "missing_next_step":
        deal.note += " Next-step field is blank."
    elif quality == "contradictory_note_table":
        deal.note += f" Table close date {deal.close} conflicts with the note that legal already marked it closed-lost. Do not resolve by guess."
        deal.record_only = True
        deal.action = False
    elif quality == "missing_contact":
        deal.contact = None
        deal.note += " No named contact is supplied."
        deal.extras["flags"] = deal.extras.get("flags", [])
    elif quality == "missing_amount":
        deal.extras["flags"] = ["missing_amount"]
        deal.amount = ""
        deal.note += " Amount is not supplied."
    elif quality == "mixed_currencies":
        deal.note += " Amounts in this book use mixed currencies. Do not convert or sum them."


def _apply_commercial(deals: list[Deal], commercial: str) -> None:
    if commercial == "small_urgent_vs_large_waiting" and len(deals) >= 2:
        small = min(deals, key=lambda d: _amount_sort(d.amount))
        large = max(deals, key=lambda d: _amount_sort(d.amount))
        small.action = True
        small.monitor = False
        small.note += " Small amount but seller-owned blocker due today."
        large.action = False
        large.monitor = True
        large.state = "customer_legal_review"
        large.note += " Largest amount; customer legal owns the next step."
    elif commercial == "late_stage_low_vs_early_high" and len(deals) >= 2:
        deals[0].stage = "Negotiation"
        deals[0].amount = deals[0].amount or "$45K"
        deals[-1].stage = "Discovery"
        if deals[-1].amount:
            deals[-1].amount = "$890K"
        deals[-1].monitor = True
        deals[-1].action = False
    elif commercial == "renewal_vs_new_logo" and deals:
        deals[0].stage = "Renewal"
        deals[0].note += " Existing account renewal, not a new logo."
    elif commercial == "quota_pressure":
        for deal in deals[:1]:
            deal.note += " Seller is behind quota; do not invent extra urgency beyond the stated facts."


def _amount_sort(amount: str) -> int:
    digits = "".join(ch for ch in amount if ch.isdigit())
    return int(digits or 0)


def _render_scenario(
    briefing_date: str,
    deals: list[Deal],
    calendar: str,
    extra: str,
    commercial: str,
    labeled_total: str | None,
) -> str:
    lines = [
        f"Good morning. Briefing date: {briefing_date}.",
        "Please write today's pipeline briefing from this handoff only.",
        "",
        "TODAY'S CALENDAR",
    ]
    calendar_lines = []
    for deal in deals:
        if deal.internal_meeting:
            calendar_lines.append(
                f"- {deal.extras.get('meeting_time', '9:00 AM')}: {deal.extras.get('meeting_label', 'internal meeting')} (internal, no customer deal work)"
            )
        elif deal.meeting:
            label = deal.extras.get("meeting_label", "customer meeting")
            calendar_lines.append(
                f"- {deal.extras.get('meeting_time', '10:00 AM')}: {label} w/ {deal.name}"
                + (f" ({deal.amount})" if deal.amount else "")
                + (f" — {deal.contact}" if deal.contact else "")
            )
    if not calendar_lines:
        calendar_lines.append("- No meetings on the calendar today.")
    lines.extend(calendar_lines)
    lines.extend(["", "OPEN DEALS"])
    for deal in deals:
        amount = deal.amount or "amount not supplied"
        contact = deal.contact or "contact not supplied"
        lines.append(
            f"- {deal.name} | {amount} | {deal.stage} | close {deal.close} | last activity {deal.last_activity} | contact {contact}"
        )
        lines.append(f"  Note: {deal.note}")
    if labeled_total:
        lines.extend(["", f"Labeled pipeline total: {labeled_total}"])
    if commercial == "quarter_end_near":
        lines.extend(["", "Period context: 9 days remain in the quarter. Quota attainment is stated as 61%."])
    elif commercial == "quarter_end_far":
        lines.extend(["", "Period context: 57 days remain in the quarter."])
    elif commercial == "quota_pressure":
        lines.extend(["", "Period context: seller is at 38% of quota."])
    if extra == "forecast_insufficient_assumptions":
        lines.extend(["", "Also give me a commit forecast for the quarter. Win rates are not supplied."])
    elif extra == "summary_requested":
        lines.extend(["", "Also give a two-sentence summary after the briefing."])
    elif extra == "risk_question":
        lines.extend(["", "After the briefing, what is the largest evidenced slippage risk?"])
    return "\n".join(lines) + "\n"
