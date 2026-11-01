# Synthetic intersection map

This map is independent of `O_cho_dua`. It runs in SUMO without an external TraCI controller.

Generated validation logs and old experiment results have been removed. The
historical measurements below are retained as notes; their output files are no
longer included. Validation commands recreate their own `validation/` outputs.
For normal use, open the `.bat` inside the desired `Map_Low`, `Map_Medium`,
`Map_High`, or `Map_Imbalance` directory. Python scripts are only needed for
regeneration or checks.

## Run the full map

1. Install Eclipse SUMO and add its `bin` directory to `PATH` (tested with SUMO 1.27.1).
2. Double-click **`run.bat`**. The GUI opens and automatically starts the main simulation.
3. Pause or adjust playback speed in the GUI; close the window to exit.

Inputs are included, so Python and input regeneration are not required to run the map. The launcher works from other directories, leaves inputs unchanged, and keeps error messages visible if startup fails. If `sumo-gui` is not recognized, check `PATH` and reopen the terminal.

From PowerShell in `Map_Nga_tu`:

```powershell
.\run.bat
# Run the full simulation without the GUI:
sumo -c config/intersection.sumocfg
# Run the separate diagnostic, rather than the main simulation:
sumo-gui -c config/movement_test.sumocfg --start
```

## Traffic flow

Four approaches, North (`N`), East (`E`), South (`S`), and West (`W`), connect to junction `J`. Each approach has two inbound and two outbound lanes; each lane is 250 m long and 3.25 m wide. There are 12 routes: straight, left, and right from each approach. U-turns and pedestrians are not modeled.

| Parameter | Default |
|---|---|
| Demand rate | 360 vehicles/hour/approach, 1440 vehicles/hour total |
| Vehicle mix | 80% motorcycles, 17% cars, 3% buses |
| Turning split | 60% straight, 20% left, 20% right |
| Demand | 36 flows with staggered start times |
| Generation / simulation end | Generation before 3600 s; simulation ends at 3720 s, including 120 s to clear traffic |
| Time step / seed | 0.1 s / 42 |
| Car following / lane changing | Krauss / SL2015, lateral resolution 0.325 m |

Lane 0 is on the right and lane 1 on the left in the direction of travel. Right turns use lane 0, left turns use lane 1, and straight movements can cross the junction in either lane. Straight-going motorcycles start in right lane 0; cars and buses start in left lane 1.
Motorcycles retain a keep-right preference (`lcKeepRight=1`); cars/buses disable
that preference (`lcKeepRight=0`). All classes can change lanes for speed gain,
cooperation and routing when safe. This is a soft departure preference, not a
calibrated guarantee of a fixed lane-occupancy percentage. Both lanes allow all three vehicle classes, with lane changes when safe. Motorcycles can move laterally and queue side by side within a lane. Vehicles depart from rest.

The fixed signal at `J` uses program `test`, with a **114 s** cycle:

| Stage | Green | Yellow | All-red |
|---|---:|---:|---:|
| North?South, all movements | 51 s | 3 s | 3 s |
| East?West, all movements | 51 s | 3 s | 3 s |

Each approach uses a shared green interval for straight, right and left turns.
Left turns use permissive green (`g`) and yield to oncoming straight/right traffic;
through/right movements have priority green (`G`). There is no protected left-turn
phase. Lane 1 is shared by straight and left movements, lane 0 by straight and right.
Both through lanes remain available; the network and its existing connections are unchanged.
SUMO gap acceptance and the existing sublane model govern movement; vehicles do
not gain permission to force their way through conflicting traffic.

During the first 3 s of green, conditional right turns on the other axis remain
closed. Afterward they use `s`: stop at least 1 s, yield, then proceed when safe.
These turns close during yellow and all-red. Sublane guide lines are hidden in the GUI.

## Structure

```text
Map_Nga_tu/
  run.bat                 Run the full main simulation
  build_inputs.py         Generate inputs and configurations
  validate.py             Validate the main simulation or diagnostic
  network/                Compiled network and node/edge/connection sources
  routes/                 36 main flows and a separate 40-vehicle diagnostic
  config/                 Two sumocfg files, signals, scenery, and GUI settings
  validation/             Generated validation output; not needed to run the map
```

`run.bat` → `config/intersection.sumocfg` → `network/intersection.net.xml`, `routes/test_routes.rou.xml`, signals, scenery, and GUI settings. The diagnostic is not added to the main flows. Existing files support running, rebuilding, or validation and have been retained.

## Regenerate and validate

Requires Python 3.9+ and uses only the standard library. Run from the map directory:

```powershell
python -B build_inputs.py --duration 3600 --rate 360
netconvert --node-files network/intersection.nod.xml --edge-files network/intersection.edg.xml --connection-files network/intersection.con.xml --no-turnarounds true --output-file network/intersection.net.xml
python -B validate.py
python -B validate.py --diagnostic
```

The generator **overwrites the inputs it generates** and does not compile `.net.xml`. If only demand changes, the existing network can be reused; geometry or connection changes require `netconvert`. Signals load separately from `config/traffic_light.add.xml`; do not embed a duplicate program using `--tllogic-files`.

`--rate` is per approach; `--duration` is the generation cutoff. The main simulation ends at `duration + 120`. Both values must be finite and positive, and duration must exceed the last staggered start time. Vehicle and turning shares are defined in the generator's `type_weights` and `turn_weights`.

The validator checks the network, lanes, shared signal phases and yielding rules, routes, lane changes, vehicle body clearance, stopping/yielding, arrivals, collisions, teleports, and warnings. Do not use `python -O`, because validation uses `assert`. `--continuous` aliases the main mode; `--output-dir validation/lan_chay_1` selects an output directory within the map. Results include `results.txt`, logs, and XML; diagnostic files use the `movement_` prefix. The `validation/` directory can be removed after inspection and will be recreated when needed.

The diagnostic runs **40 vehicles over 360 s**: 36 approach/vehicle-type/movement combinations and four motorcycles testing bus overtaking from lane 0 to lane 1. Departures are scheduled from 0 to 27 s. Times in this document are simulation times; the GUI has a display delay of 60 ms per step.

## Results and limitations

Before the shared-green signal update, SUMO 1.27.1 completed **720/720 vehicles** in the main simulation and **40/40 vehicles** in the diagnostic, with no warnings, collisions, or teleports. Simulation input contents were preserved.

Parameters have not been calibrated against field observations. Adaptive signals and time-varying demand are not modeled. Those historical results do not validate the current signal program. High demand may require more clearance time; low demand may omit combinations required by the validator. Update validator expectations when changing the model. Road vehicle body checks use rectangles; safety on curved junction paths relies on SUMO and does not replace real-world swept-path analysis. GUI rendering was not visually checked during this cleanup.

## H4 demand scenarios

The existing `Map_Nga_tu` directory is the H4 map; no `Map_H4` copy is needed.
`generate_scenarios.py` creates `Map_Low`, `Map_Medium`, `Map_High`, and
`Map_Imbalance`, each containing `traffic.rou.xml`, `simulation.sumocfg`, and a matching `.bat` launcher.
All reference the original `../network/intersection.net.xml` and existing signal,
scenery, and GUI files using relative paths. Original demand inputs and launchers remain unchanged; the shared signal file
now uses permissive left turns for every configuration.

From the repository root:

```powershell
python -B SUMO/Map_Nga_tu/generate_scenarios.py
# Change the seed consistently for all four scenarios:
python -B SUMO/Map_Nga_tu/generate_scenarios.py --seed 123
# Regenerate with seed 42 and run all four, retaining logs and summary XML:
python -B SUMO/Map_Nga_tu/generate_scenarios.py --seed 42 --validate
sumo -c SUMO/Map_Nga_tu/Map_Low/simulation.sumocfg
sumo -c SUMO/Map_Nga_tu/Map_Medium/simulation.sumocfg
sumo -c SUMO/Map_Nga_tu/Map_High/simulation.sumocfg
sumo -c SUMO/Map_Nga_tu/Map_Imbalance/simulation.sumocfg
```

Edit only `SCENARIOS` in the generator to change demand (vehicles/hour entering
from each direction). These are experimental settings, not field measurements.

| Scenario | North | South | East | West | Total veh/h |
|---|---:|---:|---:|---:|---:|
| Map_Low | 300 | 300 | 300 | 300 | 1200 |
| Map_Medium | 750 | 750 | 750 | 750 | 3000 |
| Map_High | 1350 | 1350 | 1350 | 1350 | 5400 |
| Map_Imbalance | 1800 | 1800 | 300 | 300 | 4200 |

### Topology and generation

Incoming edges are `N_in`, `S_in`, `E_in`, `W_in`; outgoing edges are
`N_out`, `S_out`, `E_out`, `W_out`. Each has two unrestricted 250 m lanes,
3.25 m wide, speed limit 13.9 m/s. Coordinates confirm the direction labels.
Connections at signal junction `J` support all 12 movements:

| Incoming | Straight | Left | Right |
|---|---|---|---|
| N_in | S_out | E_out | W_out |
| S_in | N_out | W_out | E_out |
| E_in | W_out | S_out | N_out |
| W_in | E_out | N_out | S_out |

Straight uses either lane, left lane 1, right lane 0. No U-turns.
No redistribution is necessary: 70% straight, 15% left, 15% right everywhere.
The generator reads destinations and lane connections from the compiled network
and checks them against vehicle-class permissions before writing files.
It copies the baseline vType attributes, including updated lane preferences, and the 80% motorcycle,
17% car, 3% bus composition in expectation, including departure-lane conventions.

There are 36 independent Bernoulli flows, one per direction/type/turn, all active
on [0, 3600). Each has probability `direction_rate * type_share * turn_share / 3600`
per second. Summing these preserves each direction's exact configured rate in
expectation; realized counts and realized turning/type shares vary with the seed.
This uses SUMO's native stochastic flows, rather than periodic or staggered flows:
https://sumo.dlr.de/docs/Simulation/Randomness.html
The SUMO seed controls arrivals and vehicle behavior; route XML itself is deterministic.
Reproducibility assumes the same SUMO version, inputs, and seed. Probability values
above 1 are rejected. Missing movements fail validation rather than silently changing demand.

All scenarios start at 0, end at 3600, use step length 0.1 s and default seed 42.
The smaller timestep smooths GUI movement while preserving vehicle parameters;
the GUI retains its existing 60 ms delay per step (about 1.67 simulated seconds
per real second, subject to rendering speed).
The existing additional signal program `test` remains active: 114 s cycle,
51 s shared green per axis, each with 3 s yellow and 3 s all-red. Left turns
yield to oncoming traffic; initial-green and conditional right-turn behavior remain.
The network also contains embedded program `0`; the existing additional file
loads `test`, as in the original simulation. No controllers are implemented.

### Executed validation and limitations

Python XML parsing, route connections, departure lanes, vehicle permissions,
per-direction expected demand sums, and all config input paths were checked.
SUMO 1.27.1 ran all scenarios to 3600 seconds with seed 42, exit code 0,
no invalid edges/disconnected routes/load errors. No teleports occurred; all four scenarios reported collisions.
The table below reflects the shared-green program and updated vehicle lane preferences.
Logs and per-step summaries are in `validation/scenarios/` (regenerable).
The final summary entry is time 3599.90, representing the last 0.1 s step before end 3600.

| Scenario | Inserted | Completed | Waiting to depart | Remaining | Collision events | Teleports | Warnings | Errors |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Map_Low | 1238 | 1221 | 1 | 17 | 5 | 0 | 10 | 0 |
| Map_Medium | 2958 | 2909 | 1 | 49 | 28 | 0 | 55 | 0 |
| Map_High | 5408 | 5261 | 1 | 147 | 40 | 0 | 100 | 0 |
| Map_Imbalance | 4187 | 3991 | 1 | 196 | 28 | 0 | 77 | 0 |

The timestep was reduced from 1 s to 0.1 s to smooth vehicle movement, as requested.
This also removes the former mismatch between motorcycle `tau=0.6` and the
simulation timestep. Demand rates and the sublane model remain unchanged. Vehicle lane preferences
now put straight-going motorcycles on the right and cars/buses on the left.
Signals now use the shared permissive-left program described above. Stochastic arrival counts can change with the
timestep even at the same seed; demand rates remain unchanged in expectation.
Warnings, if present, must still be reviewed before controller comparisons.
Collision counts are events, not unique vehicles; `collision.action=warn` is preserved.

Demand was initially increased by 1.5 times and then doubled again across all
four scenarios. The busiest direction now has 1260 straight, 270 left and 270
right vehicles/hour. Baseline demand was also doubled to 360 veh/h/approach. However lane assignments,
signal green fractions and the motorcycle mix determine effective capacity;
no calibrated saturation-flow estimate is available. Each scenario had one vehicle waiting to depart at the cutoff, but collision warnings prevent claiming
physically reliable capacity. Remaining vehicles are expected with arrivals
continuing until the simulation cutoff; no clearance period is added.

The original network SHA-256 before and after generation/runtime validation is
`f257a1eca18e664267ade266fd17d1628634e150b85da24c2c399cfd8d7217d8`.
The generator overwrites only its eight scenario inputs; `--validate` additionally
overwrites its named logs/summaries. Do not run Python with `-O`: its static
self-checks use assertions. The original `validate.py` targets the original
baseline demand and is not the validator for these scenarios.

Double-click `Map_Low/Map_Low.bat`, `Map_Medium/Map_Medium.bat`,
`Map_High/Map_High.bat`, or `Map_Imbalance/Map_Imbalance.bat` to open
and start that scenario in SUMO GUI. SUMO `bin` must be on `PATH`.
Launchers work from any working directory and pause on startup errors.

Shared-green verification: topology, 114 s phase cycle, priority-conflict and
left-turn yielding assertions were executed. SUMO also ran the original simulation
and the 40-vehicle diagnostic; current results are recorded in their logs. The full
FCD/body-clearance validator was not rerun; runtime warnings mean safety validation
is not clean. Signal details: https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html

Lane-preference update: straight flows start motorcycles in lane 0 and cars/buses
in lane 1. Turning flows keep the connection-required lane. The finite diagnostic
retains explicit lane exceptions to test motorcycle overtaking in both lanes.
These preferences are experimental and have not been calibrated to Vietnamese
field data. Cars/buses can move right when beneficial but have no enforced
keep-left return rule; persistent lane occupancy was not measured.

After the lane-preference update, both original/diagnostic runs exited 0 with
zero warnings. All four scenarios exited 0 with no route errors; collision
warnings remain. Departure-lane and keep-right assertions passed for all flows.

### Left-turn gap acceptance

Left-turn flows/diagnostic vehicles now use `motorcycle_left`, `car_left`, and
`bus_left` variants. They retain their original physical and lane-change parameters,
with only `impatience="0.3"` changed from `off`. Straight/right vehicles retain `off`.
This is still three physical vehicle classes with the same composition and demand.
SUMO can accept a smaller collision-avoiding gap that causes priority traffic to
slow. Impatience grows with waiting under SUMO's default 180 s growth setting.
The minimum junction time gap, conflict checks, signals and network are unchanged;
foe-ignoring and red-light violations are not enabled.

This approximates assertive gap acceptance; it does not create free-form lateral
weaving through the junction beyond SUMO's existing connection paths. It is not a
calibrated Hanoi driving model. See SUMO's documented impatience semantics:
https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#impatience

Executed baseline A/B test (same seed, only left-turn impatience changed): both
completed 143 left turns, mean waiting 17.24 s before and 17.20 s after. This is a
small change at baseline demand, not evidence of a large throughput improvement.
FCD inspection of the updated run found 14/143 left-turn entries while an opposing
straight vehicle was moving above 2 m/s in the last 50 m of its approach; this
confirms turns occur before the entire opposing approach empties, not that each
entry forced an opposing vehicle to brake. Baseline and diagnostic runs reported
zero warnings. All four demand scenarios also completed with exit 0; their current
warnings/collisions are recorded above. Full body-clearance validation and visual
GUI inspection were not executed for this change.

### Rejected maximum-assertiveness experiment

A follow-up request asked left turns to force their way through while retaining
safety. Temporary route files tested `impatience=1` for left-turn variants only;
all other simulation inputs and seeds were identical. The experiment was not
applied to the scenario inputs because collision counts increased.

| Scenario | Collisions at 0.3 | Collisions at 1 | Emergency braking at 0.3 | Emergency braking at 1 |
|---|---:|---:|---:|---:|
| Map_Low | 2 | 3 | 2 | 2 |
| Map_Medium | 9 | 9 | 5 | 8 |
| Map_High | 22 | 23 | 24 | 27 |
| Map_Imbalance | 24 | 28 | 20 | 21 |

Results are retained in `validation/scenarios/left_turn_comparison.json`.
SUMO documents that maximum impatience can demand hard braking from priority
traffic; enabling it is not evidence of collision-free operation in this map.
The active left-turn setting remains 0.3, with its previously reported collision
warnings. No claim of guaranteed safety is made. A screenshot of apparent empty
space cannot establish a safe crossing gap: approach speed, both oncoming lanes,
vehicle length, the crossing trajectory and exit space also matter.

A second temporary candidate combined impatience 1 with `jmExtraGap=1 m`
and `jmTimegapMinor=1.5 s`. Collision counts were Map_Low: 3, Map_Medium: 7, Map_High: 28, Map_Imbalance: 21.
It was also rejected: Low and High exceeded the active baseline counts.
Results: `validation/scenarios/left_turn_buffered_comparison.json`.

### Straight traffic yields more to vehicles already crossing

Straight movements now use `motorcycle_straight`, `car_straight`, and
`bus_straight` variants. Only these variants set `jmAdvance=0` and `jmExtraGap=1 m`.
When SUMO recognizes a crossing foe already inside the junction, straight traffic
waits until that foe has passed the conflict point rather than advancing toward
it, and keeps an extra clearance distance. This responds to an existing crossing
conflict, not merely to a left-turn indicator or a vehicle waiting to turn.
The variants preserve base dimensions, car following, lane preferences, and
`impatience=off`. Right-turn behavior and left-turn `impatience=0.3` remain unchanged.
There are still three physical vehicle classes with the same demand shares.

The network, conflict masks, shared green program, timestep and demand are unchanged.
This does not reverse static priority for vehicles still approaching the junction,
and does not guarantee a left-turning vehicle will be allowed to enter first.
Source: https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#junction-model-parameters

The original and diagnostic SUMO runs completed with zero warnings. Static checks
verified that only straight movements receive the two new settings. Full GUI and
body-clearance inspection have not been executed for this change.

Straight-yield trial, seed 42: all four scenarios ran to 3600 s with exit 0 and
no teleports. Collision events before -> after: Low 2 -> 2, Medium 9 -> 6,
High 22 -> 23, Imbalance 24 -> 17. The result is mixed, not a safety validation;
the requested yielding trial is active, but High has one more collision event.
The main results table reflects these current inputs. Earlier experiments above
are historical comparisons, not the current vehicle-type configuration.

The latest demand update doubles the current baseline and all four scenarios.
The fixed 40-vehicle movement diagnostic is unchanged: it checks coverage, not
traffic demand. Prior experiments and their counts above are historical.

At doubled demand, all four scenarios completed to 3600 s with exit 0 and
zero teleports, but collision/emergency-braking warnings remain. The current
results table above was refreshed. The baseline run completed 1441 inserted
vehicles by 3720 s with none remaining/waiting, 5 collision events and 27 warnings.
Its periodic flow boundary rounding can differ from the expected 1440.
