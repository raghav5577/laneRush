"""Tests for configuration loading and validation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from lanerush.config import LaneRushConfig


@pytest.fixture
def valid_config_data() -> dict:
    return {
        "mode": "adaptive_corridor",
        "sim": {
            "sumo_binary": "sumo",
            "net_file": "scenarios/grid3x3/grid3x3.net.xml",
            "route_file": "scenarios/grid3x3/grid3x3.rou.xml",
            "step_length": 1.0,
            "max_steps": 3600,
            "seed": 1,
            "gui": False,
        },
        "tls": {"min_green": 8, "max_green": 50, "yellow_wait": 3},
        "scoring": {"w_count": 1.0, "w_halt": 1.0, "w_age": 0.5},
        "corridor": {
            "enabled": True,
            "lookahead_junctions": 3,
            "eta_threshold_base": 12.0,
            "hold_until_passed": True,
        },
        "perception": {
            "provider": "ground_truth",
            "noisy": {
                "recall": 0.9,
                "false_alarm": 0.05,
                "ev_recall": 0.95,
                "ev_false_alarm": 0.01,
                "confirmation_k": 2,
                "confirmation_n": 3,
            },
        },
        "store": {
            "backend": "memory",
            "redis_url": "redis://localhost:6379/0",
            "pg_dsn": "postgresql://lanerush:lanerush@localhost:5432/lanerush",
            "batch_every_steps": 50,
        },
        "output": {"runs_dir": "runs", "log_decisions_every_n": 10},
    }


def test_valid_config_loads(valid_config_data: dict) -> None:
    """A valid config dict should parse without error."""
    cfg = LaneRushConfig(**valid_config_data)
    assert cfg.mode == "adaptive_corridor"
    assert cfg.sim.net_file == "scenarios/grid3x3/grid3x3.net.xml"
    assert cfg.tls.min_green == 8
    assert cfg.scoring.w_age == 0.5
    assert cfg.corridor.lookahead_junctions == 3


def test_valid_config_from_yaml(valid_config_data: dict) -> None:
    """Config should load from a YAML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(valid_config_data, f)
        f.flush()
        cfg = LaneRushConfig.from_yaml(Path(f.name))
    assert cfg.mode == "adaptive_corridor"


def test_invalid_mode_gives_readable_error(valid_config_data: dict) -> None:
    """An invalid mode should raise a ValidationError with a readable message."""
    valid_config_data["mode"] = "nonexistent_mode"
    with pytest.raises(Exception) as exc_info:
        LaneRushConfig(**valid_config_data)
    assert "nonexistent_mode" in str(exc_info.value)


def test_invalid_tls_negative_min_green(valid_config_data: dict) -> None:
    """Negative min_green should raise a validation error."""
    valid_config_data["tls"]["min_green"] = -1
    with pytest.raises(Exception):
        LaneRushConfig(**valid_config_data)


def test_invalid_perception_provider(valid_config_data: dict) -> None:
    """Invalid perception provider should raise an error."""
    valid_config_data["perception"]["provider"] = "magic_camera"
    with pytest.raises(Exception) as exc_info:
        LaneRushConfig(**valid_config_data)
    assert "magic_camera" in str(exc_info.value)


def test_invalid_store_backend(valid_config_data: dict) -> None:
    """Invalid store backend should raise an error."""
    valid_config_data["store"]["backend"] = "sqlite"
    with pytest.raises(Exception) as exc_info:
        LaneRushConfig(**valid_config_data)
    assert "sqlite" in str(exc_info.value)


def test_invalid_lookahead_too_high(valid_config_data: dict) -> None:
    """Lookahead > 5 should raise."""
    valid_config_data["corridor"]["lookahead_junctions"] = 10
    with pytest.raises(Exception):
        LaneRushConfig(**valid_config_data)


def test_defaults_applied() -> None:
    """Minimal config should fill in all defaults."""
    cfg = LaneRushConfig(
        sim={"net_file": "net.xml", "route_file": "routes.xml"}  # type: ignore[arg-type]
    )
    assert cfg.mode == "adaptive_corridor"
    assert cfg.tls.min_green == 8
    assert cfg.tls.max_green == 50
    assert cfg.scoring.w_count == 1.0
    assert cfg.store.backend == "memory"
