"""Internal scoring. This is not an official SN121 score."""

from __future__ import annotations

import math
import re
from statistics import mean, median, pstdev

from eval_lab.models import DeterministicReport, InternalScore, JudgeDimensionScores, RepeatSummary

WEIGHTS = {
    "grounding_accuracy": 0.22,
    "prioritization_quality": 0.20,
    "actionability": 0.16,
    "waiting_state_judgment": 0.14,
    "meeting_preparation_quality": 0.10,
    "concision": 0.08,
    "skill_adherence": 0.10,
}

SCENARIO_ID_RE = re.compile(r"\bS-0(?:0[1-9]|10)\b")
SUSPICIOUS_GRADER_RE = re.compile(
    r"dataset_derived|scenario_quality|novelty_check|official grader|hidden rubric",
    re.I,
)


def average_judges(scores: list[JudgeDimensionScores]) -> dict[str, float]:
    if not scores:
        return {key: 0.0 for key in WEIGHTS}
    out: dict[str, float] = {}
    for key in WEIGHTS:
        out[key] = mean(getattr(item, key) for item in scores)
    return out


def unpenalized_score(dimension_means: dict[str, float]) -> float:
    return sum(dimension_means[key] * weight for key, weight in WEIGHTS.items())


def apply_deterministic_penalties(score: float, report: DeterministicReport) -> tuple[float, str]:
    if report.catastrophic or any(not c.passed and c.severity == "catastrophic" for c in report.checks):
        return 0.0, "catastrophic"
    if any(not c.passed and c.severity == "major" for c in report.checks):
        return score * 0.75, "major"
    if any(not c.passed and c.severity == "minor" for c in report.checks):
        return score * 0.95, "minor"
    return score, "none"


def score_output(
    judges: list[JudgeDimensionScores],
    report: DeterministicReport,
    generalization_proxy: float | None = None,
) -> InternalScore:
    dims = average_judges(judges)
    raw = unpenalized_score(dims)
    penalized, penalty = apply_deterministic_penalties(raw, report)
    return InternalScore(
        unpenalized=round(raw, 6),
        penalized=round(penalized, 6),
        penalty_applied=penalty,
        dimension_means={key: round(val, 6) for key, val in dims.items()},
        generalization_proxy=generalization_proxy,
    )


def repeat_level_stats(scores_by_repeat: dict[int, list[float]]) -> dict:
    """Separate scenario difficulty variance from repeat-to-repeat stability.

    `scores_by_repeat` maps repeat index -> one score per selected scenario.
    Release metrics must use `repeat_mean_summary`, not the pooled scenario scores.
    """
    repeat_means: list[float] = []
    for index in sorted(scores_by_repeat):
        values = scores_by_repeat[index]
        repeat_means.append(float(mean(values)) if values else 0.0)
    pooled = [score for index in sorted(scores_by_repeat) for score in scores_by_repeat[index]]
    summary = summarize_repeats(repeat_means)
    return {
        "scenario_score_summary": summarize_repeats(pooled).model_dump(),
        "repeat_means": repeat_means,
        "repeat_mean_summary": summary.model_dump(),
        "holdout_worst_repeat": float(min(repeat_means)) if repeat_means else 0.0,
        "holdout_median": summary.median,
        "holdout_stddev": summary.stddev,
        "regression_median": summary.median,
    }


def summarize_repeats(values: list[float]) -> RepeatSummary:
    if not values:
        return RepeatSummary(mean=0.0, median=0.0, min=0.0, max=0.0, stddev=0.0, p10=None, n=0)
    ordered = sorted(values)
    p10_index = max(0, math.ceil(0.1 * len(ordered)) - 1)
    return RepeatSummary(
        mean=float(mean(ordered)),
        median=float(median(ordered)),
        min=float(ordered[0]),
        max=float(ordered[-1]),
        stddev=float(pstdev(ordered)) if len(ordered) > 1 else 0.0,
        p10=float(ordered[p10_index]),
        n=len(ordered),
    )


def generalization_proxy(skill_text: str, archived_company_names: list[str] | None = None) -> float:
    """Conservative static lint. Not the official dataset_derived grader."""
    score = 1.0
    if SCENARIO_ID_RE.search(skill_text or ""):
        score -= 0.5
    if SUSPICIOUS_GRADER_RE.search(skill_text or ""):
        score -= 0.2
    if re.search(r"\bP[12]\b", skill_text or ""):
        score -= 0.15
    if archived_company_names:
        hits = []
        lowered = skill_text.casefold()
        for name in archived_company_names:
            token = name.strip()
            if len(token) < 5:
                continue
            if token.casefold() in lowered:
                hits.append(token)
        if hits:
            score -= min(0.5, 0.1 * len(set(hits)))
    return round(max(0.0, min(1.0, score)), 6)


def tournament_sort_key(row: dict) -> tuple:
    return (
        int(row.get("catastrophic_failures", 0)),
        -float(row.get("holdout_median", 0.0)),
        -float(row.get("holdout_worst_repeat", 0.0)),
        -float(row.get("regression_median", 0.0)),
        float(row.get("stddev", 0.0)),
    )


def rank_tournament(rows: list[dict]) -> list[dict]:
    ranked = sorted(rows, key=tournament_sort_key)
    out = []
    for index, row in enumerate(ranked, start=1):
        copied = dict(row)
        copied["rank"] = index
        out.append(copied)
    return out
