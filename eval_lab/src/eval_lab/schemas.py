"""Schema helpers and JSON-shape utilities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TolerantModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class GradesByKeyItem(TolerantModel):
    score: float | int | None = None
    rationale: str | None = None
    usage: dict[str, Any] | None = None


class SampleResultBody(TolerantModel):
    weighted_score: float | None = None
    grade: dict[str, Any] | None = None
    grades_by_key: dict[str, GradesByKeyItem] = Field(default_factory=dict)
    performance: dict[str, Any] | None = None
    gate_passed: bool | int | None = None


class TrajectoryMessage(TolerantModel):
    kind: str | None = None
    role: str | None = None
    name: str | None = None
    content: Any = None
    id: str | None = None
    arguments: Any = None


class TrajectoryBody(TolerantModel):
    messages: list[TrajectoryMessage] = Field(default_factory=list)
    step_count: int | None = None
    total_tokens: int | None = None
    finish_reason: str | None = None


class RawSample(TolerantModel):
    id: str | None = None
    sample_id: str | None = None
    result: SampleResultBody | None = None
    trajectory: TrajectoryBody | None = None


class RawSummary(TolerantModel):
    metrics: dict[str, Any] = Field(default_factory=dict)


class RawEvaluation(TolerantModel):
    summary: RawSummary | None = None
    results: list[RawSample] = Field(default_factory=list)
    duration_seconds: float | None = None
