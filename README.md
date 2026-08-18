# sn121-sbc19

Public working copy of a SN121 / sundae_bar **SBC19** skill, plus validator evaluation files needed to compare the current champion with miner `jason020818`.

This repository is not a copy of the hidden grading harness. Challenge files that are already public (`suite.yaml`, lab page, submission JSON, validator result JSON) are linked. The dataset/reference answers are **not** mirrored here.

## Current SBC19 scores (retrieved 2026-08-18T07:25:31Z)

| | Score | Miner | Submission |
|---|---:|---|---|
| Champion | **0.76684** | WeirdCrystal (UID 235) | `06d07e60-50a7-4c39-bf0d-5183ab708bdd` |
| Mine (best scored) | **0.70529** | jason020818 (UID 245) | `ff6b239d-1633-4d5a-a121-73451f91d1e1` |
| Gap (mine − champion) | **-0.06155** | | |

Challenge: **SBC19 — Sales Rep Daily Briefing Composer**  
Challenge id: `a6720085-ce3b-4851-bcee-17f49e3fd635`  
Lab: https://www.sundaebar.ai/lab/challenge/a6720085-ce3b-4851-bcee-17f49e3fd635

At retrieval time the challenge was still `active` and submissions were still open. Champion was unchanged from the earlier 0.76684 submission.

A later jason020818 submission `ea5b2af0-b080-4d9a-aece-93867329dece` scored **0.00000** (pre-flight gate failed: `dataset_derived` 0.35). It is stored under `results/mine/other_submissions/` and is not the comparison baseline.

## Skill file in this repo

`SKILL.md` is the local draft. It is **not** the file that received 0.70529.

- Git `SKILL.md` sha256 at retrieval: `722bb3654baeec1071f082d8b4f63a916a6959b6488c62adaa4357fd72b5ccda`
- Evaluated mine skill sha256: `e30c1d0ca1a215b3ce8cdc8c24c98e206c1a7dd72e8f6a53b91a3590861556be`

## Evaluation files

| Path | What it is |
|---|---|
| `results/mine/` | Best scored jason020818 run (0.70529) |
| `results/champion/` | Current #1 WeirdCrystal run (0.76684) |
| `results/comparison.md` | Scenario table and grader-gap notes from those two runs |
| `results/leaderboard_snapshot.json` | Public leaderboard compact dump (204 submissions) |
| `results/mine/other_submissions/` | Gate-failed jason020818 run (0.00000) |

Inside `mine/` and `champion/`:

- `raw_evaluation.json` — unmodified public validator JSON
- `results.json` — unmodified completed task payload from `GET /api/v2/tasks`
- `metadata.json` — identifiers, scores, hashes, source URLs
- `scenario_scores.json` — per-scenario grader scores extracted for analysis (values not altered)
- `outputs.json` — agent assistant text only (user/dataset prompts not copied into this file)
- `grader_rationales.md` — grader rationale text copied from the raw JSON

Champion `SKILL.md` is **not** stored here. URL and sha256 are in `results/champion/metadata.json`.

## Official source URLs used

- https://www.sundaebar.ai/lab/challenge/a6720085-ce3b-4851-bcee-17f49e3fd635
- https://api.sundaebar.ai/api/v2/challenges/latest
- https://api.sundaebar.ai/api/v2/submissions?challenge_id=a6720085-ce3b-4851-bcee-17f49e3fd635&limit=100&page=1&sort_by=score&sort_order=desc
- https://api.sundaebar.ai/api/v2/submissions/06d07e60-50a7-4c39-bf0d-5183ab708bdd
- https://api.sundaebar.ai/api/v2/submissions/ff6b239d-1633-4d5a-a121-73451f91d1e1
- https://api.sundaebar.ai/api/v2/submissions/ea5b2af0-b080-4d9a-aece-93867329dece
- https://api.sundaebar.ai/api/v2/tasks?submission_id=06d07e60-50a7-4c39-bf0d-5183ab708bdd
- https://api.sundaebar.ai/api/v2/tasks?submission_id=ff6b239d-1633-4d5a-a121-73451f91d1e1
- https://api.sundaebar.ai/api/v2/tasks?submission_id=ea5b2af0-b080-4d9a-aece-93867329dece
- Champion raw JSON: `https://gcikyqenfadlhgpmoqco.supabase.co/storage/v1/object/public/tasks/sales-rep-daily-briefing-composer_a6720085-ce3b-4851-bcee-17f49e3fd635/WeirdCrystal_06d07e60-50a7-4c39-bf0d-5183ab708bdd/sb-validator-london_a4e14697-86c7-405a-ac8d-db560a115321.json`
- Mine raw JSON: `https://gcikyqenfadlhgpmoqco.supabase.co/storage/v1/object/public/tasks/sales-rep-daily-briefing-composer_a6720085-ce3b-4851-bcee-17f49e3fd635/jason020818_ff6b239d-1633-4d5a-a121-73451f91d1e1/sb-validator-london_ba08c811-7343-4ba1-89e5-269c1fabc872.json`
- Champion skill: https://gcikyqenfadlhgpmoqco.supabase.co/storage/v1/object/public/agent-submissions/06d07e60-50a7-4c39-bf0d-5183ab708bdd/skill.md
- Mine evaluated skill: https://gcikyqenfadlhgpmoqco.supabase.co/storage/v1/object/public/agent-submissions/ff6b239d-1633-4d5a-a121-73451f91d1e1/skill.md
- Public suite (weights/gates only; not stored in this repo): https://gcikyqenfadlhgpmoqco.supabase.co/storage/v1/object/public/challenges/a6720085-ce3b-4851-bcee-17f49e3fd635/suite.yaml

## Not obtained

- Scores from queued validators (Rizzo, Yuma, unnamed tasks): no result payload
- `scenario_type` field: absent from the evaluation JSON
- Structured penalty objects: absent (text `penalties=0.00` only)
- Login-only dashboard exports beyond the public API/storage objects above
- Challenge `dataset.jsonl` / `rubric.txt` bodies: not copied into this repo
- Champion skill body: URL + hash only
