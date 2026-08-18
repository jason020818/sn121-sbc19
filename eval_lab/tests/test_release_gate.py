"""Release-gate and tournament ranking tests."""

from eval_lab.config import ReleaseGateConfig
from eval_lab.release_gate import RELEASE_DISCLAIMER, combined_hard_failures, evaluate_release
from eval_lab.scoring import rank_tournament


def test_release_gate_pass() -> None:
    decision = evaluate_release(
        gate=ReleaseGateConfig(),
        regression_median=0.80,
        holdout_median=0.82,
        holdout_worst_repeat=0.79,
        holdout_stddev=0.01,
        grounding_pass_rate=1.0,
        catastrophic_failures=0,
        generalization_proxy=0.95,
    )
    assert decision.passed is True
    assert all(item["status"] == "PASS" for item in decision.conditions)
    assert RELEASE_DISCLAIMER in decision.disclaimer


def test_release_gate_fail_and_data_error() -> None:
    failed = evaluate_release(
        gate=ReleaseGateConfig(),
        regression_median=0.10,
        holdout_median=0.82,
        holdout_worst_repeat=0.79,
        holdout_stddev=0.01,
        grounding_pass_rate=1.0,
        catastrophic_failures=0,
        generalization_proxy=0.95,
    )
    assert failed.passed is False
    assert "regression_median" in failed.failed_names()

    missing = evaluate_release(
        gate=ReleaseGateConfig(),
        regression_median=None,
        holdout_median=0.82,
        holdout_worst_repeat=0.79,
        holdout_stddev=0.01,
        grounding_pass_rate=1.0,
        catastrophic_failures=0,
        generalization_proxy=0.95,
    )
    assert missing.mode == "data_error"
    assert missing.passed is False


def test_tournament_sorting() -> None:
    rows = [
        {
            "candidate": "lucky-max",
            "catastrophic_failures": 2,
            "holdout_median": 0.99,
            "holdout_worst_repeat": 0.98,
            "regression_median": 0.99,
            "stddev": 0.001,
        },
        {
            "candidate": "stable-a",
            "catastrophic_failures": 0,
            "holdout_median": 0.81,
            "holdout_worst_repeat": 0.78,
            "regression_median": 0.76,
            "stddev": 0.02,
        },
        {
            "candidate": "stable-b",
            "catastrophic_failures": 0,
            "holdout_median": 0.81,
            "holdout_worst_repeat": 0.79,
            "regression_median": 0.70,
            "stddev": 0.01,
        },
    ]
    ranked = rank_tournament(rows)
    assert [row["candidate"] for row in ranked] == ["stable-b", "stable-a", "lucky-max"]
    assert ranked[0]["rank"] == 1


def test_one_regression_catastrophic_fails_release_despite_high_medians() -> None:
    decision = evaluate_release(
        gate=ReleaseGateConfig(),
        regression_median=0.90,
        holdout_median=0.90,
        holdout_worst_repeat=0.88,
        holdout_stddev=0.01,
        grounding_pass_rate=1.0,
        catastrophic_failures=1,
        generalization_proxy=1.0,
    )
    assert decision.passed is False
    assert "no_catastrophic_deterministic_failures" in decision.failed_names()


def test_tournament_catastrophic_count_combines_regression_and_holdout() -> None:
    assert combined_hard_failures({"hard_failures": 1}, {"hard_failures": 2}) == 3
    rows = [
        {
            "candidate": "reg-fail",
            "catastrophic_failures": combined_hard_failures({"hard_failures": 1}, {"hard_failures": 0}),
            "holdout_median": 0.99,
            "holdout_worst_repeat": 0.98,
            "regression_median": 0.99,
            "stddev": 0.001,
        },
        {
            "candidate": "clean",
            "catastrophic_failures": combined_hard_failures({"hard_failures": 0}, {"hard_failures": 0}),
            "holdout_median": 0.80,
            "holdout_worst_repeat": 0.78,
            "regression_median": 0.76,
            "stddev": 0.02,
        },
    ]
    ranked = rank_tournament(rows)
    assert [row["candidate"] for row in ranked] == ["clean", "reg-fail"]
    assert ranked[1]["catastrophic_failures"] == 1
