# Adaptive Traffic Signal Control System

## 1. Introduction
### 1.1. Context and Motivation
In an urban traffic network, rush-hour traffic demand varies over time and across directions, making traffic light control challenging. Since conventional fixed-time traffic signal control follows predetermined schedules regardless of real-time traffic conditions, there is unnecessary waiting time and long vehicle queues. Therefore, this problem motivates us to investigate an Adaptive Traffic Signal Control System and explore a Large Language Model (LLM) as a decision-making agent. 

Adaptive traffic signal control is used to control the traffic lights based on the input of the traffic state: traffic conditions and traffic light states at the decision point. The control system then decides whether to keep the current phase or switch to the next phase to control the green time. The purpose of this project is to reduce the vehicle queue length and waiting time, where the queue length is measured as the number of vehicles waiting for the traffic light on the observed incoming lanes. Our scope is to investigate the SUMO simulation environment using TraCI through Python to observe and control the signals. The project initially focuses on a simple 4-way intersection as the baseline, then extends to the O Cho Dua 6-way intersection and Thang Long Avenue (BigC Tran Duy Hung).

The project starts with three baseline controllers: Fixed-time (FT), Rule-based (RB), and Deep Reinforcement Learning (DRL) in a simple 4-way intersection, followed by performance comparisons using simulation logs under different traffic scenarios with the same metrics. The next extension stage, in the two other complex maps, is repeated but adds the use of Large Language Model (LLM)-based control, which is used to make decisions after observing the traffic state. The LLM controller is also integrated into the DRL controller, and its performance is evaluated.

### 1.2. Objectives
- Set up the SUMO simulation environment on 3 maps and provide the vehicle density in 4 scenarios: low, medium, high, and imbalance.
- Deploy and integrate baselines on FT, RB, and DRL.
- Compare between different controllers' performance in different scenarios.
- Evaluate the ability to expand to complex maps.
- Evaluate direct LLM + DRL from baseline to complex maps.

### 1.3. Expected outcomes
- A SUMO simulation environment with three maps across four scenarios.
- Logged data, traffic states, and actions.
- An adaptive traffic control prototype integrated with the SUMO simulation for complex real-world urban traffic scenarios.
- A fine-tuned lightweight local LLM capable of making real-time traffic signal control decisions.
- An experimental evaluation comparing the proposed LLM agent method with three baseline approaches using traffic performance metrics.