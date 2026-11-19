# Adaptive Traffic Signal Control

*Updated: 10 Nov 2026*

## 1. Problem Statement
* The limitations of conventional fixed-time traffic signal control.
* How traffic demand changes over time and across different directions.
* Why an adaptive controller could make better decisions using real-time observations.
* What the controller is expected to improve.

Conventional fixed-time traffic signal control follows predetermined schedules regardless of real-time traffic conditions. When traffic demand varies between approaches, unnecessary waiting and long vehicle queues may occur. This project investigates adaptive traffic signal control in a SUMO simulation environment, with the objective of reducing vehicle waiting time and queue length (measured in vehicles) while maintaining efficient traffic throughput.

## 2. Research Objectives & Scope
| Stage | Objective | Purpose | In detail |
|---|---|---|---|
| 1 | Implement and evaluate 3 baseline controllers: Fixed-time, Rule-based, DRL at a simple 4-way intersection, then extend them to 2 more complex maps (O Cho Dua, Tran Duy Hung) | Establish a baseline performance across 3 intersection layouts | - Develop a reproducible SUMO simulation of a simple four-way intersection.<br>- Implement three baseline controllers: Fixed-time, Rule-based, and DRL within a shared simulation pipeline.<br>- Evaluate the controllers under `Low, Medium, High, and Imbalance` traffic scenarios using consistent evaluation settings and metrics.<br>- Assess performance variability across multiple random seeds and ensure reproducibility by recording configurations and seeds.<br>- Examine the stability of DRL learning and compare the performance of the three controllers.<br>- Extend the baseline controllers to the O Cho Dua six-way intersection and BigC Tran Duy Hung, adapting their observation representations, control logic, and signal constraints as needed. |
| 2 | Evaluate direct LLM-based traffic signal control at a simple 4-way intersection, then extend it to 2 more complex maps (O Cho Dua, BigC Tran Duy Hung) | Assess LLM-based control performance against the baselines | - Develop a direct LLM-based traffic signal controller for the simple four-way intersection.<br> - Define a structured observation format and prompt containing traffic conditions, signal states, and control constraints.<br> - Integrate the LLM controller into the SUMO/TraCI pipeline, validating its decisions before execution and applying a fallback when responses are invalid or unavailable.<br> - Evaluate the controller under `Low, Medium, High, and Imbalance` traffic scenarios using evaluation settings and metrics consistent with the baselines. <br> - Assess decision latency, response validity, and traffic control performance against Fixed-time, Rule-based, and DRL.<br> - Extend the LLM controller to the O Cho Dua six-way intersection, adapting its observations, prompts, and action space to the intersection layout.
| 3 | Integrate LLM expert feedback into the DRL controller and evaluate its performance | Investigate whether LLM-derived knowledge improves DRL-based traffic signal control | TBU later |

## 3. Project Scope
| | |
|---|---|
| Simulation environment | SUMO<br>Observation retrieval and traffic signal control: Python/TraCI |
| Intersection layouts | Initial: 4-way simple intersection<br>Extended: O Cho Dua's 6-way intersection, BigC Tran Duy Hung |
| Controllers | Fixed-time (FT), Rule-based (RB), Deep Reinforcement Learning (DRL), and direct LLM<br>Planned: LLM expert feedback + DRL |
| Traffic scenarios | Low, Medium, High, Imbalance |
| Control responsibility | Control traffic signal phases and green durations within predefined timing and phase-transition constraints |
| Evaluation scope | Traffic performance: mean and maximum queue count (vehicles) and total waiting time (s) <br>Proposed additional LLM metrics: `decision_latency`, `response_validity` |
| Out of scope | Deployment in real-world traffic systems<br>Coordinated control of multiple intersections within a traffic network |

## 4. Overall Approach
*System workflow diagram and each step explanation - TBU*

## 5. Current Progress
*Last updated: 10 Nov 2026*
<br>
**Completed**
- Implemented and ran FT, RB, DRL on the simple 4-way intersection.
- Collected simulation logs and baseline results for all 3 controllers.
- Compared the 3 controllers with the same evaluation metrics.

**Next Steps:**
- Extend the baseline controllers to 2 additional maps: O Cho Dua, BigC Tran Duy Hung.
- Implement direct LLM on simple 4-way intersection, then extend it to the 2 complex maps.
- Later planned: LLM feedback + DRL.