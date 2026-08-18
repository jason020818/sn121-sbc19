# Rendering-risk tournament

Rendering-risk scoring is static text analysis. It does not predict official SN121 scores and does not simulate Haiku instruction-following.

## Ranking

1. candidate-b-minimal policy=balanced risk=0.000 words=408 coverage=complete contradictions=0
2. candidate-b-ledger policy=balanced risk=0.000 words=510 coverage=complete contradictions=0
3. production-f9e5400 policy=production risk=2.675 words=1170 coverage=incomplete contradictions=0
4. candidate-c-assertive policy=assertive risk=5.250 words=475 coverage=complete contradictions=1
5. candidate-a-conservative policy=conservative risk=7.000 words=558 coverage=incomplete contradictions=1

## Historical calibration

- Historical submitted skills ranged 1107-3372 words with rendering-risk 10.52-38.40. Shorter snapshots that kept mandatory rules tracked with more stable skill_use; this is qualitative, not a predicted official score.
- Archived outputs still show deterministic execution failures (duplicate deal, pipeline sum, unsupported channel, word-limit overshoot). Rendering risk is associated with those failure classes, not a score forecast.
- Do not interpret these features as a predicted official score such as 0.81.

## Archive snapshots

- mine: total=0.7052935000000002 skill_use=0.85 scenario_quality=0.5984 rubric=0.577 dataset_derived=0.5499999999999999 words=3372 risk=36.43 failures={'pipeline sum': 7, 'duplicate deal': 2, 'unsupported channel': 9, 'word-limit overshoot': 10}
- latest: total=0.6974800000000001 skill_use=0.8 scenario_quality=0.5326000000000001 rubric=0.6589999999999999 dataset_derived=0.9000000000000001 words=1126 risk=30.565 failures={'pipeline sum': 10, 'duplicate deal': 1, 'unsupported channel': 7, 'word-limit overshoot': 10}
- run-0.7378429: total=0.7378429000000002 skill_use=0.825 scenario_quality=0.5780000000000001 rubric=0.7259999999999999 dataset_derived=0.9000000000000001 words=1107 risk=10.5175 failures={'pipeline sum': 3, 'duplicate deal': 3, 'unsupported channel': 6, 'word-limit overshoot': 5}
- champion: total=0.7668400000000002 skill_use=0.875 scenario_quality=0.6778000000000001 rubric=0.6699999999999998 dataset_derived=0.75 words=2661 risk=38.4025 failures={'unsupported channel': 8, 'word-limit overshoot': 9}
