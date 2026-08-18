"""Static rendering-risk analysis. Does not simulate Haiku instruction-following."""

from __future__ import annotations

import re
from pathlib import Path

from eval_lab.archive_loader import DEFAULT_SOURCES, load_archive
from eval_lab.candidate_store import read_candidate
from eval_lab.config import lab_root, repo_root
from eval_lab.deterministic_checks import calibrate_archived_outputs
from eval_lab.scoring import generalization_proxy

LIMITATION = (
    "Rendering-risk scoring is static text analysis. It does not predict official SN121 "
    "scores and does not simulate Haiku instruction-following."
)

MANDATORY_COVERAGE = {
    "evidence_boundary": r"handoff is the (complete )?evidence|use only (the |supplied )handoff|use supplied facts only|evidence boundary",
    "human_correction": r"human correction",
    "automated_touch": r"automated|system/automated|system or workflow activity",
    "disposition_precedence": r"`?MEETING`?.{0,80}`?RECORD`?.{0,80}`?ACTION`?|use this order|decision sequence|classify every open deal",
    "seller_owned_action": r"seller owns|seller-owned|owed deliverable|seller owes",
    "external_wait_default": r"remain(?:s)? MONITOR|stays? `?MONITOR`?|externally owned process remains MONITOR|waiting processes stay",
    "external_wait_escalation": r"timing is (now |materially )?material|checkpoint (has )?passed|no usable checkpoint|reduce .{0,20}uncertainty",
    "non_trigger_list": r"amount.{0,40}(stage|age|quota)|never create an action from amount|not actionable merely because",
    "meeting_replacement": r"meeting.{0,50}replace|do not also create outbound|already the useful",
    "do_not_contact_override": r"do-not-contact|do not contact|wait/do-not-contact|wait-until",
    "recipient_channel": r"recipient or channel only when|do not (choose|invent).{0,40}(recipient|channel)|use a recipient or channel only when",
    "no_aggregate_sum": r"never sum|do not add deal amounts|do not compute a pipeline total|never calculate a pipeline sum",
    "no_duplicate_assignment": r"only one operational section|exactly one|no deal may have two|exclusive|in at most one operational section",
    "no_filler_actions": r"never fill|no filler|never manufacture|print exactly",
    "action_count_lock": r"lock the (ACTION|action) (set|count)|count the final `ACTION`|print exactly (that count|those actions|the locked)",
    "record_embedding": r"mention (the issue|it) (inside|there)|embed record|do not repeat the deal",
    "final_audit": r"final (audit|check)|before printing, silently verify|scan all deal names",
}

CONTRADICTION_PAIRS = [
    (
        r"return only the (finished )?briefing|finished briefing first",
        r"before (the briefing|writing the briefing).{0,40}(forecast|model|adjacent analysis)",
        "only finished briefing vs mandatory extra analysis before briefing",
    ),
    (
        r"deal (name )?must appear in only one|deal may appear in only one|exclusive",
        r"repeat the deal under record|mandatory record section for every deal",
        "deal appears once vs duplicate record section",
    ),
    (
        r"do not (choose|invent) a channel|recipient or channel only when",
        r"always (call|email) the (customer|contact)",
        "do not choose channel vs unconditional call/email",
    ),
    (
        r"remain(?:s)? MONITOR|stays? `?MONITOR`?",
        r"always outreach (near|when).{0,20}close",
        "monitor default vs unconditional near-close outreach",
    ),
]

FAMILY_RENDERINGS = {
    "balanced": [
        ("production-f9e5400", "balanced"),
        ("candidate-b-ledger", "balanced"),
        ("candidate-b-minimal", "balanced"),
    ],
    "conservative": [("candidate-a-conservative", "conservative")],
    "assertive": [("candidate-c-assertive", "assertive")],
    "production": [("production-f9e5400", "production")],
}

RENDERINGS = [
    ("production-f9e5400", "production"),
    ("candidate-a-conservative", "conservative"),
    ("candidate-b-ledger", "balanced"),
    ("candidate-b-minimal", "balanced"),
    ("candidate-c-assertive", "assertive"),
]


def coverage(markdown: str) -> dict[str, bool]:
    return {key: bool(re.search(pattern, markdown, flags=re.I | re.S)) for key, pattern in MANDATORY_COVERAGE.items()}


def contradictions(markdown: str) -> list[str]:
    found = []
    for left, right, label in CONTRADICTION_PAIRS:
        if re.search(left, markdown, flags=re.I | re.S) and re.search(right, markdown, flags=re.I | re.S):
            found.append(label)
    return found


def instruction_load(markdown: str) -> dict:
    words = markdown.split()
    headings = len(re.findall(r"(?m)^#{1,3} ", markdown))
    bullets = len(re.findall(r"(?m)^\s*[-*]\s+", markdown))
    conditionals = len(re.findall(r"\b(if|unless|when|only when|otherwise)\b", markdown, flags=re.I))
    negatives = len(re.findall(r"\b(never|do not|don't|omit|without inventing)\b", markdown, flags=re.I))
    critical = [
        "do-not-contact",
        "never sum",
        "exactly one",
        "lock the ACTION",
        "human correction",
    ]
    repeated = 0
    lowered = markdown.lower()
    for phrase in critical:
        repeated += max(0, lowered.count(phrase.lower()) - 1)
    variables = set(re.findall(r"`([^`]+)`|<[^>]+>|\bN\b", markdown))
    sections = len(re.findall(r"(?m)^## ", markdown))
    audit_items = len(re.findall(r"(?m)^-\s+`", markdown.split("Final audit")[-1] if "Final audit" in markdown else ""))
    if "silently verify" in lowered:
        audit_items = max(audit_items, lowered.split("silently verify")[-1].count("- "))
    return {
        "word_count": len(words),
        "heading_count": headings,
        "bullet_count": bullets,
        "conditional_rule_count": conditionals,
        "negative_prohibition_count": negatives,
        "repeated_rule_count": repeated,
        "unique_abstract_variables": len(variables),
        "output_section_count": sections,
        "final_audit_item_count": audit_items,
    }


def rendering_risk_score(markdown: str) -> dict:
    cov = coverage(markdown)
    missing = [key for key, ok in cov.items() if not ok]
    contra = contradictions(markdown)
    load = instruction_load(markdown)
    coverage_penalty = 2.0 * len(missing)
    contradiction_penalty = 5.0 * len(contra)
    duplication_penalty = 0.25 * load["repeated_rule_count"]
    overload_penalty = 0.0
    if load["word_count"] > 900:
        overload_penalty += (load["word_count"] - 900) / 400.0
    if load["conditional_rule_count"] > 40:
        overload_penalty += (load["conditional_rule_count"] - 40) / 20.0
    underspec = 0.0
    if not cov.get("external_wait_escalation"):
        underspec += 2.0
    if not cov.get("do_not_contact_override"):
        underspec += 2.0
    proxy = generalization_proxy(markdown)
    benchmark = proxy < 0.85
    risk = coverage_penalty + contradiction_penalty + duplication_penalty + overload_penalty + underspec
    return {
        "coverage": cov,
        "missing_mandatory": missing,
        "complete_coverage": not missing,
        "contradictions": contra,
        "zero_contradictions": not contra,
        "zero_benchmark_specific": not benchmark,
        "generalization_proxy": proxy,
        "instruction_load": load,
        "coverage_penalty": coverage_penalty,
        "contradiction_penalty": contradiction_penalty,
        "duplication_penalty": duplication_penalty,
        "overload_penalty": overload_penalty,
        "underspecification_penalty": underspec,
        "rendering_risk": round(risk, 4),
        "limitation": LIMITATION,
    }


def evaluate_rendering(name: str, policy_label: str) -> dict:
    path, text, digest = read_candidate(name)
    risk = rendering_risk_score(text)
    risk.update(
        {
            "candidate": path.stem,
            "candidate_sha256": digest,
            "semantic_policy": policy_label,
            "markdown_words": len(text.split()),
        }
    )
    return risk


def rank_renderings(rows: list[dict]) -> list[dict]:
    ranked = sorted(
        rows,
        key=lambda row: (
            0 if row.get("zero_contradictions") else 1,
            0 if row.get("complete_coverage") else 1,
            0 if row.get("zero_benchmark_specific") else 1,
            float(row.get("rendering_risk", 99.0)),
            int(row.get("markdown_words", 10**9)),
        ),
    )
    out = []
    for index, row in enumerate(ranked, start=1):
        copied = dict(row)
        copied["rank"] = index
        out.append(copied)
    return out


def historical_calibration() -> dict:
    notes = []
    runs = []
    root = repo_root()
    failure_map = {
        "no_derived_pipeline_sum": "pipeline sum",
        "no_duplicate_operational_deal": "duplicate deal",
        "action_count_consistency": "action-count mismatch",
        "explicit_contact_constraint": "contact violation",
        "unsupported_channel": "unsupported channel",
        "word_limit": "word-limit overshoot",
    }
    envelopes = []
    for rel in DEFAULT_SOURCES:
        path = root / rel
        if not path.exists():
            continue
        archive = load_archive(path)
        skill = archive.skill_snapshot or ""
        risk = rendering_risk_score(skill) if skill else rendering_risk_score("")
        calib = calibrate_archived_outputs(path)
        mapped_failures = {
            failure_map.get(name, name): count
            for name, count in (calib.get("failure_counts") or {}).items()
            if name in failure_map
        }
        metrics = archive.metrics or {}
        row = {
            "archive": path.parent.name,
            "official_total": metrics.get("avg_score_total", archive.official_score),
            "skill_use": metrics.get("skill_use"),
            "scenario_quality": metrics.get("scenario_quality"),
            "rubric": metrics.get("rubric"),
            "dataset_derived": metrics.get("dataset_derived"),
            "word_count": risk["instruction_load"]["word_count"],
            "rendering_risk": risk["rendering_risk"],
            "complete_coverage": risk["complete_coverage"],
            "execution_failures": mapped_failures,
            "n_failed_samples": calib.get("n_failed_samples"),
        }
        runs.append(row)
        envelopes.append(risk["rendering_risk"])
    if runs:
        words = [row["word_count"] for row in runs]
        notes.append(
            f"Historical submitted skills ranged {min(words)}-{max(words)} words with "
            f"rendering-risk {min(envelopes):.2f}-{max(envelopes):.2f}. "
            "Shorter snapshots that kept mandatory rules tracked with more stable skill_use; "
            "this is qualitative, not a predicted official score."
        )
        failed = [row for row in runs if (row.get("n_failed_samples") or 0) > 0]
        if failed:
            notes.append(
                "Archived outputs still show deterministic execution failures "
                f"({', '.join(sorted({k for row in failed for k in row['execution_failures']}))}). "
                "Rendering risk is associated with those failure classes, not a score forecast."
            )
    notes.append("Do not interpret these features as a predicted official score such as 0.81.")
    return {"runs": runs, "notes": notes, "risk_envelope": {"min": min(envelopes) if envelopes else None, "max": max(envelopes) if envelopes else None}}


def minimal_rendering_eligible(minimal: dict, ledger: dict) -> bool:
    from eval_lab.policy_manifests import load_policy

    same_manifest = load_policy("candidate-b-minimal").model_dump() == load_policy("candidate-b-ledger").model_dump()
    return bool(
        minimal.get("complete_coverage")
        and minimal.get("zero_contradictions")
        and (minimal.get("generalization_proxy") or 0) >= 0.85
        and not minimal.get("missing_mandatory")
        and float(minimal.get("rendering_risk", 99)) <= float(ledger.get("rendering_risk", 99))
        and same_manifest
    )


def choose_recommended_renderings(family: str, ranked: list[dict]) -> tuple[str | None, str | None]:
    ledger = next((row for row in ranked if row["candidate"] == "candidate-b-ledger"), None)
    eligible = []
    for row in ranked:
        if family == "balanced" and row["candidate"] == "candidate-b-minimal":
            if not ledger or not minimal_rendering_eligible(row, ledger):
                continue
        eligible.append(row)
    if not eligible:
        eligible = list(ranked)
    recommended = eligible[0]["candidate"] if eligible else None
    reserve = eligible[1]["candidate"] if len(eligible) > 1 else (ranked[1]["candidate"] if len(ranked) > 1 else None)
    return recommended, reserve


def run_rendering_risk_tournament(
    renderings: list[tuple[str, str]] | None = None,
    family: str | None = None,
) -> dict:
    if renderings is None:
        renderings = FAMILY_RENDERINGS.get(family, RENDERINGS) if family else RENDERINGS
    rows = [evaluate_rendering(name, label) for name, label in renderings]
    ranked = rank_renderings(rows)
    calibration = historical_calibration()
    for row in ranked:
        env = calibration.get("risk_envelope") or {}
        lo, hi = env.get("min"), env.get("max")
        if lo is None or hi is None:
            row["outside_historical_envelope"] = False
        else:
            row["outside_historical_envelope"] = row["rendering_risk"] < lo - 0.5 or row["rendering_risk"] > hi + 0.5
    recommended, reserve = choose_recommended_renderings(family or "balanced", ranked)
    return {
        "kind": "rendering-risk-tournament",
        "disclaimer": LIMITATION,
        "semantic_family": family,
        "results": ranked,
        "recommended_rendering": recommended,
        "reserve_rendering": reserve,
        "historical_calibration": calibration,
        "network_calls": 0,
        "openrouter_calls": 0,
    }


def render_rendering_summary(payload: dict) -> str:
    lines = ["# Rendering-risk tournament", "", payload.get("disclaimer", LIMITATION), ""]
    if payload.get("semantic_family"):
        lines.append(f"semantic_family: {payload.get('semantic_family')}")
    lines.append(f"recommended_rendering: {payload.get('recommended_rendering')}")
    lines.append(f"reserve_rendering: {payload.get('reserve_rendering')}")
    lines.extend(["", "## Ranking", ""])
    for row in payload.get("results", []):
        lines.append(
            f"{row['rank']}. {row['candidate']} policy={row['semantic_policy']} "
            f"risk={row['rendering_risk']:.3f} words={row['markdown_words']} "
            f"coverage={'complete' if row['complete_coverage'] else 'incomplete'} "
            f"contradictions={len(row['contradictions'])}"
        )
    lines.extend(["", "## Historical calibration", ""])
    for note in (payload.get("historical_calibration") or {}).get("notes") or []:
        lines.append(f"- {note}")
    lines.extend(["", "## Archive snapshots", ""])
    for run in (payload.get("historical_calibration") or {}).get("runs") or []:
        lines.append(
            f"- {run['archive']}: total={run['official_total']} skill_use={run['skill_use']} "
            f"scenario_quality={run['scenario_quality']} rubric={run['rubric']} "
            f"dataset_derived={run['dataset_derived']} words={run['word_count']} "
            f"risk={run['rendering_risk']} failures={run['execution_failures']}"
        )
    return "\n".join(lines).rstrip() + "\n"


def rendering_summary_path() -> Path:
    path = lab_root() / "reports" / "rendering-risk-tournament.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
