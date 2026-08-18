# Free champion plan

Remaining uncertainty: Haiku instruction-following is not measured here. A live SN121 submission remains the only official validator sample. Do not promote a candidate to SKILL.md from these internal reports alone.

recommended_semantic_policy: candidate-b-ledger
recommended_rendering: candidate-b-minimal
reserve_policy_1: production-f9e5400
reserve_policy_2: candidate-a-conservative
reserve_rendering: candidate-b-ledger

SKILL.md was not modified.

## Domain ranking

1. candidate-b-ledger f1=1.0 false_action=0.0
2. production-f9e5400 f1=1.0 false_action=0.0
3. candidate-a-conservative f1=0.8005226480836237 false_action=0.0
4. candidate-c-assertive f1=0.9942238267148015 false_action=0.006666666666666667

## Rendering ranking

1. candidate-b-minimal risk=0.0 words=408
2. candidate-b-ledger risk=0.0 words=510
3. production-f9e5400 risk=2.675 words=1170
4. candidate-c-assertive risk=5.25 words=475
5. candidate-a-conservative risk=7.0 words=558

## Historical calibration

- Historical submitted skills ranged 1107-3372 words with rendering-risk 10.52-38.40. Shorter snapshots that kept mandatory rules tracked with more stable skill_use; this is qualitative, not a predicted official score.
- Archived outputs still show deterministic execution failures (duplicate deal, pipeline sum, unsupported channel, word-limit overshoot). Rendering risk is associated with those failure classes, not a score forecast.
- Do not interpret these features as a predicted official score such as 0.81.
