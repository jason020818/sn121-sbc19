# SBC19 run 0.7378429 analysis

Source: uploaded evaluation `test-output-3f329818-a96c-4b25-af3a-4ccf31cb6893.json`.
This archive does not overwrite `results/latest/` (0.69748) or earlier `results/mine/` / `results/champion/` files.

## Headline

| Metric | Previous best | Latest (0.69748) | This run | Champion baseline |
|---|---:|---:|---:|---:|
| Total | 0.70529 | 0.69748 | **0.73784** | 0.76684 |
| skill_use | 0.850 | 0.800 | **0.825** | 0.875 |
| scenario_quality | 0.5984 | 0.5326 | **0.5780** | 0.6778 |
| rubric | 0.577 | 0.659 | **0.726** | 0.670 |
| skill_alignment | 0.90 | 0.90 | **0.85** | 0.90 |
| novelty | 0.976735 | 1.00 | **0.991429** | 1.00 |
| dataset_derived | 0.55 | 0.90 | **0.90** | 0.75 |
| Gate | 10/10 | 10/10 | **10/10** | 10/10 |

This run is a new personal best versus both 0.70529 and 0.69748. The remaining gap to the 0.76684 champion baseline is **0.02900**, driven mainly by `scenario_quality` (−0.0998) and `skill_use` (−0.050). `rubric` now exceeds the prior champion average.

## Scenario scores

| Scenario | Previous best | Latest | This run | Champion | Δ vs latest | Δ vs champion |
|---|---:|---:|---:|---:|---:|---:|
| S-001 | 0.68050 | 0.74050 | 0.76300 | 0.77800 | +0.02250 | -0.01500 |
| S-002 | 0.58270 | 0.68050 | 0.66850 | 0.66850 | -0.01200 | 0.00000 |
| S-003 | 0.75100 | 0.79480 | 0.75100 | 0.75100 | -0.04380 | 0.00000 |
| S-004 | 0.78250 | 0.67150 | 0.82493 | 0.87850 | +0.15343 | -0.05357 |
| S-005 | 0.77650 | 0.72850 | 0.79900 | 0.81100 | +0.07050 | -0.01200 |
| S-006 | 0.60850 | 0.55000 | 0.65350 | 0.74950 | +0.10350 | -0.09600 |
| S-007 | 0.63474 | 0.69850 | 0.71800 | 0.69850 | +0.01950 | +0.01950 |
| S-008 | 0.74350 | 0.72850 | 0.78100 | 0.81340 | +0.05250 | -0.03240 |
| S-009 | 0.79450 | 0.66850 | 0.70600 | 0.82450 | +0.03750 | -0.11850 |
| S-010 | 0.69850 | 0.71350 | 0.71350 | 0.69550 | 0.00000 | +0.01800 |

Largest gains versus the 0.69748 run: S-004, S-006, S-005, S-008. Remaining weak spots versus champion: S-009, S-006, S-004.

## What improved

1. Gate safety held: `dataset_derived` stayed 0.90; all 10 samples passed.
2. Rubric rose from 0.659 to 0.726, now above the prior champion average of 0.670.
3. Action-count lock mostly worked: S-010 printed one Priority Action; S-005 printed two.
4. Exclusive assignment improved versus the 0.69748 run, though duplicates still leak on a few pages.

## Remaining execution failures (general, not scenario-specific)

### A. Aggregate sums are still being invented
S-001 printed `$1.523M total`. S-003 printed `$1.715M total` plus a derived `$720K combined`. S-004 printed `$1.595M total`. The handoffs supply per-deal amounts, not a labeled pipeline total. The current rule is still being treated as “sum if you can.” Next patch: never sum deal amounts; only repeat a total that the handoff already labels.

### B. Duplicate deal names still survive the exclusive-assignment pass
S-001 puts Thornfield in Priority Actions and Meeting Prep, and Redwood in Priority Actions and Needs Record Update. S-008 puts Vertex in both Priority Actions and Needs Record Update. Exclusive assignment is present, but the model needs a last-pass delete of later occurrences.

### C. Waiting-state escalation is still noisy
The model sometimes parks an externally owned process correctly, then still writes a timing/status ask, or the reverse: it leaves a near-term unsigned process in Monitor when one precise timing ask would reduce uncertainty. The rule needs a default of MONITOR, with ACTION only when timing is materially near, no usable dated checkpoint exists or it has passed, and one timing/status ask can reduce current uncertainty.

### D. Meeting prep is either too generic or too invented
Graders still penalize thin meeting notes (objective restated, no decision boundary) and also penalize invented commercial fallbacks. The next rule should allow one preparation question or decision boundary derived from the stated meeting purpose, presented as advice, never as a sourced fact, and still forbid invented pricing, concessions, product claims, or stakeholder facts.

### E. Length still overshoots
Word counts in this run: S-007 393, S-003 378, S-006 348, S-009 345, S-001 331. The 360-word ceiling was not enough for Haiku overshoot. Next target: 210–280 words, hard ceiling 330.

## Evaluator noise to ignore

Do not convert these grader claims into skill rules:

- S-006 graders again call names/deals “fabricated” that are present in the scenario input.
- S-002 / S-003 rubric claims about missing source dates or amounts often conflict with the input table.
- S-001 rubric still mentions recovery paths (LinkedIn / James at Meridian) that are not in this run’s actual output.

Those statements are judge-context problems, not evidence for scenario-specific skill patches.

## Design implication

Keep the ACTION / MEETING / MONITOR / RECORD architecture and the 0.90 `dataset_derived` safety. The next change should be a small execution-hardening patch only: no-sum aggregates, last-pass duplicate deletion, tighter waiting-state escalation, grounded meeting advice, and a shorter hard ceiling.
