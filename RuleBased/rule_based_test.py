from rule_based_controller import choose_action

state = {
    "tls": {
        "J": {
            "phase_id": 1,
            "green_elapsed": 40,
            "lanes": {
                "N_in_0": {"halting_count": 1},
                "N_in_1": {"halting_count": 1},
                "S_in_0": {"halting_count": 1},
                "S_in_1": {"halting_count": 0},
                "E_in_0": {"halting_count": 3},
                "E_in_1": {"halting_count": 3},
                "W_in_0": {"halting_count": 2},
                "W_in_1": {"halting_count": 2},
            },
        }
    }
}

action = choose_action(state)
print("Action:", action)

assert action == "SWITCH", f"Expected SWITCH, got {action}"
print("Test 1 passed")

state["tls"]["J"]["green_elapsed"] = 20
action = choose_action(state)
assert action == "KEEP", f"Expected KEEP, got {action}"
print("Test 2 passed")

state["tls"]["J"]["phase_id"] = 5
state["tls"]["J"]["green_elapsed"] = 40
action = choose_action(state)
assert action == "KEEP", f"Expected KEEP, got {action}"
print("Test 3 passed")

state["tls"]["J"]["phase_id"] = 5
state["tls"]["J"]["green_elapsed"] = 75
action = choose_action(state)
assert action == "SWITCH", f"Expected SWITCH, got {action}"
print("Test 4 passed")

state["tls"]["J"]["phase_id"] = 2
state["tls"]["J"]["green_elapsed"] = 0
action = choose_action(state)
assert action == "KEEP", f"Expected KEEP, got {action}"
print("Test 5 passed")