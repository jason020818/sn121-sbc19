"""CLI for the local pre-submission evaluation lab."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from eval_lab.archive_loader import load_archive
from eval_lab.candidate_store import (
    CandidateStoreError,
    add_candidate,
    list_candidates,
    read_candidate,
)
from eval_lab.config import LabConfig, load_config, repo_root
from eval_lab.holdout_generator import generate_holdouts, load_holdouts, write_holdouts
from eval_lab.regression import run_regression
from eval_lab.release_gate import RELEASE_DISCLAIMER, evaluate_release
from eval_lab.report import render_eval_markdown, render_release_markdown, timestamp_slug, write_pair
from eval_lab.runner import OpenRouterClient, estimate_calls, run_holdout_evaluation
from eval_lab.scoring import generalization_proxy, rank_tournament

app = typer.Typer(no_args_is_help=True, help="Local SBC19 evaluation lab. Internal scores are not official SN121 scores.")
candidate_app = typer.Typer(no_args_is_help=True, help="Manage skill candidates.")
holdout_app = typer.Typer(no_args_is_help=True, help="Generate and evaluate synthetic holdouts.")
app.add_typer(candidate_app, name="candidate")
app.add_typer(holdout_app, name="holdout")
console = Console()

PRODUCTION_SKILL = "SKILL.md"


def _config(config: Optional[Path] = None) -> LabConfig:
    return load_config(config)


def _guard_skill_md() -> None:
    path = repo_root() / PRODUCTION_SKILL
    if not path.exists():
        raise typer.BadParameter("SKILL.md is missing; refusing to continue.")


def _confirm_paid(yes: bool, dry_run: bool, estimate: dict) -> None:
    console.print(
        f"[yellow]Estimated calls[/yellow]: {estimate['agent_calls']} agent + "
        f"{estimate['judge_calls']} judge = {estimate['total_calls']} total "
        f"({estimate['scenarios']} scenarios × {estimate['repeats']} repeats × "
        f"{1 + estimate['judges']} model calls per scenario-repeat)."
    )
    if dry_run:
        console.print("[cyan]Dry-run: no paid API calls will be made.[/cyan]")
        return
    if not yes:
        console.print(
            "[red]Refusing paid execution.[/red] Re-run with --yes after reviewing the estimate, "
            "or pass --dry-run."
        )
        raise typer.Exit(code=3)


@candidate_app.command("add")
def candidate_add(
    name: str = typer.Option(..., "--name"),
    file: Path = typer.Option(..., "--file", exists=True, readable=True),
    force: bool = typer.Option(False, "--force"),
) -> None:
    _guard_skill_md()
    try:
        entry = add_candidate(name, file, force=force)
    except CandidateStoreError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=3) from exc
    console.print(f"Stored candidate [bold]{entry.name}[/bold] sha256={entry.sha256}")


@candidate_app.command("list")
def candidate_list() -> None:
    entries = list_candidates()
    if not entries:
        console.print("No candidates registered.")
        return
    table = Table(title="Candidates")
    table.add_column("name")
    table.add_column("sha256")
    table.add_column("added_at")
    for entry in entries:
        table.add_row(entry.name, entry.sha256, entry.added_at)
    console.print(table)


@holdout_app.command("generate")
def holdout_generate(
    count: int = typer.Option(60, "--count"),
    seed: int = typer.Option(1211901, "--seed"),
) -> None:
    records = generate_holdouts(count=count, seed=seed)
    path = write_holdouts(records)
    console.print(f"Wrote {len(records)} holdouts to {path}")


@app.command("regression")
def regression_cmd(
    candidate: str = typer.Option(..., "--candidate"),
    source: Path = typer.Option(Path("results/run-0.7378429/raw_evaluation.json"), "--source"),
    repeats: int = typer.Option(5, "--repeats"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes"),
    limit: Optional[int] = typer.Option(None, "--limit"),
    scenario: Optional[str] = typer.Option(None, "--scenario"),
    config: Optional[Path] = typer.Option(None, "--config"),
) -> None:
    _guard_skill_md()
    cfg = _config(config)
    try:
        path, text, digest = read_candidate(candidate)
    except CandidateStoreError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=3) from exc
    payload = run_regression(
        config=cfg,
        candidate_name=path.stem,
        candidate_text=text,
        candidate_sha256=digest,
        source=source,
        repeats=repeats,
        client=OpenRouterClient(cfg),
        limit=limit,
        scenario_id=scenario,
        dry_run=True,
    )
    _confirm_paid(yes=yes, dry_run=dry_run, estimate=payload["call_estimate"])
    if not dry_run:
        payload = run_regression(
            config=cfg,
            candidate_name=path.stem,
            candidate_text=text,
            candidate_sha256=digest,
            source=source,
            repeats=repeats,
            client=OpenRouterClient(cfg),
            limit=limit,
            scenario_id=scenario,
            dry_run=False,
        )
    stem = f"{timestamp_slug()}-{path.stem}-regression" + ("-dry-run" if dry_run else "")
    json_path, md_path = write_pair(stem, payload, render_eval_markdown("regression", payload))
    console.print(f"Wrote {json_path} and {md_path}")
    console.print("Historical official score is context only; local score is internal.")


@holdout_app.command("run")
def holdout_run(
    candidate: str = typer.Option(..., "--candidate"),
    repeats: int = typer.Option(5, "--repeats"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes"),
    limit: Optional[int] = typer.Option(None, "--limit"),
    scenario: Optional[str] = typer.Option(None, "--scenario"),
    config: Optional[Path] = typer.Option(None, "--config"),
) -> None:
    _guard_skill_md()
    cfg = _config(config)
    try:
        path, text, digest = read_candidate(candidate)
        holdouts = load_holdouts()
    except (CandidateStoreError, FileNotFoundError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=3) from exc
    payload = run_holdout_evaluation(
        config=cfg,
        candidate_name=path.stem,
        candidate_text=text,
        candidate_sha256=digest,
        holdouts=holdouts,
        repeats=repeats,
        client=OpenRouterClient(cfg),
        limit=limit,
        scenario_id=scenario,
        dry_run=True,
    )
    _confirm_paid(yes=yes, dry_run=dry_run, estimate=payload["call_estimate"])
    if not dry_run:
        payload = run_holdout_evaluation(
            config=cfg,
            candidate_name=path.stem,
            candidate_text=text,
            candidate_sha256=digest,
            holdouts=holdouts,
            repeats=repeats,
            client=OpenRouterClient(cfg),
            limit=limit,
            scenario_id=scenario,
            dry_run=False,
        )
    stem = f"{timestamp_slug()}-{path.stem}-holdout" + ("-dry-run" if dry_run else "")
    json_path, md_path = write_pair(stem, payload, render_eval_markdown("holdout", payload))
    console.print(f"Wrote {json_path} and {md_path}")


@app.command("tournament")
def tournament_cmd(
    candidates: list[str] = typer.Option(..., "--candidates"),
    repeats: int = typer.Option(5, "--repeats"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    yes: bool = typer.Option(False, "--yes"),
    limit: Optional[int] = typer.Option(None, "--limit"),
    config: Optional[Path] = typer.Option(None, "--config"),
) -> None:
    _guard_skill_md()
    cfg = _config(config)
    try:
        holdouts = load_holdouts()
        resolved = [read_candidate(name) for name in candidates]
        archive = load_archive("results/run-0.7378429/raw_evaluation.json")
    except (CandidateStoreError, FileNotFoundError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=3) from exc
    n_reg = len(archive.samples) if limit is None else min(limit, len(archive.samples))
    n_hold = len(holdouts) if limit is None else min(limit, len(holdouts))
    per_candidate = estimate_calls(n_reg + n_hold, repeats, cfg.n_judges)
    estimate = {
        "scenarios": per_candidate["scenarios"] * len(resolved),
        "repeats": repeats,
        "judges": cfg.n_judges,
        "agent_calls": per_candidate["agent_calls"] * len(resolved),
        "judge_calls": per_candidate["judge_calls"] * len(resolved),
        "total_calls": per_candidate["total_calls"] * len(resolved),
    }
    _confirm_paid(yes=yes, dry_run=dry_run, estimate=estimate)
    rows = []
    for path, text, digest in resolved:
        if dry_run:
            rows.append(
                {
                    "candidate": path.stem,
                    "candidate_sha256": digest,
                    "catastrophic_failures": 0,
                    "holdout_median": 0.0,
                    "holdout_worst_repeat": 0.0,
                    "regression_median": 0.0,
                    "stddev": 0.0,
                    "dry_run": True,
                }
            )
            continue
        client = OpenRouterClient(cfg)
        holdout_payload = run_holdout_evaluation(
            config=cfg,
            candidate_name=path.stem,
            candidate_text=text,
            candidate_sha256=digest,
            holdouts=holdouts,
            repeats=repeats,
            client=client,
            limit=limit,
            dry_run=False,
        )
        regression_payload = run_regression(
            config=cfg,
            candidate_name=path.stem,
            candidate_text=text,
            candidate_sha256=digest,
            source="results/run-0.7378429/raw_evaluation.json",
            repeats=repeats,
            client=client,
            limit=limit,
            dry_run=False,
        )
        rows.append(
            {
                "candidate": path.stem,
                "candidate_sha256": digest,
                "catastrophic_failures": holdout_payload.get("hard_failures", 0),
                "holdout_median": holdout_payload.get("repeat_summary", {}).get("median", 0.0),
                "holdout_worst_repeat": holdout_payload.get("worst_repeat", 0.0),
                "regression_median": regression_payload.get("repeat_summary", {}).get("median", 0.0),
                "stddev": holdout_payload.get("repeat_summary", {}).get("stddev", 0.0),
            }
        )
    ranked = rank_tournament(rows)
    payload = {
        "kind": "tournament",
        "dry_run": dry_run,
        "repeats": repeats,
        "call_estimate": estimate,
        "disclaimer": "Ranking uses internal quality, not official SN121 scores.",
        "results": ranked,
    }
    stem = f"{timestamp_slug()}-tournament" + ("-dry-run" if dry_run else "")
    json_path, md_path = write_pair(
        stem,
        payload,
        "# Tournament\n\n" + "\n".join(f"{row['rank']}. {row['candidate']}" for row in ranked) + "\n",
    )
    console.print(f"Wrote {json_path} and {md_path}")


@app.command("release-check")
def release_check(
    candidate: str = typer.Option(..., "--candidate"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    config: Optional[Path] = typer.Option(None, "--config"),
) -> None:
    _guard_skill_md()
    cfg = _config(config)
    try:
        path, text, digest = read_candidate(candidate)
    except CandidateStoreError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=3) from exc
    proxy = generalization_proxy(text)
    if dry_run:
        n_hold = cfg.holdout.count
        n_reg = 10
        estimate = estimate_calls(n_hold + n_reg, cfg.evaluation.repeats, cfg.n_judges)
        console.print(f"Candidate {path.stem} sha256={digest}")
        console.print(f"Generalization proxy (static lint): {proxy}")
        _confirm_paid(yes=False, dry_run=True, estimate=estimate)
        payload = {
            "candidate": path.stem,
            "candidate_sha256": digest,
            "passed": False,
            "mode": "dry-run",
            "disclaimer": RELEASE_DISCLAIMER,
            "conditions": [
                {
                    "name": "generalization_proxy",
                    "status": "PASS" if proxy >= cfg.release_gate.min_dataset_generalization_proxy else "FAIL",
                    "observed": proxy,
                    "threshold": cfg.release_gate.min_dataset_generalization_proxy,
                    "comparator": ">=",
                },
                {
                    "name": "remaining_score_conditions",
                    "status": "PENDING",
                    "observed": None,
                    "threshold": None,
                    "comparator": "requires paid evaluation reports",
                },
            ],
            "call_estimate": estimate,
        }
        stem = f"{timestamp_slug()}-{path.stem}-release-dry-run"
        json_path, md_path = write_pair(stem, payload, render_release_markdown(payload))
        console.print(RELEASE_DISCLAIMER)
        console.print(f"Wrote {json_path} and {md_path}")
        raise typer.Exit(code=0)

    metrics = _load_latest_metrics(path.stem)
    if metrics is None:
        console.print("[red]Missing regression/holdout reports for this candidate.[/red]")
        raise typer.Exit(code=3)
    decision = evaluate_release(gate=cfg.release_gate, **metrics, generalization_proxy=proxy)
    payload = {
        "candidate": path.stem,
        "candidate_sha256": digest,
        **decision.as_dict(),
    }
    stem = f"{timestamp_slug()}-{path.stem}-release"
    json_path, md_path = write_pair(stem, payload, render_release_markdown(payload))
    for item in decision.conditions:
        console.print(f"{item['status']}: {item['name']} observed={item['observed']} threshold={item['threshold']}")
    console.print(RELEASE_DISCLAIMER)
    console.print(f"Wrote {json_path} and {md_path}")
    if decision.mode == "data_error":
        raise typer.Exit(code=3)
    raise typer.Exit(code=0 if decision.passed else 2)


def _load_latest_metrics(candidate: str) -> dict | None:
    from eval_lab.report import reports_dir

    directory = reports_dir()
    regression = _latest(directory, f"{candidate}-regression.json")
    holdout = _latest(directory, f"{candidate}-holdout.json")
    if regression is None or holdout is None:
        return None
    if regression.get("dry_run") or holdout.get("dry_run"):
        return None
    return {
        "regression_median": regression.get("repeat_summary", {}).get("median"),
        "holdout_median": holdout.get("repeat_summary", {}).get("median"),
        "holdout_worst_repeat": holdout.get("worst_repeat"),
        "holdout_stddev": holdout.get("repeat_summary", {}).get("stddev"),
        "grounding_pass_rate": _grounding_from_outputs(holdout.get("outputs", []) + regression.get("outputs", [])),
        "catastrophic_failures": int(holdout.get("hard_failures") or 0),
    }


def _latest(directory: Path, suffix: str) -> dict | None:
    matches = sorted(directory.glob(f"*-{suffix}"))
    matches = [path for path in matches if "dry-run" not in path.name]
    if not matches:
        return None
    return json.loads(matches[-1].read_text(encoding="utf-8"))


def _grounding_from_outputs(outputs: list[dict]) -> float:
    total = 0
    passed = 0
    for item in outputs:
        checks = (item.get("deterministic") or {}).get("checks") or []
        for check in checks:
            if check.get("name") in {"entity_grounding", "amount_grounding"}:
                total += 1
                if check.get("passed"):
                    passed += 1
    return 1.0 if total == 0 else passed / total


def main() -> None:
    app()


if __name__ == "__main__":
    main()
