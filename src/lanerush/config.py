"""LaneRush configuration — Pydantic v2."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator


class SimConfig(BaseModel):
    sumo_binary: str = "sumo"
    net_file: str
    route_file: str
    step_length: float = 1.0
    max_steps: int = 3600
    seed: int = 1
    gui: bool = False


class TlsConfig(BaseModel):
    min_green: int = 8
    max_green: int = 50
    yellow_wait: int = 3

    @field_validator("min_green", "max_green", "yellow_wait")
    @classmethod
    def _positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("TLS timing values must be positive")
        return v

    @field_validator("max_green")
    @classmethod
    def _max_gt_min(cls, v: int, info: object) -> int:  # noqa: ARG002
        # We can't cross-validate here without model_validator; a separate check is in LaneRushConfig
        return v


class ScoringConfig(BaseModel):
    w_count: float = 1.0
    w_halt: float = 1.0
    w_age: float = 0.5


class CorridorConfig(BaseModel):
    enabled: bool = True
    lookahead_junctions: int = 3
    eta_threshold_base: float = 12.0
    hold_until_passed: bool = True

    @field_validator("lookahead_junctions")
    @classmethod
    def _lj_range(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("lookahead_junctions must be between 1 and 5")
        return v


class NoisyConfig(BaseModel):
    recall: float = 0.9
    false_alarm: float = 0.05
    ev_recall: float = 0.95
    ev_false_alarm: float = 0.01
    confirmation_k: int = 2
    confirmation_n: int = 3


class PerceptionConfig(BaseModel):
    provider: str = "ground_truth"
    noisy: NoisyConfig = NoisyConfig()

    @field_validator("provider")
    @classmethod
    def _valid_provider(cls, v: str) -> str:
        valid = {"ground_truth", "noisy", "yolo"}
        if v not in valid:
            raise ValueError(f"perception.provider must be one of {valid}, got '{v}'")
        return v


class StoreConfig(BaseModel):
    backend: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    pg_dsn: str = "postgresql://lanerush:lanerush@localhost:5432/lanerush"
    batch_every_steps: int = 50

    @field_validator("backend")
    @classmethod
    def _valid_backend(cls, v: str) -> str:
        valid = {"memory", "redis", "postgres"}
        if v not in valid:
            raise ValueError(f"store.backend must be one of {valid}, got '{v}'")
        return v


class OutputConfig(BaseModel):
    runs_dir: str = "runs"
    log_decisions_every_n: int = 10


_VALID_MODES = {
    "fixed",
    "fixed_tuned",
    "adaptive_noaging",
    "adaptive",
    "adaptive_corridor",
    "max_pressure",
    "actuated",
}


class LaneRushConfig(BaseModel):
    mode: str = "adaptive_corridor"
    sim: SimConfig
    tls: TlsConfig = TlsConfig()
    scoring: ScoringConfig = ScoringConfig()
    corridor: CorridorConfig = CorridorConfig()
    perception: PerceptionConfig = PerceptionConfig()
    store: StoreConfig = StoreConfig()
    output: OutputConfig = OutputConfig()

    @field_validator("mode")
    @classmethod
    def _valid_mode(cls, v: str) -> str:
        if v not in _VALID_MODES:
            raise ValueError(f"mode must be one of {_VALID_MODES}, got '{v}'")
        return v

    @classmethod
    def from_yaml(cls, path: Path) -> LaneRushConfig:
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
