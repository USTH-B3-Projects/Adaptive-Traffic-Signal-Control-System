"""Boundary-driven control of validated, cyclic static SUMO programs."""
import math


class SignalController:
    def __init__(self, connection, settings: dict, *, tls_ids=None, green_phases_by_tls=None) -> None:
        self.connection = connection
        self.step = float(settings.get("simulation_step", 1))
        if not math.isfinite(self.step) or self.step <= 0:
            raise ValueError("simulation_step must be positive")
        self.minimum = self._duration(settings.get("min_green", 30))
        self.maximum = self._duration(settings.get("max_green", 75))
        yellow = self._duration(settings.get("yellow_time", 3))
        red = self._duration(settings.get("all_red_time", 0))
        if self.maximum < self.minimum or self.maximum <= 0:
            raise ValueError("max_green must be positive and >= min_green")
        available_tls = tuple(connection.trafficlight.getIDList())

        if isinstance(tls_ids, str):
            raise ValueError("tls_ids must be a list or tuple, not a string")

        self.tls_ids = (
            available_tls if tls_ids is None else tuple(tls_ids)
        )

        unknown_tls = set(self.tls_ids) - set(available_tls)

        if unknown_tls:
            raise ValueError(f"Unknown TLS IDs: {sorted(unknown_tls)}")

        if len(self.tls_ids) != len(set(self.tls_ids)):
            raise ValueError("Duplicate TLS IDs")

        profiles = (
            {} if green_phases_by_tls is None else green_phases_by_tls
        )

        unknown_profiles = set(profiles) - set(self.tls_ids)

        if unknown_profiles:
            raise ValueError(
                f"Green phase profiles refer to unselected TLS: "
                f"{sorted(unknown_profiles)}"
            )
        self._signals = {}
        now = connection.simulation.getTime()
        for tls in self.tls_ids:
            api = connection.trafficlight
            programs = [p for p in api.getAllProgramLogics(tls) if p.programID == api.getProgram(tls)]
            if len(programs) != 1 or programs[0].type != 0:
                raise ValueError(f"{tls}: requires one active static program")
            phases = programs[0].phases

            explicit = profiles.get(tls)

            if explicit is not None:
                explicit = tuple(explicit)

                if (
                    len(explicit) < 2
                    or any(
                        type(i) is not int or not 0 <= i < len(phases)
                        for i in explicit
                    )
                    or len(set(explicit)) != len(explicit)
                ):
                    raise ValueError(f"{tls}: invalid green phase indices")

                self._validate_explicit_phases(tls, phases, set(explicit))
            masks, durations = [], []
            for i, phase in enumerate(phases):
                if phase.next and tuple(phase.next) != ((i + 1) % len(phases),):
                    raise ValueError(f"{tls}: branched/nonsequential phase next")
                state = phase.state
                if not state or set(state) - set("rGgys"):
                    raise ValueError(f"{tls}: unsupported signal state {state}")
                mask = tuple(
                    (j, c) for j, c in enumerate(state) if c in "Gg"
                )

                if explicit is None and mask and "y" in state:
                    raise ValueError(
                        f"{tls}: mixed green/yellow phase unsupported"
                    )

                if not mask and "s" in state:
                    raise ValueError(
                        f"{tls}: permissive movement outside a green stage"
                    )

                if explicit is not None and i not in explicit:
                    mask = ()

                masks.append(mask)
                duration = self._duration(phase.duration)
                if duration <= 0:
                    raise ValueError(f"{tls}: phase durations must be positive")
                if explicit is not None:
                    durations.append(duration)
                else:
                    durations.append(
                        max(
                            duration,
                            yellow if "y" in state else red if not mask else 0,
                        )
                    )
            if len({len(p.state) for p in phases}) != 1 or not any(masks):
                raise ValueError(f"{tls}: invalid phase states")
            if explicit is None and red and not any(set(p.state) == {"r"} for p in phases):
                raise ValueError(f"{tls}: requested all-red absent from program")
            starts = [i for i, mask in enumerate(masks) if mask and mask != masks[i - 1]]
            if len(starts) < 2:
                raise ValueError(f"{tls}: requires at least two distinct green stages")
            stage_start = {}
            for start in starts:
                i, prefix = start, 0
                while masks[i] == masks[start]:
                    stage_start[i] = (start, prefix)
                    nxt = (i + 1) % len(phases)
                    if masks[nxt] != masks[start]:
                        if masks[nxt] or "y" not in phases[nxt].state:
                            raise ValueError(f"{tls}: green must be followed by yellow")
                        if explicit is None and any(phases[nxt].state[j] != "y" for j, _ in masks[i]):
                            raise ValueError(
                                f"{tls}: yellow must clear every green movement"
                            )
                        break
                    prefix += durations[i]
                    i = nxt
                if prefix >= self.maximum:
                    raise ValueError(f"{tls}: startup phases exceed max_green")
            self._check_conflicts(tls, phases)
            index = api.getPhase(tls)
            spent = self._duration(api.getSpentDuration(tls))
            start_time = now - spent - stage_start.get(index, (0, 0))[1]
            final = bool(masks[index]) and masks[(index + 1) % len(phases)] != masks[index]
            deadline = start_time + self.maximum if final else now - spent + durations[index]
            if deadline < now or (not final and spent > durations[index]):
                raise ValueError(f"{tls}: active phase offset cannot be represented")
            self._signals[tls] = dict(phases=phases, masks=masks, durations=durations,
                                      index=index, start=start_time, deadline=deadline)
        # Validate every signal before taking ownership of any signal.
        for tls in self.tls_ids:
            connection.trafficlight.setPhaseDuration(tls, 1e9)

    @staticmethod
    def _validate_explicit_phases(tls, phases, greens):
        # Phases state length must be consistent
        if len({len(p.state) for p in phases}) != 1:
            raise ValueError(f"{tls}: inconsistent phase state lengths")

        # Selected phase must be a stable green
        # and each green phase must be followed by yellow
        for i in greens:
            state = phases[i].state
            nxt = (i + 1) % len(phases)

            if "y" in state or not any(c in "Gg" for c in state):
                raise ValueError(
                    f"{tls}: selected green phase is not a stable green"
                )

            if nxt in greens or "y" not in phases[nxt].state:
                raise ValueError(
                    f"{tls}: each green phase must be followed by yellow"
                )

        # Validate each state through phases, even end -> start
        for i, phase in enumerate(phases):
            previous = phases[i - 1].state

            for before, after in zip(previous, phase.state):
                if before in "Gg" and after not in "Ggy":
                    raise ValueError(
                        f"{tls}: green movement must clear through yellow"
                    )

                if i not in greens and after in "Gg" and before != after:
                    raise ValueError(
                        f"{tls}: transition introduces or changes a green"
                    )

    def _duration(self, value: float) -> float:
        value = float(value)
        if not math.isfinite(value) or value < 0 or not math.isclose(value / self.step, round(value / self.step), abs_tol=1e-8, rel_tol=0):
            raise ValueError("durations and phase offsets must align with simulation_step")
        return value

    def _check_conflicts(self, tls: str, phases) -> None:
        links = self.connection.trafficlight.getControlledLinks(tls)
        for phase in phases:
            if len(phase.state) != len(links):
                raise ValueError(f"{tls}: phase state does not match controlled links")
            protected = [link for i, group in enumerate(links) if phase.state[i] == "G" for link in group]
            for source, _, lane in protected:
                foes = self.connection.lane.getInternalFoes(lane)
                # A shared incoming lane serializes vehicles before its internal paths diverge.
                if any(other_source != source and other_lane in foes
                       for other_source, _, other_lane in protected):
                    raise ValueError(f"{tls}: conflicting protected green movements")

    def _next(self, tls: str, now: float) -> None:
        s = self._signals[tls]
        previous = s["masks"][s["index"]]
        s["index"] = (s["index"] + 1) % len(s["phases"])
        index = s["index"]
        mask = s["masks"][index]
        if mask and mask != previous:
            s["start"] = now
        final = mask and s["masks"][(index + 1) % len(s["phases"])] != mask
        s["deadline"] = s["start"] + self.maximum if final else now + s["durations"][index]
        self.connection.trafficlight.setPhase(tls, index)
        self.connection.trafficlight.setPhaseDuration(tls, 1e9)

    def advance(self, now: float) -> list[dict]:
        events = []
        for tls, s in self._signals.items():
            while now >= s["deadline"] - 1e-8:
                boundary = s["deadline"]
                if now > boundary + 1e-8:
                    raise ValueError("advance must run at every simulation boundary")
                mask = s["masks"][s["index"]]
                final = mask and s["masks"][(s["index"] + 1) % len(s["phases"])] != mask
                self._next(tls, boundary)
                events.append(dict(tls_id=tls, requested_action=None, executed_action="SWITCH" if final else "NOOP",
                                   override_reason="max_green" if final else "phase_progression", sim_time=boundary))
        return events

    def request(self, actions: dict[str, str], now: float) -> dict[str, dict]:
        if set(actions) - set(self.tls_ids) or any(a not in ("KEEP", "SWITCH") for a in actions.values()):
            raise ValueError("actions must map known TLS IDs to KEEP or SWITCH")
        results = {}
        for tls, action in actions.items():
            s = self._signals[tls]
            index = s["index"]
            mask = s["masks"][index]
            final = mask and s["masks"][(index + 1) % len(s["phases"])] != mask
            executed, reason = action, None
            if not mask:
                executed, reason = "NOOP", "in_transition"
            elif action == "SWITCH":
                if not final:
                    executed, reason = "KEEP", "startup_phase"
                elif now - s["start"] < self.minimum:
                    executed, reason = "KEEP", "min_green"
                else:
                    self._next(tls, now)
            results[tls] = dict(requested_action=action, executed_action=executed, override_reason=reason)
        return results

    def snapshot(self, tls_id: str, now: float) -> dict:
        s = self._signals[tls_id]
        index = s["index"]
        green = bool(s["masks"][index])
        return dict(phase_id=index, phase_state=s["phases"][index].state,
                    green_elapsed=max(0, now - s["start"]) if green else 0,
                    in_transition=not green)
