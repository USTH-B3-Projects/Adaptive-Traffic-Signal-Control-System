MAIN_TLS = "joinedS_5707161152_6677677155_6677677160_6677677161_#2more"

PHASE_TO_STAGE = {
    0: "S0",
    2: "S1",
    5: "S2",
    7: "S3",
}

STAGE_LANES = {
    "S0": [  # phase 0
        "1242184418#5_0", "1242184418#5_1",
        "711106354#0_0", "711106354#0_1",
        "711106357#0_0", "711106357#0_1",
        "774613402#25_0",
        "954341842#0_0", "954341842#0_1", "954341842#0_2", "954341842#0_3", "954341842#0_4",
        "964674137#1_0", "964674137#1_1", "964674137#1_2", "964674137#1_3",
    ],
    "S1": [  # phase 2
        "1392245988#0_0", "1392245988#0_1", "1392245988#0_2",
        "964674137#1_0", "964674137#1_1", "964674137#1_2", "964674137#1_3",
    ],
    "S2": [  # phase 5
        "1262818190#0_0", "1262818190#0_1",
        "600037938#1_0",
    ],
    "S3": [  # phase 7
        "711109718#1_0", "711109718#1_1", "711109718#1_2", "711109718#1_3",
        "871891999#0_0",
    ],
}

MIN_GREEN = 30
MAX_GREEN = 75


def _get_tls(state):
    if MAIN_TLS in state["tls"]:
        return MAIN_TLS, state["tls"][MAIN_TLS]
    tls_id = next(iter(state["tls"].keys()))
    return tls_id, state["tls"][tls_id]


def get_stage_queues(state):
    _, tls = _get_tls(state)
    lanes = tls.get("lanes", {})
    queues = {}
    for stage, lane_ids in STAGE_LANES.items():
        q = 0
        for lane_id in lane_ids:
            if lane_id in lanes:
                q += lanes[lane_id]["halting_count"]
        queues[stage] = q
    return queues


def get_current_stage(state):
    _, tls = _get_tls(state)
    return PHASE_TO_STAGE.get(tls["phase_id"])


def get_total_queue(state):
    _, tls = _get_tls(state)
    return tls["totals"]["halting_count"]


def choose_action(state):
    _, tls = _get_tls(state)

    if tls.get("in_transition"):
        return "KEEP"

    current = get_current_stage(state)
    if current is None:
        return "KEEP"

    green_elapsed = tls.get("green_elapsed", 0)
    if green_elapsed < MIN_GREEN:
        return "KEEP"
    if green_elapsed >= MAX_GREEN:
        return "SWITCH"

    queues = get_stage_queues(state)
    current_q = queues[current]
    other_max = max(q for s, q in queues.items() if s != current)

    if other_max > current_q:
        return "SWITCH"
    return "KEEP"