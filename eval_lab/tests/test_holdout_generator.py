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
