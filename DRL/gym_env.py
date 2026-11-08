"""Gymnasium wrapper around the repository's TraCI environment."""
from collections.abc import Mapping

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from .core.environment import Environment


class TrafficSignalEnv(gym.Env):
    """Single-agent environment controlling all traffic lights together."""

    metadata = {"render_modes": []}

    def __init__(self, scenario: str = "low"):
        super().__init__()
        self.scenario = scenario
        self._environment = Environment()
        self._tls_ids: tuple[str, ...] = ()
        self._expected_tls_count = 1
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(
            low=0.0,
            high=np.inf,
            shape=(6 * self._expected_tls_count,),
            dtype=np.float32,
        )

    def _observation(self, state: Mapping) -> np.ndarray:
        values = []
        for tls_id in self._tls_ids:
            totals = state["tls"][tls_id]["totals"]
            values.extend(
                (
                    totals["halting_count"],
                    totals["waiting_time"] or 0.0,
                    totals["average_speed"] or 0.0,
                    totals["vehicle_count"],
                    state["tls"][tls_id]["phase_id"],
                    state["tls"][tls_id]["green_elapsed"],
                )
            )
        return np.asarray(values, dtype=np.float32)

    def _reward(self, state: Mapping) -> float:
        queue = 0.0
        waiting = 0.0
        for tls in state["tls"].values():
            queue += tls["totals"]["halting_count"]
            waiting += tls["totals"]["waiting_time"] or 0.0
        return -(queue + 0.1 * waiting)

    def reset(self, *, seed: int | None = None, options=None):
        super().reset(seed=seed)
        state = self._environment.reset(
            self.scenario, seed=int(self.np_random.integers(0, 2**31 - 1))
        )
        self._tls_ids = tuple(sorted(state["tls"]))
        if len(self._tls_ids) != self._expected_tls_count:
            raise RuntimeError(
                f"Expected {self._expected_tls_count} traffic light, "
                f"found {len(self._tls_ids)}."
            )
        self.observation_space = spaces.Box(
            low=0.0, high=np.inf, shape=(6 * len(self._tls_ids),), dtype=np.float32
        )
        return self._observation(state), {"scenario": self.scenario}

    def step(self, action: int):
        if not self._tls_ids:
            raise RuntimeError("Call reset before step.")
        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action: {action}")
        state, terminated, truncated, info = self._environment.step(
            "SWITCH" if action else "KEEP"
        )
        info["queue_length"] = sum(
            tls["totals"]["halting_count"] for tls in state["tls"].values()
        )
        info["waiting_time"] = sum(
            tls["totals"]["waiting_time"] or 0.0 for tls in state["tls"].values()
        )
        vehicles = sum(
            tls["totals"]["vehicle_count"] for tls in state["tls"].values()
        )
        speed_weight = sum(
            (tls["totals"]["average_speed"] or 0.0) * tls["totals"]["vehicle_count"]
            for tls in state["tls"].values()
        )
        info["average_speed"] = speed_weight / vehicles if vehicles else 0.0
        return self._observation(state), self._reward(state), terminated, truncated, info

    def close(self):
        self._environment.close()
