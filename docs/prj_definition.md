# Adaptive Traffic Signal Control (Baseline Stage)

*First Created: 24 Oct 2026*

## 1. Problem Statement
* The limitations of conventional fixed-time traffic signal control.
* How traffic demand changes over time and across different directions.
* Why an adaptive controller could make better decisions using real-time observations.
* What the controller is expected to improve.

Conventional fixed-time traffic signal control follows predetermined schedules regardless of real-time traffic conditions. When traffic demand varies between approaches, this can lead to unnecessary waiting and long vehicle queues. This project investigates adaptive traffic signal control using simulation-based decision-making methods, with the objective of reducing vehicle waiting time and queue length while maintaining efficient traffic throughput.

## 2. Research Objectives & Scope
| Stage | Objective | Purpose |
|---|---|---|
| 1 | Implement and evaluate 3 baseline controllers: Fixed-time, Rule-based, DRL | Establish a baseline performance threshold |
| 2 | Evaluate direct LLM-based traffic signal control | Evaluate the direct reasoning capabilities of LLM |
| 3 | Evaluate LLM expert feedback integrated with DRL-baseline | Assess the performance gains achieved by adapting LLM-derived knowledge into RL |

**Stage 1:** in specific
* Develop a reproducible SUMO simulation of a simple 4-way intersection.
* Implement 3 controllers within a shared simulation pipeline.
* Evaluate the controllers using consistent traffic scenarios and metrics.
* Verify the reproducibility of baseline results across independent runs using consistent configurations, random seeds, and evaluation metrics.
* Determine whether the DRL controller learns a stable policy and compare the effectiveness of the controllers.

## 3. Simulation Environment
- Simulator: SUMO, controlled through Python/TraCI
- Road topology: a standard 4-way intersection
- Traffic demand: normal/rush hour scenarios
- Number of intersections: 1
- Signal configuration: 2 main green phases
- Vehicle types: motor, bus, cars
- Simulation step: 1s
- Random seed: TBD

## 4. Agent & Decision-Making Formulation
### 4.1. Agent
At Stage 1 - 4-way intersection
| | |
|---|---|
| Nb of agents | 1 |
| Controlled intersection | 4-way intersection |
| Environment | SUMO |
| Interface | Python + TraCI |
| Methods | Fixed-time, Rule-based, DRL |

### 4.2. State
The observation space represents the traffic information available to the agent at each decision point. These observations are retrieved from the SUMO simulation environment through TraCI and used as input to the control policy.

Data is retrievd from TraCI, which is *observation*.

| State variable | Unit | Symbol | Description | TraCI |
|---|---|---|---|---|
| `queue_length` | m | $q_i$ | Physical length of the detected traffic queue, including vehicle lengths and gaps | `traci.lanearea.getJamLengthMeters()` |
| `queue_count` | vehicles | $c_i$ | Number of vehicles belong to the detected traffic jam | `traci.lanearea.getJamLengthVehicle()` |
| `vehicle_count` | vehicles | $n_i$ | Total nb of vehicles detected within the observation area during the last simulation step, 0 ≤ `queue_count` ≤ `vehicle_count` | `traci.lanearea.getLastStepVehicleNumber()` |
| `avg_waiting_time` | s | $w_i$ | Average current waiting time of vehicles within the observation area | `traci.lanearea.getLastStepVehicleIDs()`<br>`traci.vehicle.getWaitingTime()` |
| `avg_speed` | m/s | $v_i$ | Average vehicle speed during the last simulation step | `traci.lanearea.getLastStepMeanSpeed()` |
| `current_signal_phase` | categorical | $p_t$ | Current traffic signal phase, mapped from the SUMO phase index | `traci.trafficlight.getPhase()` |
| `elapsed_green_time` | s | $g_t$ | Time elapsed since the current green phase began | `traci.trafficlight.getSpentDuration()` |

### 4.3. Action
Action defines the set of traffic signal control decisions that the agent can make based on the current traffic observation.

For initial baseline implementation, use $A = \{0 : KEEP, 1 : SWITCH\}$
- $0 = KEEP$: Maintain the current green phase.
- $1 = SWITCH$: Request the transition from the current green phase to the next green phase in the predefined signal sequence.

Intial 4-way intersection, 2 main green phases are proposed: `NS_GREEN`, `EW_GREEN`

Further implementation, in O Cho Dua's intersection: Choose the number of green seconds according to the discrete number. But need to define min/max duration, transitions,... define timing in detailed.

### 4.4. Decision Interval & Control Constraints
* **Simulation Step & Decision Interval**
Suggestion: A simulation step of 1 second and a decision interval of 5 seconds are proposed for the initial experiments. Alternative decision intervals, such as 10 and 15 seconds, may be evaluated.

* **Traffic Signal Control Constraints**

**1. Min-Max Green Time**

$
A_{\mathrm{valid}}(s_t)=
\begin{cases}
\{\text{KEEP}\}, & g_t<G_{\min}\\
\{\text{KEEP},\text{SWITCH}\}, & G_{\min}\leq g_t<G_{\max}\\
\{\text{SWITCH}\}, & g_t\geq G_{\max}
\end{cases}
$

$G_{\min}$: The minimum time a green phase must be maintained before it is allowed to end.
$G_{\max}$: The maximum time a green phase is maintained before the controller must end that phase according to the design rules

**2. Yellow & Clearance Interval**

Secure binding when switching phases.

Eg: NS Green (15s) ${\longrightarrow}$ NS Yellow (3s) ${\longrightarrow}$ All Red (1s) ${\longrightarrow}$ EW Green (Next)

**3. Valid Phase transition**
```
NS_GREEN
   ↓
NS_YELLOW
   ↓
ALL_RED_NS_TO_EW
   ↓
EW_GREEN
   ↓
EW_YELLOW
   ↓
ALL_RED_EW_TO_NS
   ↓
NS_GREEN
```

## 5. Reward Function & Loss Function
### 5.1. Reward Function
- Reward function evaluates the effectiveness of the agent's traffic signal control decisions based on the resulting traffic conditions
- Objective: minimize traffic congestion and vehicle waiting time while improving traffic throughput
- Traffic observations are initially collected at the lane level using E2 detectors. Each incoming lane is associated with a predefined observation area.
- Function:     $r_t = -\alpha\hat{Q}_t - \beta\hat{W}_t + \eta\hat{T}_t$

in which:
| | | | |
|---|---|---|---|
| $r_t$ | Reward obtained during a control transition | | |
| $\hat{Q}_t$ | Normalized queue length $q_i$ | $\hat{Q}(u)=\frac{1}{K}\sum_{i=1}^{K}\frac{q_i(u)}{L_i}$ | $K$: nb of incoming observed lanes<br>$q_i(u)$: jam length of lane $i$ at time $u$ (m)<br>$L_i$: detector length of lane $i$ (m) |
| $\hat{W}_t$ | Normalized avg waiting time $w_i$ | $\hat{W}(u)=\frac{1}{N(u)}\sum_{j=1}^{N(u)}w_j(u)$| $w_j(u)$: waiting time of vehicle $j$ (s)<br>$N(u)$: total vehicle count |
| $\hat{T}_t$ | Normalized traffic throughput | $\hat{T}_t = \frac{T_t/\tau_t}{T_{ref}}$ | $T_t$: number of vehicles crossing the intersection exits<br>$\tau_t$: actual seconds between 2 decision points<br>$T_{ref}$: reference throughput rate (vehicles/s) |
| $\alpha$ | Queue length weight | |
| $\beta$ | Waiting time weight | |
| $\eta$ | Throughput weight | |

The reward is calculated using traffic measurements collected during each control transition. The calculation accounts for the actual duration between consecutive eligible decision points.

### 5.2. Loss Function

