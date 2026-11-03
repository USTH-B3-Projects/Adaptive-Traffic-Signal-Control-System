"""JSON-ready snapshots of unique incoming lanes for each controlled junction."""
import math

from .signal_controller import SignalController


def _metric(value: float) -> float | None:
    value = float(value)
    return value if math.isfinite(value) and value >= 0 else None


class StateExtractor:
    def __init__(self, connection, signals: SignalController):
        self.connection = connection
        self.signals = signals
        self.incoming = {
            tls: tuple(dict.fromkeys(
                link[0]
                for group in connection.trafficlight.getControlledLinks(tls)
                for link in group
            ))
            for tls in signals.tls_ids
        }

    def extract(self, scenario: str, now: float) -> dict:
        api = self.connection.lane
        lane_data = {}
        for lane in dict.fromkeys(lane for lanes in self.incoming.values() for lane in lanes):
            count = api.getLastStepVehicleNumber(lane)
            halting = api.getLastStepHaltingNumber(lane)
            if count < 0 or halting < 0 or halting > count:
                raise ValueError(f"Invalid vehicle counts for lane {lane}")
            lane_data[lane] = {
                "vehicle_count": count,
                "halting_count": halting,
                "waiting_time": _metric(api.getWaitingTime(lane)),
                "average_speed": _metric(api.getLastStepMeanSpeed(lane)) if count else None,
            }
        tls_data = {}
        for tls, lane_ids in self.incoming.items():
            lanes = {lane: lane_data[lane] for lane in lane_ids}
            total = sum(lane["vehicle_count"] for lane in lanes.values())
            occupied = [lane for lane in lanes.values() if lane["vehicle_count"]]
            waiting = [lane["waiting_time"] for lane in lanes.values()]
            tls_data[tls] = {
                "tls_id": tls,
                **self.signals.snapshot(tls, now),
                "incoming_lane_ids": list(lane_ids),
                "lanes": lanes,
                "totals": {
                    "vehicle_count": total,
                    "halting_count": sum(lane["halting_count"] for lane in lanes.values()),
                    "waiting_time": sum(waiting) if all(v is not None for v in waiting) else None,
                    "average_speed": (
                        sum(lane["average_speed"] * lane["vehicle_count"] for lane in occupied) / total
                        if total and all(lane["average_speed"] is not None for lane in occupied) else None
                    ),
                },
            }
        return {"simulation_time": float(now), "scenario": scenario, "tls": tls_data}
