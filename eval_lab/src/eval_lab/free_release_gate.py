"""Internal free-release gate. Thresholds are not official SN121 scores."""

from __future__ import annotations

from eval_lab.free_tournament import LIMITATION, evaluate_candidate

THRESHOLDS = {
    "catastrophic_logic_failures": ("==", 0),
    "disposition_accuracy": (">=", 0.995),
    "action_precision": (">=", 0.995),
    "action_recall": (">=", 0.99),
    "constraint_accuracy": ("==", 1.0),
    "invariant_pass_rate": ("==", 1.0),
    "controlled_flip_pass_rate": (">=", 0.995),
    "pairwise_bias_pass_rate": ("==", 1.0),
    "candidate_policy_alignment_pass": ("==", True),
    "generalization_proxy": (">=", 0.85),
}

DISCLAIMER = (
    "These are INTERNAL logic thresholds, not official SN121 validator thresholds. " + LIMITATION
)


def _ok(comparator: str, observed, threshold) -> bool:
    if comparator == "==":
        return observed == threshold
    if comparator == ">=":
        return observed >= threshold
    return False


def evaluate_free_release(candidate: str, corpora: dict | None = None) -> dict:
    row = evaluate_candidate(candidate, corpora)
    conditions = []
    for name, (comparator, threshold) in THRESHOLDS.items():
        observed = row.get(name)
        status = "PASS" if _ok(comparator, observed, threshold) else "FAIL"
        conditions.append(
            {
                "name": name,
                "status": status,
                "observed": observed,
                "threshold": threshold,
                "comparator": comparator,
            }
        )
    passed = all(item["status"] == "PASS" for item in conditions)
    return {
        "candidate": row["candidate"],
        "candidate_sha256": row["candidate_sha256"],
        "passed": passed,
        "mode": "free-logic",
        "disclaimer": DISCLAIMER,
        "conditions": conditions,
        "metrics": row,
        "network_calls": 0,
        "openrouter_calls": 0,
        "paid_calls": 0,
    }
