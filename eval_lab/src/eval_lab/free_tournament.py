"""Zero-cost candidate tournament over oracle, metamorphic, and pairwise batteries."""

from __future__ import annotations

from pathlib import Path

from eval_lab.candidate_store import read_candidate
from eval_lab.config import lab_root
from eval_lab.metamorphic import (
    evaluate_metamorphic,
    evaluate_pairwise,
    generate_metamorphic,
    generate_pairwise,
    metamorphic_path,
    pairwise_path,
)
from eval_lab.oracle_evaluator import (
    coverage_summary,
    evaluate_oracle,
    generate_oracle_corpus,
    load_jsonl,
    oracle_base_path,
    write_jsonl,
)
from eval_lab.policy_lint import lint_candidate_policy
from eval_lab.policy_manifests import load_policy
from eval_lab.scoring import generalization_proxy

LIMITATION = (
    "The policy engine verifies LOGIC. It does not simulate Haiku instruction-following "
    "or official SN121 graders. Logic verification is strong evidence of policy correctness; "
    "it does not measure stochastic instruction-following. A live SN121 submission remains "
    "the only official validator sample."
)


def ensure_corpora() -> dict:
    base_path = oracle_base_path()
    meta_path = metamorphic_path()
    pair_path = pairwise_path()
    if not base_path.exists():
        write_jsonl(generate_oracle_corpus(), base_path)
    if not meta_path.exists():
        write_jsonl(generate_metamorphic(), meta_path)
    if not pair_path.exists():
        write_jsonl(generate_pairwise(), pair_path)
    bases = load_jsonl(base_path)
    variants = load_jsonl(meta_path)
    pairs = load_jsonl(pair_path)
    return {"bases": bases, "variants": variants, "pairs": pairs}


def evaluate_candidate(name: str, corpora: dict | None = None) -> dict:
    corpora = corpora or ensure_corpora()
    path, text, digest = read_candidate(name)
    policy = load_policy(name)
    alignment = lint_candidate_policy(text, policy)
    oracle = evaluate_oracle(corpora["bases"], policy)
    meta = evaluate_metamorphic(corpora["bases"], corpora["variants"], policy)
    pair = evaluate_pairwise(corpora["pairs"], policy)
    proxy = generalization_proxy(text)
    catastrophic = int(oracle.get("catastrophic_logic_failures", 0)) + int(meta.get("invariant_violation_count", 0))
    if not alignment["passed"]:
        catastrophic += 1
    row = {
        "candidate": path.stem,
        "candidate_sha256": digest,
        "markdown_words": len(text.split()),
        "markdown_bytes": len(text.encode("utf-8")),
        "policy_name": policy.name,
        "disposition_accuracy": oracle["disposition_accuracy"],
        "action_precision": oracle["action_precision"],
        "action_recall": oracle["action_recall"],
        "action_f1": oracle["action_f1"],
        "meeting_accuracy": oracle["meeting_accuracy"],
        "monitor_accuracy": oracle["monitor_accuracy"],
        "record_accuracy": oracle["record_accuracy"],
        "constraint_accuracy": oracle["constraint_accuracy"],
        "constraint_violations": oracle.get("constraint_fail_count", 0),
        "invariant_pass_rate": meta["invariant_pass_rate"],
        "controlled_flip_pass_rate": meta["controlled_flip_pass_rate"],
        "pairwise_bias_pass_rate": pair["pairwise_bias_pass_rate"],
        "candidate_policy_alignment_pass": alignment["passed"],
        "alignment": alignment,
        "generalization_proxy": proxy,
        "catastrophic_logic_failures": catastrophic,
        "invariant_violation_count": meta["invariant_violation_count"],
        "controlled_flip_miss_count": meta["controlled_flip_miss_count"],
        "collateral_change_count": meta["collateral_change_count"],
        "oracle_n": oracle["n"],
        "limitation": LIMITATION,
    }
    return row


def rank_free(rows: list[dict]) -> list[dict]:
    ranked = sorted(
        rows,
        key=lambda row: (
            int(row.get("catastrophic_logic_failures", 0)),
            int(row.get("invariant_violation_count", 0)),
            int(row.get("constraint_violations", 0)),
            -float(row.get("action_f1", 0.0)),
            -float(row.get("disposition_accuracy", 0.0)),
            -float(row.get("controlled_flip_pass_rate", 0.0)),
            int(row.get("markdown_words", 10**9)),
        ),
    )
    out = []
    for index, row in enumerate(ranked, start=1):
        copied = dict(row)
        copied["rank"] = index
        out.append(copied)
    return out


def reserves(ranked: list[dict]) -> dict:
    names = [row["candidate"] for row in ranked]
    return {
        "production_recommendation": names[0] if names else None,
        "reserve_1": names[1] if len(names) > 1 else None,
        "reserve_2": names[2] if len(names) > 2 else None,
    }


def run_free_tournament(candidates: list[str]) -> dict:
    corpora = ensure_corpora()
    rows = [evaluate_candidate(name, corpora) for name in candidates]
    ranked = rank_free(rows)
    coverage = coverage_summary(corpora["bases"])
    payload = {
        "kind": "free-tournament",
        "disclaimer": LIMITATION,
        "base_count": len(corpora["bases"]),
        "metamorphic_count": len(corpora["variants"]),
        "pairwise_count": len(corpora["pairs"]),
        "coverage": coverage,
        "results": ranked,
        **reserves(ranked),
        "network_calls": 0,
        "openrouter_calls": 0,
        "paid_calls": 0,
    }
    return payload


def render_summary(payload: dict) -> str:
    lines = [
        "# Free tournament summary",
        "",
        payload.get("disclaimer", LIMITATION),
        "",
        f"Base holdouts: {payload.get('base_count')}",
        f"Metamorphic cases: {payload.get('metamorphic_count')}",
        f"Pairwise checks: {payload.get('pairwise_count')}",
        "",
        f"production_recommendation: {payload.get('production_recommendation')}",
        f"reserve_1: {payload.get('reserve_1')}",
        f"reserve_2: {payload.get('reserve_2')}",
        "",
        "SKILL.md was not modified. results/** was not modified. No SN121 submission was made.",
        "",
        "## Ranking",
        "",
    ]
    for row in payload.get("results", []):
        lines.append(
            f"{row['rank']}. {row['candidate']} catastrophic={row['catastrophic_logic_failures']} "
            f"invariant_viol={row['invariant_violation_count']} constraint_viol={row['constraint_violations']} "
            f"action_f1={row['action_f1']:.6f} disposition={row['disposition_accuracy']:.6f} "
            f"flip={row['controlled_flip_pass_rate']:.6f} words={row['markdown_words']}"
        )
    lines.extend(["", "## Behavioral metrics", ""])
    for row in payload.get("results", []):
        lines.append(f"### {row['candidate']}")
        for key in [
            "disposition_accuracy",
            "action_precision",
            "action_recall",
            "action_f1",
            "meeting_accuracy",
            "monitor_accuracy",
            "record_accuracy",
            "constraint_accuracy",
            "invariant_pass_rate",
            "controlled_flip_pass_rate",
            "pairwise_bias_pass_rate",
            "candidate_policy_alignment_pass",
            "catastrophic_logic_failures",
            "generalization_proxy",
        ]:
            lines.append(f"- {key}: {row.get(key)}")
        lines.append("")
    lines.extend(["## Coverage minima", ""])
    coverage = payload.get("coverage") or {}
    for key, value in coverage.items():
        if key.endswith("_min"):
            lines.append(f"- {key}: {value}")
    lines.extend(["", "## Confirmations", "", "- zero network calls", "- zero paid OpenRouter calls", "- no SN121 submission", ""])
    return "\n".join(lines) + "\n"


def summary_path() -> Path:
    path = lab_root() / "reports" / "free-tournament-summary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
