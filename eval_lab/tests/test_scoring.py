"""Internal scoring and SKILL.md write-protection tests."""

from pathlib import Path

from eval_lab.candidate_store import add_candidate
from eval_lab.config import repo_root
from eval_lab.deterministic_checks import run_deterministic_checks
from eval_lab.models import JudgeDimensionScores
from eval_lab.scoring import generalization_proxy, score_output, summarize_repeats


def _judge(value: float = 0.8) -> JudgeDimensionScores:
    return JudgeDimensionScores(
        grounding_accuracy=value,
        prioritization_quality=value,
        actionability=value,
        waiting_state_judgment=value,
        meeting_preparation_quality=value,
        concision=value,
        skill_adherence=value,
    )


def test_internal_score_penalties() -> None:
    clean = run_deterministic_checks(
        "Deal Helix Bureau ($10K). Contact Ira Calder.",
        "## Priority Actions\n1. **Helix Bureau** — Send the scope to Ira Calder ($10K).\n",
    )
    scored = score_output([_judge(1.0), _judge(0.5)], clean)
    assert abs(scored.unpenalized - 0.75) < 1e-6
    assert scored.penalty_applied in {"none", "minor"}

    bad = run_deterministic_checks(
        "Deal Helix Bureau ($10K).",
        "## Priority Actions\n1. **Ghost Company** — Call nobody about $999K.\n",
    )
    zeroed = score_output([_judge(1.0)], bad)
    assert zeroed.penalized == 0.0
    assert zeroed.penalty_applied == "catastrophic"


def test_summarize_repeats() -> None:
    stats = summarize_repeats([0.2, 0.4, 0.6, 0.8, 1.0])
    assert stats.median == 0.6
    assert stats.min == 0.2
    assert stats.max == 1.0
    assert stats.n == 5


def test_generalization_proxy_flags_scenario_ids() -> None:
    clean = generalization_proxy("Use exclusive assignment and evidence boundaries.")
    dirty = generalization_proxy("For S-001 and S-006, always pick the P1 deal.")
    assert clean >= 0.85
    assert dirty < 0.85


def test_candidate_add_does_not_write_skill_md(tmp_path: Path, monkeypatch) -> None:
    skill = repo_root() / "SKILL.md"
    before = skill.read_bytes()
    monkeypatch.setattr("eval_lab.candidate_store.lab_root", lambda: tmp_path)
    source = tmp_path / "cand.md"
    source.write_text("# candidate\nUse only supplied facts.\n", encoding="utf-8")
    add_candidate("test-write-guard", source, force=True)
    assert skill.read_bytes() == before
    assert (tmp_path / "candidates" / "test-write-guard.md").exists()
