# O Cho Dua map

This OSM map of O Cho Dua is independent of `Map_Nga_tu`. Active files are directly in this directory, without the former dated subdirectory.

## Run the full map

1. Install Eclipse SUMO and add its `bin` directory to `PATH` (tested with SUMO 1.27.1).
2. Double-click **`run.bat`**. The GUI loads `osm.sumocfg` and automatically starts the full map.
3. Pause or adjust playback speed in the GUI; close the window to exit.

Python is not required to run the included inputs. The launcher works from other directories and does not regenerate demand. If startup fails, read the console message and check that `sumo-gui` is on `PATH`.

From PowerShell in `O_cho_dua`:

```powershell
.\run.bat
# Run without the GUI until all vehicles have finished:
sumo -c osm.sumocfg
```

Each run creates or overwrites `tripinfos.xml` (trips), `stats.xml` (statistics), and `edgeData.xml` (edge measurements) beside the configuration. Save any results you need before running again. The configuration has no explicit `end` time, so the simulation continues until all vehicles have finished.

## Traffic flow

There are 12 flows: straight, left, and right from four approaches, **Ton Duc Thang, Xa Dan, Nguyen Luong Bang, and O Cho Dua**. Vehicles enter at the network boundary, pass through the study junction's specified `via` edges, and leave at the boundary.

| Parameter | Default |
|---|---|
| Scenario / distribution | `medium` / `balanced` |
| Total demand | 1200 vehicles/hour, 300 vehicles/hour per approach |
| Turning split per approach | 50% straight, 25% left, 25% right |
| Expected network-wide vehicle mix | 80% motorcycles, 17% cars, 3% buses |
| Generation period | 0–3600 s, followed by traffic clearance |
| Time step / lateral resolution | 0.5 s / 0.4 m |
| Car following / lane changing | Krauss / SL2015 |
| Departure | Lane `best`, speed `max`, subject to SUMO safety constraints |

Motorcycles move laterally using SL2015; cars and buses prefer the lane center. The 12 m buses **only travel straight from Ton Duc Thang, Xa Dan, and O Cho Dua**. Nguyen Luong Bang and all turning streams contain only motorcycles/cars because an earlier trial encountered blockage with 12 m buses on that approach. Buses replace some cars without increasing total demand. With balanced demand, the three eligible straight flows use an 80/12/8 mix; other flows use an 80/20 motorcycle/car mix. Finite vehicle counts vary with random sampling.

The network contains 1,026 non-internal edges, 1,179 lanes, and 617 junctions. Its three signal controllers comprise a fixed central controller and two actuated controllers. The central controller has 47 controlled links and nine phases: four 31 s greens, four 6 s yellows, and one 1 s all-red phase, totaling **149 s**. No external TraCI controller is used.

| Study junction approach | Incoming edge | Lanes |
|---|---|---:|
| Ton Duc Thang | `954341842#0` | 5 |
| Xa Dan | `1392245988#0` | 3 |
| Nguyen Luong Bang | `1262818190#0` | 2 |
| O Cho Dua | `711109718#1` | 4 |

## Structure and dependencies

```text
O_cho_dua/
  run.bat                 Run the full GUI simulation
  build.bat               Generate demand and forward arguments to Python
  generate_demand.py      Validate paths/vehicle permissions and generate flows
  test_generate_demand.py Test vehicle shares and motorcycle behavior
  fixtures/motorcycle.xml Independent expected data for the test
  osm.sumocfg             Main configuration
  osm.fixed.net.xml       Active network, including revised signal programs
  research.rou.xml        Vehicle types and the 12 active flows
  osm.poly.xml.gz         Scenery
  output.add.xml          edgeData output declaration
  osm.view.xml            GUI settings
  source/                 OSM, original network/demand, conversion settings
```

`run.bat` → `osm.sumocfg` → `osm.fixed.net.xml`, `research.rou.xml`, `osm.poly.xml.gz`, `output.add.xml`, `osm.view.xml`. These input contents were preserved during cleanup, keeping geometry, signals, demand, and vehicle parameters unchanged.

`source/` is not loaded by the main simulation; it is retained for research and reproduction. **Do not replace `osm.fixed.net.xml` with `source/osm.net.xml.gz`**: the original network has different signal programs. Conversion settings reproduce only the original network, not subsequent signal edits. `osm.passenger.trips.xml` contains the original passenger-only demand and is not added to the current mixed flows.

A total of 108 historical files were moved out of the project: backups, candidates, rejected trials, result logs/XML, old reports, and caches. The test that previously read an experimental snapshot now reads a small fixture with the same expected data. This document summarizes usage and limitations of the current version.

Automatic approval review blocked deletion, so historical files were moved to `C:\Users\ADMIN\AppData\Local\Temp\sumo-cleanup-cttydnn4\historical-files` and have not been permanently deleted. The old dated path is no longer the entry point; use the launcher in this directory.

## Change demand and validate

Requires Python 3.9+ and `SUMO_HOME` pointing to the SUMO installation containing `tools/sumolib`. No pip packages are needed for the current script.

```powershell
$env:SUMO_HOME = "D:\Sumo"
.\build.bat
python -B -m unittest test_generate_demand -v
```

`build.bat` works from other directories and forwards arguments and exit codes. By default it **overwrites `research.rou.xml`**; reload an open GUI session afterward. To preserve active demand, generate a separate file:

```powershell
.\build.bat --scenario low --pattern balanced --output comparison.rou.xml
.\build.bat --scenario peak --pattern unbalanced --output comparison.rou.xml
.\build.bat --rate 1500 --duration 5400 --motorcycle-share 0.85 --output comparison.rou.xml
sumo-gui -c osm.sumocfg --route-files comparison.rou.xml --start
```

Relative `--output` paths are resolved from the map directory when using `build.bat`. The `low/medium/high/peak` scenarios specify 600/1200/1800/2400 vehicles/hour **across the whole network**; `--rate` overrides this. `balanced` distributes demand equally; `unbalanced` gives O Cho Dua weight 3 and each other approach weight 1 while preserving total demand. Buses account for 15% of the non-motorcycle share, with cars making up the remainder; network-wide shares are preserved under both patterns. Before writing, the generator checks paths, connections, vehicle permissions, boundary entries/exits, and the absence of U-turns.

Validate the simulation with junction collision detection:

```powershell
sumo -c osm.sumocfg --seed 42 --end 4200 --xml-validation always --collision.check-junctions true --collision.action warn
```

To reproduce the original source network, run from `source/`:

```powershell
netconvert -c osm.netccfg
polyconvert -c osm.polycfg
```

These commands overwrite network/scenery files within `source/` and do not automatically replace the active network in the parent directory. `osm.ogcfg` retains WebWizard settings with output directed to the current working directory instead of the old absolute path.

## Results and limitations

Before/after cleanup checks with SUMO 1.27.1, seed 42, and an end time of 4200 s completed **1200/1200 vehicles**: 970 motorcycles, 194 cars, and 36 buses. No vehicles remained running or waiting, and there were no collisions or teleports. The existing **five emergency-braking warnings** remain visible. Trips, edge measurements, and statistics unrelated to machine performance matched before and after cleanup. Both generator tests passed, and regenerated demand matched the active file.

Parameters and OD assumptions have not been calibrated against field observations; buses do not represent verified public transport routes or stop schedules. The network has disconnected components and very short edges before signals, without sufficient evidence to join, remove, or reshape them. Lane counts come from OSM; lane widths and some turning movements need verification. High demand can cause congestion and teleports, so default success does not guarantee all scenarios/seeds. Earlier lane-change checks found some motorcycle gaps below the reported secure gap when the lane index changed; complete trajectories and vehicle body overlap have not been independently verified. GUI rendering was not visually checked during this cleanup.
