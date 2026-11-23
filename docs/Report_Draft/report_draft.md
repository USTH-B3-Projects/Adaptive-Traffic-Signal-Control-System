# Adaptive Traffic Signal Control System for Intersection Networks using Large Language Models (LLMs)

## 1. Introduction
### 1.1. Context and Motivation
In an urban traffic network, rush-hour traffic demand varies over time and across directions, making traffic light control challenging. Because conventional fixed-time traffic signal control follows predetermined schedules regardless of real-time traffic conditions, it leads to unnecessary waiting time and long vehicle queues. Therefore, this problem motivated us to investigate an Adaptive Traffic Signal Control System and explore a Large Language Model (LLM) as a decision-making agent. 

Adaptive traffic signal control controls the traffic lights based on the traffic state: traffic conditions and traffic light states at the decision point. The control system then decides whether to keep the current phase or switch to the next phase to control the green time. The purpose of this project is to reduce the vehicle queue length and waiting time, where the queue length is measured as the number of vehicles waiting for the traffic light on the observed incoming lanes. The study used SUMO simulation environment with TraCI through Python to observe and control traffic signals. The project initially focused on a simple 4-way intersection as the baseline, then extended to the O Cho Dua 6-way intersection and Thang Long Avenue (Go! Thang Long).

The project started with three baseline controllers: Fixed-time (FT), Rule-based (RB), and Deep Reinforcement Learning (DRL) in a simple 4-way intersection, followed by performance comparisons using simulation logs under different traffic scenarios with the same metrics. The next extension stage, in the two other complex maps, was repeated but adds the use of Large Language Model (LLM)-based control, which was used to make decisions after observing the traffic state. The LLM controller was also integrated into the DRL controller, and its performance was evaluated.

### 1.2. Objectives
The project aimed to achieve the following objectives:
- Set up the SUMO simulation environment on 3 maps and provide the vehicle density in 4 scenarios: low, medium, high, and imbalance.
- Deploy and integrate baselines on FT, RB, and DRL.
- Compare different controllers' performance in different scenarios.
- Evaluate the ability to expand to complex maps.
- Evaluate direct LLM + DRL from baseline to complex maps.

### 1.3. Research Questions
This research aimed to address the following research questions:
- Which adaptive controller performs best in each scenario and road network? Is its performance consistent across the three networks?
- Does that best-performing adaptive controller outperform the fixed-time baseline? How does it reduce queue length and waiting time?
- How do direct LLM-based control and LLM-DRL integration compare with standalone DRL in terms of evaluation metrics?

### 1.4. Expected outcomes
- A SUMO simulation environment with three maps across four scenarios.
- Logged data, traffic states, and actions.
- An adaptive traffic control prototype integrated with the SUMO simulation for complex real-world urban traffic scenarios.
- A fine-tuned lightweight local LLM capable of making real-time traffic signal control decisions.
- An experimental evaluation comparing the proposed LLM agent method with three baseline approaches using traffic performance metrics.

## 2. Proposed Methods
The project’s main goal is to build and evaluate the traffic signal control system in the simulation environment. Traffic volume varies over time, and demand can be uneven across different approaches to an intersection, making it difficult to allocate green time effectively. In addition, extending green time for one movement may increase the waiting time for others. At each decision point, the adaptive controller needs to determine whether to keep the current signal phase or switch to the next phase. Therefore, this decision is based on observed traffic conditions, the current signal phase, and the elapsed green time, subject to the timing and phase-transition constraints.

### 2.1. Related work
*summarize the research of conventional controller, DRL, LLM; then come up with this project's approach*

### 2.2. Simulation environment
The traffic networks were simulated in the SUMO environment, using OpenStreetMap data for their network representation of real-world intersections. They were built with lanes, directions, and a signal controller. The vehicles were introduced at different demand levels and were configured to reflect observed real-world traffic conditions, in that they did not always form straight, orderly queues. The simulation provided an environment for testing different traffic scenarios and evaluating the effects of control decisions. 

TraCI connected the control program to SUMO, allowing the program to retrieve traffic data and signal states and send control commands to the simulation. The Python program collected and processed data through TraCI, coordinated the simulation runs, and invoked the selected controller. It was also used to execute actions, maintain logs, and perform comparative evaluations. 

Before each simulation run, the required configuration inputs included the traffic network (the road network structure), the traffic demand and its movements, signal phases and configuration, and the run configuration, including the controller, scenario, seed, and simulation duration.

### 2.3. Overall Framework
*a workflow of controller*

### 2.4. Overview of Control Approaches
*introduce FT, RB, DRL, direct LLM and LLM-DRL, role and suggested method*

## 3. Methodology
### 3.1. Traffic State and Action Retrieval
*how to retrieve, collect state and action execution through TraCI*

### 3.2. Baseline Controllers
#### 3.2.1. Fixed-time Controller

The fixed-time controller utilized a static signal program that was loaded in SUMO, which means that the phase sequence and durations were predetermined and were not adjusted in response to traffic conditions. Before the evaluation, the program verified that each selected traffic light system (TLS) was operating under a static program. The fixed-time controller served as a baseline for comparison against the adaptive controllers. The static signal program for the simple four-way intersection was configured as follows:

[caption] Fixed-time signal phases at the simple four-way intersection
| Phase index | Signal stage | Duration (s) |
|---|---|---:|
| 0 | NS initial green | 3 |
| 1 | NS green | 48 |
| 2 | NS yellow | 3 |
| 3 | All-red clearance | 3 |
| 4 | EW initial green | 3 |
| 5 | EW green | 48 |
| 6 | EW yellow | 3 |
| 7 | All-red clearance | 3 |
| **Total** | **Complete cycle** | **114** |

At a simple four-way intersection, the north-south (NS) and east-west (EW) groups were served in turn. Each phase has a fixed duration in SUMO, and the simulator automatically moved to the next phase when the current phase ended. Before the next group received a green signal, the current direction went through a 3-second yellow phase, followed by a 3-second all-red clearance phase. The signal program repeated the NS-EW sequence. For each group, the configuration included a 3-second green start phase, a 48-second green phase, a 3-second yellow phase, and a 3-second all-red clearance. In total, each group’s turn lasted 57 seconds, and the complete cycle lasted for 114 seconds.

For O Cho Dua and Thang Long Avenue, the fixed-time baseline used the static signal programs configured for the respective networks.

#### 3.2.2. Rule-based Controller

Unlike the fixed-time controller, which used predetermined phase durations, the rule-based controller used observed queue lengths calculated based on the number of halting vehicles on the incoming lanes via TraCI to decide whether to maintain the current green or move to the next phase. The rule-based controller was the simplest adaptive baseline, which utilized `if-else` rules based on the current traffic state, requiring no learning and training. The minimum and maximum green-time thresholds were set to 30 and 75 seconds, respectively. These limits were introduced to avoid overly frequent phase switches and to prevent one direction from holding the green light for too long. At each decision point, occurring every 5 seconds (i.e., `decision_interval` = 5), the controller read the current state through TraCI and selected one of two actions: KEEP or SWITCH. The rule-based controller served as an adaptive baseline for comparison with DRL and LLM controllers.

For the simple four-way intersection, the controller grouped the approaches into two main groups: North-South (NS) and East-West (EW). Each approach had two incoming lanes; the total number of halting vehicles was summed within each group. Then, the controller applied the following rules in order:

[caption] Rule-based decision logic for the simple four-way intersection
| Priority | Condition | Action |
|---|---|---|
| 1 | The signal was in a yellow or all-red transition. | KEEP |
| 2 | The elapsed green time was less than 30 seconds. | KEEP |
| 3 | The elapsed green time was greater than or equal to 75 seconds. | SWITCH |
| 4 | The opposite group had a strictly longer queue than the current group. | SWITCH |
| 5 | None of the above conditions was satisfied. | KEEP |

A SWITCH decision initiated a transition to the next green group through the configured yellow and all-red phases and was handled by the `SignalController`, which enforced the timing and phase-transition constraints: the controller was prevented from switching before the minimum green had elapsed, and it automatically transitioned through yellow and all-red into the next green when the maximum green was reached. The yellow and all-red intervals followed the signal program of the traffic light (3 seconds each in the simple intersection), ensuring a fair comparison with the fixed-time controller.

The same principle was extended to complex intersections (O Cho Dua and Thang Long Avenue) through `CyclicRuleBasedController`. In this version, the controller did not use only two opposing groups. Instead, a fixed cyclic order of green phases was defined for each traffic light. For example, O Cho Dua used phases [0,2,5,7], while each traffic light on Thang Long Avenue used phases [0,3]. The incoming lanes for each phase were taken automatically from the SUMO signal program, and the queue of a phase was the total number of halting vehicles on these lanes. At every decision point, the controller compared the queue of the current phase with the queue of the next phase in this fixed order. A SWITCH always moved to the next phase, did not choose the phase with the longest queue, or skip any phase. The minimum green (30s), maximum green (75s), and decision interval (5s) remained the same as in the simple four-way intersection, whereas the yellow and all-red durations were taken from the SUMO signal program of each traffic light rather than the 3-second values of the simple intersection. On Thang Long Avenue, which has four traffic lights, each light was controlled independently.

#### 3.2.3. Deep Reinforcement Learning (DRL) Controller

### 3.3. Direct LLM-based Controller

### 3.4. LLM-DRL Integration

## 4. Experiments and Results
### 4.1. Experimental Setup
#### 4.1.1. Traffic scenarios and Simulation Parameters
#### 4.1.2. Training and Evaluation Protocol

### 4.2. Evaluation Metrics and Log Processing
### 4.3. Baseline Comparison
#### 4.3.1. Simple Four-way Intersection
#### 4.3.2. O Cho Dua Six-way Intersection
#### 4.3.3. Thang Long Avenue

### 4.4. Evaluation of LLM-based Control
#### 4.4.1. LLM-based
#### 4.4.2. LLM-DRL Integration

### 4.5. Discussion

## 5. Discussion and Conclusion
### 5.1. Findings and Contributions
### 5.2. Limitations
### 5.3. Future work

## 6. References