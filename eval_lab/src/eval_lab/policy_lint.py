"""Conservative semantic coverage lint of markdown vs policy manifest."""

from __future__ import annotations

import re

from eval_lab.policy_models import PolicyManifest
from eval_lab.scoring import generalization_proxy

REQUIRED_PHRASES = {
    "pipeline_total_explicit": (
        r"never sum|do not (add|compute|calculate).{0,40}(total|sum)|only repeat a (pipeline )?total|"
        r"does not label a pipeline total|explicitly labels one|explicitly provides and labels",
        "explicit_only pipeline total",
    ),
    "unique_assignment": (
        r"only one operational section|exactly one|no deal may have two|assign exactly one|"
        r"exclusive|do not repeat the deal",
        "unique operational assignment",
    ),
    "no_filler": (
        r"never fill|no filler|never manufacture|print exactly",
        "no filler actions",
    ),
    "meeting_replaces": (
        r"meeting.{0,40}(replace|already the useful|accomplishes the needed|covers the interaction)|"
        r"do not also create outbound|today's scheduled customer",
        "meeting replaces same-objective outbound",
    ),
    "contact_override": (
        r"do-not-contact|do not contact|wait-until|wait/do-not-contact|channel instruction",
        "explicit contact constraints override",
    ),
    "recipient_channel": (
        r"recipient or channel only when|do not (choose|invent).{0,30}(recipient|channel)|"
        r"name a recipient or channel only|use a recipient or channel only when supplied",
        "recipient/channel grounding",
    ),
    "external_wait": (
        r"externally owned|customer-owned|stays? `?MONITOR`?|remain(?:s)? MONITOR",
        "external wait default",
    ),
    "escalation": (
        r"timing is (now |materially )?material|no usable checkpoint|checkpoint (has )?passed|"
        r"reduce (current |material |today's )?uncertainty",
        "external wait escalation conditions",
    ),
    "human_correction": (
        r"human correction|automated.{0,40}(not a human|does not reset)|system/automated",
        "human correction / automated touch",
    ),
}


def lint_candidate_policy(markdown: str, policy: PolicyManifest) -> dict:
    text = markdown.lower()
    missing = []
    contradictions = []
    for key, (pattern, label) in REQUIRED_PHRASES.items():
        if not re.search(pattern, markdown, flags=re.I | re.S):
            missing.append(label)
    if policy.output.pipeline_total == "explicit_only" and re.search(
        r"sum deal amounts into a total|compute a pipeline total unless you can", markdown, re.I
    ):
        contradictions.append("markdown permits derived pipeline totals")
    if policy.output.filler_actions is False and re.search(r"always print three actions", text):
        contradictions.append("markdown requires filler actions")
    if re.search(r"\bS-0(?:0[1-9]|10)\b", markdown):
        contradictions.append("scenario id present")
    if re.search(r"dataset_derived|official grader|hidden rubric", markdown, re.I):
        contradictions.append("grader/metric language present")
    proxy = generalization_proxy(markdown)
    passed = not missing and not contradictions and proxy >= 0.85
    return {
        "passed": passed,
        "missing": missing,
        "contradictions": contradictions,
        "generalization_proxy": proxy,
        "policy_name": policy.name,
        "markdown_words": len(markdown.split()),
    }
