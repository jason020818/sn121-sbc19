"""Configuration loading for the local evaluation lab.

Release-gate numbers in the YAML are INTERNAL thresholds only. They are not
official SN121 validator thresholds and must not be described as such.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class ModelsConfig(BaseModel):
    agent: str
    judges: list[str] = Field(min_length=1)

    @field_validator("agent", mode="before")
    @classmethod
    def agent_required(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError("models.agent must be an explicit model id")
        return str(value).strip()

    @field_validator("judges")
    @classmethod
    def judges_required(cls, value: list[str]) -> list[str]:
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        if not cleaned:
            raise ValueError("models.judges must list at least one explicit model id")
        return cleaned


class ProviderConfig(BaseModel):
    kind: str = "openrouter"
    api_key_env: str = "OPENROUTER_API_KEY"
    base_url: str = "https://openrouter.ai/api/v1"


class EvaluationConfig(BaseModel):
    repeats: int = 5
    temperature: float = 0.2
    max_concurrency: int = 4
    seed: int = 12119


class HoldoutConfig(BaseModel):
    count: int = 60
    generation_seed: int = 1211901


class ReleaseGateConfig(BaseModel):
    min_regression_median: float = 0.76
    min_holdout_median: float = 0.79
    min_holdout_worst_repeat: float = 0.77
    max_repeat_stddev: float = 0.035
    min_grounding_pass_rate: float = 0.99
    max_catastrophic_failures: int = 0
    min_dataset_generalization_proxy: float = 0.85


class LabConfig(BaseModel):
    models: ModelsConfig
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    holdout: HoldoutConfig = Field(default_factory=HoldoutConfig)
    release_gate: ReleaseGateConfig = Field(default_factory=ReleaseGateConfig)

    @property
    def n_judges(self) -> int:
        return len(self.models.judges)


def lab_root() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    searched = [here, *here.parents]
    searched.extend(Path(__file__).resolve().parents)
    seen: set[Path] = set()
    for path in searched:
        if path in seen:
            continue
        seen.add(path)
        if (path / "SKILL.md").exists() and (path / "results").is_dir():
            return path
    raise FileNotFoundError("Could not locate repository root containing SKILL.md and results/")


def default_config_path() -> Path:
    root = lab_root()
    override = root / "config.yaml"
    if override.exists():
        return override
    return root / "config.example.yaml"


def load_config(path: Path | None = None) -> LabConfig:
    config_path = path or default_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file: {config_path}")
    raw: Any = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Config is not a mapping: {config_path}")
    return LabConfig.model_validate(raw)
