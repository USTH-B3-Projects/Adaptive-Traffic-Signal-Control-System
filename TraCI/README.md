# SUMO Bridge for LLM and DRL Controllers

This package connects an external controller to SUMO. It starts SUMO, reads traffic measurements into a Python dictionary, accepts an action, and executes signal changes under the configured timing constraints.

Your integration program supplies the LLM or DRL model. It owns model loading, prompts, observation encoding, reward calculation, training, and any result storage.

## How the connection works

```text
SUMO --> TraCI library --> Environment.reset()/step() --> state --> Your model
SUMO <-- TraCI library <-- SignalController          <-- action <-- Your model
```

`Environment` is a class defined by this project in `core/environment.py`. The lowercase `traci` package is SUMO's Python communication library. The project's `TraCI/` directory contains the bridge built on top of that library.

Your model interacts with `Environment`; it does not need to call the other modules directly or read files to make decisions.

## Requirements and setup

- Python 3.10 or later.
- Eclipse SUMO, including the `sumo` binary and optionally `sumo-gui`.
- PyYAML, listed in `requirements.txt`.
- A Python `traci` package compatible with your SUMO version.

Run from the repository root, which contains both `SUMO/` and `TraCI/`:

```powershell
python -m pip install -r TraCI/requirements.txt
$env:SUMO_HOME = 'D:\Sumo'  # Replace with your SUMO installation directory.
```

The bridge finds the binary through PATH or `SUMO_HOME/bin`. It first tries the installed Python `traci` module, then `SUMO_HOME/tools`. If necessary, install a matching `traci` package in your Python environment. An explicit binary can also be configured with `sumo_binary`.

## Connect your model

Place your integration script at the repository root, alongside `SUMO/` and `TraCI/`. Add the bridge directory to the Python import path:

```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "TraCI"))
from core.environment import Environment


def run_controller(choose_action):
    with Environment(settings={"gui": True}) as env:
        state = env.reset("low", seed=42)

        while True:
            action = choose_action(state)
            state, terminated, truncated, info = env.step(action)

            # Inspect info if you need to know which action actually ran.
            if terminated or truncated:
                break
```

After constructing your model in your integration script, call `run_controller(model.act)`. `choose_action` is an ordinary Python callable that accepts the state dictionary and returns one of the action formats below. The bridge does not provide or initialize `model`.

Set `gui=False` for headless simulation. `reset()` launches SUMO and loads the selected scenario, so you do not need to open the map separately. Your integration script is the entry point; this package has no standalone runner or built-in decision algorithm.

For an LLM, build the prompt from `state` and convert its response into a valid action before calling `step`. For DRL, encode `state` into the model's observation format and map its output to a valid action. Reward calculation belongs in the DRL integration. This is a project-specific API, not a Gymnasium environment.

## Public API

| Interface | Input | Result |
| --- | --- | --- |
| `Environment(config_path=None, scenarios_path=None, *, settings=None)` | Optional configuration paths and setting overrides | Bridge instance |
| `env.reset(scenario, seed=None)` | Scenario name and optional seed | Initial `state` dictionary |
| `env.step(action)` | Global action or mapping by TLS ID | `(state, terminated, truncated, info)` |
| `env.close()` | None | Closes the TraCI connection and SUMO process |

`config_path` defaults to `configs/traci.yaml`; `scenarios_path` defaults to `configs/scenarios.yaml`. Values passed in `settings` override the loaded configuration, for example:

```python
env = Environment(settings={"gui": False, "max_episode_seconds": 180})
```

Call `reset` before the first `step`. Each `step` advances at most `decision_interval` simulated seconds, using individual `simulation_step` increments. It may return sooner if the episode ends.

- `terminated=True`: no vehicles or future demand remain according to SUMO.
- `truncated=True`: the scenario's end time or `max_episode_seconds` limit has been reached.

The bridge closes SUMO when the episode ends or a reset/step operation fails. Call `reset` to start another episode. Repeated `close()` calls are safe. Use the context manager shown above, or `try/finally`, so SUMO is also closed if your model raises an exception.

## Action input

Accepted action values are the uppercase strings `KEEP` and `SWITCH`:

| Action | Meaning |
| --- | --- |
| `KEEP` | Continue the current green, subject to the maximum green limit |
| `SWITCH` | Request the next valid green stage through the existing transition phases |

A string applies to every TLS (traffic light system):

```python
state, terminated, truncated, info = env.step("SWITCH")
```

A mapping controls TLS IDs individually. Discover the IDs from the returned state:

```python
actions = {tls_id: "KEEP" for tls_id in state["tls"]}
selected_tls = next(iter(state["tls"]))
actions[selected_tls] = "SWITCH"

state, terminated, truncated, info = env.step(actions)
```

Missing IDs in a mapping default to `KEEP`. Unknown IDs and invalid action values raise an error. Arbitrary phase IDs and raw signal-state strings are not action inputs.

During yellow or all-red, a request for that TLS is ignored and reported as `NOOP`; it is not queued for the next green. Other TLSs can still receive actions independently.

## State output

`state` is a JSON-serializable Python dictionary passed directly in memory:

```text
state
  simulation_time                 Simulation time in seconds
  scenario                        Selected scenario name
  tls
    <tls_id>
      tls_id
      phase_id                    Index in the active SUMO program
      phase_state                 Original SUMO signal-state string
      green_elapsed               Seconds elapsed in the current green stage
      in_transition               True during yellow/all-red
      incoming_lane_ids           Unique incoming lanes controlled by this TLS
      lanes
        <lane_id>
          vehicle_count
          halting_count
          waiting_time
          average_speed
      totals
        vehicle_count
        halting_count
        waiting_time
        average_speed
```

| Metric | Definition and unit |
| --- | --- |
| `vehicle_count` | Number of vehicles on the lane during the last SUMO step |
| `halting_count` | Number of vehicles moving below 0.1 m/s; a vehicle count, not queue length in meters |
| `waiting_time` | Sum of the vehicles' current consecutive waiting times, in seconds; SUMO excludes intentional stops |
| `average_speed` | Mean speed in m/s; `None` when the lane is empty or the value is unavailable |

TLS totals sum vehicle counts, halting counts, and waiting times across unique incoming lanes at the same instant. TLS average speed is weighted by vehicle count. Unavailable continuous metrics are represented as `None` in Python (`null` in JSON); dependent totals are also unavailable.

Do not sum consecutive waiting-time snapshots and label the result total waiting time. Do not sum TLS totals to obtain network totals without checking for shared incoming lanes.

State is extracted at reset and at the end of each `step`. Last-step measurements describe the final SUMO step, not an average over the whole decision interval. `green_elapsed` is zero during yellow/all-red and continues across startup/main green phases belonging to the same stage.

## Execution feedback: `info`

The model proposes an action; signal timing rules determine what is executed. `info` provides:

| Field | Contents |
| --- | --- |
| `requested_action` | Requested action by TLS ID, including default KEEP values |
| `executed_action` | Executed action by TLS ID: KEEP, SWITCH, or NOOP |
| `override_reason` | Reason by TLS ID, or `None` if there was no override |
| `sim_time` | Simulation time after the step, in seconds |
| `phase_id` | Current phase index by TLS ID |
| `green_elapsed` | Current green elapsed time by TLS ID |
| `automatic_events` | Phase progression and forced switches occurring within this step, with timestamps |
| `end_reason` | `demand_exhausted`, `time_limit`, or `None` |

Override reasons include `startup_phase`, `min_green`, `max_green`, and `in_transition`. If a maximum-green override occurs inside a decision interval, the action summary reflects that override; `automatic_events` contains the exact transition time. Automatic phase-progression events use the reason `phase_progression`.

## Configuration and scenarios

`configs/scenarios.yaml` maps names to existing SUMO configurations:

| Name | SUMO configuration, relative to the repository root |
| --- | --- |
| `low` | `SUMO/Map_Nga_tu/Map_Low/simulation.sumocfg` |
| `medium` | `SUMO/Map_Nga_tu/Map_Medium/simulation.sumocfg` |
| `high` | `SUMO/Map_Nga_tu/Map_High/simulation.sumocfg` |
| `imbalance` | `SUMO/Map_Nga_tu/Map_Imbalance/simulation.sumocfg` |

The mapping file uses paths relative to its own directory. These scenarios reuse the original shared network and signal files. Network, route, and additional-file references are read from each `.sumocfg`; TLS and lane IDs are discovered through TraCI.

Defaults in `configs/traci.yaml`:

| Setting | Default | Meaning |
| --- | --- | --- |
| `simulation_step` | `1` | SUMO step length in simulated seconds |
| `decision_interval` | `5` | Maximum simulated duration of one `step()` call |
| `min_green` | `30` | Minimum green duration before a requested switch |
| `max_green` | `75` | Forced end of a green stage |
| `yellow_time` | `3` | Minimum duration of an existing yellow phase |
| `all_red_time` | `0` | Minimum duration of an existing all-red phase |
| `gui` | `false` | Use headless SUMO; set true for SUMO-GUI |
| `max_episode_seconds` | `null` | Optional episode duration cap, measured from scenario begin |
| `sumo_binary` | `null` | Optional binary name or path; relative paths in YAML use the YAML directory |
| `seed` | `null` | Optional seed; priority is reset argument, YAML, then scenario |

Time settings must be finite and align with `simulation_step`; `min_green` must not exceed `max_green`. Existing phase durations and offsets must also align with this time grid. Unknown settings are rejected.

## Signal execution rules

Signal safety checks run at every simulation step, even when the decision interval is longer. With the defaults, a green ends at 75 seconds even if decisions occur every 7 seconds.

The bridge supports sequential static programs with at least two green stages. Consecutive green phases with the same G/g movement pattern form one stage. Startup phase timing is preserved, and SWITCH follows the existing yellow and clearance sequence to the next green stage. The bridge never constructs a new green-state string.

The current scenarios include 3-second all-red phases. Those phases remain active even though `all_red_time` defaults to zero. Yellow/all-red settings can extend existing safety phases; they do not shorten them or create an additional all-red phase.

Unsupported programs, such as branched sequences, direct changes between green stages, mixed green/yellow phases, or conflicting protected greens from different incoming lanes, are rejected before signal control starts. Existing permissive `g` and `s` behavior remains governed by SUMO.

## Module connections

| File | Responsibility | Called by |
| --- | --- | --- |
| `core/environment.py` | Public reset/step/close API and decision loop | Your integration program |
| `core/simulation.py` | SUMO process and independent TraCI connection | Environment |
| `core/scenario_loader.py` | YAML/XML loading, input paths, and configuration validation | Environment and Simulation |
| `core/state_extractor.py` | Read and normalize incoming-lane and TLS measurements | Environment |
| `core/signal_controller.py` | Validate programs, track green timing, and execute phase changes | Environment |
| `configs/traci.yaml` | Operational settings | Scenario loader |
| `configs/scenarios.yaml` | Scenario-to-configuration mapping | Scenario loader |

`SignalController` executes timing rules; it is not the LLM/DRL decision algorithm. `core/__init__.py` marks the Python package, and `requirements.txt` lists the Python dependency.

Do not add `TraCI/__init__.py`: on Windows, that directory name can conflict with SUMO's lowercase `traci` package. Use the import setup shown above.

## Files, errors, and limitations

State and feedback are returned in memory. The bridge does not write JSONL, metadata, or log files, or create result directories. SUMO console messages, warnings, and errors appear in the launching terminal. Configurations requesting SUMO file outputs are rejected to protect the input tree.

Earlier `run.py`, smoke controllers, recording/output folders, and settings such as `mode`, `controller_name`, `output_root`, and `state_extraction_interval` have been removed. Existing integration programs must use the four-value `step()` return shown above. The bridge does not calculate or return a reward.

The existing vehicle model can produce collision warnings. In particular, the default 1-second step exceeds motorcycle `tau=0.6`. Signal-transition checks do not establish that the vehicle model is collision-free or calibrated for controller comparisons.

The reduced bridge was verified on 2026-11-03 using 23 checks in a disposable directory outside the repository: all passed, with no skips. Real SUMO ran all four scenarios for 90 seconds, covering timing, state, connection cleanup, and absence of generated files. All 49 SUMO input files retained their SHA-256 hashes. These are prior verification results; this documentation rewrite did not rerun them. A real LLM integration and visual GUI behavior have not been verified.
# TraCI smoke test

From the repository root, activate the `atsc` environment and run:

```cmd
python TraCI\test_connection.py --scenario low --steps 100
```

The script runs SUMO without the GUI and writes queue and basic traffic
metrics to `TraCI\outputs\queue_low.csv`. Use `--scenario medium`,
`--scenario high`, or `--scenario imbalance` to test another route set.

## PPO baseline

Run a short baseline from the repository root:

```cmd
python -m TraCI.train_baseline --scenario low --timesteps 10000
tensorboard --logdir runs
```

The policy uses two actions: `0` keeps the current signal stage and `1`
requests a safe switch. The reward is the negative sum of queue length and
`0.1` times lane waiting time.

## Evaluate four scenarios

After training a model, evaluate it on all four demand levels:

```cmd
python -m TraCI.evaluate --model models\ppo_low.zip --output-dir evaluation
```

This writes `metrics.csv` (one row per decision), `summary.csv` (scenario
means), and `comparison.png` (time-series comparison). The reported metrics
are queue length, waiting time, average speed, cumulative arrived vehicles,
and vehicles remaining in the network.
