"""Free tournament ranking and CLI network-forbidden tests."""

from typer.testing import CliRunner

from eval_lab.cli import app
from eval_lab.free_tournament import rank_free, reserves
from eval_lab.metamorphic import generate_pairwise


def test_pairwise_count() -> None:
    records = generate_pairwise(count=1000, seed=121190100)
    assert len(records) >= 1000
    families = {item.transform for item in records}
    assert "amount_bias" in families
    assert "deal_order_bias" in families


def test_rank_uses_catastrophic_then_length() -> None:
    rows = [
        {
            "candidate": "long",
            "catastrophic_logic_failures": 0,
            "invariant_violation_count": 0,
            "constraint_violations": 0,
            "action_f1": 1.0,
            "disposition_accuracy": 1.0,
            "controlled_flip_pass_rate": 1.0,
            "markdown_words": 400,
        },
        {
            "candidate": "short",
            "catastrophic_logic_failures": 0,
            "invariant_violation_count": 0,
            "constraint_violations": 0,
            "action_f1": 1.0,
            "disposition_accuracy": 1.0,
            "controlled_flip_pass_rate": 1.0,
            "markdown_words": 200,
        },
        {
            "candidate": "bad",
            "catastrophic_logic_failures": 2,
            "invariant_violation_count": 0,
            "constraint_violations": 0,
            "action_f1": 1.0,
            "disposition_accuracy": 1.0,
            "controlled_flip_pass_rate": 1.0,
            "markdown_words": 10,
        },
    ]
    ranked = rank_free(rows)
    assert [row["candidate"] for row in ranked] == ["short", "long", "bad"]
    chosen = reserves(ranked)
    assert chosen["production_recommendation"] == "short"
    assert chosen["reserve_1"] == "long"
    assert chosen["reserve_2"] == "bad"


def test_free_cli_commands_make_zero_network_calls(network_forbidden, tmp_path, monkeypatch) -> None:
    base = tmp_path / "oracle_base.jsonl"
    meta = tmp_path / "oracle_metamorphic.jsonl"
    pair = tmp_path / "oracle_pairwise.jsonl"
    summary = tmp_path / "free-tournament-summary.md"
    monkeypatch.setattr("eval_lab.oracle_evaluator.oracle_base_path", lambda: base)
    monkeypatch.setattr("eval_lab.metamorphic.oracle_base_path", lambda: base)
    monkeypatch.setattr("eval_lab.metamorphic.metamorphic_path", lambda: meta)
    monkeypatch.setattr("eval_lab.metamorphic.pairwise_path", lambda: pair)
    monkeypatch.setattr("eval_lab.free_tournament.oracle_base_path", lambda: base)
    monkeypatch.setattr("eval_lab.free_tournament.metamorphic_path", lambda: meta)
    monkeypatch.setattr("eval_lab.free_tournament.pairwise_path", lambda: pair)
    monkeypatch.setattr("eval_lab.free_tournament.summary_path", lambda: summary)

    runner = CliRunner()
    result = runner.invoke(app, ["oracle-generate", "--count", "8", "--seed", "121190100"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["metamorphic-generate", "--variants-per-base", "4"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["pairwise-generate", "--count", "16"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["policy-check", "--candidate", "production-f9e5400"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["oracle-run", "--candidate", "production-f9e5400"])
    assert result.exit_code == 0, result.output
    result = runner.invoke(
        app,
        [
            "free-tournament",
            "--candidates",
            "production-f9e5400",
            "--candidates",
            "candidate-a-conservative",
        ],
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["free-release-check", "--candidate", "production-f9e5400"])
    assert result.exit_code == 0, result.output
