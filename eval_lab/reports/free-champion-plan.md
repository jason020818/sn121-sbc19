# Free champion plan

Remaining uncertainty: Haiku instruction-following is not measured here. A live SN121 submission remains the only official validator sample. The recommended rendering does not have a predicted official score.

semantic_policy_family: balanced
semantic_equivalents: ['candidate-b-ledger', 'production-f9e5400']
recommended_rendering: candidate-b-minimal
reserve_rendering: candidate-b-ledger
aggressive_policy_status: rank=4 f1=0.9942238267148015 false_action=0.006666666666666667 missed_action=0.0 flip_exact=0.9933333333333333
conservative_policy_status: rank=3 f1=0.8005226480836237 false_action=0.0 missed_action=0.19083333333333333 flip_exact=0.49333333333333335
controlled_flip_exact_pass_rate: 1.0

No predicted official score is attached to the recommended rendering.
SKILL.md was not modified.

## Domain ranking

1. candidate-b-ledger family=balanced f1=1.0 false_action=0.0 flip_exact=1.0
2. production-f9e5400 family=balanced f1=1.0 false_action=0.0 flip_exact=1.0
3. candidate-a-conservative family=conservative f1=0.8005226480836237 false_action=0.0 flip_exact=0.49333333333333335
4. candidate-c-assertive family=assertive f1=0.9942238267148015 false_action=0.006666666666666667 flip_exact=0.9933333333333333

## Rendering ranking

1. candidate-b-minimal risk=0.0 words=408
2. candidate-b-ledger risk=0.0 words=510
3. production-f9e5400 risk=2.675 words=1170

## Historical calibration

- Historical submitted skills ranged 1107-3372 words with rendering-risk 10.52-38.40. Shorter snapshots that kept mandatory rules tracked with more stable skill_use; this is qualitative, not a predicted official score.
- Archived outputs still show deterministic execution failures (duplicate deal, pipeline sum, unsupported channel, word-limit overshoot). Rendering risk is associated with those failure classes, not a score forecast.
- Do not interpret these features as a predicted official score such as 0.81.
