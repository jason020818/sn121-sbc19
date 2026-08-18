"""Free release gate tests."""

from eval_lab.free_release_gate import THRESHOLDS, evaluate_free_release
from eval_lab.free_tournament import evaluate_candidate
from eval_lab.metamorphic import generate_metamorphic, generate_pairwise
from eval_lab.oracle_evaluator import generate_oracle_corpus


def test_thresholds_are_internal_not_official() -> None:
    assert THRESHOLDS["catastrophic_logic_failures"] == ("==", 0)
    assert THRESHOLDS["disposition_accuracy"] == (">=", 0.995)
    assert THRESHOLDS["constraint_accuracy"] == ("==", 1.0)


def test_free_release_passes_on_tiny_consistent_corpus() -> None:
    bases = generate_oracle_corpus(count=24, seed=121190100)
    corpora = {
        "bases": bases,
        "variants": generate_metamorphic(bases, variants_per_base=4),
        "pairs": generate_pairwise(count=24),
    }
    decision = evaluate_free_release("candidate-c-minimal", corpora)
    assert decision["passed"]
    assert decision["network_calls"] == 0
    row = evaluate_candidate("candidate-b-ledger", corpora)
    assert row["candidate_policy_alignment_pass"] is True
    assert row["catastrophic_logic_failures"] == 0
