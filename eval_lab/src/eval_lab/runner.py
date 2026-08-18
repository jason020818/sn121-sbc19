"""Agent runner over OpenRouter chat completions."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from eval_lab.config import LabConfig

AGENT_SYSTEM = "You are evaluating a reusable skill. Follow the supplied skill instructions faithfully."


class ChatClient(Protocol):
    def complete(self, model: str, messages: list[dict[str, str]], temperature: float = 0.0) -> str: ...


@dataclass
class ModelResponse:
    text: str
    model: str
    latency_ms: float
    usage: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None


class ModelUnavailableError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(self, config: LabConfig, api_key: str | None = None) -> None:
        self.config = config
        self.api_key = api_key if api_key is not None else os.environ.get(config.provider.api_key_env, "")
        self.base_url = config.provider.base_url.rstrip("/")

    def complete(self, model: str, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        return self.complete_detailed(model, messages, temperature).text

    def complete_detailed(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> ModelResponse:
        if not self.api_key:
            raise ModelUnavailableError(
                f"Missing API key in environment variable {self.config.provider.api_key_env}. "
                "No paid call was attempted."
            )
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        started = time.perf_counter()
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers, json=payload)
        latency_ms = (time.perf_counter() - started) * 1000
        body: dict[str, Any]
        try:
            body = response.json()
        except ValueError as exc:
            raise ModelUnavailableError(f"Non-JSON response from provider for model {model}") from exc
        if response.status_code >= 400:
            message = _error_message(body) or response.text[:300]
            lowered = message.lower()
            if any(token in lowered for token in ("not found", "unavailable", "does not exist", "invalid model")):
                raise ModelUnavailableError(
                    f"Configured model {model!r} is unavailable. Refusing to substitute another model. {message}"
                )
            raise ModelUnavailableError(f"Provider error for model {model!r}: {message}")
        text = _choice_text(body)
        return ModelResponse(
            text=text,
            model=model,
            latency_ms=latency_ms,
            usage=body.get("usage") if isinstance(body.get("usage"), dict) else None,
            raw={"id": body.get("id"), "model": body.get("model")},
        )


def _error_message(body: dict[str, Any]) -> str:
    error = body.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error)
    return str(error or "")


def _choice_text(body: dict[str, Any]) -> str:
    choices = body.get("choices") or []
    if not choices:
        raise ModelUnavailableError("Provider returned no choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        return "".join(parts)
    raise ModelUnavailableError("Provider returned an empty message")


def agent_messages(skill: str, scenario: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": AGENT_SYSTEM},
        {
            "role": "user",
            "content": f"SKILL\n{skill}\n\nSCENARIO\n{scenario}",
        },
    ]


def estimate_calls(n_scenarios: int, repeats: int, n_judges: int) -> dict[str, int]:
    agent = n_scenarios * repeats
    judges = agent * n_judges
    return {
        "scenarios": n_scenarios,
        "repeats": repeats,
        "judges": n_judges,
        "agent_calls": agent,
        "judge_calls": judges,
        "total_calls": agent + judges,
    }


def run_holdout_evaluation(
    *,
    config: "LabConfig",
    candidate_name: str,
    candidate_text: str,
    candidate_sha256: str,
    holdouts: list,
    repeats: int,
    client: ChatClient,
    limit: int | None = None,
    scenario_id: str | None = None,
    dry_run: bool = False,
) -> dict:
    from collections import Counter, defaultdict

    from eval_lab.deterministic_checks import run_deterministic_checks
    from eval_lab.llm_judges import run_judges
    from eval_lab.scoring import score_output, summarize_repeats

    selected = list(holdouts)
    if scenario_id:
        selected = [item for item in selected if item.id == scenario_id]
    if limit is not None:
        selected = selected[:limit]
    estimate = estimate_calls(len(selected), repeats, config.n_judges)
    payload = {
        "kind": "holdout",
        "candidate": candidate_name,
        "candidate_sha256": candidate_sha256,
        "dry_run": dry_run,
        "repeats": repeats,
        "models": {"agent": config.models.agent, "judges": list(config.models.judges)},
        "call_estimate": estimate,
        "disclaimer": "Local internal_quality is not an official SN121 score.",
        "holdout_ids": [item.id for item in selected],
    }
    if dry_run:
        return payload

    all_scores: list[float] = []
    by_repeat: dict[int, list[float]] = defaultdict(list)
    by_dimension: dict[str, list[float]] = defaultdict(list)
    failure_counts: Counter[str] = Counter()
    hard_failures = 0
    dim_means_acc: dict[str, list[float]] = defaultdict(list)
    outputs: list[dict] = []
    for item in selected:
        for repeat_index in range(repeats):
            output = client.complete(
                model=config.models.agent,
                messages=agent_messages(candidate_text, item.scenario),
                temperature=config.evaluation.temperature,
            )
            checks = run_deterministic_checks(item.scenario, output, item.hidden_expectations)
            if checks.catastrophic:
                hard_failures += 1
            for check in checks.checks:
                if not check.passed:
                    failure_counts[str(check.name)] += 1
            judges = run_judges(
                client=client,
                models=config.models.judges,
                scenario=item.scenario,
                skill=candidate_text,
                output=output,
                checks=checks,
            )
            internal = score_output(judges, checks)
            all_scores.append(internal.penalized)
            by_repeat[repeat_index].append(internal.penalized)
            for key, value in item.dimensions.items():
                by_dimension[f"{key}={value}"].append(internal.penalized)
            for key, value in internal.dimension_means.items():
                dim_means_acc[key].append(value)
            outputs.append(
                {
                    "scenario_id": item.id,
                    "repeat_index": repeat_index,
                    "model": config.models.agent,
                    "candidate_sha256": candidate_sha256,
                    "latency_ms": None,
                    "usage": None,
                    "response_text": output,
                    "internal_score": internal.model_dump(),
                    "deterministic": checks.model_dump(),
                }
            )
    repeat_means = [summarize_repeats(vals).mean for vals in by_repeat.values()]
    worst_repeat = min(repeat_means) if repeat_means else 0.0
    summary = summarize_repeats(all_scores)
    payload.update(
        {
            "repeat_summary": summary.model_dump(),
            "worst_repeat": worst_repeat,
            "hard_failures": hard_failures,
            "deterministic_failures": dict(failure_counts),
            "dimension_means": {key: summarize_repeats(vals).mean for key, vals in dim_means_acc.items()},
            "performance_by_holdout_dimension": {
                key: summarize_repeats(vals).model_dump() for key, vals in by_dimension.items()
            },
            "outputs": outputs,
        }
    )
    return payload


class FakeChatClient:
    """Offline stand-in used by tests. Never performs network I/O."""

    def __init__(self, text: str = "offline-fake-output") -> None:
        self.text = text
        self.calls: list[dict[str, Any]] = []

    def complete(self, model: str, messages: list[dict[str, str]], temperature: float = 0.0) -> str:
        self.calls.append({"model": model, "messages": messages, "temperature": temperature})
        if "grounding_accuracy" in (messages[-1]["content"] if messages else ""):
            return (
                '{"grounding_accuracy":0.8,"prioritization_quality":0.8,'
                '"actionability":0.8,"waiting_state_judgment":0.8,'
                '"meeting_preparation_quality":0.8,"concision":0.8,'
                '"skill_adherence":0.8,"rationale":"offline fixture"}'
            )
        return self.text
