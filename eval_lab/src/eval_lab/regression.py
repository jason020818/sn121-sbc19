"""Regression evaluation over archived public scenario inputs."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from eval_lab.archive_loader import load_archive
from eval_lab.candidate_store import sha256_text
from eval_lab.config import LabConfig, repo_root
from eval_lab.runner import ChatClient, ScenarioJob, estimate_calls, run_jobs_with_concurrency
from eval_lab.scoring import generalization_proxy, repeat_level_stats, summarize_repeats


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
        "max_concurrency": config.evaluation.max_concurrency,
        "hard_failures": 0,
    }
    if dry_run:
        return payload

    jobs = [
        ScenarioJob(scenario_id=sample.scenario_id, scenario_text=sample.scenario_input, repeat_index=repeat_index)
        for sample in samples
        for repeat_index in range(repeats)
    ]
    records = run_jobs_with_concurrency(
        jobs=jobs,
        config=config,
        client=client,
        candidate_text=candidate_text,
        candidate_sha256=candidate_sha256,
        score_one=lambda job, agent, judges: {},
    )
    per_scenario: dict[str, list[float]] = defaultdict(list)
    by_repeat: dict[int, list[float]] = defaultdict(list)
    failure_counts: Counter[str] = Counter()
    hard_failures = 0
    raw_outputs: list[dict[str, Any]] = []
    for record in records:
        score = float(record["internal_score"]["penalized"])
        per_scenario[str(record["scenario_id"])].append(score)
        by_repeat[int(record["repeat_index"])].append(score)
        checks = record["_checks"]
        if checks.catastrophic:
            hard_failures += 1
        for check in checks.checks:
            if not check.passed:
                failure_counts[str(check.name)] += 1
        raw_outputs.append({key: value for key, value in record.items() if not key.startswith("_")})
    stats = repeat_level_stats(dict(by_repeat))
    payload["scenario_score_summary"] = stats["scenario_score_summary"]
    payload["repeat_means"] = stats["repeat_means"]
    payload["repeat_mean_summary"] = stats["repeat_mean_summary"]
    payload["repeat_summary"] = stats["repeat_mean_summary"]
    payload["per_scenario"] = {
        key: summarize_repeats(vals).model_dump() for key, vals in per_scenario.items()
    }
    payload["deterministic_failures"] = dict(failure_counts)
    payload["hard_failures"] = hard_failures
    payload["outputs"] = raw_outputs
    payload["generalization_proxy"] = generalization_proxy(candidate_text)
    return payload
