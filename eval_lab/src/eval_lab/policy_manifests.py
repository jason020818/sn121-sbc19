"""Load policy manifests by candidate name."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from eval_lab.config import lab_root
from eval_lab.policy_models import PolicyManifest

CANDIDATE_POLICY_FILES = {
    "production": "production.yaml",
    "production-f9e5400": "production.yaml",
    "candidate-a": "candidate-a.yaml",
    "candidate-a-conservative": "candidate-a.yaml",
    "candidate-b": "candidate-b.yaml",
    "candidate-b-ledger": "candidate-b.yaml",
    "candidate-c": "candidate-c.yaml",
    "candidate-c-minimal": "candidate-c.yaml",
}


def policies_dir() -> Path:
    return lab_root() / "policies"


@lru_cache(maxsize=16)
def load_policy(name: str) -> PolicyManifest:
    filename = CANDIDATE_POLICY_FILES.get(name, f"{name}.yaml")
    path = policies_dir() / filename
    if not path.exists():
        raise FileNotFoundError(f"No policy manifest for {name}: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return PolicyManifest.model_validate(raw)
