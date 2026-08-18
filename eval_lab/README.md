# SBC19 evaluation lab

Local pre-submission laboratory. Treat live SN121 submissions as production releases, not experiments.

Internal lab scores are **not** official SN121 validator scores. They exist to catch grounding failures, waiting-state mistakes, length overshoot, and brittle candidates before a scarce live submission.

On PEP 668 systems, use a local venv:

```bash
cd eval_lab
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m eval_lab.cli --help
```

```bash
cd eval_lab
python -m pytest -q
python -m eval_lab.cli candidate add --name candidate-a --file ../SKILL.md
python -m eval_lab.cli holdout generate --count 60 --seed 1211901
python -m eval_lab.cli regression --candidate candidate-a --repeats 5 --dry-run
python -m eval_lab.cli holdout run --candidate candidate-a --repeats 5 --dry-run
python -m eval_lab.cli release-check --candidate candidate-a --dry-run
```

Paid OpenRouter runs require `--yes` after the CLI prints the call estimate. Dry-runs never call the API.

Copy `config.example.yaml` to `config.yaml` only if you need a local override. Configured model ids are required; the lab will not silently substitute another model.
