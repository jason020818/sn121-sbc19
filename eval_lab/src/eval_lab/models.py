"""Pydantic models used across the lab."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Severity = Literal["info", "minor", "major", "catastrophic"]
CheckName = Literal[
    "entity_grounding",
    "amount_grounding",
    "no_derived_pipeline_sum",
    "no_duplicate_operational_deal",
    "explicit_contact_constraint",
    "meeting_action_duplication",
    "word_limit",
    "action_count_consistency",
    "unsupported_channel",
    "record_correction",
]


class GraderScore(BaseModel):
    name: str
    score: float | None = None
    rationale: str | None = None


class ArchivedSample(BaseModel):
    scenario_id: str
    source_path: str
    scenario_input: str
    assistant_output: str | None = None
    gate_passed: bool | None = None
    weighted_score: float | None = None
    grader_scores: list[GraderScore] = Field(default_factory=list)
    skill_snapshot: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ArchiveRun(BaseModel):
    source_path: str
    label: str
    official_score: float | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    samples: list[ArchivedSample] = Field(default_factory=list)
    skill_snapshot: str | None = None


class HiddenExpectations(BaseModel):
    allowed_action_deals: list[str] = Field(default_factory=list)
    required_monitor_deals: list[str] = Field(default_factory=list)
    meeting_deals: list[str] = Field(default_factory=list)
    record_only_deals: list[str] = Field(default_factory=list)
    explicit_constraints: list[str] = Field(default_factory=list)
    source_entities: list[str] = Field(default_factory=list)
    source_people: list[str] = Field(default_factory=list)
    source_amounts: list[str] = Field(default_factory=list)


class HoldoutRecord(BaseModel):
    id: str
    seed: int
    scenario: str
    hidden_expectations: HiddenExpectations
    dimensions: dict[str, Any] = Field(default_factory=dict)
    deals: list[dict[str, Any]] = Field(default_factory=list)
    expected_dispositions: dict[str, str] = Field(default_factory=dict)
    variant_kind: str | None = None
    parent_id: str | None = None
    transform: str | None = None
    name_map: dict[str, str] = Field(default_factory=dict)
    flip_deals: list[str] = Field(default_factory=list)
    expected_before: dict[str, str] = Field(default_factory=dict)
    expected_after: dict[str, str] = Field(default_factory=dict)


class CheckResult(BaseModel):
    name: CheckName | str
    passed: bool
    severity: Severity
    evidence: list[str] = Field(default_factory=list)
    detail: str = ""


class DeterministicReport(BaseModel):
    passed: bool
    checks: list[CheckResult] = Field(default_factory=list)
    catastrophic: bool = False
    major_count: int = 0
    minor_count: int = 0

    @property
    def worst_severity(self) -> Severity | None:
        order = {"info": 0, "minor": 1, "major": 2, "catastrophic": 3}
        if not self.checks:
            return None
        return max((item.severity for item in self.checks if not item.passed), default="info", key=lambda s: order[s]) if any(not c.passed for c in self.checks) else None


class JudgeDimensionScores(BaseModel):
    grounding_accuracy: float
    prioritization_quality: float
    actionability: float
    waiting_state_judgment: float
    meeting_preparation_quality: float
    concision: float
    skill_adherence: float
    rationale: str | None = None
    model: str | None = None


class InternalScore(BaseModel):
    unpenalized: float
    penalized: float
    penalty_applied: str = "none"
    dimension_means: dict[str, float] = Field(default_factory=dict)
    generalization_proxy: float | None = None


class RepeatSummary(BaseModel):
    mean: float
    median: float
    min: float
    max: float
    stddev: float
    p10: float | None = None
    n: int


class CandidateManifestEntry(BaseModel):
    name: str
    path: str
    sha256: str
    added_at: str
    source_file: str | None = None
    bytes: int | None = None
