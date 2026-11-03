"""Own one SUMO process and one independent TraCI connection."""
import importlib
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import xml.etree.ElementTree as ET

from .scenario_loader import Scenario, config_inputs


def _traci():
    try:
        module = importlib.import_module("traci")
        if callable(getattr(module, "connect", None)):
            return module
    except ImportError:
        pass
    home = os.environ.get("SUMO_HOME")
    if home:
        sys.path.insert(0, str(Path(home) / "tools"))
        sys.modules.pop("traci", None)
        importlib.invalidate_caches()
        try:
            module = importlib.import_module("traci")
            if callable(getattr(module, "connect", None)):
                return module
        except ImportError:
            pass
    raise RuntimeError("TraCI is unavailable. Install SUMO and set SUMO_HOME to its installation, or install the traci Python package.") from None


def _binary(settings):
    name = "sumo-gui" if settings["gui"] else "sumo"
    configured = settings.get("sumo_binary")
    if configured:
        found = shutil.which(str(configured))
        if found:
            return found
        raise FileNotFoundError(f"Configured SUMO binary not found: {configured}")
    found = shutil.which(name)
    if found:
        return found
    home = os.environ.get("SUMO_HOME")
    if home:
        for suffix in (".exe", ""):
            candidate = Path(home) / "bin" / (name + suffix)
            if candidate.is_file():
                return str(candidate)
    raise FileNotFoundError(f"Cannot find {name}. Add SUMO/bin to PATH, set SUMO_HOME, or set sumo_binary in traci.yaml.")


def _safe_inputs(scenario):
    root, paths = config_inputs(scenario.config_path)
    # Reject output configuration rather than accidentally writing alongside immutable inputs.
    for element in root.iter():
        if element.tag == "output" and len(element):
            raise ValueError("Configured SUMO outputs require explicit redirection support")
        if element.tag in ("log", "message-log", "error-log", "save-state.files", "save-state.prefix"):
            raise ValueError(f"Configured SUMO output is unsupported: {element.tag}")
    for path in paths.get("additional-files", ()):
        for element in ET.parse(path).getroot().iter():
            if any(key in element.attrib for key in ("file", "output", "outputFile")):
                raise ValueError(f"Additional-file output/file attributes require explicit safe handling: {path}")


class Simulation:
    def __init__(self, settings: dict) -> None:
        self.settings = settings
        self.connection = None
        self._process = None

    def start(self, scenario: Scenario, seed: int | None):
        if self.connection is not None or self._process is not None:
            raise RuntimeError("Simulation already started")
        _safe_inputs(scenario)
        traci = _traci()
        binary = _binary(self.settings)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        command = [binary, "-c", str(scenario.config_path), "--step-length", str(self.settings["simulation_step"]),
                   "--remote-port", str(port)]
        if self.settings["gui"]:
            command.extend(("--start", "--quit-on-end"))
        if seed is not None:
            if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
                raise ValueError("seed must be a nonnegative integer or None")
            command.extend(("--seed", str(seed)))
        try:
            self._process = subprocess.Popen(command)
            self.connection = traci.connect(port=port, host="127.0.0.1", proc=self._process)
            return self.connection
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        connection, self.connection = self.connection, None
        try:
            if connection is not None:
                connection.close(wait=False)
        finally:
            process, self._process = self._process, None
            if process is not None and process.poll() is None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
