# EVAL_LAB.md

Local pre-submission evaluation laboratory for this SBC19 skill.

The local score is an **internal signal only**. It is not an exact reproduction of the official validator score and must never be described as one.

Release metrics use **repeat-mean** statistics, not pooled scenario×repeat scores:

- `repeat_means`: mean score of all selected scenarios inside each repeat index
- `repeat_mean_summary`: mean/median/min/max/stddev/p10 of those repeat means
- `scenario_score_summary`: informational only; mixes scenario difficulty with stochastic variance

`max_repeat_stddev` is stddev of `repeat_means`.

## 1. Why live submissions are scarce production releases

Public SN121 validator runs consume budget, expose a candidate to official graders, and cannot be cheaply repeated. The working rule is:

- iterate locally on archived public inputs plus synthetic holdouts;
- live-submit only a candidate that already passed the internal release gate;
- treat `SKILL.md` as production, not a scratchpad.

## 2. Public regression vs synthetic holdout

| Stream | Source | Purpose |
|---|---|---|
| Regression | Archived `results/*/raw_evaluation.json` files already in this repo | Repeatability against public scenario *inputs* and historical official scores as context |
| Holdout | Independently generated synthetic books | Generalization across sales-ops dimensions the public sample does not exhaust |

Regression **does not** treat archived grader rationales as ground truth. Deterministic checks compare the candidate output to the scenario text. Historical official scores are displayed separately as context.

Holdouts are generated from general dimensions (book size, calendar, ownership, data quality, communication constraints, commercial context). They are not copies of the 10 public scenarios and do not reuse those company names.

## 3. Why local score != official score

The lab uses:

- deterministic structure/grounding checks;
- two local judges on general quality dimensions;
- an `internal_quality` weighted composite with explicit penalties.

That stack is intentionally **not** a clone of the hidden official graders, weights, or dataset_derived logic. A high local score can still fail SN121. A low local score is still a reason not to burn a live submission.

Internal composite:

```text
internal_quality =
  0.22 grounding_accuracy
+ 0.20 prioritization_quality
+ 0.16 actionability
+ 0.14 waiting_state_judgment
+ 0.10 meeting_preparation_quality
+ 0.08 concision
+ 0.10 skill_adherence
```

Penalties: catastrophic zeros the scenario; major multiplies by 0.75; minor multiplies by 0.95.

Release-gate numbers in `eval_lab/config.example.yaml` are **internal** thresholds, not official SN121 thresholds.

## 4. How to add candidate A/B/C

Never edit production `SKILL.md` just to try a variant.

```bash
cd eval_lab
python -m eval_lab.cli candidate add --name candidate-a --file ./path/to/variant.md
python -m eval_lab.cli candidate add --name candidate-b --file ./path/to/other.md
python -m eval_lab.cli candidate list
```

Copies are stored at `eval_lab/candidates/<name>.md`. Overwrite requires `--force`. SHA256 and timestamps live in `eval_lab/candidates/manifest.json`.

Current production snapshot: `eval_lab/candidates/production-f9e5400.md`.

## 5. Cheap smoke tests

These require no internet and no API key:

```bash
cd eval_lab
python -m pytest -q
python -m eval_lab.cli holdout generate --count 60 --seed 1211901
python -m eval_lab.cli regression --candidate production-f9e5400 --repeats 5 --dry-run --limit 1
python -m eval_lab.cli holdout run --candidate production-f9e5400 --repeats 1 --dry-run --limit 3
```

A committed 3-scenario smoke sample lives at `eval_lab/tests/fixtures/synthetic_smoke.jsonl`.

Offline deterministic calibration against archived public outputs (zero model calls):

```bash
python -m eval_lab.cli calibrate-deterministic --source ../results/run-0.7378429/raw_evaluation.json
```

## 6. Full repeated evaluation

Default configuration: 5 repeats, agent `anthropic/claude-haiku-4.5`, judges Sonnet 4.6 and Opus 4.8, temperature 0.2.

```bash
python -m eval_lab.cli regression --candidate candidate-a --repeats 5 --yes
python -m eval_lab.cli holdout run --candidate candidate-a --repeats 5 --yes
python -m eval_lab.cli tournament --candidates candidate-a --candidates candidate-b --repeats 5 --yes
```

Tournament ranking (never by a lucky max):

1. catastrophic failures ascending
2. holdout median descending
3. holdout worst-repeat descending
4. regression median descending
5. stddev ascending

If a configured model is unavailable, the lab fails closed. It does not silently substitute another model.

## 7. How to interpret the release gate

```bash
python -m eval_lab.cli release-check --candidate candidate-a
```

Exit codes: `0` PASS, `2` FAIL, `3` configuration/data error.

Mandatory internal conditions (from `config.example.yaml`):

- no catastrophic deterministic failures
- generalization proxy >= 0.85
- regression median >= 0.76
- holdout median >= 0.79
- holdout worst repeat >= 0.77
- holdout stddev <= 0.035
- grounding pass rate >= 0.99

The report always includes:

> PASS means this candidate met our internal release criteria. It does not guarantee an official SN121 score.

## 8. How to preserve a reserve candidate

Keep production and reserve files separate:

- production: `eval_lab/candidates/production-f9e5400.md` (or a later production snapshot)
- reserve: `eval_lab/candidates/reserve-<sha>.md`

Do not overwrite historical `results/` folders when a new official run arrives; archive a new `results/run-<score>/` directory instead.

## 9. Estimated API call counts and cost awareness

Before any paid run the CLI prints an estimate and requires `--yes`.

Examples:

- 10 archived scenarios × 5 repeats = 50 agent calls, plus 50 × 2 judges = 100 judge calls (150 total) for regression
- 60 holdouts × 5 repeats = 300 agent calls, plus 300 × 2 judges = 600 judge calls (900 total) for holdout
- tournament of 3 candidates ≈ 3 × (regression + holdout)

Use `--limit`, `--scenario`, `--repeats`, and `--dry-run` to shrink cost. API keys are read from `OPENROUTER_API_KEY` and are never printed or written to reports.

## 10. No benchmark-specific tuning policy

Do not add scenario names, benchmark IDs, P1/P2 taxonomies, numeric scenario thresholds, or company-specific instructions to a skill because one public grader rationale complained.

The generalization proxy is a conservative static lint, not the official `dataset_derived` grader.

### Operating policy

- Never edit SKILL.md merely because one grader rationale says so.
- A failure must reproduce on multiple independent holdouts before it becomes a skill rule.
- Keep production candidate and reserve candidate separate.
- Do not live-submit a candidate that fails release-check.
- Do not overwrite historical result folders.

## 11. Zero-cost oracle / metamorphic lab

A markdown skill cannot be exhaustively verified by static lint. Each candidate has a
machine-readable policy manifest and a deterministic policy engine. The engine verifies
LOGIC. It does not simulate Haiku instruction-following. A live SN121 submission remains
the only official validator sample.

These commands make zero network calls and zero OpenRouter calls:

```bash
python -m eval_lab.cli domain-oracle-generate --count 3000 --seed 121190200
python -m eval_lab.cli domain-policy-tournament
python -m eval_lab.cli rendering-risk-tournament
python -m eval_lab.cli free-champion-plan
```

Domain expected labels are an independent sales-ops contract. They are not produced by
`apply_policy(production)` or any candidate manifest. Semantic-policy ranking does not use
markdown length. Rendering-risk is a separate static layer and does not simulate Haiku.

Committed summaries:
- `eval_lab/reports/domain-policy-tournament.md`
- `eval_lab/reports/rendering-risk-tournament.md`
- `eval_lab/reports/free-champion-plan.md`

Full corpora stay gitignored under `eval_lab/generated/`. Do not promote a candidate to
`SKILL.md` from these internal reports alone.
