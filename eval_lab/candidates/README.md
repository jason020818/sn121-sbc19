# Skill candidates

Store markdown skill files here. `SKILL.md` at the repository root is the production file and must not be overwritten by lab commands.

```bash
python -m eval_lab.cli candidate add --name candidate-a --file ./some_skill.md
python -m eval_lab.cli candidate list
```

Copies land at `eval_lab/candidates/<name>.md`. Overwrite requires `--force`. SHA256 and timestamps are recorded in `manifest.json`.
