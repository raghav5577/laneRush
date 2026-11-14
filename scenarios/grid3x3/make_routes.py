#!/usr/bin/env python3
"""Generate routes for the 3×3 grid scenario.

vTypes: passenger, emergency (vClass=emergency, red, speedDev=0)
Stochastic flows via <flow probability=...> (NOT period).
Heavy EW, medium NS, two light side roads (~0.012 veh/s).
4 EVs at t=120/300/480/660 with fixed multi-junction routes.

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
    vtype_pass = ET.SubElement(root, "vType")
    vtype_pass.set("id", "passenger")
    vtype_pass.set("vClass", "passenger")
    vtype_pass.set("color", "1,1,0")

    vtype_ev = ET.SubElement(root, "vType")
    vtype_ev.set("id", "emergency")
    vtype_ev.set("vClass", "emergency")
    vtype_ev.set("color", "1,0,0")
    vtype_ev.set("speedDev", "0")

    # --- Grid edge naming convention for netgenerate --grid ---
    # Edges: top/bottom/left/right and internal grid edges
    # For a 3x3 grid with netgenerate, edges are named like:
    #   Horizontal: A0B0, B0C0, ... (from left to right)
    #   Vertical:   A0A1, A1A2, ... (from bottom to top)
    # The actual names depend on netgenerate output; these are typical patterns.
    # We'll use edge-id references from the network.

    # Heavy EW flows (East-West, through the grid)
    ew_flows = [
        ("ew_flow_1", "left0A0", "C0right0", 0.018),
        ("ew_flow_2", "left1A1", "C1right1", 0.020),
        ("ew_flow_3", "left2A2", "C2right2", 0.018),
        # Reverse
        ("we_flow_1", "right0C0", "A0left0", 0.018),
        ("we_flow_2", "right1C1", "A1left1", 0.020),
        ("we_flow_3", "right2C2", "A2left2", 0.018),
    ]

    # Medium NS flows (North-South)
    ns_flows = [
        ("ns_flow_1", "top0A2", "A0bottom0", 0.0095),
        ("ns_flow_2", "top1B2", "B0bottom1", 0.0095),
        ("ns_flow_3", "top2C2", "C0bottom2", 0.0095),
        # Reverse
        ("sn_flow_1", "bottom0A0", "A2top0", 0.0095),
        ("sn_flow_2", "bottom1B0", "B2top1", 0.0095),
        ("sn_flow_3", "bottom2C0", "C2top2", 0.0095),
    ]

    # Light side roads (~0.012 veh/s ≈ 43 veh/hr)
    side_flows = [
        ("side_flow_1", "left0A0", "A2top0", 0.012),
        ("side_flow_2", "bottom2C0", "C2right2", 0.012),
    ]

    all_flows = ew_flows + ns_flows + side_flows

    for flow_id, from_edge, to_edge, prob in all_flows:
        flow = ET.SubElement(root, "flow")
        flow.set("id", flow_id)
        flow.set("type", "passenger")
        flow.set("from", from_edge)
        flow.set("to", to_edge)
        flow.set("begin", "0")
        flow.set("end", "3600")
        flow.set("probability", str(prob))

    # --- 4 Emergency Vehicles at t=120, 300, 480, 660 ---
    ev_routes = [
        # EV1: West→East through all 3 junctions on row 1
        ("EV1", 120, ["left1A1", "A1B1", "B1C1", "C1right1"]),
        # EV2: South→North through 3 junctions on col B
        ("EV2", 300, ["bottom1B0", "B0B1", "B1B2", "B2top1"]),
        # EV3: East→West through row 0
        ("EV3", 480, ["right0C0", "C0B0", "B0A0", "A0left0"]),
        # EV4: North→South through col A
        ("EV4", 660, ["top0A2", "A2A1", "A1A0", "A0bottom0"]),
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
    expected_vehicles = total_prob * 3600
    print(f"Expected ordinary vehicles per seed: ~{expected_vehicles:.0f}")
    print(f"Emergency vehicles: {len(ev_routes)}")


if __name__ == "__main__":
    main()
