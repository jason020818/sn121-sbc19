"""Deterministic check tests. Fixtures are synthetic, not public benchmark copies."""

from eval_lab.deterministic_checks import run_deterministic_checks
from eval_lab.models import HiddenExpectations


SCENARIO = """
Handoff for Tuesday, May 6.

TODAY'S CALENDAR
- 10:00 AM: working session w/ Quill Cooperative ($120K) — Ira Calder
- 2:00 PM: internal forecast review (internal)

OPEN DEALS
- Quill Cooperative | $120K | Negotiation | close May 20 | contact Ira Calder
  Note: Customer meeting today is the useful work.
- Emberwick Labs | $80K | Proposal | close May 28 | contact Noemi Voss
  Note: Seller still owes Noemi Voss a revised scope document.
- Nautilus Outfit | $400K | Negotiation | close May 18 | contact Soren Pike
  Note: Contract is with their legal team. Do not contact Nautilus Outfit until September 30.
- Bramble Works | $55K | Demo | close June 2 | contact Hana Quill
  Note: Human correction: CRM last activity shows May 1; actual last human touch is April 2.
"""


def test_duplicate_deal_detection() -> None:
    output = """
## Pipeline Health
2 genuine seller moves today.

## Priority Actions
1. **Emberwick Labs** — Send the revised scope to Noemi Voss.

## Meeting Prep
**10:00 AM — Quill Cooperative**
Objective: working session.

## Needs Record Update
- **Emberwick Labs** — last activity needs repair.
"""
    report = run_deterministic_checks(SCENARIO, output)
    dup = next(item for item in report.checks if item.name == "no_duplicate_operational_deal")
    assert dup.passed is False
    meet = next(item for item in report.checks if item.name == "meeting_action_duplication")
    assert meet.passed is True


def test_entity_and_amount_grounding() -> None:
    output = """
## Pipeline Health
1 genuine seller move today.

## Priority Actions
1. **Emberwick Labs** — Send the revised scope ($80K).

## Meeting Prep
**Quill Cooperative** working session ($120K).
"""
    report = run_deterministic_checks(SCENARIO, output)
    entity = next(item for item in report.checks if item.name == "entity_grounding")
    amount = next(item for item in report.checks if item.name == "amount_grounding")
    assert entity.passed is True
    assert amount.passed is True

    invented = output.replace("Emberwick Labs", "Ghost Foundry Inc")
    report2 = run_deterministic_checks(SCENARIO, invented)
    entity2 = next(item for item in report2.checks if item.name == "entity_grounding")
    assert entity2.passed is False
    assert entity2.severity == "catastrophic"

    money = output.replace("$80K", "$999K")
    report3 = run_deterministic_checks(SCENARIO, money)
    amount3 = next(item for item in report3.checks if item.name == "amount_grounding")
    assert amount3.passed is False


def test_do_not_contact_violation() -> None:
    output = """
## Priority Actions
1. **Nautilus Outfit** — Call Soren Pike to push legal.

## Meeting Prep
**Quill Cooperative** working session.
"""
    report = run_deterministic_checks(SCENARIO, output)
    check = next(item for item in report.checks if item.name == "explicit_contact_constraint")
    assert check.passed is False
    assert check.severity == "catastrophic"
    assert report.catastrophic is True


def test_pipeline_total_detection() -> None:
    output = """
## Pipeline Health
4 open deals, $655K total. 1 genuine seller move today.

## Priority Actions
1. **Emberwick Labs** — Send the revised scope.
"""
    report = run_deterministic_checks(SCENARIO, output)
    total = next(item for item in report.checks if item.name == "no_derived_pipeline_sum")
    assert total.passed is False

    labeled_scenario = SCENARIO + "\nLabeled pipeline total: $655K\n"
    report_ok = run_deterministic_checks(labeled_scenario, output)
    total_ok = next(item for item in report_ok.checks if item.name == "no_derived_pipeline_sum")
    assert total_ok.passed is True


def test_word_limit_and_action_count() -> None:
    words = " ".join(["word"] * 331)
    output = f"""
## Pipeline Health
1 genuine seller moves today.

## Priority Actions
1. **Emberwick Labs** — Send the revised scope.

{words}
"""
    report = run_deterministic_checks(SCENARIO, output)
    words_check = next(item for item in report.checks if item.name == "word_limit")
    count_check = next(item for item in report.checks if item.name == "action_count_consistency")
    assert words_check.passed is False
    assert count_check.passed is True


def test_record_correction_and_channel() -> None:
    output = """
## Priority Actions
1. **Bramble Works** — LinkedIn Hana Quill. Last activity is May 1.

## Meeting Prep
**Quill Cooperative** working session.
"""
    report = run_deterministic_checks(SCENARIO, output)
    record = next(item for item in report.checks if item.name == "record_correction")
    channel = next(item for item in report.checks if item.name == "unsupported_channel")
    assert record.passed is False
    assert channel.passed is False


def test_hidden_expectations_are_optional() -> None:
    expectations = HiddenExpectations(
        source_entities=["Quill Cooperative", "Emberwick Labs", "Nautilus Outfit", "Bramble Works"],
        source_people=["Ira Calder", "Noemi Voss", "Soren Pike", "Hana Quill"],
        source_amounts=["$120K", "$80K", "$400K", "$55K"],
        explicit_constraints=["Do not contact Nautilus Outfit until September 30."],
    )
    output = """
## Priority Actions
1. **Emberwick Labs** — Send the revised scope to Noemi Voss ($80K).
"""
    report = run_deterministic_checks(SCENARIO, output, expectations)
    assert any(item.name == "entity_grounding" and item.passed for item in report.checks)
