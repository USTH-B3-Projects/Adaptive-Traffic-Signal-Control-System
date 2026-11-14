#!/usr/bin/env python3
"""Generate reproducible traffic scenarios through the O Cho Dua junction."""

import argparse
import csv
import random
import math
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCENARIO_RATES = {"high": 5400, "imbalance": 4200}
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
    parser.add_argument("--scenario", type=str.lower, choices=(*SCENARIO_RATES, "all"), default="all")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--motorcycle-share", type=float, default=0.80)
    parser.add_argument("--rate", type=float, help="override total vehicles/hour")
    parser.add_argument("--duration", type=int)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def load_network():
    sumo_home = os.environ.get("SUMO_HOME")
    if not sumo_home:
        raise SystemExit("SUMO_HOME is not set")
    sys.path.append(str(Path(sumo_home) / "tools"))
    import sumolib

    return sumolib.net.readNet(str(ROOT / "network/osm.fixed.net.xml"))


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


def make_profile(scenario, rate, duration, seed):
    """30-second average rates, interpolated between seeded demand peaks."""
    rng = random.Random(seed)
    names = list(APPROACHES)
    balanced = {name: .25 for name in names}
    anchors = [(0, balanced)]
    if scenario == "imbalance":
        time = 600
        order = names[:]
        rng.shuffle(order)
        index = 0
        while time < duration - 600:
            dominant = order[index % len(order)]
            peak = rng.uniform(.50, .65)
            weights = {name: (1-peak)/3 for name in names}
            weights[dominant] = peak
            anchors.append((time, weights))
            time += rng.randint(900, 1500)
            index += 1
    anchors.append((duration, balanced))
    rows = []
    index = 0
    for begin in range(0, duration, 30):
        end = min(begin + 30, duration)
        midpoint = (begin + end)/2
        while index + 1 < len(anchors)-1 and midpoint > anchors[index+1][0]:
            index += 1
        start, left = anchors[index]
        stop, right = anchors[index+1]
        fraction = (midpoint-start)/(stop-start)
        fraction = fraction*fraction*(3-2*fraction)
        weights = {name: left[name]*(1-fraction)+right[name]*fraction for name in names}
        rows.append((begin, end, weights))
    return rows


def generate(scenario, args):
    rate = args.rate if args.rate is not None else SCENARIO_RATES[scenario]
    duration = args.duration if args.duration is not None else (10800 if scenario == "imbalance" else 3600)
    if duration <= 0 or not math.isfinite(rate) or rate <= 0:
        raise SystemExit("Duration and finite rate must be positive")
    directory = ROOT / "scenarios" / scenario.capitalize()
    directory.mkdir(parents=True, exist_ok=True)
    route_file = args.output.resolve() if args.output else directory / "traffic.rou.xml"
    root = ET.Element("routes")
    root.append(ET.Comment(f"Experimental {scenario}; {rate:g} veh/h; seed {args.seed}"))
    profile = make_profile(scenario, rate, duration, args.seed)
    if any(rate * max(weights.values()) * max(MOVEMENT_SHARES.values()) / 3600 > 1
           for _, _, weights in profile):
        raise SystemExit("Rate exceeds the per-flow probability limit (1 vehicle/second)")
    for index, (begin, end, weights) in enumerate(profile):
        # Each interval needs its own mix: buses cannot enter from Nguyen Luong Bang.
        types = ET.Element("routes")
        add_vehicle_types(types, args.motorcycle_share, sum(weights[n] for n in BUS_APPROACHES))
        suffix = f"_{index}"
        if index == 0:
            root.extend(types.findall("vType"))
        for mix in types.findall("vTypeDistribution"):
            mix.set("id", mix.get("id") + suffix)
            root.append(mix)
        for name, approach in APPROACHES.items():
            for movement, (outgoing, destination) in approach["movements"].items():
                mix = "traffic_mix_straight" if movement == "straight" and name in BUS_APPROACHES else "traffic_mix"
                ET.SubElement(root, "flow", id=f"{name}_{movement}_{index}",
                    type=mix+suffix, begin=str(begin), end=str(end),
                    probability=f"{rate*weights[name]*MOVEMENT_SHARES[movement]/3600:.17g}",
                    **{"from": approach["source"], "to": destination,
                       "via": f'{approach["incoming"]} {outgoing}',
                       "departLane": "best", "departSpeed": "max"})
    ET.indent(root, space="    ")
    ET.ElementTree(root).write(route_file, encoding="utf-8", xml_declaration=True)
    with (directory / "demand_profile.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["begin", "end", *APPROACHES])
        for begin, end, weights in profile:
            writer.writerow([begin, end, *(f"{rate*weights[n]:.6f}" for n in APPROACHES)])
    config = ET.parse(ROOT / "config/base.sumocfg")
    config.find("input/net-file").set("value", "../../network/osm.fixed.net.xml")
    config.find("input/route-files").set("value", os.path.relpath(route_file, directory).replace("\\", "/"))
    config.find("input/additional-files").set("value", "../../network/osm.poly.xml.gz")
    config.find("gui_only/gui-settings-file").set("value", "../../config/osm.view.xml")
    output = ROOT / "output" / scenario.capitalize() / f"seed{args.seed}"
    output.mkdir(parents=True, exist_ok=True)
    for key, filename in [("tripinfo-output", "tripinfos.xml"), ("statistic-output", "stats.xml")]:
        config.find("output/"+key).set("value", os.path.relpath(output/filename, directory).replace("\\", "/"))
    extra = ET.parse(ROOT / "config/output.add.xml").getroot()
    extra.find("edgeData").set("period", "60")
    extra.find("edgeData").set("file", os.path.relpath(output/"edgeData.xml", directory).replace("\\", "/"))
    ET.indent(extra)
    ET.ElementTree(extra).write(directory/"output.add.xml", encoding="utf-8", xml_declaration=True)
    config.find("input/additional-files").set("value", "../../network/osm.poly.xml.gz,output.add.xml")
    ET.SubElement(config.getroot(), "random_number").append(ET.Element("seed", value=str(args.seed)))
    ET.indent(config)
    config.write(directory/"simulation.sumocfg", encoding="utf-8", xml_declaration=True)
    print(f"{scenario}: {rate:g} veh/h, demand 0-{duration}s, clearance until empty; seed {args.seed}")


def main():
    args = parse_args()
    if not 0 <= args.motorcycle_share <= 1:
        raise SystemExit("--motorcycle-share must be between 0 and 1")
    if args.output and args.scenario == "all":
        raise SystemExit("--output requires one scenario")
    net = load_network()
    validate_movements(net)
    for scenario in SCENARIO_RATES if args.scenario == "all" else [args.scenario]:
        generate(scenario, args)


if __name__ == "__main__":
    main()
