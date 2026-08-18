"""Oracle corpus and scoring tests."""

from collections import Counter

from eval_lab.oracle_evaluator import (
    BOOK_SIZES,
    ACTION_COUNTS,
    CALENDARS,
    COMMERCIAL,
    CONSTRAINTS,
    DATA,
    OWNERSHIP,
    evaluate_oracle,
    generate_oracle_corpus,
)
from eval_lab.policy_manifests import load_policy


def test_oracle_generation_is_deterministic() -> None:
    a = generate_oracle_corpus(count=40, seed=121190100)
    b = generate_oracle_corpus(count=40, seed=121190100)
    assert [item.model_dump() for item in a] == [item.model_dump() for item in b]
    c = generate_oracle_corpus(count=40, seed=121190101)
    assert a[0].scenario != c[0].scenario


def test_oracle_1200_coverage() -> None:
    records = generate_oracle_corpus(count=1200, seed=121190100)
    assert len(records) == 1200
    assert {item.dimensions["book_size"] for item in records} == set(BOOK_SIZES)
    expected = {
        "book_size": BOOK_SIZES,
        "action_count": ACTION_COUNTS,
        "calendar": CALENDARS,
        "ownership": OWNERSHIP,
        "data": DATA,
        "constraint": CONSTRAINTS,
        "commercial": COMMERCIAL,
    }
    for key, values in expected.items():
        counts = Counter(item.dimensions[key] for item in records)
        assert set(counts) == set(values)
        assert min(counts.values()) >= 30
    assert all(item.deals and item.expected_dispositions for item in records)


def test_production_oracle_is_self_consistent() -> None:
    records = generate_oracle_corpus(count=80, seed=121190100)
    metrics = evaluate_oracle(records, load_policy("production"))
    assert metrics["disposition_accuracy"] == 1.0
    assert metrics["action_precision"] == 1.0
    assert metrics["catastrophic_logic_failures"] == 0
    assert metrics["constraint_accuracy"] == 1.0
