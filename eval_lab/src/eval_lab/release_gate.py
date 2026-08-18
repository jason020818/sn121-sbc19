"""Internal release gate. PASS is not an official SN121 guarantee."""

from __future__ import annotations

from typing import Any

from eval_lab.config import ReleaseGateConfig
from eval_lab.models import InternalScore

RELEASE_DISCLAIMER = (
    "PASS means this candidate met our internal release criteria. "
    "It does not guarantee an official SN121 score."
)


def combined_hard_failures(regression: dict | None, holdout: dict | None) -> int:
    """Sum catastrophic deterministic failures across regression and holdout."""
    return int((regression or {}).get("hard_failures") or 0) + int((holdout or {}).get("hard_failures") or 0)


class ReleaseDecision:
    def __init__(self, passed: bool, conditions: list[dict[str, Any]], mode: str = "live") -> None:
        self.passed = passed
        self.conditions = conditions
        self.mode = mode
        self.disclaimer = RELEASE_DISCLAIMER

    def failed_names(self) -> list[str]:
        return [item["name"] for item in self.conditions if item.get("status") == "FAIL"]

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "mode": self.mode,
            "disclaimer": self.disclaimer,
            "conditions": self.conditions,
        }


def _condition(name: str, passed: bool, observed: Any, threshold: Any, comparator: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "threshold": threshold,
        "comparator": comparator,
    }


def evaluate_release(
    *,
    gate: ReleaseGateConfig,
    regression_median: float | None,
    holdout_median: float | None,
    holdout_worst_repeat: float | None,
    holdout_stddev: float | None,
    grounding_pass_rate: float | None,
    catastrophic_failures: int | None,
    generalization_proxy: float | None,
) -> ReleaseDecision:
    missing = []
    required = {
        "regression_median": regression_median,
        "holdout_median": holdout_median,
        "holdout_worst_repeat": holdout_worst_repeat,
        "holdout_stddev": holdout_stddev,
        "grounding_pass_rate": grounding_pass_rate,
        "catastrophic_failures": catastrophic_failures,
        "generalization_proxy": generalization_proxy,
    }
    for key, value in required.items():
        if value is None:
            missing.append(key)
    if missing:
        conditions = [
            {
                "name": key,
                "status": "DATA_ERROR",
                "observed": None,
                "threshold": None,
                "comparator": "present",
            }
            for key in missing
        ]
        return ReleaseDecision(passed=False, conditions=conditions, mode="data_error")

    conditions = [
        _condition(
            "no_catastrophic_deterministic_failures",
            catastrophic_failures <= gate.max_catastrophic_failures,
            catastrophic_failures,
            gate.max_catastrophic_failures,
            "<=",
        ),
        _condition(
            "generalization_proxy",
            generalization_proxy >= gate.min_dataset_generalization_proxy,
            generalization_proxy,
            gate.min_dataset_generalization_proxy,
            ">=",
        ),
        _condition(
            "regression_median",
            regression_median >= gate.min_regression_median,
            regression_median,
            gate.min_regression_median,
            ">=",
        ),
        _condition(
            "holdout_median",
            holdout_median >= gate.min_holdout_median,
            holdout_median,
            gate.min_holdout_median,
            ">=",
        ),
        _condition(
            "holdout_worst_repeat",
            holdout_worst_repeat >= gate.min_holdout_worst_repeat,
            holdout_worst_repeat,
            gate.min_holdout_worst_repeat,
            ">=",
        ),
        _condition(
            "holdout_stddev",
            holdout_stddev <= gate.max_repeat_stddev,
            holdout_stddev,
            gate.max_repeat_stddev,
            "<=",
        ),
        _condition(
            "grounding_pass_rate",
            grounding_pass_rate >= gate.min_grounding_pass_rate,
            grounding_pass_rate,
            gate.min_grounding_pass_rate,
            ">=",
        ),
    ]
    passed = all(item["status"] == "PASS" for item in conditions)
    return ReleaseDecision(passed=passed, conditions=conditions, mode="live")


def grounding_pass_rate(reports: list[Any]) -> float:
    if not reports:
        return 0.0
    passed = 0
    total = 0
    for report in reports:
        checks = report.checks if hasattr(report, "checks") else report.get("checks", [])
        for check in checks:
            name = check.name if hasattr(check, "name") else check.get("name")
            ok = check.passed if hasattr(check, "passed") else check.get("passed")
            if name in {"entity_grounding", "amount_grounding"}:
                total += 1
                if ok:
                    passed += 1
    if total == 0:
        return 1.0
    return passed / total


def scores_from_internal(items: list[InternalScore]) -> list[float]:
    return [item.penalized for item in items]
