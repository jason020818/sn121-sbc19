"""Combine domain-policy and rendering-risk results into a champion plan. No SKILL.md edits."""

from __future__ import annotations

from pathlib import Path

from eval_lab.config import lab_root
from eval_lab.domain_tournament import run_domain_policy_tournament
from eval_lab.rendering_risk import run_rendering_risk_tournament

LIMITATION = (
    "Remaining uncertainty: Haiku instruction-following is not measured here. "
    "A live SN121 submission remains the only official validator sample. "
    "The recommended rendering does not have a predicted official score."
)


def _status(rows: list[dict], name: str) -> str:
    row = next((item for item in rows if item.get("candidate") == name), None)
    if row is None:
        return "not evaluated"
    return (
        f"rank={row.get('rank')} f1={row.get('action_f1')} "
        f"false_action={row.get('false_action_rate')} "
        f"missed_action={row.get('missed_action_rate')} "
        f"flip_exact={row.get('controlled_flip_exact_pass_rate')}"
    )


def run_free_champion_plan(domain: dict | None = None, rendering: dict | None = None) -> dict:
    domain = domain or run_domain_policy_tournament()
    family = domain.get("recommended_semantic_policy_family") or domain.get("recommended_semantic_policy")
    rendering = rendering or run_rendering_risk_tournament(family=family)
    winner_flip = domain.get("winning_controlled_flip_exact_pass_rate")
    if winner_flip is None:
        members = set(domain.get("semantic_equivalents") or [])
        rates = [row.get("controlled_flip_exact_pass_rate") for row in domain.get("results") or [] if row.get("candidate") in members]
        winner_flip = min(rates) if rates else None
    return {
        "kind": "free-champion-plan",
        "semantic_policy_family": family,
        "semantic_equivalents": domain.get("semantic_equivalents"),
        "recommended_rendering": rendering.get("recommended_rendering"),
        "reserve_rendering": rendering.get("reserve_rendering"),
        "aggressive_policy_status": _status(domain.get("results") or [], "candidate-c-assertive"),
        "conservative_policy_status": _status(domain.get("results") or [], "candidate-a-conservative"),
        "controlled_flip_exact_pass_rate": winner_flip,
        "remaining_uncertainty": LIMITATION,
        "domain_metrics": domain["results"],
        "rendering_risk_metrics": rendering["results"],
        "historical_calibration_notes": (rendering.get("historical_calibration") or {}).get("notes", []),
        "skill_md_modified": False,
        "network_calls": 0,
        "openrouter_calls": 0,
        "sn121_submitted": False,
        "predicted_official_score": None,
    }


def render_champion_plan(payload: dict) -> str:
    lines = [
        "# Free champion plan",
        "",
        payload.get("remaining_uncertainty", LIMITATION),
        "",
        f"semantic_policy_family: {payload.get('semantic_policy_family')}",
        f"semantic_equivalents: {payload.get('semantic_equivalents')}",
        f"recommended_rendering: {payload.get('recommended_rendering')}",
        f"reserve_rendering: {payload.get('reserve_rendering')}",
        f"aggressive_policy_status: {payload.get('aggressive_policy_status')}",
        f"conservative_policy_status: {payload.get('conservative_policy_status')}",
        f"controlled_flip_exact_pass_rate: {payload.get('controlled_flip_exact_pass_rate')}",
        "",
        "No predicted official score is attached to the recommended rendering.",
        "SKILL.md was not modified.",
        "",
        "## Domain ranking",
        "",
    ]
    for row in payload.get("domain_metrics") or []:
        lines.append(
            f"{row.get('rank')}. {row.get('candidate')} family={row.get('semantic_family')} "
            f"f1={row.get('action_f1')} false_action={row.get('false_action_rate')} "
            f"flip_exact={row.get('controlled_flip_exact_pass_rate')}"
        )
    lines.extend(["", "## Rendering ranking", ""])
    for row in payload.get("rendering_risk_metrics") or []:
        lines.append(f"{row.get('rank')}. {row.get('candidate')} risk={row.get('rendering_risk')} words={row.get('markdown_words')}")
    lines.extend(["", "## Historical calibration", ""])
    for note in payload.get("historical_calibration_notes") or []:
        lines.append(f"- {note}")
    return "\n".join(lines).rstrip() + "\n"


def champion_plan_path() -> Path:
    path = lab_root() / "reports" / "free-champion-plan.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
