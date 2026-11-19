def get_group_queues(state):
    lanes = state["tls"]["J"]["lanes"]
    ns_lanes = ["N_in_0", "N_in_1", "S_in_0", "S_in_1"]
    ew_lanes = ["E_in_0", "E_in_1", "W_in_0", "W_in_1"]

    queue_ns = 0
    for lane_id in ns_lanes:
        queue_ns += lanes[lane_id]["halting_count"]

    queue_ew = 0
    for lane_id in ew_lanes:
        queue_ew += lanes[lane_id]["halting_count"]

    return {"NS": queue_ns, "EW": queue_ew}

def get_current_group(state):
    phase_id = state["tls"]["J"]["phase_id"]

    if phase_id in (0, 1):
        return "NS"
    elif phase_id in (4, 5):
        return "EW"
    else:
        return None

def choose_action(state):
    tls = state["tls"]["J"]

    current_group = get_current_group(state)
    if current_group is None or tls["green_elapsed"] < 30:
        return "KEEP"
    if tls["green_elapsed"] >= 75:
        return "SWITCH"

    queues = get_group_queues(state)
    if current_group == "NS":
        other_group = "EW"
    else:
        other_group = "NS"

    if queues[other_group] > queues[current_group]:
        return "SWITCH"
    return "KEEP"