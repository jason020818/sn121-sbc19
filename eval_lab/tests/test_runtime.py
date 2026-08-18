"""Runtime dry-run and calibration tests. No network."""

from eval_lab.config import load_config
from eval_lab.deterministic_checks import calibrate_archived_outputs, run_deterministic_checks
from eval_lab.holdout_generator import generate_holdouts
from eval_lab.regression import run_regression
from eval_lab.runner import FakeChatClient, run_holdout_evaluation


def test_dry_run_performs_zero_client_calls() -> None:
    cfg = load_config()
    client = FakeChatClient()
    skill = "# skill\nUse only supplied facts.\n"
    regression = run_regression(
        config=cfg,
        candidate_name="dry",
        candidate_text=skill,
        candidate_sha256="abc",
        source="results/run-0.7378429/raw_evaluation.json",
        repeats=5,
        client=client,
        dry_run=True,
    )
    holdouts = generate_holdouts(count=3, seed=99)
    holdout = run_holdout_evaluation(
        config=cfg,
        candidate_name="dry",
        candidate_text=skill,
        candidate_sha256="abc",
        holdouts=holdouts,
        repeats=5,
        client=client,
        dry_run=True,
    )
    assert client.calls == []
    assert regression["call_estimate"]["total_calls"] == 10 * 5 * 3
    assert holdout["call_estimate"]["total_calls"] == 3 * 5 * 3


def test_fake_client_records_agent_temperature_02_and_judge_temperature_00() -> None:
    cfg = load_config()
    client = FakeChatClient()
    skill = "# skill\nUse only supplied facts.\n"
    run_regression(
        config=cfg,
        candidate_name="temp",
        candidate_text=skill,
        candidate_sha256="abc",
        source="results/run-0.7378429/raw_evaluation.json",
        repeats=1,
        client=client,
        limit=1,
        dry_run=False,
    )
    assert client.calls
    agent_temps = []
    judge_temps = []
    for call in client.calls:
        contents = " ".join(message.get("content", "") for message in call["messages"])
        if "local quality judge" in contents or "grounding_accuracy" in contents:
            judge_temps.append(call["temperature"])
        else:
            agent_temps.append(call["temperature"])
    assert agent_temps
    assert judge_temps
    assert set(agent_temps) == {0.2}
    assert set(judge_temps) == {0.0}


def test_calibration_performs_zero_client_calls() -> None:
    client = FakeChatClient()
    payload = calibrate_archived_outputs("results/run-0.7378429/raw_evaluation.json")
    assert client.calls == []
    assert payload["n_samples"] == 10
    assert "Zero model/API calls" in payload["disclaimer"]


def test_calibration_examples_grounding_and_totals() -> None:
    scenario = (
        "Deal Helix Bureau ($80K). Contact Ira Calder. Labeled pipeline total: $80K. "
        "Do not contact Nautilus Outfit until 2026-09-30. "
        "Human correction: CRM last activity shows May 1; actual last human touch is April 2."
    )
    good = (
        "## Priority Actions\n1. **Helix Bureau** — Send the scope to Ira Calder ($80K).\n"
        "## Pipeline Health\n1 genuine seller move today. Labeled pipeline total: $80K.\n"
    )
    report = run_deterministic_checks(scenario, good)
    names = {item.name: item.passed for item in report.checks}
    assert names["entity_grounding"] is True
    assert names["amount_grounding"] is True

    invented_ent = run_deterministic_checks(scenario, good.replace("Helix Bureau", "Ghost Foundry Inc"))
    assert any(item.name == "entity_grounding" and not item.passed for item in invented_ent.checks)

    invented_amt = run_deterministic_checks(scenario, good.replace("$80K", "$999K"))
    assert any(item.name == "amount_grounding" and not item.passed for item in invented_amt.checks)

    derived = run_deterministic_checks(
        "Deal Helix Bureau ($40K). Deal Emberwick Labs ($40K).",
        "## Pipeline Health\n2 open deals, $80K total.\n",
    )
    assert any(item.name == "no_derived_pipeline_sum" and not item.passed for item in derived.checks)

    labeled = run_deterministic_checks(
        "Deal Helix Bureau ($40K). Deal Emberwick Labs ($40K).\nLabeled pipeline total: $80K\n",
        "## Pipeline Health\n2 open deals, $80K total.\n",
    )
    assert any(item.name == "no_derived_pipeline_sum" and item.passed for item in labeled.checks)

    dup = run_deterministic_checks(
        scenario,
        "## Priority Actions\n1. **Helix Bureau** — Send the scope.\n## Needs Record Update\n- **Helix Bureau** — repair.\n",
    )
    assert any(item.name == "no_duplicate_operational_deal" and not item.passed for item in dup.checks)

    contact = run_deterministic_checks(
        scenario,
        "## Priority Actions\n1. **Nautilus Outfit** — Call someone.\n",
    )
    assert any(item.name == "explicit_contact_constraint" and not item.passed for item in contact.checks)

    stamp = run_deterministic_checks(
        scenario,
        "## Priority Actions\n1. **Helix Bureau** — Send the scope. Last activity is May 1.\n",
    )
    assert any(item.name == "record_correction" and not item.passed for item in stamp.checks)
