"""TraCI client — THE ONLY MODULE THAT MAY IMPORT traci/libsumo.

FakeSim is a pure-Python test double that never imports traci.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lanerush.models import EVState, LaneObservation, is_emergency

# ---------------------------------------------------------------------------
# FakeSim — test double, no traci import
# ---------------------------------------------------------------------------

class FakeSim:
    """Minimal simulation state for unit/integration tests without SUMO."""

    def __init__(
        self,
        tls_ids: list[str] | None = None,
        lanes: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._tls_ids: list[str] = tls_ids or []
        self._lanes: dict[str, dict[str, Any]] = lanes or {}
        self._tls_phases: dict[str, int] = {t: 0 for t in self._tls_ids}
        self._tls_states: dict[str, str] = {t: "GrGr" for t in self._tls_ids}
        self._step: int = 0

    # -- simulation control --

    def step(self) -> None:
        self._step += 1

    def close(self) -> None:
        pass

    @property
    def current_time(self) -> int:
        return self._step

    # -- TLS --

    def get_tls_ids(self) -> list[str]:
        return list(self._tls_ids)

    def get_tls_phase(self, tls_id: str) -> int:
        return self._tls_phases.get(tls_id, 0)

    def get_tls_state(self, tls_id: str) -> str:
        return self._tls_states.get(tls_id, "GrGr")

    def get_tls_program(self, tls_id: str) -> list[tuple[str, float]]:
        """Return list of (state_string, duration) for each phase."""
        return [("GGrr", 42.0), ("yyrr", 3.0), ("rrGG", 42.0), ("rryy", 3.0)]

    def get_tls_controlled_links(self, tls_id: str) -> list[tuple[tuple[str, str, str], ...]]:
        return []

    def set_tls_phase_durations(self, tls_id: str, phase_durations: dict[int, float]) -> None:
        pass

    def set_phase(self, tls_id: str, phase: int) -> None:
        self._tls_phases[tls_id] = phase

    def set_phase_duration(self, tls_id: str, duration: float) -> None:
        pass

    # -- Lane observations --

    def get_lane_vehicle_count(self, lane_id: str) -> int:
        return self._lanes.get(lane_id, {}).get("count", 0)

    def get_lane_halting_number(self, lane_id: str) -> int:
        return self._lanes.get(lane_id, {}).get("halting", 0)

    def get_lane_max_wait(self, lane_id: str) -> float:
        return self._lanes.get(lane_id, {}).get("max_wait", 0.0)

    def get_lane_ids(self) -> list[str]:
        return list(self._lanes.keys())

    # -- Vehicle / EV --

    def get_vehicle_ids(self) -> list[str]:
        return []

    def get_departed_vehicle_ids(self) -> list[str]:
        return []

    def get_vehicle_route(self, vid: str) -> list[str]:
        return []

    def get_vehicle_type(self, vid: str) -> str:
        return "passenger"

    def get_ev_states(self) -> list[EVState]:
        return []

    # -- Snapshot --

    def snapshot(self) -> SimSnapshot:
        """Return a single consistent read of all simulation state."""
        obs: dict[str, LaneObservation] = {}
        for lane_id in self._lanes:
            count = self.get_lane_vehicle_count(lane_id)
            halting = self.get_lane_halting_number(lane_id)
            max_wait = self.get_lane_max_wait(lane_id)
            obs[lane_id] = LaneObservation(
                lane_id=lane_id,
                count=count,
                halting=halting,
                max_wait=max_wait,
                emergency=False,
                source="fake",
            )
        return SimSnapshot(
            t=self._step,
            observations=obs,
            tls_phases=dict(self._tls_phases),
            tls_states=dict(self._tls_states),
            ev_states=[],
        )


@dataclass
class SimSnapshot:
    """Immutable snapshot of sim state at one timestep."""

    t: int
    observations: dict[str, LaneObservation]
    tls_phases: dict[str, int]
    tls_states: dict[str, str]
    ev_states: list[EVState]


# ---------------------------------------------------------------------------
# TraciClient — real SUMO client, the only file that imports traci
# ---------------------------------------------------------------------------

def _resolve_sumo_binary(binary: str) -> str:
    """Resolve binary using PATH or SUMO_HOME."""
    import os
    import shutil
    from pathlib import Path

    if shutil.which(binary):
        return binary
    try:
        import sumo  # type: ignore[import-untyped]

        sumo_home = Path(str(sumo.SUMO_HOME))
        bin_dir = sumo_home / "bin"
        if bin_dir.exists():
            os.environ["SUMO_HOME"] = str(sumo_home)
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            for ext in (".exe", ""):
                candidate = bin_dir / f"{binary}{ext}"
                if candidate.exists():
                    return str(candidate)
    except Exception:
        pass
    return binary


class TraciClient:
    """Thin wrapper around TraCI that returns dataclasses.

    Only instantiated at runtime when SUMO is available.
    """

    def __init__(self, port: int = 8813) -> None:
        import traci  # noqa: PLC0415 — intentional, only file that imports traci

        self._traci = traci
        self._port = port
        self._connected = False

    def connect(
        self,
        sumo_binary: str,
        net_file: str,
        route_file: str,
        step_length: float,
        seed: int,
        gui: bool = False,
        extra_args: list[str] | None = None,
    ) -> None:
        target_binary = "sumo-gui" if gui else sumo_binary
        bin_path = _resolve_sumo_binary(target_binary)

        cmd = [
            bin_path,
            "-n", net_file,
            "-r", route_file,
            "--step-length", str(step_length),
            "--seed", str(seed),
            "--time-to-teleport", "-1",
            "--no-step-log", "true",
            "--no-warnings", "true",
        ]
        if gui:
            cmd.extend(["--start", "true", "--delay", "350"])
            gui_settings = Path(net_file).parent / "viewsettings.xml"
            if gui_settings.exists():
                cmd.extend(["--gui-settings-file", str(gui_settings)])
            add_file = Path(net_file).parent / "city_blocks.add.xml"
            if add_file.exists():
                cmd.extend(["-a", str(add_file)])
        if extra_args:
            cmd.extend(extra_args)

        self._traci.start(cmd, port=self._port)
        self._connected = True

    def step(self) -> None:
        self._traci.simulationStep()

    def close(self) -> None:
        if self._connected:
            self._traci.close()
            self._connected = False

    @property
    def current_time(self) -> int:
        return int(self._traci.simulation.getTime())

    def get_tls_ids(self) -> list[str]:
        return list(self._traci.trafficlight.getIDList())

    def get_tls_phase(self, tls_id: str) -> int:
        return int(self._traci.trafficlight.getPhase(tls_id))

    def get_tls_state(self, tls_id: str) -> str:
        return str(self._traci.trafficlight.getRedYellowGreenState(tls_id))

    def get_tls_program(self, tls_id: str) -> list[tuple[str, float]]:
        logic = self._traci.trafficlight.getAllProgramLogics(tls_id)[0]
        return [(p.state, p.duration) for p in logic.phases]

    def get_tls_controlled_links(self, tls_id: str) -> list[tuple[tuple[str, str, str], ...]]:
        return list(self._traci.trafficlight.getControlledLinks(tls_id))

    def set_tls_phase_durations(self, tls_id: str, phase_durations: dict[int, float]) -> None:
        logics = self._traci.trafficlight.getAllProgramLogics(tls_id)
        if logics:
            logic = logics[0]
            for p_idx, dur in phase_durations.items():
                if p_idx < len(logic.phases):
                    logic.phases[p_idx].duration = dur
            self._traci.trafficlight.setProgramLogic(tls_id, logic)

    def set_phase(self, tls_id: str, phase: int) -> None:
        self._traci.trafficlight.setPhase(tls_id, phase)

    def set_phase_duration(self, tls_id: str, duration: float) -> None:
        self._traci.trafficlight.setPhaseDuration(tls_id, duration)

    def get_lane_ids(self) -> list[str]:
        return list(self._traci.lane.getIDList())

    def get_lane_vehicle_count(self, lane_id: str) -> int:
        return int(self._traci.lane.getLastStepVehicleNumber(lane_id))

    def get_lane_halting_number(self, lane_id: str) -> int:
        return int(self._traci.lane.getLastStepHaltingNumber(lane_id))

    def get_lane_max_wait(self, lane_id: str) -> float:
        """Max consecutive waiting time among vehicles on this lane."""
        vids = self._traci.lane.getLastStepVehicleIDs(lane_id)
        if not vids:
            return 0.0
        return max(self._traci.vehicle.getWaitingTime(v) for v in vids)

    def get_vehicle_ids(self) -> list[str]:
        return list(self._traci.vehicle.getIDList())

    def get_departed_vehicle_ids(self) -> list[str]:
        return list(self._traci.simulation.getDepartedIDList())

    def get_vehicle_route(self, vid: str) -> list[str]:
        return list(self._traci.vehicle.getRoute(vid))

    def get_vehicle_type(self, vid: str) -> str:
        return str(self._traci.vehicle.getTypeID(vid))

    def get_ev_states(self) -> list[EVState]:
        ev_states: list[EVState] = []
        for vid in self.get_vehicle_ids():
            vtype = self.get_vehicle_type(vid)
            if not is_emergency(vtype):
                continue
            edge = str(self._traci.vehicle.getRoadID(vid))
            if edge.startswith(":"):
                continue  # inside junction, skip
            lane_id = str(self._traci.vehicle.getLaneID(vid))
            lane_pos = float(self._traci.vehicle.getLanePosition(vid))
            lane_len = float(self._traci.lane.getLength(lane_id))
            speed = float(self._traci.vehicle.getSpeed(vid))
            route = tuple(self._traci.vehicle.getRoute(vid))
            route_index = int(self._traci.vehicle.getRouteIndex(vid))
            ev_states.append(
                EVState(
                    vehicle_id=vid,
                    edge=edge,
                    lane_id=lane_id,
                    lane_pos=lane_pos,
                    lane_len=lane_len,
                    speed=speed,
                    route=route,
                    route_index=route_index,
                )
            )
        return ev_states

    def snapshot(self) -> SimSnapshot:
        """Read all simulation state in one sweep — reuse this, don't call twice per step."""
        t = self.current_time
        lane_ids = self.get_lane_ids()
        obs: dict[str, LaneObservation] = {}
        for lane_id in lane_ids:
            if lane_id.startswith(":"):
                continue
            count = self.get_lane_vehicle_count(lane_id)
            halting = self.get_lane_halting_number(lane_id)
            max_wait = self.get_lane_max_wait(lane_id)
            # EV presence: check if any vehicle on this lane is emergency type
            vids = self._traci.lane.getLastStepVehicleIDs(lane_id)
            emergency = any(is_emergency(self.get_vehicle_type(v)) for v in vids)
            obs[lane_id] = LaneObservation(
                lane_id=lane_id,
                count=count,
                halting=halting,
                max_wait=max_wait,
                emergency=emergency,
                source="ground_truth",
            )

        tls_ids = self.get_tls_ids()
        tls_phases = {t_id: self.get_tls_phase(t_id) for t_id in tls_ids}
        tls_states = {t_id: self.get_tls_state(t_id) for t_id in tls_ids}
        ev_states = self.get_ev_states()

        return SimSnapshot(
            t=t,
            observations=obs,
            tls_phases=tls_phases,
            tls_states=tls_states,
            ev_states=ev_states,
        )
