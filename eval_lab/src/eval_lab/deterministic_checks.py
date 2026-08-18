"""Deterministic grounding and structure checks.

Compare generated answers against the supplied scenario text. Grader rationales
are never treated as ground truth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from eval_lab.models import CheckResult, DeterministicReport, HiddenExpectations

WORD_LIMIT = 330

OPERATIONAL_SECTIONS = (
    "priority actions",
    "meeting prep",
    "other actions today",
    "needs record update",
)

AMOUNT_RE = re.compile(
    r"""
    (?<![A-Za-z])
    (?:
        (?:USD|EUR|GBP|CAD|AUD|\$|€|£)\s?\d[\d,]*(?:\.\d+)?\s*[KkMmBb]?
        |
        \d[\d,]*(?:\.\d+)?\s*(?:USD|EUR|GBP|CAD|AUD)
        |
        \$\s?\d[\d,]*(?:\.\d+)?
    )
    """,
    re.VERBOSE,
)

TOTAL_HINT_RE = re.compile(
    r"(pipeline\s+total|total\s+pipeline|open\s+deals?,\s*\$|"
    r"\$[\d.,]+\s*[KkMm]?\s+(?:total|combined|overall)|"
    r"(?:total|combined|overall)\s+(?:of\s+)?\$|"
    r"totaling\s+\$|worth\s+\$[\d.,]+\s+combined)",
    re.I,
)

GENUINE_MOVES_RE = re.compile(
    r"(?P<n>\d+)\s+genuine\s+seller\s+(?:moves?|actions?)",
    re.I,
)

CHANNEL_RE = re.compile(
    r"\b(call|email|text|sms|linkedin)\b.{0,80}?\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b"
    r"|"
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b.{0,40}?\b(call|email|text|sms|linkedin)\b",
    re.I,
)

DO_NOT_CONTACT_RE = re.compile(
    r"(do\s+not\s+contact|don't\s+contact|do\s+not\s+reach\s+out|no\s+outreach|"
    r"wait\s+until|no\s+contact\s+before|requested\s+no\s+outreach)",
    re.I,
)
DO_NOT_CONTACT_TARGET_RE = re.compile(
    r"(?i:do\s+not\s+contact|don't\s+contact|no\s+outreach(?:\s+before|\s+to)?)\s+"
    r"([A-Z][A-Za-z0-9&.'/-]*(?:\s+[A-Z][A-Za-z0-9&.'/-]*){0,4}?)"
    r"(?=\s+until\b|\s+before\b|\s+through\b|[.,]|$)"
)

BOLD_NAME_RE = re.compile(r"\*\*([^*]{2,80}?)\*\*")
DEAL_AMOUNT_RE = re.compile(
    r"([A-Z][A-Za-z0-9&.'/-]*(?:\s+[A-Z][A-Za-z0-9&.'/-]*){0,5})\s*\(\s*[$€£]"
)
STOP_NAME_PREFIXES = {
    "deal",
    "contact",
    "note",
    "open",
    "last",
    "close",
    "stage",
    "human",
    "actual",
    "labeled",
    "pipeline",
    "send",
    "call",
    "email",
}
GENERIC_PERSON_RE = re.compile(
    r"\b(champion|procurement|legal|manager|seller|buyer|customer|rep|team|"
    r"board|sponsor|contact|cfo|ceo|cto|cpo|vp|director)\b",
    re.I,
)


@dataclass
class ParsedBriefing:
    sections: dict[str, str]
    word_count: int
    amounts: list[str]


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))


def parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "_preamble"
    sections[current] = []
    for line in (text or "").splitlines():
        heading = _heading(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(val).strip() for key, val in sections.items()}


def _heading(line: str) -> str | None:
    stripped = line.strip()
    if stripped.startswith("#"):
        name = stripped.lstrip("#").strip().lower()
        return name
    if re.match(r"^\*\*[^*]+\*\*\s*$", stripped):
        return stripped.strip("* ").lower()
    return None


def extract_amounts(text: str) -> list[str]:
    return [match.group(0).strip() for match in AMOUNT_RE.finditer(text or "")]


def normalize_amount(raw: str) -> str:
    text = raw.replace(",", "").replace(" ", "").upper()
    text = text.replace("USD", "$").replace("EUR", "€").replace("GBP", "£")
    multiplier = 1.0
    if text.endswith("K"):
        multiplier = 1_000
        text = text[:-1]
    elif text.endswith("M"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("B"):
        multiplier = 1_000_000_000
        text = text[:-1]
    currency = ""
    for symbol in ("$", "€", "£"):
        if symbol in text:
            currency = symbol
            text = text.replace(symbol, "")
            break
    try:
        value = float(text) * multiplier
    except ValueError:
        return raw.strip().upper()
    if abs(value - round(value)) < 1e-6:
        number = str(int(round(value)))
    else:
        number = f"{value:.2f}"
    return f"{currency}{number}"


def amount_in_source(amount: str, source_amounts: list[str]) -> bool:
    target = normalize_amount(amount)
    normalized_source = {normalize_amount(item) for item in source_amounts}
    if target in normalized_source:
        return True
    # Tolerate $1.523M vs $1.52M display rounding only when exact token exists.
    return amount.strip() in {item.strip() for item in source_amounts}


def extract_entities_from_text(text: str) -> list[str]:
    names: list[str] = []
    for match in BOLD_NAME_RE.finditer(text or ""):
        names.append(_clean_entity(match.group(1)))
    for match in DEAL_AMOUNT_RE.finditer(text or ""):
        names.append(_clean_entity(match.group(1)))
    for match in re.finditer(
        r"(?:w/|with|call\s+w/|meeting\s+w/)\s+([A-Z][A-Za-z0-9&.'/-]*(?:\s+[A-Z][A-Za-z0-9&.'/-]*){0,5})",
        text or "",
    ):
        names.append(_clean_entity(match.group(1)))
    return [name for name in names if name]


def extract_people(text: str) -> list[str]:
    people: list[str] = []
    for match in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b", text or ""):
        parts = match.group(1).split()
        while parts and parts[0].lower() in STOP_NAME_PREFIXES:
            parts.pop(0)
        if len(parts) < 2:
            continue
        name = " ".join(parts)
        if GENERIC_PERSON_RE.search(name):
            continue
        if _looks_like_date_or_header(name):
            continue
        people.append(name)
    return people


def _looks_like_date_or_header(name: str) -> bool:
    lowered = name.lower()
    blocked = {
        "priority actions",
        "meeting prep",
        "pipeline health",
        "daily briefing",
        "needs record",
        "other actions",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "january",
        "february",
        "march",
        "april",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    }
    return lowered in blocked or any(part.lower() in blocked for part in name.split())


def _clean_entity(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name).strip(" -:;,.")
    cleaned = re.sub(r"\s+\(.*$", "", cleaned)
    cleaned = re.sub(
        r"\s+(?:—|-|–)\s+(?:send|request|confirm|prep|identify|reach).*$",
        "",
        cleaned,
        flags=re.I,
    )
    return cleaned


def _entity_in_source(name: str, source_entities: list[str]) -> bool:
    needle = name.casefold()
    if len(needle) < 3:
        return True
    for entity in source_entities:
        hay = entity.casefold()
        if needle == hay or needle in hay or hay in needle:
            return True
    return False


def _section_deal_names(body: str) -> list[str]:
    names: list[str] = []
    for raw_line in (body or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        bold = BOLD_NAME_RE.search(line)
        if bold:
            names.append(_clean_entity(bold.group(1)))
            continue
        bullet = re.match(r"^(?:\d+\.|-|\*)\s+(.+)$", line)
        if bullet:
            token = re.split(r"\s+[—–:-]\s+", bullet.group(1), maxsplit=1)[0]
            token = re.sub(r"\s+\(.*$", "", token)
            names.append(_clean_entity(token.strip("* ")))
    return [name for name in names if name]


def labeled_source_totals(scenario: str) -> list[str]:
    totals: list[str] = []
    for line in (scenario or "").splitlines():
        if re.search(r"\b(pipeline\s+total|total\s+pipeline|labeled total|book total)\b", line, re.I):
            totals.extend(extract_amounts(line))
    return totals


def run_deterministic_checks(
    scenario: str,
    output: str,
    expectations: HiddenExpectations | None = None,
) -> DeterministicReport:
    source_entities = list(expectations.source_entities) if expectations else extract_entities_from_text(scenario)
    source_people = list(expectations.source_people) if expectations else extract_people(scenario)
    source_amounts = list(expectations.source_amounts) if expectations else extract_amounts(scenario)
    if expectations:
        source_entities = list(dict.fromkeys(source_entities + extract_entities_from_text(scenario)))
        source_people = list(dict.fromkeys(source_people + extract_people(scenario)))
        source_amounts = list(dict.fromkeys(source_amounts + extract_amounts(scenario)))

    known_names = source_entities + source_people
    sections = parse_sections(output)
    checks = [
        _entity_grounding(output, sections, known_names),
        _amount_grounding(output, source_amounts, labeled_source_totals(scenario)),
        _no_derived_pipeline_sum(output, scenario, source_amounts),
        _no_duplicate_operational_deal(sections),
        _explicit_contact_constraint(scenario, sections, expectations),
        _meeting_action_duplication(sections, scenario),
        _word_limit(output),
        _action_count_consistency(sections),
        _unsupported_channel(output, scenario, source_people),
        _record_correction(scenario, output),
    ]
    failed = [item for item in checks if not item.passed]
    catastrophic = any(item.severity == "catastrophic" and not item.passed for item in checks)
    return DeterministicReport(
        passed=not failed,
        checks=checks,
        catastrophic=catastrophic,
        major_count=sum(1 for item in failed if item.severity == "major"),
        minor_count=sum(1 for item in failed if item.severity == "minor"),
    )


def _entity_grounding(output: str, sections: dict[str, str], known_names: list[str]) -> CheckResult:
    operational = "\n".join(
        body for key, body in sections.items() if any(key.endswith(name) or name in key for name in OPERATIONAL_SECTIONS + ("monitor",))
    )
    candidates = _section_deal_names(operational) + extract_entities_from_text(operational or output)
    invented = []
    for name in dict.fromkeys(candidates):
        if GENERIC_PERSON_RE.fullmatch(name):
            continue
        if not _entity_in_source(name, known_names):
            invented.append(name)
    if invented:
        return CheckResult(
            name="entity_grounding",
            passed=False,
            severity="catastrophic",
            evidence=invented[:8],
            detail="Named deal/company in the output is not present in the scenario.",
        )
    return CheckResult(name="entity_grounding", passed=True, severity="catastrophic", detail="All named deals exist in the scenario.")


def _amount_grounding(output: str, source_amounts: list[str], labeled_totals: list[str]) -> CheckResult:
    allowed = source_amounts + labeled_totals
    invented = []
    for amount in extract_amounts(output):
        if amount_in_source(amount, allowed):
            continue
        invented.append(amount)
    if invented:
        return CheckResult(
            name="amount_grounding",
            passed=False,
            severity="major",
            evidence=invented[:8],
            detail="Printed currency amount is not present in the scenario.",
        )
    return CheckResult(name="amount_grounding", passed=True, severity="major", detail="All printed amounts occur in the scenario.")


def _no_derived_pipeline_sum(output: str, scenario: str, source_amounts: list[str]) -> CheckResult:
    labeled = labeled_source_totals(scenario)
    hits: list[str] = []
    for line in output.splitlines():
        if not TOTAL_HINT_RE.search(line):
            continue
        amounts = extract_amounts(line)
        for amount in amounts:
            if labeled and amount_in_source(amount, labeled):
                continue
            if amount_in_source(amount, source_amounts) and labeled_source_totals(line):
                continue
            if not labeled:
                hits.append(line.strip())
                break
            if not amount_in_source(amount, labeled):
                hits.append(line.strip())
                break
    if hits:
        return CheckResult(
            name="no_derived_pipeline_sum",
            passed=False,
            severity="major",
            evidence=hits[:5],
            detail="Answer prints a pipeline-total-like aggregate that was not explicitly labeled in source.",
        )
    return CheckResult(
        name="no_derived_pipeline_sum",
        passed=True,
        severity="major",
        detail="No unlabeled pipeline total detected.",
    )


def _no_duplicate_operational_deal(sections: dict[str, str]) -> CheckResult:
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    operational_keys = []
    for key, body in sections.items():
        lowered = key.lower()
        if any(name in lowered for name in OPERATIONAL_SECTIONS):
            operational_keys.append((key, body, False))
        elif "monitor" in lowered:
            operational_keys.append((key, body, True))
    for key, body, is_monitor in operational_keys:
        for name in _section_deal_names(body):
            token = name.casefold()
            if token in seen:
                if is_monitor:
                    duplicates.append(f"{name} in {key} after {seen[token]}")
                else:
                    duplicates.append(f"{name} in {key} after {seen[token]}")
            else:
                seen[token] = key
    if duplicates:
        return CheckResult(
            name="no_duplicate_operational_deal",
            passed=False,
            severity="major",
            evidence=duplicates[:8],
            detail="A deal appears in more than one operational section.",
        )
    return CheckResult(
        name="no_duplicate_operational_deal",
        passed=True,
        severity="major",
        detail="Deal names are unique across operational sections.",
    )


def _constraint_targets(scenario: str, expectations: HiddenExpectations | None) -> list[str]:
    targets: list[str] = []
    if expectations:
        targets.extend(expectations.explicit_constraints)
    for line in (scenario or "").splitlines():
        if DO_NOT_CONTACT_RE.search(line):
            targets.append(line.strip())
        for match in DO_NOT_CONTACT_TARGET_RE.finditer(line):
            targets.append(match.group(0).strip())
    return targets


def _explicit_contact_constraint(
    scenario: str,
    sections: dict[str, str],
    expectations: HiddenExpectations | None,
) -> CheckResult:
    constraints = _constraint_targets(scenario, expectations)
    if not constraints:
        return CheckResult(
            name="explicit_contact_constraint",
            passed=True,
            severity="catastrophic",
            detail="No explicit contact constraint in scenario.",
        )
    action_text = "\n".join(
        body
        for key, body in sections.items()
        if "priority actions" in key.lower() or "other actions" in key.lower()
    )
    violations: list[str] = []
    for constraint in constraints:
        names = extract_entities_from_text(constraint) + _section_deal_names(constraint)
        names.extend(match.group(1) for match in DO_NOT_CONTACT_TARGET_RE.finditer(constraint))
        if not names:
            names = [word for word in re.findall(r"\b[A-Z][A-Za-z0-9&.'/-]+\b", constraint)]
        for name in names:
            if len(name) < 4:
                continue
            if re.search(rf"\b{re.escape(name)}\b", action_text, re.I):
                if re.search(r"\b(call|email|text|reach|send|contact|linkedin|message)\b", action_text, re.I):
                    violations.append(name)
    if violations:
        return CheckResult(
            name="explicit_contact_constraint",
            passed=False,
            severity="catastrophic",
            evidence=sorted(set(violations)),
            detail="Outbound action contradicts a do-not-contact or wait-until instruction.",
        )
    return CheckResult(
        name="explicit_contact_constraint",
        passed=True,
        severity="catastrophic",
        detail="Contact constraints were respected.",
    )


def _meeting_action_duplication(sections: dict[str, str], scenario: str) -> CheckResult:
    meeting_body = "\n".join(body for key, body in sections.items() if "meeting prep" in key.lower())
    action_body = "\n".join(
        body
        for key, body in sections.items()
        if "priority actions" in key.lower() or "other actions" in key.lower()
    )
    meeting_deals = []
    for name in _section_deal_names(meeting_body):
        block = _block_for_name(meeting_body, name)
        if re.search(r"\binternal\b", block, re.I):
            continue
        meeting_deals.append(name)
    overlap = []
    for name in meeting_deals:
        if re.search(rf"\b{re.escape(name)}\b", action_body, re.I):
            overlap.append(name)
    if overlap:
        return CheckResult(
            name="meeting_action_duplication",
            passed=False,
            severity="major",
            evidence=overlap,
            detail="A scheduled customer-meeting deal also received an outbound action.",
        )
    return CheckResult(
        name="meeting_action_duplication",
        passed=True,
        severity="major",
        detail="Meeting deals are not duplicated as outbound actions.",
    )


def _block_for_name(body: str, name: str) -> str:
    lines = (body or "").splitlines()
    collected: list[str] = []
    capturing = False
    for line in lines:
        if re.search(rf"\b{re.escape(name)}\b", line, re.I):
            capturing = True
            collected.append(line)
            continue
        if capturing:
            if line.strip().startswith(("-", "*", "#")) or re.match(r"^\d+\.", line.strip()) or line.strip().startswith("**"):
                break
            collected.append(line)
    return "\n".join(collected)


def _word_limit(output: str) -> CheckResult:
    count = word_count(output)
    if count > WORD_LIMIT:
        return CheckResult(
            name="word_limit",
            passed=False,
            severity="minor",
            evidence=[str(count)],
            detail=f"Output has {count} words; production ceiling is {WORD_LIMIT}.",
        )
    return CheckResult(
        name="word_limit",
        passed=True,
        severity="minor",
        evidence=[str(count)],
        detail=f"Output is {count} words.",
    )


def _action_count_consistency(sections: dict[str, str]) -> CheckResult:
    health = "\n".join(body for key, body in sections.items() if "pipeline health" in key.lower())
    match = GENUINE_MOVES_RE.search(health)
    if not match:
        return CheckResult(
            name="action_count_consistency",
            passed=True,
            severity="minor",
            detail="Pipeline Health does not state a genuine-move count.",
        )
    claimed = int(match.group("n"))
    action_items = 0
    for key, body in sections.items():
        if "priority actions" in key.lower() or "other actions" in key.lower():
            action_items += len(_section_deal_names(body))
    if action_items != claimed:
        return CheckResult(
            name="action_count_consistency",
            passed=False,
            severity="minor",
            evidence=[f"claimed={claimed}", f"printed={action_items}"],
            detail="Pipeline Health genuine-move count does not match action items.",
        )
    return CheckResult(
        name="action_count_consistency",
        passed=True,
        severity="minor",
        detail="Genuine-move count matches printed action items.",
    )


def _unsupported_channel(output: str, scenario: str, source_people: list[str]) -> CheckResult:
    flags: list[str] = []
    scenario_l = scenario.lower()
    for match in CHANNEL_RE.finditer(output or ""):
        groups = [g for g in match.groups() if g]
        if len(groups) < 2:
            continue
        channel = next((g.lower() for g in groups if g.lower() in {"call", "email", "text", "sms", "linkedin"}), "")
        person = next((g for g in groups if g.lower() not in {"call", "email", "text", "sms", "linkedin"}), "")
        if not channel or not person:
            continue
        if GENERIC_PERSON_RE.search(person):
            continue
        if not _entity_in_source(person, source_people + extract_people(scenario)):
            flags.append(f"{channel} to unknown recipient {person}")
            continue
        if channel in {"linkedin", "text", "sms"} and channel not in scenario_l:
            flags.append(f"{channel} to {person} is not supplied in the scenario")
        elif channel in {"call", "email"} and channel not in scenario_l:
            artifact_ok = bool(re.search(r"e-?sign|phone|inbox|voicemail|email", scenario_l))
            if channel == "call" and not re.search(r"call|phone", scenario_l) and not artifact_ok:
                flags.append(f"call to {person} is not supplied or required by a source artifact")
    if flags:
        return CheckResult(
            name="unsupported_channel",
            passed=False,
            severity="minor",
            evidence=flags[:6],
            detail="Channel or recipient is not grounded in the scenario.",
        )
    return CheckResult(
        name="unsupported_channel",
        passed=True,
        severity="minor",
        detail="No unsupported call/email/text/LinkedIn instruction detected.",
    )


def _record_correction(scenario: str, output: str) -> CheckResult:
    patterns = [
        re.compile(
            r"(?:crm|record|system|field).{0,40}?(?:wrong|incorrect|stale|should be|actually).{0,40}?(\S+).{0,20}?(?:actual(?:ly)?|correct(?:ed)?(?: to)?)\s+(\S+)",
            re.I,
        ),
        re.compile(
            r"(?:actual(?:ly)?|correct(?:ed)?(?: to)?|true last activity is)\s+([A-Za-z]{3,9}\s+\d{1,2}|\d{4}-\d{2}-\d{2}|[A-Za-z]{3}\s+\d{1,2})",
            re.I,
        ),
    ]
    superseded: list[str] = []
    corrected: list[str] = []
    for line in (scenario or "").splitlines():
        if not re.search(r"wrong|incorrect|stale|correction|actually|should be|true last", line, re.I):
            continue
        match = re.search(
            r"(?:shows|lists|says|recorded as|crm(?:\s+last activity)?)\s+"
            r"([A-Za-z]{3,9}\s+\d{1,2}|\d{4}-\d{2}-\d{2}).{0,120}?"
            r"(?:actual(?:ly)?|correct(?:ed)?(?: to)?|true.{0,40}is).{0,40}?"
            r"([A-Za-z]{3,9}\s+\d{1,2}|\d{4}-\d{2}-\d{2})",
            line,
            re.I,
        )
        if match:
            superseded.append(match.group(1))
            corrected.append(match.group(2))
        else:
            match = re.search(
                r"(?:actual(?:ly)?|correct(?:ed)?(?: to)?)\s+([A-Za-z]{3,9}\s+\d{1,2}|\d{4}-\d{2}-\d{2}).{0,40}?(?:not|not as)\s+([A-Za-z]{3,9}\s+\d{1,2}|\d{4}-\d{2}-\d{2})",
                line,
                re.I,
            )
            if match:
                corrected.append(match.group(1))
                superseded.append(match.group(2))
    if not superseded:
        return CheckResult(
            name="record_correction",
            passed=True,
            severity="major",
            detail="No explicit human field correction detected.",
        )
    violations = []
    for old, new in zip(superseded, corrected):
        if re.search(rf"\b{re.escape(old)}\b", output, re.I) and not re.search(
            rf"\b{re.escape(old)}\b.{0,40}(wrong|stale|incorrect|superseded|crm)",
            output,
            re.I,
        ):
            if not re.search(rf"\b{re.escape(new)}\b", output, re.I):
                violations.append(old)
            elif re.search(rf"(last activity|as of|current).{0,20}{re.escape(old)}", output, re.I):
                violations.append(old)
    if violations:
        return CheckResult(
            name="record_correction",
            passed=False,
            severity="major",
            evidence=violations,
            detail="Answer restates a superseded structured value as current truth.",
        )
    return CheckResult(
        name="record_correction",
        passed=True,
        severity="major",
        detail="Human corrections were not contradicted.",
    )


def report_to_json(report: DeterministicReport) -> dict:
    return report.model_dump()


def calibrate_archived_outputs(source) -> dict:
    """Run deterministic checks on archived outputs. Makes zero model calls."""
    from pathlib import Path

    from eval_lab.archive_loader import load_archive

    archive = load_archive(Path(source))
    samples = []
    for item in archive.samples:
        report = run_deterministic_checks(item.scenario_input, item.assistant_output or "")
        failed = [check for check in report.checks if not check.passed]
        samples.append(
            {
                "scenario_id": item.scenario_id,
                "passed": report.passed,
                "catastrophic": report.catastrophic,
                "failures": [check.model_dump() for check in failed],
            }
        )
    return {
        "kind": "deterministic_calibration",
        "source": str(source),
        "n_samples": len(samples),
        "n_failed_samples": sum(1 for row in samples if not row["passed"]),
        "failure_counts": {
            name: sum(1 for row in samples for item in row["failures"] if item["name"] == name)
            for name in sorted({item["name"] for row in samples for item in row["failures"]})
        },
        "samples": samples,
        "disclaimer": (
            "Compares archived assistant outputs to scenario inputs only. "
            "Grader rationales are not treated as ground truth. Zero model/API calls."
        ),
    }
