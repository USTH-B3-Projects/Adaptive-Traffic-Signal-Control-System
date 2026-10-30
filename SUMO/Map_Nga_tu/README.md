# Synthetic intersection map

This map is independent of `O_cho_dua`. It runs in SUMO without an external TraCI controller.

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
| Demand rate | 180 vehicles/hour/approach, 720 vehicles/hour total |
| Vehicle mix | 80% motorcycles, 17% cars, 3% buses |
| Turning split | 60% straight, 20% left, 20% right |
| Demand | 36 flows with staggered start times |
| Generation / simulation end | Generation before 3600 s; simulation ends at 3720 s, including 120 s to clear traffic |
| Time step / seed | 0.1 s / 42 |
| Car following / lane changing | Krauss / SL2015, lateral resolution 0.325 m |

Lane 0 is on the right and lane 1 on the left in the direction of travel. Right turns use lane 0, left turns use lane 1, and straight movements can cross the junction in either lane. Straight-going motorcycles start in lane 1; cars and buses start in lane 0. Both lanes allow all three vehicle classes, with lane changes when safe. Motorcycles can move laterally and queue side by side within a lane. Vehicles depart from rest.

The fixed signal at `J` uses program `test`, with a **114 s** cycle:

| Stage | Green | Yellow | All-red |
|---|---:|---:|---:|
| North–South straight/right | 30 s | 3 s | 3 s |
| North–South protected left | 15 s | 3 s | 3 s |
| East–West straight/right | 30 s | 3 s | 3 s |
| East–West protected left | 15 s | 3 s | 3 s |

During the first 3 s of each green stage, conditional right turns outside the priority stream remain closed. Afterward, straight/right stages allow conditional right turns from the other axis; left-turn stages allow them from all four approaches. Signal `s` requires a stop of at least 1 s, followed by yielding to conflicting traffic and proceeding only when safe. Conditional right turns are closed during yellow and all-red stages. This is a modeling assumption, not a rule for every real intersection.

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
python -B build_inputs.py --duration 3600 --rate 180
netconvert --node-files network/intersection.nod.xml --edge-files network/intersection.edg.xml --connection-files network/intersection.con.xml --no-turnarounds true --output-file network/intersection.net.xml
python -B validate.py
python -B validate.py --diagnostic
```

The generator **overwrites the inputs it generates** and does not compile `.net.xml`. If only demand changes, the existing network can be reused; geometry or connection changes require `netconvert`. Signals load separately from `config/traffic_light.add.xml`; do not embed a duplicate program using `--tllogic-files`.

`--rate` is per approach; `--duration` is the generation cutoff. The main simulation ends at `duration + 120`. Both values must be finite and positive, and duration must exceed the last staggered start time. Vehicle and turning shares are defined in the generator's `type_weights` and `turn_weights`.

The validator checks the network, lanes, signal phases, routes, lane changes, vehicle body clearance, stopping/yielding, arrivals, collisions, teleports, and warnings. Do not use `python -O`, because validation uses `assert`. `--continuous` aliases the main mode; `--output-dir validation/lan_chay_1` selects an output directory within the map. Results include `results.txt`, logs, and XML; diagnostic files use the `movement_` prefix. The `validation/` directory can be removed after inspection and will be recreated when needed.

The diagnostic runs **40 vehicles over 360 s**: 36 approach/vehicle-type/movement combinations and four motorcycles testing bus overtaking from lane 0 to lane 1. Departures are scheduled from 0 to 27 s. Times in this document are simulation times; the GUI has a display delay of 60 ms per step.

## Results and limitations

After cleanup, SUMO 1.27.1 completed **720/720 vehicles** in the main simulation and **40/40 vehicles** in the diagnostic, with no warnings, collisions, or teleports. Simulation input contents were preserved.

Parameters have not been calibrated against field observations. Adaptive signals and time-varying demand are not modeled. Default results do not guarantee performance at every density or seed. High demand may require more clearance time; low demand may omit combinations required by the validator. Update validator expectations when changing the model. Road vehicle body checks use rectangles; safety on curved junction paths relies on SUMO and does not replace real-world swept-path analysis. GUI rendering was not visually checked during this cleanup.
