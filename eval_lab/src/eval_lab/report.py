"""JSON and Markdown report writers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eval_lab.config import lab_root
from eval_lab.release_gate import RELEASE_DISCLAIMER


def reports_dir() -> Path:
    path = lab_root() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def write_markdown(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def write_pair(stem: str, payload: dict[str, Any], markdown: str) -> tuple[Path, Path]:
    json_path = reports_dir() / f"{stem}.json"
    md_path = reports_dir() / f"{stem}.md"
    write_json(json_path, payload)
    write_markdown(md_path, markdown)
    return json_path, md_path


def render_repeat_block(title: str, stats: dict[str, Any]) -> list[str]:
    return [
        f"## {title}",
        "",
        f"- mean: {stats.get('mean')}",
        f"- median: {stats.get('median')}",
        f"- min: {stats.get('min')}",
        f"- max: {stats.get('max')}",
        f"- stddev: {stats.get('stddev')}",
        f"- p10: {stats.get('p10')}",
        f"- n: {stats.get('n')}",
        "",
    ]


def render_release_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Release check: {payload.get('candidate')}",
        "",
        RELEASE_DISCLAIMER,
        "",
        f"Mode: {payload.get('mode')}",
        f"Result: {'PASS' if payload.get('passed') else 'FAIL'}",
        "",
        "## Conditions",
        "",
    ]
    for item in payload.get("conditions", []):
        lines.append(
            f"- {item.get('status')}: {item.get('name')} "
            f"(observed={item.get('observed')}, threshold={item.get('threshold')} {item.get('comparator', '')})"
        )
    lines.append("")
    return "\n".join(lines)


def render_eval_markdown(kind: str, payload: dict[str, Any]) -> str:
    lines = [
        f"# {kind.title()} evaluation: {payload.get('candidate')}",
        "",
        "Internal quality is not an official SN121 score.",
        "",
        f"Dry run: {payload.get('dry_run')}",
        f"Candidate sha256: {payload.get('candidate_sha256')}",
        "",
    ]
    if payload.get("call_estimate"):
        estimate = payload["call_estimate"]
        lines.extend(
            [
                "## Call estimate",
                "",
                f"- agent_calls: {estimate.get('agent_calls')}",
                f"- judge_calls: {estimate.get('judge_calls')}",
                f"- total_calls: {estimate.get('total_calls')}",
                "",
            ]
        )
    if payload.get("repeat_summary"):
        lines.extend(render_repeat_block("Repeat summary", payload["repeat_summary"]))
    if payload.get("historical_official_score") is not None:
        lines.extend(
            [
                "## Historical official context",
                "",
                f"- archived official score: {payload.get('historical_official_score')}",
                "- This number is historical context only and is not the local score.",
                "",
            ]
        )
    if payload.get("skill_delta"):
        lines.extend(["## Candidate vs current SKILL.md", "", payload["skill_delta"], ""])
    if payload.get("deterministic_failures"):
        lines.extend(["## Deterministic failure counts", ""])
        for name, count in payload["deterministic_failures"].items():
            lines.append(f"- {name}: {count}")
        lines.append("")
    return "\n".join(lines)
