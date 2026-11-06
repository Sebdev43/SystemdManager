"""Timer units managed by this tool, shared by every interface that deletes one."""

import subprocess
from pathlib import Path

from src.models.service_model import ServiceModel

SYSTEMD_UNIT_DIR = Path("/etc/systemd/system")


def has_managed_timer(config: Path, timer_path: Path) -> bool:
    """True when ``timer_path`` exists and the tool's configuration declares it.

    A hand-written timer of the same name is not ours and stays untouched.
    """
    if not timer_path.exists():
        return False
    try:
        return ServiceModel.load_from_json(str(config)).has_timer
    except ValueError:
        return False


def timer_action_units(
    action: str, name: str, config: Path, unit_dir: Path = SYSTEMD_UNIT_DIR
) -> list[str] | None:
    """Units an action applies to when a timer drives the service, else None."""
    timer_path = unit_dir / f"{name}.timer"
    if not has_managed_timer(config, timer_path):
        return None
    # Stopping only the timer would leave a run in progress.
    if action == "stop":
        return [timer_path.name, f"{name}.service"]
    return [timer_path.name]


def remove_managed_timer(
    name: str, config: Path, unit_dir: Path = SYSTEMD_UNIT_DIR
) -> bool:
    """Stop, disable and delete the service's timer; return whether one existed.

    Raises subprocess.CalledProcessError or OSError when a step fails.
    """
    timer_path = unit_dir / f"{name}.timer"
    if not has_managed_timer(config, timer_path):
        return False
    for verb in ("stop", "disable"):
        subprocess.run(
            ["systemctl", verb, timer_path.name],
            capture_output=True,
            text=True,
            check=True,
        )
    timer_path.unlink()
    return True
