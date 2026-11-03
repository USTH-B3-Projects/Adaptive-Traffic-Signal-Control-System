"""Read local settings and existing SUMO inputs without modifying them."""
from dataclasses import dataclass
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"
DEFAULTS = dict(simulation_step=1, decision_interval=5,
                min_green=30, max_green=75, yellow_time=3, all_red_time=0,
                gui=False, max_episode_seconds=None, sumo_binary=None, seed=None)


def _yaml(path):
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return value


def _number(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and >= {minimum}")
    return value


def load_settings(path: Path | str | None = None) -> dict:
    path = Path(path) if path is not None else CONFIG_DIR / "traci.yaml"
    settings = DEFAULTS | _yaml(path)
    binary = settings["sumo_binary"]
    if isinstance(binary, str) and binary.strip() and Path(binary).parent != Path("."):
        settings["sumo_binary"] = (path.resolve().parent / binary).resolve()
    return validate_settings(settings)


def validate_settings(settings: dict) -> dict:
    """Validate merged settings, including programmatic overrides."""
    unknown = settings.keys() - DEFAULTS.keys()
    if unknown:
        raise ValueError(f"Unknown settings: {sorted(unknown)}")
    settings = DEFAULTS | settings
    step = _number(settings["simulation_step"], "simulation_step", 0)
    if step == 0:
        raise ValueError("simulation_step must be positive")
    for name in ("decision_interval", "min_green", "max_green", "yellow_time", "all_red_time", "max_episode_seconds"):
        value = settings[name]
        if name == "max_episode_seconds" and value is None:
            continue
        _number(value, name)
        if value == 0 and name not in ("all_red_time", "yellow_time"):
            raise ValueError(f"{name} must be positive")
        if not math.isclose(value / step, round(value / step), abs_tol=1e-9, rel_tol=0):
            raise ValueError(f"{name} must be a multiple of simulation_step")
    if settings["min_green"] > settings["max_green"]:
        raise ValueError("min_green must not exceed max_green")
    if not isinstance(settings["gui"], bool):
        raise ValueError("gui must be a boolean")
    seed = settings["seed"]
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2147483647):
        raise ValueError("seed must be an integer from 0 to 2147483647 or None")
    binary = settings["sumo_binary"]
    if binary is not None and (not isinstance(binary, (str, Path)) or not str(binary).strip()):
        raise ValueError("sumo_binary must be a nonempty path or None")
    return settings


@dataclass(frozen=True)
class Scenario:
    name: str
    config_path: Path
    net_path: Path
    route_paths: tuple[Path, ...]
    begin: float
    end: float | None
    seed: int | None


def config_inputs(config_path: Path) -> tuple[ET.Element, dict[str, tuple[Path, ...]]]:
    """Validate configured input files, including auxiliary and GUI inputs."""
    root = ET.parse(config_path).getroot()
    paths = {}
    for section in ("input", "gui_only"):
        for element in root.findall(f"./{section}/*"):
            if element.tag.endswith(("-file", "-files")):
                values = element.get("value", "")
                paths[element.tag] = tuple((config_path.parent / value.strip()).resolve()
                                           for value in values.split(",") if value.strip())
                for file in paths[element.tag]:
                    if not file.is_file():
                        raise FileNotFoundError(f"Missing SUMO {element.tag}: {file}")
    return root, paths


class ScenarioLoader:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else CONFIG_DIR / "scenarios.yaml"

    def load(self, name: str) -> Scenario:
        mapping = _yaml(self.path)
        if name not in mapping:
            raise ValueError(f"Unknown scenario {name!r}; choose from {', '.join(mapping)}")
        if not isinstance(mapping[name], str):
            raise ValueError("Scenario configuration must be a path string")
        config = (self.path.resolve().parent / mapping[name]).resolve()
        root, paths = config_inputs(config)
        if len(paths.get("net-file", ())) != 1 or not paths.get("route-files"):
            raise ValueError("Scenario requires one net-file and route-files")
        def time_value(tag, default):
            element = root.find(f"./time/{tag}")
            value = default if element is None else float(element.attrib["value"])
            return None if value is None else _number(value, tag)
        begin, end = time_value("begin", 0.0), time_value("end", None)
        if end is not None and end < begin:
            raise ValueError("Scenario end precedes begin")
        seed_element = root.find("./random_number/seed")
        seed = None if seed_element is None else int(seed_element.attrib["value"])
        return Scenario(name, config, paths["net-file"][0], paths["route-files"], begin, end, seed)
