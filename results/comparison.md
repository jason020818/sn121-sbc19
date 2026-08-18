# SBC19 comparison: jason020818 vs champion

Retrieved at `2026-08-18T07:25:31Z` from public sundae_bar API and public validator result JSON.

This file uses only scores and grader rationales from those files. It does not invent missing fields. It does not copy hidden ground-truth answers.

## What is being compared

| | Mine (best scored) | Champion |
|---|---|---|
| Miner | jason020818 (UID 245) | WeirdCrystal (UID 235) |
| Submission | `ff6b239d-1633-4d5a-a121-73451f91d1e1` (`SKL-ff6b-aee6-SBC19`) | `06d07e60-50a7-4c39-bf0d-5183ab708bdd` (`SKL-06d0-d1cf-SBC19`) |
| Score | **0.70529** | **0.76684** |
| Gap (mine − champion) | **-0.06155** | |
| Miner rank (best score per username, 48 miners) | 44 | 1 |
| Submission rank (204 scored submissions) | 97 | 1 |
| Evaluated at | 2026-08-18T05:43:07.619Z | 2026-08-17T22:27:04.935Z |
| Validator with a completed result | SB Validator - London | SB Validator - London |
| Gate | passed (`skill_alignment` 0.90, `dataset_derived` 0.55) | passed (`skill_alignment` 0.90, `dataset_derived` 0.75) |

The `SKILL.md` currently in this git repository is **not** the evaluated mine file.

- Evaluated mine skill sha256: `e30c1d0ca1a215b3ce8cdc8c24c98e206c1a7dd72e8f6a53b91a3590861556be`
- Git `SKILL.md` sha256 at retrieval: `722bb3654baeec1071f082d8b4f63a916a6959b6488c62adaa4357fd72b5ccda`

A later jason020818 submission `ea5b2af0-b080-4d9a-aece-93867329dece` scored **0.00000** because the pre-flight gate failed (`dataset_derived` 0.35, threshold 0.45). Per-sample graders were skipped. It is stored under `results/mine/other_submissions/` and is **not** used in the scenario table below.

Leaderboard snapshot time: `2026-08-18T07:25:31Z`. Challenge: SBC19 / Sales Rep Daily Briefing Composer / id `a6720085-ce3b-4851-bcee-17f49e3fd635`. Challenge still `active`; submissions still open.

`scenario_type` was **not present** in the public evaluation JSON. Those cells are omitted rather than guessed.

## Scenario table

Scores are `weighted_score` from each sample in the public raw evaluation JSON.

Biggest grader gap is the largest absolute difference among weighted graders (`skill_use` 0.3, `scenario_quality` 0.3, `rubric` 0.3, `novelty_check` 0.1).

| Scenario | Mine | Champion | Delta | Biggest grader gap |
| -------- | ---: | -------: | ----: | ------------------ |
| S-001 | 0.68050 | 0.77800 | -0.09750 | rubric 0.31 vs 0.72 (−0.41) |
| S-002 | 0.58270 | 0.66850 | -0.08580 | rubric 0.31 vs 0.62 (−0.31) |
| S-003 | 0.75100 | 0.75100 | 0.00000 | none (all four weighted graders equal) |
| S-004 | 0.78250 | 0.87850 | -0.09600 | rubric 0.51 vs 0.72 (−0.21) |
| S-005 | 0.77650 | 0.81100 | -0.03450 | scenario_quality 0.66 vs 0.775 (−0.115) |
| S-006 | 0.60850 | 0.74950 | -0.14100 | skill_use 0.625 vs 0.875 (−0.25) |
| S-007 | 0.63474 | 0.69850 | -0.06376 | novelty_check 0.76735 vs 1.00 (−0.23265) |
| S-008 | 0.74350 | 0.81340 | -0.06990 | scenario_quality 0.55 vs 0.783 (−0.233) |
| S-009 | 0.79450 | 0.82450 | -0.03000 | rubric 0.62 vs 0.72 (−0.10) |
| S-010 | 0.69850 | 0.69550 | +0.00300 | rubric 0.62 vs 0.42 (+0.20) |

Mean of the ten sample `weighted_score` values: mine 0.705294, champion 0.766840. These match `summary.metrics.avg_score_total` in the raw files.

### A. Scenarios where champion is ahead (largest loss first)

1. **S-006 (−0.14100)** — largest gap. Mine `skill_use` 0.625 vs champion 0.875. Mine scenario_quality 0.45 vs 0.67. Rubric tied at 0.62. Mine rationale: did not address the Pacific Rim Cargo note inconsistency; pipeline total stated as $5.845M rather than $5.595M; Top 3 missed ClearRoute Trucking and elevated Polar Express Cargo.
2. **S-001 (−0.09750)** — mine rubric 0.31 vs 0.72. Mine rationale: pipeline stated as $1.583M vs $1,363K; Cascade Renewables treated as Top 3; Thornfield listed under both Top 3 and Tier A; Redwood recovery via unrelated Meridian/LinkedIn contacts. Mine scenario_quality (0.75) was actually higher than champion (0.665).
3. **S-004 (−0.09600)** — mine rubric 0.51 vs 0.72. Mine rationale: Nova Semiconductor elevated to Tier A; Fairbanks Telecom demoted to Tier B; values/tiers for several deals described as invented or misattributed. Mine scenario_quality 0.89 vs champion 1.00.
4. **S-002 (−0.08580)** — mine rubric 0.31 vs 0.62. Mine rationale: pipeline $1.825M vs $1.885M; Keystone Agri demoted to Tier B; recommended calling Stormbridge when the source said not to call. Both sides were penalized for inflating action count; mine scenario_quality 0.424 vs champion 0.40.
5. **S-008 (−0.06990)** — mine scenario_quality 0.55 vs 0.783. Mine rationale: Vertex buried in Tier A instead of Top 3; pipeline $1.82M vs $1.655M; claimed no hygiene issues.
6. **S-007 (−0.06376)** — mine novelty_check 0.76735 vs 1.00 (only sample where novelty was not 1.0 for mine). Mine scenario_quality 0.365 vs 0.40. Mine rationale: Silica quiet counted as 13 business days rather than 15; Quartz Financial amount/close date described as fabricated.
7. **S-005 (−0.03450)** — mine scenario_quality 0.66 vs 0.775.
8. **S-009 (−0.03000)** — mine rubric 0.62 vs 0.72. Mine rationale: Crownview quiet counted as 19 days vs 27; Waverly ask went to the deal contact rather than legal/procurement; false “no hygiene flags”; Maple Street ask was the wrong question.

### B. Scenarios where mine is ahead or tied

- **S-010 (+0.00300)** — only win. Mine rubric 0.62 vs champion 0.42. Mine scenario_quality still lost (0.50 vs 0.69). Rationales conflict with each other: scenario_quality says Ashwood was not mentioned; rubric says an Ashwood hard-constraint note was present.
- **S-003 (0.00000)** — exact tie on every weighted grader (`skill_use` 0.875, `scenario_quality` 0.575, `rubric` 0.72, `novelty_check` 1.0).

### C. Grader averages

Values below are `summary.metrics` from the raw evaluation JSON (same as the mean of the 10 samples).

```text
skill_use:
mine 0.85000
champion 0.87500
delta -0.02500

scenario_quality:
mine 0.59840
champion 0.67780
delta -0.07940

rubric:
mine 0.57700
champion 0.67000
delta -0.09300

novelty_check:
mine 0.976735
champion 1.00000
delta -0.023265
```

Gate graders (weight 0.0 in `suite.yaml`; they do not enter the weighted sample score, but failing the gate zeros all samples):

```text
skill_alignment:
mine 0.90
champion 0.90
delta 0.00
threshold 0.45
both pass

dataset_derived:
mine 0.55
champion 0.75
delta -0.20
threshold 0.45
both pass on the compared submissions
```

The later mine submission `ea5b2af0` had `dataset_derived` 0.35 and failed the gate. That run is not in the averages above.

### D. Repeated failure patterns (from mine rationales only)

Counted only when the same issue is stated in more than one scenario rationale for submission `ff6b239d`.

- **Amount / pipeline-total errors** — S-001, S-002, S-006, S-008, S-010. Graders repeatedly say the printed total does not match the ledger.
- **False clean hygiene / missed record flags** — S-003, S-008, S-009 (“no hygiene flags” while a named record issue existed). S-006 separately says the Pacific Rim contradiction was not addressed.
- **Calendar / section duplication** — S-001 Thornfield in Top 3 and Tier A; S-003 Tier A restates meeting-covered deals.
- **Quiet-book inflation / extra Tier A seats** — S-002 (Fenwick/Oaktree extra); S-004 Nova elevated, Fairbanks demoted.
- **Channel inverted against an explicit instruction** — S-002 call vs do-not-call; S-006 email vs call; S-010 email vs phone.
- **Working-day miscount from the wrong timestamp** — S-007 (13 vs 15), S-009 (19 vs 27).
- **Invented or misattributed figures/dates** — S-004 deal values/tiers; S-007 Quartz amount and Feb 28 close; S-008 Frontier $460K.
- **Wrong recipient for a live legal/procurement hold** — S-009 Waverly.

Patterns that appear once in mine rationales, so not listed as repeated: S-006 `skill_use` drop; S-007 novelty_check 0.76735; S-008 Vertex ranking; S-001 Redwood contact improvisation.

Champion rationales also mention pipeline-total errors (S-001, S-002, S-010) and some ranking mistakes. Those are recorded here only to avoid treating arithmetic errors as unique to mine. The repeated mine pattern is still the higher rate of total/hygiene/duplication/channel misses on this submission.

## Public data that was not available

- Other validators (Rizzo, Yuma, unnamed queued tasks): `status=queued`, no `raw_result_url`, no scores.
- `scenario_type` / category field: not in the evaluation JSON.
- Structured `penalties` arrays: not present. Several `scenario_quality` rationales contain the text `penalties=0.00`.
- Submission-level `model` / `model_provider` fields: `null` on the API submission object. Model names **are** present in `raw_evaluation.json` → `summary.models` (agent `anthropic/claude-haiku-4.5`, judges `anthropic/claude-sonnet-4.6` and `anthropic/claude-opus-4.8` via openrouter).
- Champion `SKILL.md` body: not copied. Public URL and sha256 are in `results/champion/metadata.json`.
- Per-sample evaluation for gate-failed mine submission `ea5b2af0`: skipped by the harness.
- Any private dashboard-only download that requires login beyond the public API/storage URLs used here.
