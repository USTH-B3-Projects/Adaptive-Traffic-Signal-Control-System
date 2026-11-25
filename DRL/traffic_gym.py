from pathlib import Path
import sys
import gymnasium as gym
import numpy as np
from gymnasium import spaces

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "TraCI").is_dir())
sys.path.insert(0, str(ROOT / "TraCI"))
from core.environment import Environment

ACTIONS = ("KEEP", "SWITCH")

TEST_SEEDS = (57, 367, 1024)

# Normalisation constants. Observation values are clipped to [0, 1].
Q_SCALE = 20.0   # halting vehicles per direction group
V_SCALE = 30.0   # vehicles per direction group
W_SCALE = 60.0   # average waiting time per vehicle (s)
S_SCALE = 15.0   # average speed (m/s)

# Reward: r = -(ALPHA * queue_hat + BETA * wait_hat)
ALPHA, BETA = 1.0, 0.5

# Reward v2 ("total_wait"): r = -(queue / (2 * Q_SCALE) + total_wait / TOTAL_WAIT_SCALE),
# using the same queue and total waiting time (sum over all incoming lanes) that evaluate.py reports.
TOTAL_WAIT_SCALE = 1000.0
REWARDS = ("avg_wait", "total_wait")   # "avg_wait" = reward v1

# ---------------------------------------------------------------------------------------------
# Maps. "simple_intersection" = SUMO/Map_Nga_tu (4-way, 2 phases, lane ids start with N/E/S/W).
# "o_cho_dua" = SUMO/O_cho_dua: only the main junction is controlled, as in the fixed-time and
# rule-based baselines (nhanh maianh); 4 green phases (SUMO phases 0, 2, 5, 7) in a fixed cycle,
# SWITCH = go to the next green phase of the cycle.
OCD_TLS = "joinedS_5707161152_6677677155_6677677160_6677677161_#2more"
MAPS = {
    "simple_intersection": {
        "scenarios": None, "tls_ids": None, "green_phases": None,
        # observation scales (queue / vehicles per group, wait per vehicle s), reward normalisers
        "scales": (Q_SCALE, V_SCALE, W_SCALE),
        "reward_queue_norm": 2 * Q_SCALE, "reward_wait_norm": TOTAL_WAIT_SCALE,
    },
    "o_cho_dua": {
        "scenarios": "scenarios_o_cho_dua.yaml", "tls_ids": [OCD_TLS], "green_phases": [0, 2, 5, 7],
        # Observation scales chosen so that, under the always-SWITCH reference policy, at most ~5% of the
        # steps clip in every scenario. evaluate.py suggested (q, v, w) = 20/21/103 (Low), 81/82/252 (High),
        # 76/77/256 (Imbalance); the largest values are used for all scenarios.
        "scales": (85.0, 85.0, 260.0),
        "reward_queue_norm": 100.0, "reward_wait_norm": 5000.0,
    },
}


def default_scales(map_name):
    return MAPS[map_name]["scales"]


def obs_names(map_name):
    if map_name == "simple_intersection":
        return list(OBS_NAMES)
    n = len(MAPS[map_name]["green_phases"])
    return ([f"queue_s{k}" for k in range(n)] + [f"vehicles_s{k}" for k in range(n)]
            + [f"wait_s{k}" for k in range(n)] + [f"speed_s{k}" for k in range(n)]
            + [f"stage_is_{k}" for k in range(n)] + ["in_transition", "elapsed_green"])

OBS_NAMES = [
    "queue_ns", "queue_ew", "vehicles_ns", "vehicles_ew",
    "wait_ns", "wait_ew", "speed_ns", "speed_ew",
    "phase_is_ns", "in_transition", "elapsed_green",
]


class TrafficEnv(gym.Env):
    # Single-intersection signal control. Action: 0 = KEEP, 1 = SWITCH.

    metadata = {"render_modes": []}
    DEFAULT_SCALES = (Q_SCALE, V_SCALE, W_SCALE)

    def __init__(self, scenario="low", traffic_seeds=None, settings=None, reward="total_wait",
                 scales=None, map_name="simple_intersection"):
        super().__init__()
        if reward not in REWARDS:
            raise ValueError(f"reward must be one of {REWARDS}")
        if map_name not in MAPS:
            raise ValueError(f"map must be one of {tuple(MAPS)}")
        self.map_name = map_name
        cfg = MAPS[map_name]
        self.reward_mode = reward
        self._q_norm, self._w_norm = cfg["reward_queue_norm"], cfg["reward_wait_norm"]
        self.obs_names = obs_names(map_name)
        # Observation scales (queue per group, vehicles per group, wait per vehicle).
        # A feature above its scale is clipped to 1, so use larger scales for heavy traffic.
        q, v, w = scales if scales else cfg["scales"]
        self.scales = {"q_scale": float(q), "v_scale": float(v), "w_scale": float(w)}
        self.scenario = scenario
        self.traffic_seeds = list(traffic_seeds) if traffic_seeds else None
        if cfg["scenarios"] is None:
            self._env = Environment(settings=settings)
        else:
            self._green_phases = list(cfg["green_phases"])
            self._env = Environment(
                scenarios_path=ROOT / "TraCI" / "configs" / cfg["scenarios"], settings=settings,
                tls_ids=list(cfg["tls_ids"]), green_phases_by_tls={cfg["tls_ids"][0]: self._green_phases})
        self.settings = self._env.settings
        self.max_green = float(self.settings["max_green"])
        self.min_green = float(self.settings["min_green"])
        self.observation_space = spaces.Box(0.0, 1.0, shape=(len(self.obs_names),), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self._tls = None
        self.n_groups = 2 if map_name == "simple_intersection" else len(cfg["green_phases"])

    # ---------------------------------------------------------------- helpers
    def _build_groups(self):
        if self.map_name != "simple_intersection":
            return self._build_stages()
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

    def _build_stages(self):
        """Incoming lanes served by each green phase (O Cho Dua), from the signal program."""
        api = self._env.connection.trafficlight
        links = api.getControlledLinks(self._tls)
        logic = next(p for p in api.getAllProgramLogics(self._tls) if p.programID == api.getProgram(self._tls))
        self._stage_lanes = []
        for ph in self._green_phases:
            st = logic.phases[ph].state
            lanes = list(dict.fromkeys(links[i][0][0] for i, c in enumerate(st) if c in "Gg" and links[i]))
            if not lanes:
                raise ValueError(f"green phase {ph} serves no incoming lane")
            self._stage_lanes.append(lanes)

    @staticmethod
    def _agg_lanes(lanes, ids):
        sel = [lanes[i] for i in ids if i in lanes]
        veh = sum(v["vehicle_count"] for v in sel)
        halt = sum(v["halting_count"] for v in sel)
        wait = sum(v["waiting_time"] or 0.0 for v in sel)
        speed = sum((v["average_speed"] or 0.0) * v["vehicle_count"] for v in sel)
        return veh, halt, (wait / veh if veh else 0.0), (speed / veh if veh else 0.0)

    def _obs_stages(self, state):
        t = state["tls"][self._tls]
        if t["phase_id"] in self._green_phases:       # during yellow/all-red keep the last green stage
            self._last_stage = self._green_phases.index(t["phase_id"])
        agg = [self._agg_lanes(t["lanes"], ids) for ids in self._stage_lanes]
        qs, vs, ws = self.scales["q_scale"], self.scales["v_scale"], self.scales["w_scale"]
        obs = np.array(
            [a[1] / qs for a in agg] + [a[0] / vs for a in agg] + [a[2] / ws for a in agg]
            + [a[3] / S_SCALE for a in agg]
            + [float(k == self._last_stage) for k in range(len(agg))]
            + [float(t["in_transition"]), t["green_elapsed"] / self.max_green], dtype=np.float32)
        self.last_raw = obs.copy()
        self.last_clipped = obs > 1.0
        return np.clip(obs, 0.0, 1.0)

    def _totals(self, state):
        """(queue, total waiting time) over all incoming lanes, same definition as the
        fixed-time / rule-based logs: sum of halting vehicles and sum of lane waiting times."""
        tot = state["tls"][self._tls]["totals"]
        return float(tot["halting_count"]), float(tot["waiting_time"] or 0.0)

    def _obs(self, state):
        if self.map_name != "simple_intersection":
            return self._obs_stages(state)
        t = state["tls"][self._tls]
        ns = self._aggregate(t["lanes"], "NS")
        ew = self._aggregate(t["lanes"], "EW")
        ps = t["phase_state"]
        ns_green = any(ps[i] in "Gg" for i in self._ns_links)
        ew_green = any(ps[i] in "Gg" for i in self._ew_links)
        if ns_green != ew_green:          # during yellow/all-red keep the last green
            self._last_ns = ns_green
        qs, vs, ws = self.scales["q_scale"], self.scales["v_scale"], self.scales["w_scale"]
        obs = np.array([
            ns[1] / qs, ew[1] / qs,
            ns[0] / vs, ew[0] / vs,
            ns[2] / ws, ew[2] / ws,
            ns[3] / S_SCALE, ew[3] / S_SCALE,
            float(self._last_ns), float(t["in_transition"]),
            t["green_elapsed"] / self.max_green,
        ], dtype=np.float32)
        self.last_raw = obs.copy()          # before clipping (diagnostic)
        self.last_clipped = obs > 1.0      # features saturated at 1 (diagnostic)
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
        if self.map_name != "simple_intersection":
            ph = state["tls"][self._tls]["phase_id"]
            self._last_stage = self._green_phases.index(ph) if ph in self._green_phases else 0
        queue, total_wait = self._totals(state)
        return self._obs(state), {"sumo_seed": sumo_seed,
                                  "total_queue": queue, "total_wait": total_wait}

    def step(self, action):
        state, terminated, truncated, info = self._env.step(ACTIONS[int(action)])
        t = state["tls"][self._tls]
        queue, total_wait = self._totals(state)
        if self.map_name == "simple_intersection":
            ns = self._aggregate(t["lanes"], "NS")
            ew = self._aggregate(t["lanes"], "EW")
            veh, halt = ns[0] + ew[0], ns[1] + ew[1]
            avg_wait = (ns[0] * ns[2] + ew[0] * ew[2]) / veh if veh else 0.0
        else:   # lanes can belong to several stages, so use the junction totals
            veh, halt = t["totals"]["vehicle_count"], t["totals"]["halting_count"]
            avg_wait = total_wait / veh if veh else 0.0
        obs = self._obs(state)   # compute first so that last_clipped / last_raw belong to this observation
        if self.reward_mode == "total_wait":
            reward = -(queue / self._q_norm + total_wait / self._w_norm)
        else:   # v1
            reward = -(ALPHA * halt / self._q_norm + BETA * avg_wait / W_SCALE)
        out = {
            "total_queue": queue,
            "total_wait": total_wait,
            "halting": halt,
            "clipped": self.last_clipped.tolist(),
            "raw": self.last_raw.tolist(),
            "avg_wait": avg_wait,
            "executed_action": info["executed_action"][self._tls],
            "sim_time": info["sim_time"],
            "end_reason": info["end_reason"],
        }
        return obs, float(reward), bool(terminated), bool(truncated), out

    def close(self):
        self._env.close()
