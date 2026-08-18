"""Deterministic reference policy engine. Verifies logic, not Haiku following."""

from __future__ import annotations

from eval_lab.policy_models import DealFact, Disposition, PolicyDecision, PolicyManifest

ACTION_STATES = {
    "seller_owned_deliverable",
    "seller_answer_due",
    "schedule_needed_interaction",
    "correct_operational_blocker",
}
OWNER_STATES = {"champion_left", "unknown_owner", "unknown_decision_owner"}
EXTERNAL_WAIT_STATES = {
    "customer_legal",
    "procurement",
    "board",
    "signature",
    "evaluation",
    "explicit_wait_date",
    "verbal_paperwork",
    "future_meeting",
    "newly_qualified",
}


def _active_contact_hold(deal: DealFact) -> bool:
    if deal.constraint_expired:
        return False
    return deal.constraint in {"do_not_contact", "wait_until"}


def _seller_owned_move(deal: DealFact, policy: PolicyManifest) -> bool:
    if deal.seller_deliverable_due or deal.seller_owns_next:
        return True
    if deal.state == "seller_owned_deliverable" and policy.action.seller_owned_deliverable:
        return True
    if deal.state == "seller_answer_due" and policy.action.seller_answer_due:
        return True
    if deal.state == "schedule_needed_interaction" and policy.action.schedule_needed_interaction:
        return True
    if deal.state == "correct_operational_blocker" and policy.action.correct_operational_blocker:
        return True
    return False


def _owner_identification_action(deal: DealFact, policy: PolicyManifest) -> bool:
    if not policy.action.identify_missing_owner_when_needed:
        return False
    if deal.owner_named:
        return False
    if deal.state == "champion_left":
        return True
    if deal.state in OWNER_STATES and deal.owner_identification_needed_now:
        return True
    return False


def _wait_escalation(deal: DealFact, policy: PolicyManifest) -> bool:
    if policy.action.external_wait_default != "monitor":
        return True
    esc = policy.action.external_wait_escalation
    timing_ok = deal.timing_material or esc.timing_material != "required"
    if esc.checkpoint == "passed_only":
        checkpoint_ok = deal.checkpoint == "passed"
    elif esc.checkpoint == "missing_or_passed":
        checkpoint_ok = deal.checkpoint in {"missing", "passed"}
    else:
        checkpoint_ok = True
    info_ok = deal.uncertainty_reduction or esc.uncertainty_reduction != "required"
    if timing_ok and checkpoint_ok and info_ok:
        return True
    if esc.champion_silence_near_close and deal.champion_silent:
        if deal.timing_material or deal.close_offset_days <= 7:
            return True
    return False


def _eligible_action(deal: DealFact, policy: PolicyManifest) -> bool:
    if deal.meeting_today and policy.meeting.replaces_same_objective_outbound:
        return False
    if policy.constraints.explicit_wait_overrides and _active_contact_hold(deal):
        return False
    if _seller_owned_move(deal, policy):
        return True
    if _owner_identification_action(deal, policy):
        return True
    external = deal.state in EXTERNAL_WAIT_STATES or deal.checkpoint in {"missing", "passed"} or deal.champion_silent
    if external and not deal.seller_owns_next and not deal.seller_deliverable_due:
        return _wait_escalation(deal, policy)
    return False


def _blocking_record(deal: DealFact, policy: PolicyManifest) -> bool:
    if deal.decision_blocking_record_problem:
        return True
    if policy.action.record_only_decision_blocking:
        return False
    return bool(deal.record_kind)


def classify_deal(deal: DealFact, policy: PolicyManifest) -> tuple[Disposition, str]:
    if deal.meeting_today and policy.meeting.replaces_same_objective_outbound:
        return "MEETING", "rule.meeting_covers_objective"
    for step in policy.disposition_precedence:
        if step == "meeting" and deal.meeting_today:
            return "MEETING", "rule.meeting_covers_objective"
        if step == "record" and _blocking_record(deal, policy):
            return "RECORD", "rule.record_blocks_decision"
        if step == "action" and _eligible_action(deal, policy):
            return "ACTION", "rule.seller_owned_or_escalated_wait"
        if step == "monitor":
            return "MONITOR", "rule.default_monitor"
    return "MONITOR", "rule.default_monitor"


def apply_policy(deals: list[DealFact], policy: PolicyManifest) -> PolicyDecision:
    dispositions: dict[str, Disposition] = {}
    reasons: dict[str, str] = {}
    holds: dict[str, str] = {}
    catastrophic: list[str] = []
    seen: set[str] = set()
    for deal in deals:
        if deal.name in seen:
            catastrophic.append(f"duplicate_disposition:{deal.name}")
        seen.add(deal.name)
        disp, reason = classify_deal(deal, policy)
        if _active_contact_hold(deal) and disp == "ACTION":
            if policy.constraints.explicit_wait_overrides:
                disp = "MONITOR"
                reason = "rule.explicit_wait_overrides"
            else:
                catastrophic.append(f"do_not_contact_action:{deal.name}")
        if deal.meeting_today and disp == "ACTION" and policy.meeting.replaces_same_objective_outbound:
            disp = "MEETING"
            reason = "rule.meeting_covers_objective"
            catastrophic.append(f"meeting_action_duplicate:{deal.name}")
        dispositions[deal.name] = disp
        reasons[deal.name] = reason
        if deal.constraint and not deal.constraint_expired:
            holds[deal.name] = deal.constraint
    if policy.evidence.allow_invented_recipient or policy.evidence.allow_invented_channel:
        catastrophic.append("policy_allows_invented_recipient_or_channel")
    if policy.evidence.allow_derived_pipeline_total or policy.output.pipeline_total == "derived_ok":
        catastrophic.append("policy_allows_derived_aggregate")
    if policy.output.filler_actions:
        catastrophic.append("policy_allows_filler_actions")
    groups: dict[str, list[str]] = {"ACTION": [], "MEETING": [], "MONITOR": [], "RECORD": []}
    for name, disp in dispositions.items():
        groups[disp].append(name)
    return PolicyDecision(
        dispositions=dispositions,
        reasons=reasons,
        action_set=groups["ACTION"],
        meeting_set=groups["MEETING"],
        monitor_set=groups["MONITOR"],
        record_set=groups["RECORD"],
        constraint_holds=holds,
        catastrophic=catastrophic,
    )
