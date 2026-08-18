"""Agent runner over OpenRouter chat completions."""

from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

import httpx

from eval_lab.config import LabConfig
from eval_lab.models import HiddenExpectations

AGENT_SYSTEM = "You are evaluating a reusable skill. Follow the supplied skill instructions faithfully."


class ChatClient(Protocol):
    def complete(self, model: str, messages: list[dict[str, str]], temperature: float = 0.0) -> str: ...


@dataclass
class ModelResponse:
    text: str
    model: str
    latency_ms: float | None
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
        returned_model = body.get("model") if isinstance(body.get("model"), str) else model
        return ModelResponse(
            text=text,
            model=returned_model,
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


def invoke_model(client: ChatClient, model: str, messages: list[dict[str, str]], temperature: float) -> ModelResponse:
    detailed = getattr(client, "complete_detailed", None)
    if callable(detailed):
        return detailed(model=model, messages=messages, temperature=temperature)
    text = client.complete(model=model, messages=messages, temperature=temperature)
    return ModelResponse(text=text, model=model, latency_ms=None, usage=None, raw=None)


@dataclass
class ScenarioJob:
    scenario_id: str
    scenario_text: str
    repeat_index: int
    expectations: HiddenExpectations | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def run_jobs_with_concurrency(
    *,
    jobs: list[ScenarioJob],
    config: LabConfig,
    client: ChatClient,
    candidate_text: str,
    candidate_sha256: str,
    score_one: Callable[[ScenarioJob, ModelResponse, list[ModelResponse]], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run agent-then-judges jobs with a global concurrency cap.

    Results are sorted by (scenario_id, repeat_index). One provider failure
    fails closed; models are never substituted.
    """
    cap = max(1, int(config.evaluation.max_concurrency))
    gate = threading.Semaphore(cap)

    def guarded_invoke(model: str, messages: list[dict[str, str]]) -> ModelResponse:
        with gate:
            return invoke_model(client, model, messages, config.evaluation.temperature)

    def run_one(job: ScenarioJob) -> dict[str, Any]:
        agent = guarded_invoke(config.models.agent, agent_messages(candidate_text, job.scenario_text))
        from eval_lab.deterministic_checks import run_deterministic_checks
        from eval_lab.llm_judges import JUDGE_SYSTEM, judge_prompt, parse_judge_json

        checks = run_deterministic_checks(job.scenario_text, agent.text, job.expectations)
        judge_responses: list[ModelResponse] = []
        parsed_judges = []
        for model in config.models.judges:
            messages = [
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": judge_prompt(job.scenario_text, candidate_text, agent.text, checks)},
            ]
            response = guarded_invoke(model, messages)
            judge_responses.append(response)
            parsed_judges.append(parse_judge_json(response.text, model=response.model))
        record = score_one(job, agent, judge_responses)
        record.update(
            {
                "scenario_id": job.scenario_id,
                "repeat_index": job.repeat_index,
                "model": agent.model,
                "candidate_sha256": candidate_sha256,
                "latency_ms": agent.latency_ms,
                "usage": agent.usage,
                "response_text": agent.text,
                "deterministic": checks.model_dump(),
                "judges": [
                    {
                        "model": item.model,
                        "latency_ms": item.latency_ms,
                        "usage": item.usage,
                    }
                    for item in judge_responses
                ],
            }
        )
        record.setdefault("internal_score", None)
        from eval_lab.scoring import score_output

        if record.get("internal_score") is None:
            record["internal_score"] = score_output(parsed_judges, checks).model_dump()
            record["_parsed_judges"] = parsed_judges
            record["_checks"] = checks
        else:
            record["_parsed_judges"] = parsed_judges
            record["_checks"] = checks
        return record

    results: list[dict[str, Any]] = []
    errors: list[str] = []
    workers = min(cap, max(1, len(jobs)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_one, job): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001 — fail closed with context
                errors.append(f"{job.scenario_id} repeat {job.repeat_index}: {exc}")
    if errors:
        raise ModelUnavailableError(
            "Provider call failed; refusing to substitute models or continue. " + " | ".join(errors[:8])
        )
    results.sort(key=lambda item: (str(item["scenario_id"]), int(item["repeat_index"])))
    return results


def run_holdout_evaluation(
    *,
    config: LabConfig,
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

    from eval_lab.scoring import repeat_level_stats, summarize_repeats

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
        "max_concurrency": config.evaluation.max_concurrency,
    }
    if dry_run:
        return payload

    jobs: list[ScenarioJob] = []
    holdout_by_id = {item.id: item for item in selected}
    for item in selected:
        for repeat_index in range(repeats):
            jobs.append(
                ScenarioJob(
                    scenario_id=item.id,
                    scenario_text=item.scenario,
                    repeat_index=repeat_index,
                    expectations=item.hidden_expectations,
                )
            )

    def score_one(job: ScenarioJob, agent: ModelResponse, judge_responses: list[ModelResponse]) -> dict[str, Any]:
        return {}

    records = run_jobs_with_concurrency(
        jobs=jobs,
        config=config,
        client=client,
        candidate_text=candidate_text,
        candidate_sha256=candidate_sha256,
        score_one=score_one,
    )
    all_scores: list[float] = []
    by_repeat: dict[int, list[float]] = defaultdict(list)
    by_dimension: dict[str, list[float]] = defaultdict(list)
    failure_counts: Counter[str] = Counter()
    hard_failures = 0
    dim_means_acc: dict[str, list[float]] = defaultdict(list)
    outputs: list[dict] = []
    for record in records:
        internal = record["internal_score"]
        score = float(internal["penalized"])
        all_scores.append(score)
        by_repeat[int(record["repeat_index"])].append(score)
        item = holdout_by_id[record["scenario_id"]]
        for key, value in item.dimensions.items():
            by_dimension[f"{key}={value}"].append(score)
        for key, value in internal.get("dimension_means", {}).items():
            dim_means_acc[key].append(value)
        checks = record["_checks"]
        if checks.catastrophic:
            hard_failures += 1
        for check in checks.checks:
            if not check.passed:
                failure_counts[str(check.name)] += 1
        outputs.append({k: v for k, v in record.items() if not k.startswith("_")})
    stats = repeat_level_stats(dict(by_repeat))
    payload.update(
        {
            "scenario_score_summary": stats["scenario_score_summary"],
            "repeat_means": stats["repeat_means"],
            "repeat_mean_summary": stats["repeat_mean_summary"],
            "repeat_summary": stats["repeat_mean_summary"],
            "holdout_worst_repeat": stats["holdout_worst_repeat"],
            "worst_repeat": stats["holdout_worst_repeat"],
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
        return self.complete_detailed(model, messages, temperature).text

    def complete_detailed(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> ModelResponse:
        self.calls.append({"model": model, "messages": messages, "temperature": temperature})
        if "grounding_accuracy" in (messages[-1]["content"] if messages else ""):
            text = (
                '{"grounding_accuracy":0.8,"prioritization_quality":0.8,'
                '"actionability":0.8,"waiting_state_judgment":0.8,'
                '"meeting_preparation_quality":0.8,"concision":0.8,'
                '"skill_adherence":0.8,"rationale":"offline fixture"}'
            )
        else:
            text = self.text
        return ModelResponse(text=text, model=model, latency_ms=None, usage=None, raw=None)
