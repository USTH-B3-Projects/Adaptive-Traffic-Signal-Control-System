from pathlib import Path
import sys
import gymnasium as gym
import numpy as np
from gymnasium import spaces

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "TraCI"))
from core.environment import Environment

ACTIONS = ("KEEP", "SWITCH")

# Normalisation constants. Observation values are clipped to [0, 1].
Q_SCALE = 20.0   # halting vehicles per direction group
V_SCALE = 30.0   # vehicles per direction group
W_SCALE = 60.0   # average waiting time per vehicle (s)
S_SCALE = 15.0   # average speed (m/s)

# Reward: r = -(ALPHA * queue_hat + BETA * wait_hat)
ALPHA, BETA = 1.0, 0.5

OBS_NAMES = [
    "queue_ns", "queue_ew", "vehicles_ns", "vehicles_ew",
    "wait_ns", "wait_ew", "speed_ns", "speed_ew",
    "phase_is_ns", "in_transition", "elapsed_green",
]


class TrafficEnv(gym.Env):
    # Single-intersection signal control. Action: 0 = KEEP, 1 = SWITCH.

    metadata = {"render_modes": []}

    def __init__(self, scenario="low", traffic_seeds=None, settings=None):
        super().__init__()
        self.scenario = scenario
        self.traffic_seeds = list(traffic_seeds) if traffic_seeds else None
        self._env = Environment(settings=settings)
        self.settings = self._env.settings
        self.max_green = float(self.settings["max_green"])
        self.min_green = float(self.settings["min_green"])
        self.observation_space = spaces.Box(0.0, 1.0, shape=(len(OBS_NAMES),), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self._tls = None

    # ---------------------------------------------------------------- helpers
    def _build_groups(self):
        links = self._env.connection.trafficlight.getControlledLinks(self._tls)
        self._ns_links = [i for i, g in enumerate(links) if g and g[0][0][0] in "NS"]
        self._ew_links = [i for i, g in enumerate(links) if g and g[0][0][0] in "EW"]
        if not self._ns_links or not self._ew_links:
            raise ValueError("Could not split links into NS and EW groups; "
                             "this wrapper expects lane ids starting with N/E/S/W")

    @staticmethod
    def _aggregate(lanes, letters):
        sel = [v for k, v in lanes.items() if k[0] in letters]
        veh = sum(v["vehicle_count"] for v in sel)
        halt = sum(v["halting_count"] for v in sel)
        wait = sum(v["waiting_time"] or 0.0 for v in sel)
        speed = sum((v["average_speed"] or 0.0) * v["vehicle_count"] for v in sel)
        return veh, halt, (wait / veh if veh else 0.0), (speed / veh if veh else 0.0)

    def _obs(self, state):
        t = state["tls"][self._tls]
        ns = self._aggregate(t["lanes"], "NS")
        ew = self._aggregate(t["lanes"], "EW")
        ps = t["phase_state"]
        ns_green = any(ps[i] in "Gg" for i in self._ns_links)
        ew_green = any(ps[i] in "Gg" for i in self._ew_links)
        if ns_green != ew_green:          # during yellow/all-red keep the last green
            self._last_ns = ns_green
        obs = np.array([
            ns[1] / Q_SCALE, ew[1] / Q_SCALE,
            ns[0] / V_SCALE, ew[0] / V_SCALE,
            ns[2] / W_SCALE, ew[2] / W_SCALE,
            ns[3] / S_SCALE, ew[3] / S_SCALE,
            float(self._last_ns), float(t["in_transition"]),
            t["green_elapsed"] / self.max_green,
        ], dtype=np.float32)
        return np.clip(obs, 0.0, 1.0)

    # ---------------------------------------------------------- Gymnasium API
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        options = options or {}
        sumo_seed = options.get("sumo_seed")
        if sumo_seed is None and self.traffic_seeds:
            sumo_seed = int(self.np_random.choice(self.traffic_seeds))
        state = self._env.reset(self.scenario, seed=sumo_seed)
        self._tls = next(iter(state["tls"]))
        self._build_groups()
        self._last_ns = True
        return self._obs(state), {"sumo_seed": sumo_seed}

    def step(self, action):
        state, terminated, truncated, info = self._env.step(ACTIONS[int(action)])
        t = state["tls"][self._tls]
        ns = self._aggregate(t["lanes"], "NS")
        ew = self._aggregate(t["lanes"], "EW")
        veh, halt = ns[0] + ew[0], ns[1] + ew[1]
        avg_wait = (ns[0] * ns[2] + ew[0] * ew[2]) / veh if veh else 0.0
        reward = -(ALPHA * halt / (2 * Q_SCALE) + BETA * avg_wait / W_SCALE)
        out = {
            "halting": halt,
            "avg_wait": avg_wait,
            "executed_action": info["executed_action"][self._tls],
            "sim_time": info["sim_time"],
            "end_reason": info["end_reason"],
        }
        return self._obs(state), float(reward), bool(terminated), bool(truncated), out

    def close(self):
        self._env.close()
        