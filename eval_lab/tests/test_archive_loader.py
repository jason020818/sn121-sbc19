"""Offline tests for archive loading. Loads real archived JSON at runtime."""

from pathlib import Path

from eval_lab.archive_loader import discover_archive_paths, load_archive, load_archives
from eval_lab.config import repo_root


def test_discovers_archived_raw_json() -> None:
    paths = discover_archive_paths()
    names = {path.parent.name for path in paths}
    assert {"mine", "latest", "run-0.7378429", "champion"} <= names


def test_parse_current_archived_raw_json() -> None:
    archive = load_archive("results/run-0.7378429/raw_evaluation.json")
    assert archive.official_score is not None
    assert abs(archive.official_score - 0.7378429) < 1e-6
    assert len(archive.samples) == 10
    first = archive.samples[0]
    assert first.scenario_input
    assert first.assistant_output
    assert first.grader_scores
    assert first.gate_passed is True
    assert archive.skill_snapshot
    assert "morning-read" in archive.skill_snapshot


def test_load_all_archives_without_hardcoded_answers() -> None:
    runs = load_archives()
    assert len(runs) >= 3
    for run in runs:
        assert run.samples
        for sample in run.samples:
            assert sample.scenario_id
            assert isinstance(sample.scenario_input, str)


def test_does_not_write_skill_md(tmp_path: Path) -> None:
    skill = repo_root() / "SKILL.md"
    before = skill.read_bytes()
    load_archives()
    assert skill.read_bytes() == before
