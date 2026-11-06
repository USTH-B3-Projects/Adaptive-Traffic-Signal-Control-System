"""Decision-level API with signal safety enforced at every simulation step."""
from collections.abc import Mapping
import math
from pathlib import Path

from .scenario_loader import ScenarioLoader, load_settings, validate_settings
from .signal_controller import SignalController
from .simulation import Simulation
from .state_extractor import StateExtractor


class Environment:
    def __init__(self, config_path: Path | str | None = None,
                 scenarios_path: Path | str | None = None, *, settings: dict | None = None):
        self.settings = validate_settings(load_settings(config_path) | (settings or {}))
        self.loader = ScenarioLoader(scenarios_path)
        self.simulation = Simulation(self.settings)
        self.signals = None
        self._done = True

    @property
    def connection(self):
        return self.simulation.connection

    def reset(self, scenario: str, seed: int | None = None) -> dict:
        self.close()
        try:
            self.scenario = self.loader.load(scenario)
            actual_seed = seed if seed is not None else self.settings["seed"]
            if actual_seed is None:
                actual_seed = self.scenario.seed
            if actual_seed is not None and (
                isinstance(actual_seed, bool) or not isinstance(actual_seed, int)
                or not 0 <= actual_seed <= 2147483647
            ):
                raise ValueError("seed must be an integer in [0, 2147483647]")
            self._begin = self.scenario.begin
            limits = [v for v in (self.scenario.end,
                      self._begin + self.settings["max_episode_seconds"]
                      if self.settings["max_episode_seconds"] is not None else None) if v is not None]
            self._end = min(limits) if limits else None
            if self._end is not None:
                steps = (self._end - self._begin) / self.settings["simulation_step"]
                if steps <= 0 or not math.isclose(steps, round(steps), abs_tol=1e-8, rel_tol=0):
                    raise ValueError("Episode end must be after begin and align with simulation_step")
            connection = self.simulation.start(self.scenario, actual_seed)
            self.signals = SignalController(connection, self.settings)
            if not self.signals.tls_ids:
                raise ValueError("Scenario contains no traffic lights to control")
            self.extractor = StateExtractor(connection, self.signals)
            now = connection.simulation.getTime()
            self.signals.advance(now)
            self._state = self.extractor.extract(self.scenario.name, now)
            self._done = False
            return self._state
        except BaseException:
            self.close()
            raise

    def step(self, action: str | Mapping[str, str]) -> tuple[dict, bool, bool, dict]:
        if self._done or self.connection is None:
            raise RuntimeError("Call reset before step; the episode may already be finished")
        try:
            now = self.connection.simulation.getTime()
            if isinstance(action, str):
                actions = dict.fromkeys(self.signals.tls_ids, action)
            elif isinstance(action, Mapping):
                unknown = action.keys() - set(self.signals.tls_ids)
                if unknown:
                    raise ValueError(f"Unknown TLS IDs: {sorted(unknown)}")
                actions = {tls: action.get(tls, "KEEP") for tls in self.signals.tls_ids}
            else:
                raise ValueError("Action must be KEEP, SWITCH, or a mapping by TLS ID")
            decisions = self.signals.request(actions, now)
            deadline = now + self.settings["decision_interval"]
            if self._end is not None:
                deadline = min(deadline, self._end)
            automatic = []
            terminated = self.connection.simulation.getMinExpectedNumber() == 0
            truncated = False
            while not terminated and now < deadline - 1e-8:
                self.connection.simulationStep()
                now = self.connection.simulation.getTime()
                events = self.signals.advance(now)
                for event in events:
                    if event["override_reason"] == "max_green":
                        decisions[event["tls_id"]].update(
                            executed_action="SWITCH", override_reason="max_green")
                automatic.extend(events)
                terminated = self.connection.simulation.getMinExpectedNumber() == 0
                truncated = not terminated and self._end is not None and now >= self._end - 1e-8
                if terminated or truncated:
                    break
            self._state = self.extractor.extract(self.scenario.name, now)
            info = {
                key: {tls: decision[key] for tls, decision in decisions.items()}
                for key in ("requested_action", "executed_action", "override_reason")
            }
            info.update(
                sim_time=now,
                phase_id={tls: value["phase_id"] for tls, value in self._state["tls"].items()},
                green_elapsed={tls: value["green_elapsed"] for tls, value in self._state["tls"].items()},
                automatic_events=automatic,
                arrived_count=self.connection.simulation.getArrivedNumber(),
                vehicles_in_network=self.connection.vehicle.getIDCount(),
                end_reason="demand_exhausted" if terminated else "time_limit" if truncated else None,
            )
            state = self._state
            if terminated or truncated:
                self.close()
            return state, terminated, truncated, info
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        self._done = True
        self.simulation.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
