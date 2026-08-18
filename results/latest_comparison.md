# SBC19 latest evaluation comparison
Uploaded result: `SKL-7471-aee6-SBC19`
| Metric | Previous mine | Latest | Champion baseline | Latest vs previous | Latest vs champion |
|---|---:|---:|---:|---:|---:|
| Total | 0.705290 | **0.697480** | 0.766840 | -0.007810 | -0.069360 |
| skill_use | 0.850000 | **0.800000** | 0.875000 | -0.050000 | -0.075000 |
| scenario_quality | 0.598400 | **0.532600** | 0.677800 | -0.065800 | -0.145200 |
| rubric | 0.577000 | **0.659000** | 0.670000 | +0.082000 | -0.011000 |
| novelty_check | 0.976735 | **1.000000** | 1.000000 | +0.023265 | +0.000000 |
| skill_alignment | 0.900000 | **0.900000** | 0.900000 | +0.000000 | +0.000000 |
| dataset_derived | 0.550000 | **0.900000** | 0.750000 | +0.350000 | +0.150000 |

## Scenario comparison

| Scenario | Previous mine | Latest | Champion | Δ vs previous | Δ vs champion |
|---|---:|---:|---:|---:|---:|
| S-001 | 0.68050 | **0.74050** | 0.77800 | +0.06000 | -0.03750 |
| S-002 | 0.58270 | **0.68050** | 0.66850 | +0.09780 | +0.01200 |
| S-003 | 0.75100 | **0.79480** | 0.75100 | +0.04380 | +0.04380 |
| S-004 | 0.78250 | **0.67150** | 0.87850 | -0.11100 | -0.20700 |
| S-005 | 0.77650 | **0.72850** | 0.81100 | -0.04800 | -0.08250 |
| S-006 | 0.60850 | **0.55000** | 0.74950 | -0.05850 | -0.19950 |
| S-007 | 0.63474 | **0.69850** | 0.69850 | +0.06376 | +0.00000 |
| S-008 | 0.74350 | **0.72850** | 0.81340 | -0.01500 | -0.08490 |
| S-009 | 0.79450 | **0.66850** | 0.82450 | -0.12600 | -0.15600 |
| S-010 | 0.69850 | **0.71350** | 0.69550 | +0.01500 | +0.01800 |

## Key findings

- Gate safety improved sharply: `dataset_derived` rose from 0.55 to 0.90 while `skill_alignment` stayed 0.90; all 10 samples passed the gate.
- `rubric` improved from 0.577 to 0.659, nearly matching the prior champion baseline 0.670.
- The main regression is `scenario_quality` (0.5984 → 0.5326) and `skill_use` (0.85 → 0.80), so execution consistency—not gate safety—is now the dominant issue.
- Largest regressions vs previous: S-009, S-004, S-006. Largest gains: S-002, S-007, S-001, S-003.
- Several rubric rationales incorrectly label facts that are visibly present in the scenario input as fabricated (for example S-006 Renata/Copperhead Carriers, S-010 Cypress/Stellar amounts, S-005 Meridian Ports amount). Treat those judge statements as evaluator error/noise rather than skill-grounded evidence.
