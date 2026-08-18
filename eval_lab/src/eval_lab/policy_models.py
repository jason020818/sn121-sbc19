"""Machine-readable general sales-ops policy. No benchmark-specific content."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Disposition = Literal["ACTION", "MEETING", "MONITOR", "RECORD"]


class EvidencePolicy(BaseModel):
    human_correction_overrides_field: bool = True
    automated_activity_counts_as_human_touch: bool = False
    allow_derived_pipeline_total: bool = False
    allow_invented_recipient: bool = False
    allow_invented_channel: bool = False


class EscalationPolicy(BaseModel):
    timing_material: Literal["required", "optional"] = "required"
    checkpoint: Literal["missing_or_passed", "optional"] = "missing_or_passed"
    uncertainty_reduction: Literal["required", "optional"] = "required"


class ActionPolicy(BaseModel):
    seller_owned_deliverable: bool = True
    seller_answer_due: bool = True
    schedule_needed_interaction: bool = True
    identify_missing_owner_when_needed: bool = True
    correct_operational_blocker: bool = True
    external_wait_default: Literal["monitor", "action"] = "monitor"
    external_wait_escalation: EscalationPolicy = Field(default_factory=EscalationPolicy)
    ranking: list[str] = Field(default_factory=list)


class MeetingPolicy(BaseModel):
    replaces_same_objective_outbound: bool = True
    max_derived_prep_questions: int = 1


class OutputPolicy(BaseModel):
    max_priority_actions: int = 3
    filler_actions: bool = False
    unique_operational_assignment: bool = True
    pipeline_total: Literal["explicit_only", "never", "derived_ok"] = "explicit_only"
    target_words: list[int] = Field(default_factory=lambda: [210, 280])
    max_words: int = 330


class ConstraintPolicy(BaseModel):
    explicit_wait_overrides: bool = True
    explicit_channel_overrides: bool = True


class PolicyManifest(BaseModel):
    name: str
    evidence: EvidencePolicy = Field(default_factory=EvidencePolicy)
    disposition_precedence: list[str] = Field(
        default_factory=lambda: ["meeting", "record", "action", "monitor"]
    )
    action: ActionPolicy = Field(default_factory=ActionPolicy)
    non_triggers: list[str] = Field(
        default_factory=lambda: [
            "amount_alone",
            "stage_alone",
            "age_alone",
            "quota_pressure_alone",
            "close_date_alone",
        ]
    )
    meeting: MeetingPolicy = Field(default_factory=MeetingPolicy)
    output: OutputPolicy = Field(default_factory=OutputPolicy)
    constraints: ConstraintPolicy = Field(default_factory=ConstraintPolicy)


class DealFact(BaseModel):
    name: str
    amount: str | None = None
    stage: str = "Proposal"
    close_offset_days: int = 14
    last_offset_days: int = 5
    contact: str | None = None
    state: str = "customer_legal_review"
    meeting_today: bool = False
    record_kind: str | None = None
    constraint: str | None = None
    timing_material: bool = False
    checkpoint: Literal["present", "missing", "passed", "none"] = "present"
    owner_named: bool = True
    seller_owns_next: bool = False
    uncertainty_reduction: bool = False
    channel: str | None = None


class PolicyDecision(BaseModel):
    dispositions: dict[str, Disposition]
    reasons: dict[str, str]
    action_set: list[str]
    meeting_set: list[str]
    monitor_set: list[str]
    record_set: list[str]
    constraint_holds: dict[str, str] = Field(default_factory=dict)
    catastrophic: list[str] = Field(default_factory=list)
