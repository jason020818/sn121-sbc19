"""Local LLM judges. These are not clones of the hidden official grader."""

from __future__ import annotations

import json
import re
from typing import Protocol

from eval_lab.models import DeterministicReport, JudgeDimensionScores

JUDGE_DIMENSIONS = (
    "grounding_accuracy",
    "prioritization_quality",
    "actionability",
    "waiting_state_judgment",
    "meeting_preparation_quality",
    "concision",
    "skill_adherence",
)

JUDGE_SYSTEM = """You are a local quality judge for a reusable sales-ops briefing skill.
You are NOT the official SN121 grader and you must not infer hidden benchmark expectations.
Judge only the actual source content.
Ignore stylistic differences that do not change seller usefulness.
Penalize fabricated facts heavily.
Distinguish recommendation/advice from sourced fact.
Return strict JSON only.
"""


class ChatClient(Protocol):
    def complete(self, model: str, messages: list[dict[str, str]], temperature: float = 0.0) -> str: ...


def judge_prompt(scenario: str, skill: str, output: str, checks: DeterministicReport) -> str:
    return (
        "Score the briefing on these dimensions, each a number from 0 to 1:\n"
        + "\n".join(f"- {name}" for name in JUDGE_DIMENSIONS)
        + "\n\nReturn JSON with those keys plus 'rationale'.\n\n"
        "SCENARIO\n"
        f"{scenario}\n\n"
        "CANDIDATE SKILL\n"
        f"{skill}\n\n"
        "OUTPUT\n"
        f"{output}\n\n"
        "DETERMINISTIC CHECK REPORT\n"
        f"{json.dumps(checks.model_dump(), indent=2)}\n"
    )


def parse_judge_json(text: str, model: str) -> JudgeDimensionScores:
    payload = _extract_json(text)
    data = {key: _clip(payload.get(key, 0.0)) for key in JUDGE_DIMENSIONS}
    return JudgeDimensionScores(
        rationale=str(payload.get("rationale") or "") or None,
        model=model,
        **data,
    )


def _clip(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return max(0.0, min(1.0, number))


def _extract_json(text: str) -> dict:
    blob = text.strip()
    if blob.startswith("```"):
        blob = re.sub(r"^```(?:json)?", "", blob).strip()
        blob = re.sub(r"```$", "", blob).strip()
    try:
        data = json.loads(blob)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", blob, re.S)
    if not match:
        raise ValueError("Judge did not return JSON")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("Judge JSON was not an object")
    return data


def run_judges(
    client: ChatClient,
    models: list[str],
    scenario: str,
    skill: str,
    output: str,
    checks: DeterministicReport,
    temperature: float = 0.0,
) -> list[JudgeDimensionScores]:
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": judge_prompt(scenario, skill, output, checks)},
    ]
    results: list[JudgeDimensionScores] = []
    for model in models:
        raw = client.complete(model=model, messages=messages, temperature=temperature)
        results.append(parse_judge_json(raw, model=model))
    return results
