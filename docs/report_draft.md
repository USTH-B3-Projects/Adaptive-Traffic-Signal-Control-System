# Adaptive Traffic Signal Control System

## 1. Introduction
### 1.1. Context and Motivation
In an urban traffic network, rush-hour traffic demand varies over time and across directions, making traffic light control challenging. Because conventional fixed-time traffic signal control follows predetermined schedules regardless of real-time traffic conditions, it leads to unnecessary waiting time and long vehicle queues. Therefore, this problem motivated us to investigate an Adaptive Traffic Signal Control System and explore a Large Language Model (LLM) as a decision-making agent. 

Adaptive traffic signal control controls the traffic lights based on the traffic state: traffic conditions and traffic light states at the decision point. The control system then decides whether to keep the current phase or switch to the next phase to control the green time. The purpose of this project is to reduce the vehicle queue length and waiting time, where the queue length is measured as the number of vehicles waiting for the traffic light on the observed incoming lanes. The study used SUMO simulation environment with TraCI through Python to observe and control traffic signals. The project initially focused on a simple 4-way intersection as the baseline, then extended to the O Cho Dua 6-way intersection and Thang Long Avenue (BigC Tran Duy Hung).

The project started with three baseline controllers: Fixed-time (FT), Rule-based (RB), and Deep Reinforcement Learning (DRL) in a simple 4-way intersection, followed by performance comparisons using simulation logs under different traffic scenarios with the same metrics. The next extension stage, in the two other complex maps, was repeated but adds the use of Large Language Model (LLM)-based control, which was used to make decisions after observing the traffic state. The LLM controller was also integrated into the DRL controller, and its performance was evaluated.

### 1.2. Objectives
The project aimed to achieve the following objectives:
- Set up the SUMO simulation environment on 3 maps and provide the vehicle density in 4 scenarios: low, medium, high, and imbalance.
- Deploy and integrate baselines on FT, RB, and DRL.
- Compare different controllers' performance in different scenarios.
- Evaluate the ability to expand to complex maps.
- Evaluate direct LLM + DRL from baseline to complex maps.

### 1.3. Research Questions


### 1.4. Expected outcomes
- A SUMO simulation environment with three maps across four scenarios.
- Logged data, traffic states, and actions.
- An adaptive traffic control prototype integrated with the SUMO simulation for complex real-world urban traffic scenarios.
- A fine-tuned lightweight local LLM capable of making real-time traffic signal control decisions.
- An experimental evaluation comparing the proposed LLM agent method with three baseline approaches using traffic performance metrics.

## 2. Proposed Methods
The project’s main goal is to build and evaluate the traffic signal control system in the simulation environment. Traffic volume varies over time, and demand can be uneven across different approaches to an intersection, making it difficult to allocate green time effectively. In addition, extending green time for one movement may increase the waiting time for others. At each decision point, the adaptive controller needs to determine whether to keep the current signal phase or switch to the next phase. Therefore, this decision is based on observed traffic conditions, the current signal phase, and the elapsed green time, subject to the timing and phase-transition constraints.

### 2.1. Simulation environment
The traffic networks were simulated in the SUMO environment, using OpenStreetMap data for their network representation of real-world intersections. They were built with lanes, directions, and a signal controller. The vehicles were introduced at different demand levels and were configured to reflect observed real-world traffic conditions, in that they did not always form straight, orderly queues. The simulation provided an environment for testing different traffic scenarios and evaluating the effects of control decisions. 

TraCI connected the control program to SUMO, allowing the program to retrieve traffic data and signal states and send control commands to the simulation. The Python program collected and processed data through TraCI, coordinated the simulation runs, and invoked the selected controller. It was also used to execute actions, maintain logs, and perform comparative evaluations. 

Before each simulation run, the required configuration inputs included the traffic network (the road network structure), the traffic demand and its movements, signal phases and configuration, and the run configuration, including the controller, scenario, seed, and simulation duration.