"""Load archived public validator runs for regression evidence.

Scenario inputs are read at runtime from archived raw_evaluation.json files.
This module does not copy benchmark prompts into new fixture files and does
not branch on scenario names.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from eval_lab.config import repo_root
from eval_lab.models import ArchiveRun, ArchivedSample, GraderScore
from eval_lab.schemas import RawEvaluation, RawSample


DEFAULT_SOURCES = (
    "results/mine/raw_evaluation.json",
    "results/latest/raw_evaluation.json",
    "results/run-0.7378429/raw_evaluation.json",
    "results/champion/raw_evaluation.json",
)


def discover_archive_paths(root: Path | None = None) -> list[Path]:
    base = root or repo_root()
    found: list[Path] = []
    for rel in DEFAULT_SOURCES:
        path = base / rel
        if path.exists():
            found.append(path)
    return found


def _first_message(sample: RawSample, kind: str, name: str | None = None) -> str | None:
    traj = sample.trajectory
    if traj is None:
        return None
    for message in traj.messages:
        if message.kind != kind:
            continue
        if name is not None and message.name != name:
            continue
        content = message.content
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, dict):
            text = content.get("text") or content.get("content")
            if isinstance(text, str) and text.strip():
                return text
    return None


def _assistant_output(sample: RawSample) -> str | None:
    direct = _first_message(sample, "assistant")
    if direct:
        return direct
    traj = sample.trajectory
    if traj is None:
        return None
    for message in reversed(traj.messages):
        if message.kind in {"assistant", "output"} and isinstance(message.content, str):
            return message.content
    return None


def parse_raw_evaluation(path: Path) -> ArchiveRun:
    raw = RawEvaluation.model_validate_json(path.read_text(encoding="utf-8"))
    metrics = dict(raw.summary.metrics) if raw.summary else {}
    official = metrics.get("avg_score_total")
    try:
        official_score = float(official) if official is not None else None
    except (TypeError, ValueError):
        official_score = None

    skill_snapshot = None
    samples: list[ArchivedSample] = []
    for item in raw.results:
        sample_skill = _first_message(item, "tool_return", name="load_skill")
        if skill_snapshot is None and sample_skill:
            skill_snapshot = sample_skill
        samples.append(_sample_from_raw(item, path, sample_skill or skill_snapshot))

    return ArchiveRun(
        source_path=str(path),
        label=path.parent.name,
        official_score=official_score,
        metrics=metrics,
        samples=samples,
        skill_snapshot=skill_snapshot,
    )


def _sample_from_raw(item: RawSample, path: Path, skill_snapshot: str | None) -> ArchivedSample:
    result = item.result
    grades: list[GraderScore] = []
    gate_passed = None
    weighted = None
    if result is not None:
        weighted = result.weighted_score
        if result.gate_passed is not None:
            gate_passed = bool(result.gate_passed)
        for name, body in result.grades_by_key.items():
            grades.append(
                GraderScore(name=name, score=_as_float(body.score), rationale=body.rationale)
            )
    scenario_id = item.sample_id or item.id or "unknown"
    return ArchivedSample(
        scenario_id=str(scenario_id),
        source_path=str(path),
        scenario_input=_first_message(item, "user") or "",
        assistant_output=_assistant_output(item),
        gate_passed=gate_passed,
        weighted_score=weighted,
        grader_scores=grades,
        skill_snapshot=skill_snapshot,
    )


def _as_float(value: float | int | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_archives(
    sources: Iterable[Path | str] | None = None,
    root: Path | None = None,
) -> list[ArchiveRun]:
    base = root or repo_root()
    if sources is None:
        paths = discover_archive_paths(base)
    else:
        paths = []
        for source in sources:
            path = Path(source)
            if not path.is_absolute():
                path = (base / path).resolve() if not path.exists() else path.resolve()
            if path.exists():
                paths.append(path)
    return [parse_raw_evaluation(path) for path in paths]


def load_archive(path: Path | str, root: Path | None = None) -> ArchiveRun:
    runs = load_archives([path], root=root)
    if not runs:
        raise FileNotFoundError(f"Archive not found: {path}")
    return runs[0]
