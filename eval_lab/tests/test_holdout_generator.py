"""Holdout generator tests."""

from pathlib import Path

from eval_lab.holdout_generator import generate_holdouts, write_holdouts


def test_deterministic_generation_from_seed() -> None:
    a = generate_holdouts(count=60, seed=1211901)
    b = generate_holdouts(count=60, seed=1211901)
    assert len(a) == 60
    assert [item.model_dump() for item in a] == [item.model_dump() for item in b]
    changed = generate_holdouts(count=60, seed=1211902)
    assert a[0].scenario != changed[0].scenario


def test_dimension_coverage_and_fictional_names() -> None:
    records = generate_holdouts(count=60, seed=1211901)
    books = {item.dimensions["book_size"] for item in records}
    calendars = {item.dimensions["calendar"] for item in records}
    densities = {item.dimensions["action_density"] for item in records}
    assert books == {5, 8, 12, 18, 30, 40}
    assert calendars == {"none", "one_internal", "one_customer", "multi_customer", "imminent"}
    assert densities == {0, 1, 2, 3, 4}
    joined = "\n".join(item.scenario for item in records)
    for banned in ("Thornfield", "Meridian Health", "Bluewater Shipping", "S-001", "Nightfall Insurance"):
        assert banned not in joined
    assert all(item.hidden_expectations.source_entities for item in records)
    assert all(item.id.startswith("H-") for item in records)


def test_smoke_fixture_exists_and_is_tiny() -> None:
    fixture = Path(__file__).parent / "fixtures" / "synthetic_smoke.jsonl"
    lines = [line for line in fixture.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 3
    assert "Thornfield" not in fixture.read_text(encoding="utf-8")


def test_write_holdouts_roundtrip(tmp_path: Path) -> None:
    records = generate_holdouts(count=3, seed=99)
    path = write_holdouts(records, path=tmp_path / "holdouts.jsonl")
    text = path.read_text(encoding="utf-8")
    assert text.count("\n") == 3


def test_final_action_density_matches_metadata_after_calendar() -> None:
    for record in generate_holdouts(count=60, seed=1211901):
        density = record.dimensions["action_density"]
        n_actions = len(record.hidden_expectations.allowed_action_deals)
        meetings = set(record.hidden_expectations.meeting_deals)
        if density <= 3:
            assert n_actions == density
        else:
            assert n_actions >= 4
        assert meetings.isdisjoint(record.hidden_expectations.allowed_action_deals)
        if record.dimensions["calendar"] == "one_internal":
            assert n_actions == density or (density >= 4 and n_actions >= 4)


def test_channel_constraint_does_not_create_action() -> None:
    for record in generate_holdouts(count=60, seed=1211901):
        if record.dimensions["communication"] not in {"call_requested", "email_only"}:
            continue
        density = record.dimensions["action_density"]
        n_actions = len(record.hidden_expectations.allowed_action_deals)
        if density <= 3:
            assert n_actions == density
        else:
            assert n_actions >= 4
        assert "asked for a phone call" in record.scenario or "Email only" in record.scenario


def test_density_zero_has_no_action_semantics() -> None:
    zeros = [r for r in generate_holdouts(count=60, seed=1211901) if r.dimensions["action_density"] == 0]
    assert zeros
    for record in zeros:
        assert record.hidden_expectations.allowed_action_deals == []
        assert "Seller still owes" not in record.scenario


def test_action_monitor_sets_disjoint() -> None:
    for record in generate_holdouts(count=60, seed=1211901):
        actions = set(record.hidden_expectations.allowed_action_deals)
        monitors = set(record.hidden_expectations.required_monitor_deals)
        meetings = set(record.hidden_expectations.meeting_deals)
        records = set(record.hidden_expectations.record_only_deals)
        assert actions.isdisjoint(monitors)
        assert actions.isdisjoint(meetings)
        assert records.isdisjoint(actions | meetings | monitors)


def test_generated_dates_are_temporally_valid() -> None:
    import re
    from datetime import date

    close_re = re.compile(r"close (\d{4}-\d{2}-\d{2})")
    last_re = re.compile(r"last activity (\d{4}-\d{2}-\d{2})")
    brief_re = re.compile(r"\((\d{4}-\d{2}-\d{2})\)")
    for record in generate_holdouts(count=60, seed=1211901):
        briefing = date.fromisoformat(brief_re.search(record.scenario).group(1))
        for match in close_re.finditer(record.scenario):
            close = date.fromisoformat(match.group(1))
            if close < briefing:
                assert "labeled stale/contradictory-data" in record.scenario.lower()
                assert record.dimensions["data_quality"] == "contradictory_note_table"
            else:
                assert close >= briefing
        for match in last_re.finditer(record.scenario):
            last = date.fromisoformat(match.group(1))
            assert last <= briefing
