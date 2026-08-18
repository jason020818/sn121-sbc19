"""Regression evaluation over archived public scenario inputs."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from eval_lab.archive_loader import load_archive
from eval_lab.config import LabConfig, repo_root
from eval_lab.candidate_store import sha256_text
from eval_lab.deterministic_checks import run_deterministic_checks
from eval_lab.llm_judges import run_judges
from eval_lab.models import DeterministicReport
from eval_lab.runner import ChatClient, agent_messages, estimate_calls
from eval_lab.scoring import generalization_proxy, score_output, summarize_repeats


def skill_delta(candidate_text: str, production_text: str) -> str:
    if candidate_text == production_text:
        return "Candidate text matches current SKILL.md."
    return (
        f"Candidate differs from current SKILL.md "
        f"(candidate_sha256={sha256_text(candidate_text)}, "
        f"skill_sha256={sha256_text(production_text)})."
    )


def run_regression(
    *,
    config: LabConfig,
    candidate_name: str,
    candidate_text: str,
    candidate_sha256: str,
    source: Path | str,
    repeats: int,
    client: ChatClient,
    limit: int | None = None,
    scenario_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    archive = load_archive(source)
    samples = list(archive.samples)
    if scenario_id:
        samples = [item for item in samples if item.scenario_id == scenario_id]
    if limit is not None:
        samples = samples[:limit]
    estimate = estimate_calls(len(samples), repeats, config.n_judges)
    production = (repo_root() / "SKILL.md").read_text(encoding="utf-8")
    payload: dict[str, Any] = {
        "kind": "regression",
        "candidate": candidate_name,
        "candidate_sha256": candidate_sha256,
        "source": str(source),
        "dry_run": dry_run,
        "repeats": repeats,
        "models": {"agent": config.models.agent, "judges": list(config.models.judges)},
        "call_estimate": estimate,
        "historical_official_score": archive.official_score,
        "skill_delta": skill_delta(candidate_text, production),
        "disclaimer": "Local internal_quality is not an official SN121 score.",
        "scenario_ids": [item.scenario_id for item in samples],
    }
    if dry_run:
        return payload

    per_scenario: dict[str, list[float]] = {}
    failure_counts: Counter[str] = Counter()
    reports: list[DeterministicReport] = []
    raw_outputs: list[dict[str, Any]] = []
    all_scores: list[float] = []
    for sample in samples:
        per_scenario.setdefault(sample.scenario_id, [])
        for repeat_index in range(repeats):
            output = client.complete(
                model=config.models.agent,
                messages=agent_messages(candidate_text, sample.scenario_input),
                temperature=config.evaluation.temperature,
            )
            checks = run_deterministic_checks(sample.scenario_input, output)
            reports.append(checks)
            for check in checks.checks:
                if not check.passed:
                    failure_counts[str(check.name)] += 1
            judges = run_judges(
                client=client,
                models=config.models.judges,
                scenario=sample.scenario_input,
                skill=candidate_text,
                output=output,
                checks=checks,
            )
            internal = score_output(judges, checks)
            per_scenario[sample.scenario_id].append(internal.penalized)
            all_scores.append(internal.penalized)
            raw_outputs.append(
                {
                    "scenario_id": sample.scenario_id,
                    "repeat_index": repeat_index,
                    "model": config.models.agent,
                    "candidate_sha256": candidate_sha256,
                    "latency_ms": None,
                    "usage": None,
                    "response_text": output,
                    "internal_score": internal.model_dump(),
                    "deterministic": checks.model_dump(),
                }
            )
    payload["repeat_summary"] = summarize_repeats(all_scores).model_dump()
    payload["per_scenario"] = {
        key: summarize_repeats(vals).model_dump() for key, vals in per_scenario.items()
    }
    payload["deterministic_failures"] = dict(failure_counts)
    payload["outputs"] = raw_outputs
    payload["generalization_proxy"] = generalization_proxy(candidate_text)
    return payload
