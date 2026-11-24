"""V2: 12D directional normalized observations and scaled reward."""
import gymnasium as gym
import numpy as np
from gymnasium import spaces

from .core.environment import Environment
from .metrics import NS_LANES, EW_LANES, directional


class TrafficSignalEnv(gym.Env):
    metadata = {'render_modes': []}

    def __init__(self, scenario='low'):
        super().__init__()
        self.scenario = scenario
        self._sumo_seed = None
        self._environment = Environment()
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(0.0, 1.0, shape=(12,), dtype=np.float32)

    def _observation(self, state):
        tls = state['tls']['J']
        qn, nn, wn, vn = directional(tls['lanes'], NS_LANES)
        qe, ne, we, ve = directional(tls['lanes'], EW_LANES)
        phase, elapsed = tls['phase_id'], tls['green_elapsed']
        values = (qn/60.0, qe/60.0, nn/80.0, ne/80.0, wn/1500.0, we/1500.0,
                  vn/13.9, ve/13.9, float(phase in (0, 1)), float(phase in (4, 5)),
                  elapsed/75.0, float(not tls['in_transition'] and elapsed >= 15.0))
        return np.clip(np.asarray(values, dtype=np.float32), 0.0, 1.0)

    def _reward(self, state):
        lanes = state['tls']['J']['lanes']
        qn, _, wn, _ = directional(lanes, NS_LANES)
        qe, _, we, _ = directional(lanes, EW_LANES)
        raw_penalty = (qn + qe) + 0.05 * (wn + we) + 0.02 * ((qn - qe) ** 2)
        return float(np.clip(-raw_penalty / 100.0, -10.0, 0.0))

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        try:
            state = self._environment.reset(self.scenario, seed=seed)
            self._sumo_seed = seed
            if set(state['tls']) != {'J'}:
                raise ValueError('V2 requires the single J intersection with NS/EW lanes')
            return self._observation(state), {'scenario': self.scenario, 'sumo_seed': seed}
        except BaseException:
            self.close()
            raise

    def step(self, action):
        if not self.action_space.contains(action):
            raise ValueError(f'Invalid action: {action}')
        state, terminated, truncated, info = self._environment.step('SWITCH' if action else 'KEEP')
        totals = state['tls']['J']['totals']
        info.update(queue_length=totals['halting_count'],
                    waiting_time=totals['waiting_time'] or 0.0,
                    average_speed=totals['average_speed'] or 0.0,
                    scenario=self.scenario, sumo_seed=self._sumo_seed)
        return self._observation(state), self._reward(state), terminated, truncated, info

    def close(self):
        self._environment.close()
