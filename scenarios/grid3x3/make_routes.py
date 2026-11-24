#!/usr/bin/env python3
"""Generate routes for the 3×3 grid scenario.

vTypes: passenger, emergency (vClass=emergency, red, speedDev=0)
Stochastic flows via <flow probability=...> (NOT period).
Heavy EW, medium NS, two light side roads (~0.012 veh/s).
Emergency vehicle showcases with queue pre-clearing.

Run from project root:
    python scenarios/grid3x3/make_routes.py
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

OUTPUT_DIR = Path("scenarios/grid3x3")
OUTPUT_FILE = OUTPUT_DIR / "grid3x3.rou.xml"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    root = ET.Element("routes")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:noNamespaceSchemaLocation",
             "http://sumo.dlr.de/xsd/routes_file.xsd")

    # --- Vehicle types ---
    # Realistic 2D vehicle shapes and proportions for clear microscopic viewing
    vtype_pass = ET.SubElement(root, "vType")
    vtype_pass.set("id", "passenger")
    vtype_pass.set("vClass", "passenger")
    vtype_pass.set("guiShape", "passenger/sedan")
    vtype_pass.set("length", "4.8")
    vtype_pass.set("width", "1.95")
    vtype_pass.set("color", "0.92,0.92,0.95")  # Pearl white default
    vtype_pass.set("maxSpeed", "7.0")  # ~25 km/h urban speed, easily observable
    vtype_pass.set("accel", "1.2")
    vtype_pass.set("decel", "2.5")

    vtype_ev = ET.SubElement(root, "vType")
    vtype_ev.set("id", "emergency")
    vtype_ev.set("vClass", "emergency")
    vtype_ev.set("guiShape", "emergency")
    vtype_ev.set("length", "6.8")
    vtype_ev.set("width", "2.3")
    vtype_ev.set("color", "1,0,0")  # Vibrant emergency red
    vtype_ev.set("maxSpeed", "9.5")  # ~34 km/h, visibly faster than cars
    vtype_ev.set("speedDev", "0")
    vtype_ev.set("accel", "2.2")
    vtype_ev.set("decel", "3.5")

    # --- Common Routes ---
    route_ew_main = ET.SubElement(root, "route")
    route_ew_main.set("id", "route_ew_row1")
    route_ew_main.set("edges", "left1A1 A1B1 B1C1 C1right1")

    route_ns_col0 = ET.SubElement(root, "route")
    route_ns_col0.set("id", "route_ns_col0")
    route_ns_col0.set("edges", "top0A2 A2A1 A1A0 A0bottom0")

    route_ns_approach = ET.SubElement(root, "route")
    route_ns_approach.set("id", "route_ns_approach")
    route_ns_approach.set("edges", "A2A1 A1A0 A0bottom0")

    # --- Showcase Sequence: 4 stuck cars + immediate EV release ---
    # North-South vehicles start on A2A1 to keep Phase 0 active and East-West at RED
    showcase_vehicles = [
        ("cross_ns_1", "passenger", "route_ns_approach", 1, "0.2,0.4,0.8"),    # Royal Blue
        ("stuck_car_1", "passenger", "route_ew_row1", 2, "0.95,0.95,0.98"),    # Pearl White
        ("stuck_car_2", "passenger", "route_ew_row1", 6, "0.2,0.6,0.9"),       # Sky Blue Metallic
        ("cross_ns_2", "passenger", "route_ns_approach", 7, "0.75,0.75,0.8"),   # Silver
        ("stuck_car_3", "passenger", "route_ew_row1", 10, "0.9,0.55,0.1"),     # Sunset Amber
        ("cross_ns_3", "passenger", "route_ns_approach", 13, "0.2,0.25,0.3"),   # Dark Slate
        ("stuck_car_4", "passenger", "route_ew_row1", 14, "0.45,0.45,0.5"),    # Charcoal
        ("cross_ns_4", "passenger", "route_ns_approach", 19, "0.8,0.2,0.2"),    # Crimson
        ("cross_ns_5", "passenger", "route_ns_approach", 25, "0.95,0.95,0.98"), # Pearl White
        ("cross_ns_6", "passenger", "route_ns_approach", 31, "0.15,0.35,0.7"),  # Navy
        ("cross_ns_7", "passenger", "route_ns_approach", 37, "0.7,0.7,0.75"),   # Silver
        ("EV0", "emergency", "route_ew_row1", 40, "1,0,0"),                     # Fire-Engine Red
    ]
    showcase_vehicles.sort(key=lambda item: item[3])

    for vid, vtype, route_id, dep, col in showcase_vehicles:
        veh = ET.SubElement(root, "vehicle")
        veh.set("id", vid)
        veh.set("type", vtype)
        veh.set("route", route_id)
        veh.set("depart", str(dep))
        veh.set("color", col)

    # --- Background stochastic flows (EW, NS, side) ---
    ew_flows = [
        ("ew_flow_1", "left0A0", "C0right0", 0.022),
        ("ew_flow_2", "left1A1", "C1right1", 0.024),
        ("ew_flow_3", "left2A2", "C2right2", 0.022),
        # Reverse
        ("we_flow_1", "right0C0", "A0left0", 0.022),
        ("we_flow_2", "right1C1", "A1left1", 0.024),
        ("we_flow_3", "right2C2", "A2left2", 0.022),
    ]

    ns_flows = [
        ("ns_flow_1", "top0A2", "A0bottom0", 0.015),
        ("ns_flow_2", "top1B2", "B0bottom1", 0.015),
        ("ns_flow_3", "top2C2", "C0bottom2", 0.015),
        # Reverse
        ("sn_flow_1", "bottom0A0", "A2top0", 0.015),
        ("sn_flow_2", "bottom1B0", "B2top1", 0.015),
        ("sn_flow_3", "bottom2C0", "C2top2", 0.015),
    ]

    side_flows = [
        ("side_flow_1", "left0A0", "A2top0", 0.010),
        ("side_flow_2", "bottom2C0", "C2right2", 0.010),
    ]

    all_flows = ew_flows + ns_flows + side_flows

    for flow_id, from_edge, to_edge, prob in all_flows:
        flow = ET.SubElement(root, "flow")
        flow.set("id", flow_id)
        flow.set("type", "passenger")
        flow.set("from", from_edge)
        flow.set("to", to_edge)
        flow.set("begin", "60")  # Start background flows after the initial showcase sequence
        flow.set("end", "3600")
        flow.set("probability", str(prob))
        flow.set("color", "random")

    # --- Additional Emergency Vehicles at later intervals ---
    ev_routes = [
        # EV1: South→North through col B (Central Boulevard) at t=120
        ("EV1", 120, ["bottom1B0", "B0B1", "B1B2", "B2top1"]),
        # EV2: West→East through row 1 at t=240
        ("EV2", 240, ["left1A1", "A1B1", "B1C1", "C1right1"]),
        # EV3: East→West through row 0 at t=360
        ("EV3", 360, ["right0C0", "C0B0", "B0A0", "A0left0"]),
        # EV4: North→South through col A at t=480
        ("EV4", 480, ["top0A2", "A2A1", "A1A0", "A0bottom0"]),
    ]

    for ev_id, depart, edges in ev_routes:
        route = ET.SubElement(root, "route")
        route.set("id", f"route_{ev_id}")
        route.set("edges", " ".join(edges))

        vehicle = ET.SubElement(root, "vehicle")
        vehicle.set("id", ev_id)
        vehicle.set("type", "emergency")
        vehicle.set("route", f"route_{ev_id}")
        vehicle.set("depart", str(depart))

    # Write output
    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(str(OUTPUT_FILE), encoding="unicode", xml_declaration=True)
    print(f"Routes generated: {OUTPUT_FILE}")

    # Count flows for verification
    total_prob = sum(prob for _, _, _, prob in all_flows)
    expected_vehicles = total_prob * (3600 - 60) + 9  # background + explicit showcase
    print(f"Expected ordinary vehicles per seed: ~{expected_vehicles:.0f}")
    print(f"Emergency vehicles: {1 + len(ev_routes)}")


if __name__ == "__main__":
    main()
