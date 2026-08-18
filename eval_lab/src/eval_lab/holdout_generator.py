"""Compositional synthetic holdout generator.

Holdouts are built from general sales-ops dimensions. They are not derived by
copying public benchmark scenarios, company names, or grader answers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from random import Random

from eval_lab.config import lab_root
from eval_lab.models import HiddenExpectations, HoldoutRecord

BOOK_SIZES = [5, 8, 12, 18, 30, 40]
CALENDARS = ["none", "one_internal", "one_customer", "multi_customer", "imminent"]
ACTION_DENSITIES = [0, 1, 2, 3, 4]
ACTION_CAPABLE_STATES = [
    "seller_owned_deliverable",
    "champion_left",
    "missed_checkpoint",
    "no_dated_checkpoint",
    "unknown_decision_owner",
]
MONITOR_STATES = [
    "customer_legal_review",
    "procurement_review",
    "board_approval",
    "explicit_waiting_date",
    "verbal_paperwork_in_motion",
    "scheduled_future_meeting",
    "newly_qualified",
]
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
    close_date: date | None = None
    last_date: date | None = None
    hold: bool = False


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


def briefing_date_for_index(index: int) -> date:
    start = date(2026, 1, 5)
    return start + timedelta(days=(index * 7) % 350)


def format_briefing(value: date) -> str:
    return f"{value.strftime('%A')}, {value.strftime('%B')} {value.day}, {value.year}"


def iso(value: date) -> str:
    return value.isoformat()


def needed_action_count(density: int) -> tuple[int, bool]:
    if density >= 4:
        return 4, True
    return density, False


def _contact(deal: Deal) -> str:
    return deal.contact or "the unnamed contact"


def _state_note(state: str, contact: str, last: str, briefing: date) -> str:
    wait_until = iso(briefing + timedelta(days=10))
    future_meet = iso(briefing + timedelta(days=7))
    mapping = {
        "seller_owned_deliverable": f"Seller still owes {contact} a revised scope document.",
        "customer_legal_review": f"Contract is with their legal team since {last}; credible legal process, no seller deliverable.",
        "procurement_review": f"Procurement is evaluating pricing. Credible process; ball is not with the seller.",
        "board_approval": "Commercial terms agreed; waiting on their board packet. Credible process is in motion.",
        "explicit_waiting_date": f"{contact} asked the seller to wait until {wait_until}.",
        "no_dated_checkpoint": f"Proposal sent {last}. Timing is material and no return date was given.",
        "missed_checkpoint": "They promised a decision last week and missed it. No new date exists.",
        "newly_qualified": "Qualified yesterday. Discovery is not yet scheduled.",
        "scheduled_future_meeting": f"Next conversation is already scheduled on {future_meet} with {contact}.",
        "verbal_paperwork_in_motion": "Verbal agreement is in place; paperwork is moving through their process.",
        "champion_left": f"Named champion {contact} has left. No successor is identified.",
        "unknown_decision_owner": "Identifying the decision owner is itself necessary today; no owner is named.",
        "customer_meeting_today": "Today's scheduled customer meeting is the useful work for this deal.",
    }
    return mapping[state]


def _set_action(deal: Deal, briefing: date, state: str | None = None) -> None:
    deal.action = True
    deal.monitor = False
    deal.record_only = False
    deal.meeting = False
    deal.state = state or "seller_owned_deliverable"
    if deal.state == "no_dated_checkpoint" and deal.close_date and deal.close_date > briefing + timedelta(days=14):
        deal.close_date = briefing + timedelta(days=9)
        deal.close = iso(deal.close_date)
    deal.note = _state_note(deal.state, _contact(deal), deal.last_activity, briefing)


def _set_monitor(deal: Deal, briefing: date, state: str | None = None) -> None:
    deal.action = False
    deal.monitor = True
    deal.record_only = False
    deal.meeting = False
    deal.state = state or "customer_legal_review"
    deal.note = _state_note(deal.state, _contact(deal), deal.last_activity, briefing)


def _set_meeting(deal: Deal, briefing: date, time_label: str, imminent: bool) -> None:
    deal.action = False
    deal.monitor = False
    deal.record_only = False
    deal.meeting = True
    deal.internal_meeting = False
    deal.state = "customer_meeting_today"
    deal.extras["meeting_time"] = "in 40 minutes" if imminent else time_label
    deal.extras["meeting_label"] = "customer working session" if imminent else "customer meeting"
    deal.note = _state_note("customer_meeting_today", _contact(deal), deal.last_activity, briefing)


def _set_record(deal: Deal, briefing: date, quality: str) -> None:
    deal.action = False
    deal.monitor = False
    deal.meeting = False
    deal.record_only = True
    if quality == "contradictory_note_table":
        stale = briefing - timedelta(days=12)
        deal.close_date = stale
        deal.close = iso(stale)
        deal.extras["stale_close"] = iso(stale)
        deal.note = (
            f"Labeled stale/contradictory-data: table close date {iso(stale)} is before the briefing date "
            "and conflicts with the note that legal already marked it closed-lost. Do not resolve by guess."
        )
    else:
        superseded = iso(briefing - timedelta(days=20))
        actual = iso(briefing - timedelta(days=3))
        deal.extras["superseded_last"] = superseded
        deal.extras["true_last"] = actual
        deal.note = (
            f"Human correction: CRM last activity shows {superseded}; actual last human touch is {actual}."
        )


def _wanted_meetings(calendar: str, rng: Random) -> int:
    if calendar in {"none", "one_internal"}:
        return 0
    if calendar in {"one_customer", "imminent"}:
        return 1
    return 3 + rng.randint(0, 2)


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
    briefing = briefing_date_for_index(index)
    stages = ["Discovery", "Demo", "Proposal", "Negotiation", "Verbal", "Renewal"]
    deals: list[Deal] = []
    for i, name in enumerate(names[:book]):
        amount_n = 40 + ((seed + index * 17 + i * 13) % 860)
        currency = "$"
        if quality == "mixed_currencies" and i % 3 == 0:
            currency = "€" if i % 2 == 0 else "£"
        close_d = briefing + timedelta(days=5 + (i * 3))
        last_d = briefing - timedelta(days=1 + (i % 10))
        contact = contacts[i]
        state = MONITOR_STATES[(i + index) % len(MONITOR_STATES)]
        deal = Deal(
            name=name,
            amount=f"{currency}{amount_n}K",
            stage=stages[i % len(stages)],
            close=iso(close_d),
            last_activity=iso(last_d),
            contact=contact,
            note="",
            state=state,
            close_date=close_d,
            last_date=last_d,
        )
        deal.note = _state_note(state, contact, deal.last_activity, briefing)
        deals.append(deal)

    if quality == "near_duplicate_names" and len(names) > book:
        base = deals[0]
        twin_close = briefing + timedelta(days=21)
        twin_last = briefing - timedelta(days=2)
        deals.append(
            Deal(
                name=names[book],
                amount="€90K" if (base.amount or "").startswith("$") else "$90K",
                stage="Discovery",
                close=iso(twin_close),
                last_activity=iso(twin_last),
                contact=contacts[0],
                note="Separate legal entity; do not merge with similarly named account.",
                state="newly_qualified",
                monitor=True,
                close_date=twin_close,
                last_date=twin_last,
            )
        )

    needed, at_least = needed_action_count(density)
    wanted_meetings = _wanted_meetings(calendar, rng)
    n_meetings = min(wanted_meetings, max(0, len(deals) - needed))
    times = ["8:30 AM", "10:00 AM", "1:00 PM", "2:30 PM", "4:00 PM"]
    meeting_deals = deals[:n_meetings]
    remaining = deals[n_meetings:]
    for i, deal in enumerate(meeting_deals):
        _set_meeting(deal, briefing, times[i % len(times)], imminent=(calendar == "imminent"))

    action_pool = remaining[:needed]
    leftover = remaining[needed:]
    action_states_cycle = list(ACTION_CAPABLE_STATES)
    if ownership in ACTION_CAPABLE_STATES and action_pool:
        action_states_cycle.remove(ownership)
        action_states_cycle.insert(0, ownership)
    for i, deal in enumerate(action_pool):
        _set_action(deal, briefing, action_states_cycle[i % len(action_states_cycle)])
    monitor_states_cycle = list(MONITOR_STATES)
    if ownership in MONITOR_STATES:
        monitor_states_cycle.remove(ownership)
        monitor_states_cycle.insert(0, ownership)
    for i, deal in enumerate(leftover):
        _set_monitor(deal, briefing, monitor_states_cycle[i % len(monitor_states_cycle)])

    if at_least and len(action_pool) < 4:
        for deal in leftover:
            if len([d for d in deals if d.action]) >= 4:
                break
            if deal.meeting or deal.record_only:
                continue
            _set_action(deal, briefing, "seller_owned_deliverable")

    _overlay_quality(deals, leftover, quality, briefing)
    _overlay_commercial(deals, commercial, briefing)
    _overlay_communication(deals, leftover, communication, briefing)

    if calendar == "one_internal":
        deals[0].extras["internal_calendar"] = True
        deals[0].extras["meeting_time"] = "9:00 AM"
        deals[0].extras["meeting_label"] = "internal forecast review"

    expectations = _hidden_from_deals(deals, density)
    scenario = _render_scenario(
        briefing_date=format_briefing(briefing),
        briefing=briefing,
        deals=deals,
        calendar=calendar,
        extra=extra,
        commercial=commercial,
        labeled_total=None,
        quality=quality,
    )
    return HoldoutRecord(
        id=f"H-{index + 1:04d}",
        seed=seed + index,
        scenario=scenario,
        hidden_expectations=expectations,
        dimensions={
            "book_size": book,
            "calendar": calendar,
            "action_density": density,
            "ownership": ownership,
            "data_quality": quality,
            "communication": communication,
            "commercial": commercial,
            "extra_request": extra,
            "briefing_date": iso(briefing),
        },
    )


def _overlay_communication(
    deals: list[Deal],
    leftover: list[Deal],
    communication: str,
    briefing: date,
) -> None:
    if not deals:
        return
    monitors = [d for d in deals if d.monitor]
    target = monitors[-1] if monitors else leftover[-1] if leftover else deals[-1]
    if communication == "do_not_contact_until_date":
        hold_until = iso(briefing + timedelta(days=14))
        if target.action:
            _set_monitor(target, briefing, "explicit_waiting_date")
            replacement = next((d for d in deals if not d.action and not d.meeting and not d.record_only and d is not target), None)
            if replacement is not None:
                _set_action(replacement, briefing, "seller_owned_deliverable")
        target.hold = True
        target.constraint = f"Do not contact {target.name} until {hold_until}."
        target.note += f" {target.constraint}"
        if not target.action and not target.meeting:
            target.monitor = True
            target.record_only = False
    elif communication == "email_only":
        target.constraint = f"Email only for {target.name}; {_contact(target)} requested no calls."
        target.note += f" {target.constraint}"
    elif communication == "call_requested":
        target.constraint = f"{_contact(target)} at {target.name} asked for a phone call, not email."
        target.note += f" {target.constraint}"
    elif communication == "second_hand_information":
        target.note += (
            f" Second-hand note from customer success: {_contact(target)} may be evaluating alternatives. "
            "Treat as unconfirmed."
        )
    elif communication == "no_explicit_channel":
        target.note += " No channel is specified."


def _overlay_quality(deals: list[Deal], leftover: list[Deal], quality: str, briefing: date) -> None:
    if not deals:
        return
    monitors = [d for d in deals if d.monitor]
    deal = monitors[0] if monitors else leftover[0] if leftover else deals[-1]
    if quality == "stale_system_timestamp":
        deal.note += f" CRM last activity shows {deal.last_activity}, but that stamp is a system sync, not a human touch."
        deal.extras["true_last"] = iso(briefing - timedelta(days=14))
    elif quality == "automated_workflow_vs_human":
        deal.note += " Last activity is an automated CRM workflow email, not a seller-initiated touch."
    elif quality in {"explicit_human_correction", "contradictory_note_table"}:
        if deal.action:
            replacement = next((d for d in deals if d.monitor and d is not deal), None)
            if replacement is None:
                return
            deal = replacement
        _set_record(deal, briefing, quality)
    elif quality == "missing_next_step":
        deal.note += " Next-step field is blank."
    elif quality == "missing_contact":
        deal.contact = None
        deal.note += " No named contact is supplied."
    elif quality == "missing_amount":
        deal.extras["flags"] = ["missing_amount"]
        deal.amount = ""
        deal.note += " Amount is not supplied."
    elif quality == "mixed_currencies":
        deal.note += " Amounts in this book use mixed currencies. Do not convert or sum them."


def _overlay_commercial(deals: list[Deal], commercial: str, briefing: date) -> None:
    actions = [d for d in deals if d.action]
    monitors = [d for d in deals if d.monitor]
    if commercial == "small_urgent_vs_large_waiting" and actions and monitors:
        small = min(actions, key=lambda d: _amount_sort(d.amount))
        large = max(monitors, key=lambda d: _amount_sort(d.amount))
        _set_action(small, briefing, "seller_owned_deliverable")
        small.note += " Small amount but seller-owned blocker due today."
        _set_monitor(large, briefing, "customer_legal_review")
        large.note += " Largest amount; customer legal owns the next step."
    elif commercial == "late_stage_low_vs_early_high" and len(deals) >= 2:
        deals[0].stage = "Negotiation"
        deals[-1].stage = "Discovery"
        if deals[-1].amount:
            deals[-1].amount = "$890K"
    elif commercial == "renewal_vs_new_logo" and deals:
        deals[0].stage = "Renewal"
        deals[0].note += " Existing account renewal, not a new logo."
    elif commercial == "quota_pressure" and deals:
        deals[0].note += " Seller is behind quota; do not invent extra urgency beyond the stated facts."


def _amount_sort(amount: str) -> int:
    digits = "".join(ch for ch in amount if ch.isdigit())
    return int(digits or 0)


def _hidden_from_deals(deals: list[Deal], density: int) -> HiddenExpectations:
    actions = [d.name for d in deals if d.action]
    monitors = [d.name for d in deals if d.monitor]
    meetings = [d.name for d in deals if d.meeting and not d.internal_meeting]
    records = [d.name for d in deals if d.record_only]
    action_set, monitor_set, meeting_set, record_set = map(set, (actions, monitors, meetings, records))
    if action_set & monitor_set:
        raise ValueError(f"action/monitor overlap: {action_set & monitor_set}")
    if action_set & meeting_set:
        raise ValueError(f"meeting deals also marked action: {action_set & meeting_set}")
    if record_set & action_set or record_set & meeting_set or record_set & monitor_set:
        raise ValueError("record-only deals overlap operational classes")
    if density <= 3 and len(actions) != density:
        raise ValueError(f"action_density {density} != final actions {len(actions)} {actions}")
    if density >= 4 and len(actions) < 4:
        raise ValueError(f"action_density 4+ requires >=4 actions, got {len(actions)}")
    return HiddenExpectations(
        allowed_action_deals=actions,
        required_monitor_deals=monitors,
        meeting_deals=meetings,
        record_only_deals=records,
        explicit_constraints=[d.constraint for d in deals if d.constraint],
        source_entities=[d.name for d in deals],
        source_people=[d.contact for d in deals if d.contact],
        source_amounts=[d.amount for d in deals if d.amount and "missing" not in (d.extras.get("flags") or [])],
    )


def _render_scenario(
    briefing_date: str,
    briefing: date,
    deals: list[Deal],
    calendar: str,
    extra: str,
    commercial: str,
    labeled_total: str | None,
    quality: str,
) -> str:
    lines = [
        f"Good morning. Briefing date: {briefing_date} ({iso(briefing)}).",
        "Please write today's pipeline briefing from this handoff only.",
        "",
        "TODAY'S CALENDAR",
    ]
    calendar_lines = []
    if calendar == "one_internal":
        calendar_lines.append("- 9:00 AM: internal forecast review (internal, no customer deal work)")
    for deal in deals:
        if deal.meeting:
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


def final_action_names(record: HoldoutRecord) -> list[str]:
    return list(record.hidden_expectations.allowed_action_deals)
