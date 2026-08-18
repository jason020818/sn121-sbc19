"""Combine domain-policy and rendering-risk results into a champion plan. No SKILL.md edits."""

from __future__ import annotations

from pathlib import Path

from eval_lab.config import lab_root
from eval_lab.domain_tournament import run_domain_policy_tournament
from eval_lab.rendering_risk import run_rendering_risk_tournament

LIMITATION = (
    "Remaining uncertainty: Haiku instruction-following is not measured here. "
    "A live SN121 submission remains the only official validator sample. "
    "Do not promote a candidate to SKILL.md from these internal reports alone."
)

POLICY_RENDERINGS = {
    "candidate-b-ledger": ["candidate-b-ledger", "candidate-b-minimal"],
    "production-f9e5400": ["production-f9e5400"],
    "candidate-a-conservative": ["candidate-a-conservative"],
    "candidate-c-assertive": ["candidate-c-assertive"],
    "balanced": ["candidate-b-ledger", "candidate-b-minimal"],
    "production": ["production-f9e5400"],
    "conservative": ["candidate-a-conservative"],
    "assertive": ["candidate-c-assertive"],
}


def run_free_champion_plan(domain: dict | None = None, rendering: dict | None = None) -> dict:
    domain = domain or run_domain_policy_tournament()
    rendering = rendering or run_rendering_risk_tournament()
    policy = domain["recommended_semantic_policy"]
    allowed = set(POLICY_RENDERINGS.get(policy, [policy]))
    matching = [row for row in rendering["results"] if row["candidate"] in allowed or row["semantic_policy"] in allowed]
    if not matching:
        matching = list(rendering["results"])
    recommended_rendering = matching[0]["candidate"]
    reserve_rendering = matching[1]["candidate"] if len(matching) > 1 else rendering["results"][1]["candidate"]
    return {
        "kind": "free-champion-plan",
        "recommended_semantic_policy": policy,
        "recommended_rendering": recommended_rendering,
        "reserve_policy_1": domain.get("reserve_policy_1"),
        "reserve_policy_2": domain.get("reserve_policy_2"),
        "reserve_rendering": reserve_rendering,
        "domain_metrics": domain["results"],
        "rendering_risk_metrics": rendering["results"],
        "historical_calibration_notes": (rendering.get("historical_calibration") or {}).get("notes", []),
        "remaining_uncertainty": LIMITATION,
        "skill_md_modified": False,
        "network_calls": 0,
        "openrouter_calls": 0,
        "sn121_submitted": False,
    }


def render_champion_plan(payload: dict) -> str:
    lines = [
        "# Free champion plan",
        "",
        payload.get("remaining_uncertainty", LIMITATION),
        "",
        f"recommended_semantic_policy: {payload.get('recommended_semantic_policy')}",
        f"recommended_rendering: {payload.get('recommended_rendering')}",
        f"reserve_policy_1: {payload.get('reserve_policy_1')}",
        f"reserve_policy_2: {payload.get('reserve_policy_2')}",
        f"reserve_rendering: {payload.get('reserve_rendering')}",
        "",
        "SKILL.md was not modified.",
        "",
        "## Domain ranking",
        "",
    ]
    for row in payload.get("domain_metrics") or []:
        lines.append(f"{row.get('rank')}. {row.get('candidate')} f1={row.get('action_f1')} false_action={row.get('false_action_rate')}")
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
