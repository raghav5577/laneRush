"""Scenario utilities — build and validate SUMO scenarios."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def get_sumo_home() -> str:
    """Return SUMO_HOME; never hard-code a path."""
    if "SUMO_HOME" in os.environ:
        return os.environ["SUMO_HOME"]
    try:
        import sumo  # type: ignore[import-untyped]

        return str(sumo.SUMO_HOME)
    except ImportError:
        raise RuntimeError(
            "SUMO not found. Install eclipse-sumo or set SUMO_HOME environment variable."
        )


def build_grid3x3(output_dir: Path) -> Path:
    """Generate the 3×3 grid network using netgenerate."""
    output_dir.mkdir(parents=True, exist_ok=True)
    net_file = output_dir / "grid3x3.net.xml"
    if net_file.exists():
        logger.info("Net file already exists: %s", net_file)
        return net_file

    cmd = [
        "netgenerate",
        "--grid",
        "--grid.number=3",
        "--grid.length=250",
        "--grid.attach-length=250",
        "--default.lanenumber=1",
        "--default.speed=13.89",
        "--default-junction-type=traffic_light",
        "--tls.discard-simple=true",
        "-o", str(net_file),
    ]
    logger.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)  # noqa: S603
    return net_file
