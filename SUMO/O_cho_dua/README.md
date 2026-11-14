# O Cho Dua map

The O Cho Dua map is independent of `Map_Nga_tu`. Both scenarios share the existing network, signal programs, vehicle behavior and boundary-to-boundary routes through the study junction.

## Layout

```text
O_cho_dua/
  network/
    osm.fixed.net.xml       Active network with revised signals
    osm.poly.xml.gz         Scenery
  config/
    base.sumocfg            Shared simulation settings
    osm.view.xml            GUI settings
    output.add.xml          Edge measurements
  scenarios/
    High/
      simulation.sumocfg
      traffic.rou.xml
      demand_profile.csv
      output.add.xml
    Imbalance/
      simulation.sumocfg
      traffic.rou.xml
      demand_profile.csv
      output.add.xml
  output/                   Results grouped by scenario and seed
  source/                   Original OSM/network and conversion inputs
  fixtures/motorcycle.xml   Independent expected motorcycle parameters
  generate_demand.py
  test_generate_demand.py
  build.bat
  run.bat
```

Do not replace `network/osm.fixed.net.xml` with the original network in `source/`: their signal programs differ. The source files are retained for reproduction, not loaded by either scenario.

Double-click `scenarios/High/High.bat` or `scenarios/Imbalance/Imbalance.bat` to launch the existing scenario inputs directly, without regenerating demand. These launchers require SUMO GUI on `PATH` and create the default seed42 output folder if needed.

## Build and run

Requires Python 3.9+, Eclipse SUMO on `PATH`, and `SUMO_HOME` pointing to the SUMO installation containing `tools/sumolib`. No pip packages are required.

From PowerShell in this directory:

```powershell
$env:SUMO_HOME = "D:\Sumo"
.\build.bat
.\run.bat High 42
.\run.bat Imbalance 42
python -B -m unittest test_generate_demand -v
```

`build.bat` generates both scenarios by default, using seed 42. `run.bat` defaults to `High` and seed 42 and regenerates that scenario with default rate/duration before launching. To run custom generated inputs, use the headless command below or `sumo-gui -c scenarios/High/simulation.sumocfg --start` directly. The launchers work from other directories. Close SUMO GUI to finish a run; reload the configuration after rebuilding demand.

```powershell
.\build.bat --scenario imbalance --seed 57
.\build.bat --scenario high --rate 4800 --duration 3600
.\build.bat --scenario high --motorcycle-share 0.85 --output comparison.rou.xml
```

`--scenario` accepts `high`, `imbalance`, or `all`. `--rate` overrides total vehicles/hour; `--duration` overrides the demand generation period in seconds. `--output` writes a custom route file for one scenario. Building normally replaces the selected generated scenario inputs. Save custom inputs before rebuilding.

For a headless run:

```powershell
sumo -c scenarios/High/simulation.sumocfg --seed 42
sumo -c scenarios/Imbalance/simulation.sumocfg --seed 42
```

Use `run.bat` to select the output directory for a scenario and seed. Results are grouped under `output/High/seed42/` or `output/Imbalance/seed42/`; running the same scenario and seed again overwrites that run's results. Changing the SUMO seed alone changes vehicle sampling, not the generated demand profile: rebuild with `--seed` to change the Imbalance profile as well.

## Scenarios

| Parameter | High | Imbalance |
|---|---|---|
| Demand generation period | 0–3600 s | 0–10800 s (3 hours) |
| Total demand | 5400 vehicles/hour | 4200 vehicles/hour |
| Approach distribution | Constant 25% each | Smoothly changing dominant approach |
| Purpose | Sustained balanced high load | Adaptation as the busiest approach changes |

High uses the same total demand, per-approach demand (1350 vehicles/hour), and duration as `Map_Nga_tu` High. It retains O Cho Dua's own turning proportions and vehicle/lane behavior.

Imbalance keeps the total demand constant while redistributing it between Ton Duc Thang, Xa Dan, Nguyen Luong Bang and O Cho Dua. Seeded transitions move the peak between approaches, with balanced periods and overlapping pressure during transitions. The profile is approximated by consecutive 30-second flow intervals. It does not claim physically continuous arrival rates inside each interval. `demand_profile.csv` records interval begin/end times and each approach's vehicles/hour so the generated experiment can be inspected and reproduced.

The demand period ends at 1 or 3 hours; simulations can continue afterward until remaining vehicles clear. Report clearance time separately from demand-period performance. Check vehicles waiting to enter as well as vehicles already on the network: congestion may prevent SUMO from inserting all requested demand.

## Shared traffic assumptions

- Turning split: 50% straight, 25% left, 25% right per approach.
- Expected network-wide mix: 80% motorcycles, 17% cars, 3% buses.
- Motorcycles use Krauss/SL2015 with lateral movement; cars and buses prefer lane centers.
- Buses only travel straight from Ton Duc Thang, Xa Dan and O Cho Dua. The 12 m bus movement from Nguyen Luong Bang remains excluded because of previously observed blockage.
- Time step: 0.5 s; lateral resolution: 0.4 m.
- Departures use lane `best` and speed `max`, subject to SUMO safety constraints.

Before writing routes, the generator validates paths, vehicle permissions, boundary entries/exits and absence of U-turns. Vehicle type distributions compensate for bus-eligible demand, preserving the expected network-wide mix even when approach demand changes. Flows use per-second probabilities (scaled by SUMO for the 0.5 s step), avoiding rounding up each short interval. Actual sampled vehicle counts can differ. Overrides exceeding one vehicle/second per individual flow are rejected.

| Approach | Incoming edge | Lanes |
|---|---|---:|
| Ton Duc Thang | `954341842#0` | 5 |
| Xa Dan | `1392245988#0` | 3 |
| Nguyen Luong Bang | `1262818190#0` | 2 |
| O Cho Dua | `711109718#1` | 4 |

The central signal controller retains its existing nine phases (149 s total cycle); two other controllers are actuated. These scenarios do not add a TraCI control policy.

## Validation and limits

Run unit tests with the command above. For a bounded diagnostic run with junction collision checks:

```powershell
sumo -c scenarios/High/simulation.sumocfg --seed 42 --end 4200 --xml-validation always --collision.check-junctions true --collision.action warn
```

A bounded run can leave vehicles unfinished; it is not evidence that the full demand clears. Inspect statistics, trip information, insertion backlog, collisions and teleports when comparing scenarios or controllers.

Demand rates, OD assumptions and bus routes are experimental, not calibrated against field observations. Equal demand does not imply equal pressure: Nguyen Luong Bang has fewer lanes than the other approaches. High demand can produce gridlock, teleports or long clearance times. Existing network disconnected components, short edges, lane widths and turning movements still need field review. GUI appearance and complete motorcycle body-overlap trajectories require separate validation.

### Verification in this project (2026-11-14)

Six unit/integration tests passed. Network and scenery SHA-256 hashes match the original files before relocation. Both scenarios were exercised with SUMO 1.27.1, seed 42, XML validation and junction collision checks, bounded at 1200 simulation seconds:

| Scenario | Inserted | Waiting to enter at cutoff | Collisions | Teleports |
|---|---:|---:|---:|---:|
| High | 1704 | 140 | 6 | 15 |
| Imbalance | 1193 | 236 | 4 | 7 |

Diagnostic logs and summaries are under `output/<scenario>/seed42/`. The network and vehicle behavior were retained; these results expose traffic-model limitations rather than certify collision-free operation. Neither a complete 3-hour episode nor final clearance nor GUI appearance was verified. Demand profiles, including all 3 hours, were checked by automated tests.
