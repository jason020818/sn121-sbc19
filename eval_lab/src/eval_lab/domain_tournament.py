"""Domain-policy tournament against the independent oracle. No markdown-length ranking."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from eval_lab.config import lab_root
from eval_lab.domain_oracle import (
    domain_metamorphic_path,
    domain_oracle_path,
    domain_pairwise_path,
    generate_domain_metamorphic,
    generate_domain_oracle,
    generate_domain_pairwise,
    load_jsonl,
    write_jsonl,
)
from eval_lab.models import HoldoutRecord
from eval_lab.policy_engine import apply_policy
from eval_lab.policy_manifests import load_policy
from eval_lab.policy_models import DealFact, PolicyManifest

NON_DISCRIMINATING = "NON_DISCRIMINATING_ORACLE"
LIMITATION = (
    "Domain scoring compares candidate policy engines to an independent sales-ops contract. "
    "It does not simulate Haiku instruction-following."
)
DOMAIN_CANDIDATES = [
    "candidate-b-ledger",
    "production-f9e5400",
    "candidate-a-conservative",
    "candidate-c-assertive",
]


def ensure_domain_corpora(count: int = 3000, seed: int = 121190200) -> dict:
    base_path = domain_oracle_path()
    meta_path = domain_metamorphic_path()
    pair_path = domain_pairwise_path()
    if not base_path.exists():
        write_jsonl(generate_domain_oracle(count=count, seed=seed), base_path)
    bases = load_jsonl(base_path)
    if not meta_path.exists():
        write_jsonl(generate_domain_metamorphic(bases), meta_path)
    if not pair_path.exists():
        write_jsonl(generate_domain_pairwise(count=1000, seed=seed), pair_path)
    return {"bases": bases, "variants": load_jsonl(meta_path), "pairs": load_jsonl(pair_path)}


def _deals(record: HoldoutRecord) -> list[DealFact]:
    return [DealFact.model_validate({k: v for k, v in item.items() if k != "_right"}) for item in record.deals if not item.get("_right")]


def score_against_oracle(records: list[HoldoutRecord], policy: PolicyManifest) -> dict:
    sums: Counter[str] = Counter()
    n_deals = 0
    n_cases = 0
    tp = fp = fn = 0
    catastrophic = 0
    constraint_fail = 0
    slice_hit = {"external_wait": [0, 0], "record": [0, 0], "communication": [0, 0]}
    for record in records:
        deals = _deals(record)
        actual = apply_policy(deals, policy)
        expected = record.expected_dispositions
        catastrophic += len(actual.catastrophic)
        n_cases += 1
        family = str(record.dimensions.get("family", ""))
        for name, exp in expected.items():
            got = actual.dispositions.get(name)
            n_deals += 1
            correct = int(got == exp)
            sums["disposition_correct"] += correct
            if family in slice_hit:
                slice_hit[family][1] += 1
                slice_hit[family][0] += correct
            if exp == "ACTION" and got == "ACTION":
                tp += 1
            elif exp != "ACTION" and got == "ACTION":
                fp += 1
            elif exp == "ACTION" and got != "ACTION":
                fn += 1
            for label in ("MEETING", "MONITOR", "RECORD"):
                key = f"{label.lower()}_union"
                if exp == label or got == label:
                    sums[key] += 1
                    if exp == got:
                        sums[f"{label.lower()}_inter"] += 1
            hold = actual.constraint_holds.get(name)
            if hold in {"do_not_contact", "wait_until"} and got == "ACTION":
                constraint_fail += 1
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 1.0

    def acc(label: str) -> float:
        union = sums[f"{label}_union"]
        return sums[f"{label}_inter"] / union if union else 1.0

    def slice_acc(name: str) -> float:
        good, total = slice_hit[name]
        return good / total if total else 1.0

    return {
        "disposition_accuracy": sums["disposition_correct"] / n_deals if n_deals else 1.0,
        "action_precision": precision,
        "action_recall": recall,
        "action_f1": f1,
        "false_action_rate": fp / n_deals if n_deals else 0.0,
        "missed_action_rate": fn / n_deals if n_deals else 0.0,
        "meeting_accuracy": acc("meeting"),
        "record_accuracy": acc("record"),
        "monitor_accuracy": acc("monitor"),
        "constraint_accuracy": 1.0 if constraint_fail == 0 else max(0.0, 1.0 - constraint_fail / n_deals),
        "catastrophic_logic_failures": catastrophic,
        "boundary_accuracy_external_wait": slice_acc("external_wait"),
        "boundary_accuracy_record": slice_acc("record"),
        "boundary_accuracy_contact": slice_acc("communication"),
        "n_deals": n_deals,
        "n_cases": n_cases,
        "scored_against": "domain_oracle",
    }


def evaluate_invariants(bases: list[HoldoutRecord], variants: list[HoldoutRecord], policy: PolicyManifest) -> dict:
    by_id = {item.id: item for item in bases}
    inv_n = inv_pass = 0
    flip_n = flip_pass = 0
    for variant in variants:
        parent = by_id.get(variant.parent_id or "")
        if parent is None:
            continue
        actual = apply_policy(_deals(variant), policy)
        if variant.variant_kind == "invariant":
            inv_n += 1
            mapping = variant.name_map or {}
            expected = {mapping.get(k, k): v for k, v in parent.expected_dispositions.items()}
            ok = all(actual.dispositions.get(name) == disp for name, disp in expected.items())
            extra = set(actual.dispositions) - set(expected)
            ok = ok and all(actual.dispositions[name] == "MONITOR" for name in extra)
            inv_pass += int(ok)
        elif variant.variant_kind == "controlled_flip":
            flip_n += 1
            before = variant.expected_before or parent.expected_dispositions
            changed = [name for name in before if actual.dispositions.get(name) != before[name]]
            new_names = [name for name in actual.dispositions if name not in before]
            collateral = [name for name in changed if name not in set(variant.flip_deals)]
            flip_pass += int(bool(not collateral and (changed or new_names)))
    return {
        "invariant_pass_rate": inv_pass / inv_n if inv_n else 1.0,
        "controlled_flip_pass_rate": flip_pass / flip_n if flip_n else 1.0,
        "invariant_n": inv_n,
        "controlled_flip_n": flip_n,
    }


def evaluate_pairwise(records: list[HoldoutRecord], policy: PolicyManifest) -> dict:
    n = passed = 0
    for record in records:
        left = [DealFact.model_validate({k: v for k, v in item.items() if k != "_right"}) for item in record.deals if not item.get("_right")]
        right = [DealFact.model_validate({k: v for k, v in item.items() if k != "_right"}) for item in record.deals if item.get("_right")]
        left_dec = apply_policy(left, policy)
        right_dec = apply_policy(right, policy)
        family = record.transform
        if family == "company_name_bias":
            ok = list(left_dec.dispositions.values()) == list(right_dec.dispositions.values())
        elif family == "add_monitor":
            shared = set(left_dec.dispositions)
            ok = all(left_dec.dispositions[name] == right_dec.dispositions.get(name) for name in shared)
            ok = ok and all(right_dec.dispositions[name] == "MONITOR" for name in set(right_dec.dispositions) - shared)
        else:
            ok = left_dec.dispositions == right_dec.dispositions or list(left_dec.dispositions.values()) == list(right_dec.dispositions.values())
            if set(left_dec.dispositions) == set(right_dec.dispositions):
                ok = left_dec.dispositions == right_dec.dispositions
        n += 1
        passed += int(ok)
    return {"pairwise_bias_pass_rate": passed / n if n else 1.0, "pairwise_n": n}


def evaluate_domain_policy(name: str, corpora: dict) -> dict:
    policy = load_policy(name)
    metrics = score_against_oracle(corpora["bases"], policy)
    metrics.update(evaluate_invariants(corpora["bases"], corpora["variants"], policy))
    metrics.update(evaluate_pairwise(corpora["pairs"], policy))
    metrics["candidate"] = name
    metrics["policy_name"] = policy.name
    return metrics


def discriminating_case_count(corpora: dict, names: list[str] | None = None) -> int:
    names = names or DOMAIN_CANDIDATES
    policies = [(name, load_policy(name)) for name in names]
    count = 0
    for record in corpora["bases"]:
        deals = _deals(record)
        maps = [tuple(sorted(apply_policy(deals, policy).dispositions.items())) for _, policy in policies]
        if len(set(maps)) >= 2:
            count += 1
    return count


def rank_domain_policies(rows: list[dict]) -> list[dict]:
    ranked = sorted(
        rows,
        key=lambda row: (
            int(row.get("catastrophic_logic_failures", 0)),
            -float(row.get("constraint_accuracy", 0.0)),
            float(row.get("false_action_rate", 0.0)),
            -float(row.get("action_f1", 0.0)),
            -float(row.get("boundary_accuracy_external_wait", 0.0)),
            -float(row.get("disposition_accuracy", 0.0)),
        ),
    )
    out = []
    for index, row in enumerate(ranked, start=1):
        copied = dict(row)
        copied["rank"] = index
        out.append(copied)
    return out


def run_domain_policy_tournament(candidates: list[str] | None = None, corpora: dict | None = None) -> dict:
    candidates = candidates or DOMAIN_CANDIDATES
    corpora = corpora or ensure_domain_corpora()
    rows = [evaluate_domain_policy(name, corpora) for name in candidates]
    metric_keys = (
        "disposition_accuracy",
        "action_f1",
        "false_action_rate",
        "boundary_accuracy_external_wait",
    )
    identical = all(all(abs(row[k] - rows[0][k]) < 1e-12 for k in metric_keys) for row in rows)
    if identical:
        raise RuntimeError(NON_DISCRIMINATING)
    ranked = rank_domain_policies(rows)
    payload = {
        "kind": "domain-policy-tournament",
        "disclaimer": LIMITATION,
        "base_count": len(corpora["bases"]),
        "metamorphic_count": len(corpora["variants"]),
        "pairwise_count": len(corpora["pairs"]),
        "total_independent_cases": len(corpora["bases"]) + len(corpora["variants"]) + len(corpora["pairs"]),
        "discriminating_cases": discriminating_case_count(corpora, candidates),
        "results": ranked,
        "recommended_semantic_policy": ranked[0]["candidate"],
        "reserve_policy_1": ranked[1]["candidate"] if len(ranked) > 1 else None,
        "reserve_policy_2": ranked[2]["candidate"] if len(ranked) > 2 else None,
        "network_calls": 0,
        "openrouter_calls": 0,
    }
    return payload


def render_domain_summary(payload: dict) -> str:
    lines = [
        "# Domain policy tournament",
        "",
        payload.get("disclaimer", LIMITATION),
        "",
        f"Independent oracle cases: {payload.get('base_count')}",
        f"Metamorphic cases: {payload.get('metamorphic_count')}",
        f"Pairwise cases: {payload.get('pairwise_count')}",
        f"Total independent cases: {payload.get('total_independent_cases')}",
        f"Discriminating cases: {payload.get('discriminating_cases')}",
        "",
        f"recommended_semantic_policy: {payload.get('recommended_semantic_policy')}",
        f"reserve_policy_1: {payload.get('reserve_policy_1')}",
        f"reserve_policy_2: {payload.get('reserve_policy_2')}",
        "",
        "## Ranking",
        "",
    ]
    for row in payload.get("results", []):
        lines.append(
            f"{row['rank']}. {row['candidate']} false_action={row['false_action_rate']:.4f} "
            f"f1={row['action_f1']:.4f} wait_boundary={row['boundary_accuracy_external_wait']:.4f} "
            f"disposition={row['disposition_accuracy']:.4f}"
        )
    lines.extend(["", "## Metrics", ""])
    keys = [
        "disposition_accuracy",
        "action_precision",
        "action_recall",
        "action_f1",
        "false_action_rate",
        "missed_action_rate",
        "meeting_accuracy",
        "record_accuracy",
        "monitor_accuracy",
        "constraint_accuracy",
        "catastrophic_logic_failures",
        "boundary_accuracy_external_wait",
        "boundary_accuracy_record",
        "boundary_accuracy_contact",
        "pairwise_bias_pass_rate",
        "invariant_pass_rate",
        "controlled_flip_pass_rate",
    ]
    for row in payload.get("results", []):
        lines.append(f"### {row['candidate']}")
        for key in keys:
            lines.append(f"- {key}: {row.get(key)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def domain_summary_path() -> Path:
    path = lab_root() / "reports" / "domain-policy-tournament.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
