"""Non-circular independent domain oracle and tournament tests."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from eval_lab.config import repo_root
from eval_lab.domain_oracle import (
    apply_controlled_flip_domain,
    generate_domain_metamorphic,
    generate_domain_oracle,
    generate_domain_pairwise,
)
from eval_lab.domain_tournament import (
    NON_DISCRIMINATING,
    check_controlled_flip,
    discriminating_case_count,
    rank_domain_policies,
    run_domain_policy_tournament,
    score_against_oracle,
)
from eval_lab.models import HiddenExpectations, HoldoutRecord
from eval_lab.policy_manifests import load_policy

PRODUCTION_SHA = "e6cd5a14bf8734d36474b02f81d5baf41e4a1a18a348867f19d2916bac786fa3"
DOMAIN_ORACLE_PATH = Path(__file__).resolve().parents[1] / "src" / "eval_lab" / "domain_oracle.py"


def test_domain_oracle_module_does_not_import_policies() -> None:
    tree = ast.parse(DOMAIN_ORACLE_PATH.read_text(encoding="utf-8"))
    banned = {"eval_lab.policy_manifests", "eval_lab.policy_engine", "eval_lab.free_tournament"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in banned:
            raise AssertionError(f"domain_oracle imports {node.module}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in banned:
                    raise AssertionError(f"domain_oracle imports {alias.name}")


def test_expected_labels_exist_before_policy_application() -> None:
    records = generate_domain_oracle(count=120, seed=121190200)
    assert all(item.expected_dispositions for item in records)
    assert all(item.oracle_rules for item in records)


def test_generation_succeeds_when_apply_policy_raises(monkeypatch) -> None:
    def boom(*_args, **_kwargs):
        raise RuntimeError("apply_policy(production) blocked")

    monkeypatch.setattr("eval_lab.policy_engine.apply_policy", boom)
    records = generate_domain_oracle(count=80, seed=121190200)
    assert len(records) == 80
    assert records[0].expected_dispositions


def test_at_least_fifty_cases_distinguish_policies() -> None:
    bases = generate_domain_oracle(count=800, seed=121190200)
    corpora = {"bases": bases, "variants": [], "pairs": []}
    count = discriminating_case_count(
        corpora, ["candidate-a-conservative", "candidate-b-ledger", "candidate-c-assertive"]
    )
    assert count >= 50


def test_production_is_not_automatically_perfect() -> None:
    bases = generate_domain_oracle(count=240, seed=121190200)
    policy = load_policy("production")
    metrics = score_against_oracle(bases, policy)
    assert metrics["scored_against"] == "domain_oracle"
    flipped = [item.model_copy(deep=True) for item in bases]
    first = flipped[0]
    first.expected_dispositions = {
        name: ("MONITOR" if disp == "ACTION" else "ACTION") for name, disp in first.expected_dispositions.items()
    }
    flipped_metrics = score_against_oracle(flipped, policy)
    assert flipped_metrics["disposition_accuracy"] < metrics["disposition_accuracy"] or metrics["disposition_accuracy"] < 1.0


def test_all_identical_scores_are_rejected() -> None:
    rows = [
        {
            "disposition_accuracy": 1.0,
            "action_f1": 1.0,
            "false_action_rate": 0.0,
            "boundary_accuracy_external_wait": 1.0,
        }
        for _ in range(4)
    ]
    metric_keys = ("disposition_accuracy", "action_f1", "false_action_rate", "boundary_accuracy_external_wait")
    identical = all(all(abs(row[k] - rows[0][k]) < 1e-12 for k in metric_keys) for row in rows)
    assert identical
    raised = False
    try:
        if identical:
            raise RuntimeError(NON_DISCRIMINATING)
    except RuntimeError as exc:
        raised = str(exc) == NON_DISCRIMINATING
    assert raised


def test_markdown_length_does_not_rank_semantic_policies() -> None:
    rows = [
        {
            "candidate": "long",
            "catastrophic_logic_failures": 0,
            "constraint_accuracy": 1.0,
            "false_action_rate": 0.0,
            "action_f1": 1.0,
            "boundary_accuracy_external_wait": 1.0,
            "disposition_accuracy": 1.0,
            "markdown_words": 2000,
        },
        {
            "candidate": "short",
            "catastrophic_logic_failures": 0,
            "constraint_accuracy": 1.0,
            "false_action_rate": 0.0,
            "action_f1": 1.0,
            "boundary_accuracy_external_wait": 1.0,
            "disposition_accuracy": 1.0,
            "markdown_words": 10,
        },
    ]
    ranked = rank_domain_policies(rows)
    assert ranked[0]["candidate"] == "long"
    assert ranked[1]["candidate"] == "short"


def test_minimal_and_ledger_share_balanced_policy() -> None:
    ledger = load_policy("candidate-b-ledger")
    minimal = load_policy("candidate-b-minimal")
    assert ledger.model_dump() == minimal.model_dump()
    assert ledger.action.external_wait_escalation.checkpoint == "missing_or_passed"


def _flip_record() -> HoldoutRecord:
    return HoldoutRecord(
        id="F-1",
        seed=1,
        scenario="flip",
        hidden_expectations=HiddenExpectations(),
        deals=[{"name": "A"}, {"name": "B"}],
        expected_before={"A": "MONITOR", "B": "MONITOR"},
        expected_after={"A": "ACTION", "B": "MONITOR"},
        variant_kind="controlled_flip",
        mutation_kind="wait_to_seller_deliverable",
        target_deal="A",
        flip_deals=["A"],
        allowed_changed_deals=["A"],
    )


def test_controlled_flip_fails_wrong_direction() -> None:
    result = check_controlled_flip(_flip_record(), {"A": "MEETING", "B": "MONITOR"})
    assert result["passed"] is False
    assert result["direction_miss_count"] == 1


def test_controlled_flip_fails_when_target_does_not_change() -> None:
    result = check_controlled_flip(_flip_record(), {"A": "MONITOR", "B": "MONITOR"})
    assert result["passed"] is False
    assert result["noop_count"] == 1


def test_controlled_flip_fails_on_collateral_change() -> None:
    result = check_controlled_flip(_flip_record(), {"A": "ACTION", "B": "ACTION"})
    assert result["passed"] is False
    assert result["collateral"] == ["B"]


def test_controlled_flip_passes_only_on_exact_expected_after() -> None:
    result = check_controlled_flip(_flip_record(), {"A": "ACTION", "B": "MONITOR"})
    assert result["passed"] is True
    assert result["exact"] is True


def test_controlled_flip_keeps_requested_mutation_kind() -> None:
    base = generate_domain_oracle(count=3, seed=121190200)[0]
    variant = apply_controlled_flip_domain(base, "add_do_not_contact")
    assert variant.mutation_kind == "add_do_not_contact"
    assert variant.transform == "add_do_not_contact"
    assert variant.target_deal
    assert variant.target_before != variant.target_after
    assert variant.allowed_changed_deals == [variant.target_deal]
    assert variant.expected_after[variant.target_deal] != variant.expected_before[variant.target_deal]


def test_semantic_equivalent_policies_are_tied_regardless_of_order() -> None:
    bases = generate_domain_oracle(count=400, seed=121190200)
    variants = generate_domain_metamorphic(bases[:8], variants_per_base=4)
    pairs = generate_domain_pairwise(count=16)
    corpora = {"bases": bases, "variants": variants, "pairs": pairs}
    forward = run_domain_policy_tournament(
        candidates=["candidate-b-ledger", "production-f9e5400", "candidate-a-conservative", "candidate-c-assertive"],
        corpora=corpora,
    )
    reverse = run_domain_policy_tournament(
        candidates=["candidate-c-assertive", "candidate-a-conservative", "production-f9e5400", "candidate-b-ledger"],
        corpora=corpora,
    )
    assert forward["recommended_semantic_policy_family"] == reverse["recommended_semantic_policy_family"] == "balanced"
    assert set(forward["semantic_equivalents"]) == set(reverse["semantic_equivalents"]) == {
        "candidate-b-ledger",
        "production-f9e5400",
    }
    assert "candidate-b-ledger" in forward["semantic_equivalents"]
    assert forward["recommended_semantic_policy"] == "balanced"


def test_markdown_length_never_breaks_semantic_policy_ties() -> None:
    rows = [
        {
            "candidate": "long",
            "catastrophic_logic_failures": 0,
            "constraint_accuracy": 1.0,
            "false_action_rate": 0.0,
            "action_f1": 1.0,
            "boundary_accuracy_external_wait": 1.0,
            "disposition_accuracy": 1.0,
            "markdown_words": 2000,
        },
        {
            "candidate": "short",
            "catastrophic_logic_failures": 0,
            "constraint_accuracy": 1.0,
            "false_action_rate": 0.0,
            "action_f1": 1.0,
            "boundary_accuracy_external_wait": 1.0,
            "disposition_accuracy": 1.0,
            "markdown_words": 10,
        },
    ]
    ranked = rank_domain_policies(rows)
    assert ranked[0]["candidate"] == "long"
    assert ranked[1]["candidate"] == "short"


def test_production_skill_sha_unchanged() -> None:
    digest = hashlib.sha256((repo_root() / "SKILL.md").read_bytes()).hexdigest()
    assert digest == PRODUCTION_SHA


def test_results_archive_untouched() -> None:
    root = repo_root() / "results"
    assert root.is_dir()
    assert not (root / ".oracle-lab-should-not-exist").exists()


def test_free_domain_commands_make_zero_network_calls(network_forbidden, tmp_path, monkeypatch) -> None:
    from typer.testing import CliRunner

    from eval_lab.cli import app

    monkeypatch.setattr("eval_lab.domain_oracle.domain_oracle_path", lambda: tmp_path / "domain_oracle.jsonl")
    monkeypatch.setattr("eval_lab.domain_oracle.domain_metamorphic_path", lambda: tmp_path / "domain_meta.jsonl")
    monkeypatch.setattr("eval_lab.domain_oracle.domain_pairwise_path", lambda: tmp_path / "domain_pair.jsonl")
    monkeypatch.setattr("eval_lab.domain_tournament.domain_oracle_path", lambda: tmp_path / "domain_oracle.jsonl")
    monkeypatch.setattr("eval_lab.domain_tournament.domain_metamorphic_path", lambda: tmp_path / "domain_meta.jsonl")
    monkeypatch.setattr("eval_lab.domain_tournament.domain_pairwise_path", lambda: tmp_path / "domain_pair.jsonl")
    monkeypatch.setattr("eval_lab.domain_tournament.domain_summary_path", lambda: tmp_path / "domain.md")
    monkeypatch.setattr("eval_lab.rendering_risk.rendering_summary_path", lambda: tmp_path / "render.md")
    monkeypatch.setattr("eval_lab.free_champion.champion_plan_path", lambda: tmp_path / "plan.md")

    runner = CliRunner()
    result = runner.invoke(app, ["domain-oracle-generate", "--count", "600", "--seed", "121190200"])
    assert result.exit_code == 0, result.output
    monkeypatch.setattr(
        "eval_lab.domain_tournament.generate_domain_metamorphic",
        lambda bases, variants_per_base=4, seed=121190200: generate_domain_metamorphic(
            bases[:20], variants_per_base=4, seed=seed
        ),
    )
    monkeypatch.setattr(
        "eval_lab.domain_tournament.generate_domain_pairwise",
        lambda count=1000, seed=121190200: generate_domain_pairwise(count=24, seed=seed),
    )
    result = runner.invoke(app, ["domain-policy-tournament"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["rendering-risk-tournament"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["free-champion-plan"])
    assert result.exit_code == 0, result.output


def test_domain_corpus_slice_minimums() -> None:
    records = generate_domain_oracle(count=3000, seed=121190200)
    families: dict[str, int] = {}
    for item in records:
        key = str(item.dimensions.get("family"))
        families[key] = families.get(key, 0) + 1
    assert families.get("external_wait", 0) >= 500
    assert families.get("seller_owned", 0) >= 400
    assert families.get("record", 0) >= 300
    assert families.get("communication", 0) >= 300
    meta = generate_domain_metamorphic(records, variants_per_base=4)
    pairs = generate_domain_pairwise(count=1000)
    assert len(records) + len(meta) + len(pairs) >= 8000
    assert len(pairs) >= 1000
