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

"""
Expand the rule-based controller from simple intersection to O Cho Dua, 
keep the principle of adjusting green time according to queue and update the phase structure with mapping lane
"""

class CyclicRuleBasedController:
    """Rule-based controller with a fixed green-phase order, based on baseline intersection."""

    def __init__(
        self,
        tls_id,
        green_phases,
        phase_lanes,
        min_green=30,
        max_green=75,
    ):
        self.tls_id = tls_id
        self.green_phases = tuple(green_phases)
        self.min_green = min_green
        self.max_green = max_green

        if len(self.green_phases) < 2:
            raise ValueError("At least two green phases are required.")

        if len(set(self.green_phases)) != len(self.green_phases):
            raise ValueError("Green phases must be unique.")

        if not 0 <= min_green < max_green:
            raise ValueError("Require 0 <= min_green < max_green.")

        # Remove duplicate lanes within each phase.
        self.phase_lanes = {
            phase: tuple(dict.fromkeys(phase_lanes[phase]))
            for phase in self.green_phases
        }

        if any(not lanes for lanes in self.phase_lanes.values()):
            raise ValueError("Each green phase must serve incoming lanes.")

    def get_phase_queues(self, state):
        """Calculate queue for each green phase."""
        lanes = state["tls"][self.tls_id]["lanes"]

        return {
            phase: sum(
                lanes[lane_id]["halting_count"]
                for lane_id in self.phase_lanes[phase]
            )
            for phase in self.green_phases
        }

    def get_next_green(self, phase_id):
        """Find the next green phase in the fixed cycle."""
        index = self.green_phases.index(phase_id)
        return self.green_phases[
            (index + 1) % len(self.green_phases)
        ]

    def choose_action(self, state):
        tls = state["tls"][self.tls_id]

        # Rule 1: let the signal controller finish transitions.
        if tls["in_transition"]:
            return "KEEP"

        current_phase = tls["phase_id"]

        if current_phase not in self.green_phases:
            raise ValueError(
                f"Unexpected green phase: {current_phase}"
            )

        green_elapsed = tls["green_elapsed"]

        # Rule 2: respect minimum green time.
        if green_elapsed < self.min_green:
            return "KEEP"

        # Rule 3: enforce maximum green time.
        if green_elapsed >= self.max_green:
            return "SWITCH"

        # Rule 4: compare current and next green-phase queues.
        queues = self.get_phase_queues(state)
        next_phase = self.get_next_green(current_phase)

        if queues[next_phase] > queues[current_phase]:
            return "SWITCH"

        # Rule 5: keep the current green otherwise.
        return "KEEP"