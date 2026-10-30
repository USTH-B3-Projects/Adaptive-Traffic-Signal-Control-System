#!/usr/bin/env python3
"""Generate reproducible traffic scenarios through the O Cho Dua junction."""

import argparse
import math
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SCENARIO_RATES = {"low": 600, "medium": 1200, "high": 1800, "peak": 2400}
MOVEMENT_SHARES = {"straight": 0.50, "left": 0.25, "right": 0.25}
# shortcut: exclude the blocked 12 m bus movement at Nguyen Luong Bang, revisit after junction review.
BUS_APPROACHES = {"ton_duc_thang", "xa_dan", "o_cho_dua"}

# Experimental OD assumptions, based on the network's existing, validated connections.
APPROACHES = {
    "ton_duc_thang": {
        "source": "599146734",
        "incoming": "954341842#0",
        "movements": {
            "right": ("964674137#1", "711101759#3"),
            "straight": ("882269315#1", "1204846893#1"),
            "left": ("964868047#1", "36869877#7"),
        },
    },
    "xa_dan": {
        "source": "402400378#0",
        "incoming": "1392245988#0",
        "movements": {
            "right": ("687098302#1", "1242184419"),
            "straight": ("964674137#1", "711101759#3"),
            "left": ("882269315#1", "1204846893#1"),
        },
    },
    "nguyen_luong_bang": {
        "source": "1204846892#0",
        "incoming": "1262818190#0",
        "movements": {
            "right": ("964868047#1", "36869877#7"),
            "straight": ("687098302#1", "1242184419"),
            "left": ("964674137#1", "711101759#3"),
        },
    },
    "o_cho_dua": {
        "source": "506383095#0",
        "incoming": "711109718#1",
        "movements": {
            "right": ("882269315#1", "1204846893#1"),
            "straight": ("964868047#1", "36869877#7"),
            "left": ("687098302#1", "1242184419"),
        },
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIO_RATES, default="medium")
    parser.add_argument("--pattern", choices=("balanced", "unbalanced"), default="balanced")
    parser.add_argument("--motorcycle-share", type=float, default=0.80)
    parser.add_argument("--rate", type=float, help="override total vehicles/hour")
    parser.add_argument("--duration", type=int, default=3600)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("research.rou.xml"))
    return parser.parse_args()


def load_network():
    sumo_home = os.environ.get("SUMO_HOME")
    if not sumo_home:
        raise SystemExit("SUMO_HOME is not set")
    sys.path.append(str(Path(sumo_home) / "tools"))
    import sumolib

    config = ET.parse(Path(__file__).with_name("osm.sumocfg"))
    net_file = config.find("./input/net-file").get("value")
    return sumolib.net.readNet(str(Path(__file__).with_name(net_file)))


def validate_movements(net):
    def path_between(start, end, vehicle_class):
        path = net.getShortestPath(start, end, vClass=vehicle_class)[0]
        if not path:
            raise SystemExit(f"No {vehicle_class} path from {start.getID()} to {end.getID()}")
        if any(all(c.getDirection().lower() == "t" for c in edge.getConnections(next_edge))
               for edge, next_edge in zip(path, path[1:])):
            raise SystemExit(f"U-turn in path from {start.getID()} to {end.getID()}")

    for name, approach in APPROACHES.items():
        source = net.getEdge(approach["source"])
        incoming = net.getEdge(approach["incoming"])
        if source.getIncoming():
            raise SystemExit(f"Source {source.getID()} is not a boundary entry")
        for movement, (outgoing_id, destination_id) in approach["movements"].items():
            outgoing = net.getEdge(outgoing_id)
            destination = net.getEdge(destination_id)
            if destination.getOutgoing():
                raise SystemExit(f"Destination {destination.getID()} is not a boundary exit")
            for vehicle_class in (["motorcycle", "passenger", "bus"] if movement == "straight" and name in BUS_APPROACHES else ["motorcycle", "passenger"]):
                path_between(source, incoming, vehicle_class)
                if not any(c.getFromLane().allows(vehicle_class) and c.getToLane().allows(vehicle_class)
                           for c in incoming.getConnections(outgoing)):
                    raise SystemExit(f"Missing {vehicle_class} movement {incoming.getID()} -> {outgoing_id}")
                path_between(outgoing, destination, vehicle_class)


def add_vehicle_types(root, motorcycle_share, bus_approach_share):
    ET.SubElement(
        root,
        "vType",
        id="motorcycle",
        vClass="motorcycle",
        guiShape="motorcycle",
        length="2.0",
        width="0.8",
        minGap="0.8",
        maxSpeed="13.9",
        accel="3.0",
        decel="4.5",
        tau="1.0",
        sigma="0.5",
        carFollowModel="Krauss",
        laneChangeModel="SL2015",
        lcStrategic="2.0",
        lcCooperative="1.0",
        lcSpeedGain="1.0",
        lcKeepRight="0.5",
        lcSublane="1.0",
        latAlignment="arbitrary",
        minGapLat="0.6",
        maxSpeedLat="0.6",
        color="240,190,35",
    )
    ET.SubElement(
        root,
        "vType",
        id="passenger_car",
        vClass="passenger",
        guiShape="passenger",
        length="4.5",
        width="1.8",
        minGap="2.5",
        maxSpeed="13.9",
        accel="2.0",
        decel="4.5",
        tau="1.2",
        sigma="0.5",
        carFollowModel="Krauss",
        laneChangeModel="SL2015",
        latAlignment="center",
        minGapLat="0.6",
        lcSpeedGain="0",
        lcKeepRight="1",
        color="45,125,215",
    )
    ET.SubElement(root, "vType", id="bus", vClass="bus", guiShape="bus",
                  length="12", width="2.5", minGap="3", tau="1.5", maxSpeed="11.1",
                  accel="1.2", decel="3.5", sigma="0.5", carFollowModel="Krauss",
                  laneChangeModel="SL2015", lcSpeedGain="0", lcKeepRight="1",
                  latAlignment="center", minGapLat="0.6", color="225,90,55")
    other = 1 - motorcycle_share
    # Keep network-wide shares even when approach demand is unbalanced.
    bus_straight = other * .15 / (MOVEMENT_SHARES["straight"] * bus_approach_share)
    ET.SubElement(root, "vTypeDistribution", id="traffic_mix",
                  vTypes="motorcycle passenger_car", probabilities=f"{motorcycle_share:.12g} {other:.12g}")
    ET.SubElement(root, "vTypeDistribution", id="traffic_mix_straight",
                  vTypes="motorcycle passenger_car bus",
                  probabilities=f"{motorcycle_share:.12g} {other - bus_straight:.12g} {bus_straight:.12g}")


def main():
    args = parse_args()
    if not 0 <= args.motorcycle_share <= 1:
        raise SystemExit("--motorcycle-share must be between 0 and 1")
    if args.duration <= 0:
        raise SystemExit("--duration must be positive")
    rate = args.rate if args.rate is not None else SCENARIO_RATES[args.scenario]
    if not math.isfinite(rate) or rate <= 0:
        raise SystemExit("--rate must be finite and positive")

    net = load_network()
    validate_movements(net)
    root = ET.Element("routes")
    root.append(ET.Comment(
        f" Experimental assumptions: {args.scenario}/{args.pattern}, "
        f"{rate:g} veh/h, {args.motorcycle_share:.0%} motorcycles. "
    ))
    approach_weights = {name: 1.0 for name in APPROACHES}
    if args.pattern == "unbalanced":
        approach_weights["o_cho_dua"] = 3.0
    weight_total = sum(approach_weights.values())
    add_vehicle_types(root, args.motorcycle_share,
                      sum(approach_weights[name] for name in BUS_APPROACHES) / weight_total)

    for name, approach in APPROACHES.items():
        approach_rate = rate * approach_weights[name] / weight_total
        for movement, (outgoing, destination) in approach["movements"].items():
            ET.SubElement(
                root,
                "flow",
                id=f"{name}_{movement}",
                type="traffic_mix_straight" if movement == "straight" and name in BUS_APPROACHES else "traffic_mix",
                begin="0",
                end=str(args.duration),
                vehsPerHour=f"{approach_rate * MOVEMENT_SHARES[movement]:.3f}",
                **{
                    "from": approach["source"],
                    "to": destination,
                    "via": f'{approach["incoming"]} {outgoing}',
                    "departLane": "best",
                    "departSpeed": "max",
                },
            )

    ET.indent(root, space="    ")
    args.output.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output}: {rate:g} veh/h, {args.motorcycle_share:.0%} motorcycles")


if __name__ == "__main__":
    main()
