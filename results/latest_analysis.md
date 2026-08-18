# SBC19 latest submission analysis

## Executive result

- Latest score: **0.69748**
- Previous best: **0.70529** (delta **-0.00781**)
- Previous champion baseline: **0.76684** (gap **-0.06936**)
- Gate: **PASS (10/10)**
- dataset_derived: **0.90** (previous 0.55)
- skill_alignment: **0.90**
- rubric: **0.659** (previous 0.577; champion baseline 0.670)
- scenario_quality: **0.5326** (previous 0.5984; champion baseline 0.6778)
- skill_use: **0.800** (previous 0.850; champion baseline 0.875)
- novelty: **1.00**

The generalization change solved the gate problem and nearly closed the rubric gap, but execution consistency regressed.

## Scenario deltas

| Scenario | Previous | Latest | Champion baseline | Δ vs previous | Δ vs champion |
|---|---:|---:|---:|---:|---:|
| S-001 | 0.68050 | 0.74050 | 0.77800 | +0.06000 | -0.03750 |
| S-002 | 0.58270 | 0.68050 | 0.66850 | +0.09780 | +0.01200 |
| S-003 | 0.75100 | 0.79480 | 0.75100 | +0.04380 | +0.04380 |
| S-004 | 0.78250 | 0.67150 | 0.87850 | -0.11100 | -0.20700 |
| S-005 | 0.77650 | 0.72850 | 0.81100 | -0.04800 | -0.08250 |
| S-006 | 0.60850 | 0.55000 | 0.74950 | -0.05850 | -0.19950 |
| S-007 | 0.63474 | 0.69850 | 0.69850 | +0.06376 | +0.00000 |
| S-008 | 0.74350 | 0.72850 | 0.81340 | -0.01500 | -0.08490 |
| S-009 | 0.79450 | 0.66850 | 0.82450 | -0.12600 | -0.15600 |
| S-010 | 0.69850 | 0.71350 | 0.69550 | +0.01500 | +0.01800 |

## What genuinely improved

1. **Gate robustness**
   - dataset_derived 0.55 -> 0.90.
   - All ten samples passed.
   - The new skill is being recognized as a general sales-operations procedure rather than dataset-specific encoding.

2. **Holistic rubric**
   - 0.577 -> 0.659, only 0.011 below the prior champion average.
   - The decision framework, evidence boundary, meeting/action separation, and waiting-state logic are broadly judged as strong.

3. **Several scenarios now beat the prior champion baseline**
   - S-002: +0.012
   - S-003: +0.0438
   - S-010: +0.018
   - S-007: tie

## Genuine execution failures in the latest outputs

### A. The model still fills three actions after saying there are fewer
- S-005 says there is one genuine action beyond the meeting, then outputs three actions.
- S-009 says there are two genuine moves, then outputs three.
This directly violates the skill's "do not manufacture a third action" rule.

### B. Duplicate deal placement remains
- S-004 places Lynx in Top 3 and again in Tier B ("also above").
- S-005 places Ironclad in Top 3 and again in Needs Record Update.
- Similar record/action duplication appears elsewhere.
The current "accounted for once" instruction is not strong enough for Haiku.

### C. Aggregate arithmetic is still unreliable
Computed directly from the supplied pipeline tables:
- S-002 source total: $1.880M; output: $1.825M.
- S-006 source total: $5.805M; output: $5.895M.
- S-008 source total: $1.820M; output: $1.660M.
- S-010 source total: $1.850M; output: $1.860M.
The safest next version should normally omit aggregate pipeline totals unless the handoff itself supplies a verified total.

### D. Word-limit compliance is weak
- S-003: 512 words
- S-006: 476 words
- S-007: 471 words
All exceed the skill's hard maximum of 450 words. Tier B expansion is the main source of bloat.

### E. Unsupported operational specificity still leaks through
Examples include choosing unlisted contact paths ("CEO or their office", unnamed legal contacts), inventing commercial fallback structures, or suggesting exact future deadlines not supplied by the handoff.
The evidence-boundary principle is good, but it needs a stronger output-time constraint.

## Evaluator inconsistencies / likely stale or mismatched judge context

These should NOT be converted into benchmark-specific skill rules.

1. **S-001 rubric appears to judge text that is not in the actual output.**
   It criticizes "Harmon account LinkedIn network" and "James at Meridian" recovery paths, but the actual latest S-001 output contains neither.

2. **S-002 rubric says Sunrise EdTech and Vantage Robotics are not in the source.**
   Both are explicitly present in the scenario input.

3. **S-006 graders call Renata and Copperhead Carriers fabricated.**
   Both are explicitly present in the scenario input. The rubric also discusses a $5.845M output although the actual output says $5.895M, indicating likely stale/mismatched evaluation context.

4. **S-004 graders contradict each other.**
   scenario_quality says Holloway was chosen where Meridian should have been; rubric describes the reverse substitution.

5. **S-005 rubric says Meridian Ports $210K is invented/unspecified.**
   The scenario input explicitly lists Meridian Ports at $210K, while the actual latest action line does not even print that amount.

6. **S-010 rubric says Cypress $195K and Stellar $110K are unsupported.**
   Both amounts are explicitly present in the scenario input.

This means the nominal 0.69748 includes non-trivial judge noise. A fair corrected score cannot be calculated from the available evidence; a rerun or validator-side investigation would be required.

## Recommended next design change

Do NOT reintroduce scenario-specific rules. Keep the 0.90 dataset_derived safety.

Make only general execution-hardening changes:

1. **Default: no aggregate sum**
   Report deal count and named exposure. Print a total only if the handoff itself provides one explicitly.

2. **Exclusive assignment pass**
   Before writing, assign each deal to exactly one of:
   ACTION / MEETING / MONITOR / RECORD.
   Once assigned, never print the same deal name in another operational section.

3. **Action count lock**
   Determine N genuine actions first.
   Print exactly N (max 3 in Top Actions); never infer N from the heading.

4. **Recipient grounding**
   If no person or explicit role is supplied, state the information needed without inventing a recipient or channel.

5. **Shorter target**
   Target 220-300 words and hard-cap the instruction at ~360 words so Haiku's typical overshoot remains under 450.

6. **Meeting prep grounding**
   Ask questions or state objectives only. Do not invent concessions, pricing structures, fallback offers, product claims, or stakeholder duties.

7. **Adjacent request handling**
   If asked for a forecast or another analysis, finish the briefing, then provide only what can be computed from supplied data and list missing assumptions compactly.

## Recommendation

Do not submit the exact same skill again. The gate/generalization architecture should be retained, but the next revision should be a small execution-hardening patch, not a larger rule catalog.
