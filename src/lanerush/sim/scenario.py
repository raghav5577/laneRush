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


def _resolve_binary(name: str) -> str:
    """Resolve a binary name using PATH or SUMO_HOME."""
    import shutil

    if shutil.which(name):
        return name
    try:
        sumo_home = Path(get_sumo_home())
        bin_dir = sumo_home / "bin"
        if bin_dir.exists():
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            for ext in (".exe", ""):
                candidate = bin_dir / f"{name}{ext}"
                if candidate.exists():
                    return str(candidate)
    except Exception:
        pass
    return name


def build_grid3x3(output_dir: Path) -> Path:
    """Generate the 3×3 grid network using netgenerate."""
    output_dir.mkdir(parents=True, exist_ok=True)
    net_file = output_dir / "grid3x3.net.xml"
    if net_file.exists():
        logger.info("Net file already exists: %s", net_file)
        return net_file

    bin_path = _resolve_binary("netgenerate")
    cmd = [
        bin_path,
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


class SumolibNetView:
    """NetView implementation backed by sumolib."""

    def __init__(self, net_file: str | Path) -> None:
        import sumolib  # type: ignore[import-untyped]

        self._net = sumolib.net.readNet(str(net_file))

    def get_edge_length(self, edge_id: str) -> float:
        try:
            return float(self._net.getEdge(edge_id).getLength())
        except KeyError:
            return 250.0

    def get_edge_speed_limit(self, edge_id: str) -> float:
        try:
            return float(self._net.getEdge(edge_id).getSpeed())
        except KeyError:
            return 13.89

    def get_tls_id_for_edge(self, edge_id: str) -> str | None:
        try:
            edge = self._net.getEdge(edge_id)
            to_node = edge.getToNode()
            if to_node.getType() == "traffic_light":
                return str(to_node.getID())
        except KeyError:
            pass
        return None

    def get_lanes_connecting(self, from_edge: str, to_edge: str) -> list[str]:
        try:
            edge1 = self._net.getEdge(from_edge)
            edge2 = self._net.getEdge(to_edge)
            conns = edge1.getConnections(edge2)
            lanes = [c.getFromLane().getID() for c in conns]
            if lanes:
                return lanes
        except KeyError:
            pass
        return [f"{from_edge}_0"]

    def get_next_tls_junctions(
        self,
        edge_id: str,
        route: tuple[str, ...],
        route_index: int,
        max_junctions: int,
    ) -> list[tuple[str, float]]:
        junctions: list[tuple[str, float]] = []
        cumulative_dist = 0.0

        for idx in range(route_index, len(route)):
            curr_edge_id = route[idx]
            try:
                edge = self._net.getEdge(curr_edge_id)
            except KeyError:
                continue

            cumulative_dist += edge.getLength()
            to_node = edge.getToNode()
            if to_node.getType() == "traffic_light":
                tls_id = str(to_node.getID())
                junctions.append((tls_id, cumulative_dist))
                if len(junctions) >= max_junctions:
                    break

        return junctions

