"""Non-interactive command-line interface for SystemD Manager.

``systemd-manager <command> [options]`` drives services in one command, for
scripts, monitoring and agents. It reuses ``ServiceModel`` (unit generation,
JSON persistence) and ``ServiceValidator`` (validation); systemctl is always
called with an argument list, never through a shell.

Output contract:
    * stdout carries only the command's data: a unit file (``show``,
      ``create --dry-run``), a status or a list. With ``--json`` it is a single
      JSON object, including on error (``{"error": {...}}``).
    * Everything else (progress, warnings, errors) goes to stderr.

Exit codes (stable):
    0  success
    1  usage error (bad arguments, invalid configuration, missing --yes)
    2  service not found
    3  systemd operation failed
    4  insufficient privileges (root required)
"""

import argparse
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any, NoReturn

from src.i18n.translations import i18n
from src.models.screen import (
    SCREEN_BIN,
    build_screen_command,
    screen_session_name,
)
from src.models.service_model import ServiceModel, is_valid_service_name
from src.utils.service_validator import ServiceValidator
from src.utils.timer_units import (
    SYSTEMD_UNIT_DIR,
    remove_managed_timer,
    timer_action_units,
)

PROG = "systemd-manager"
RESTART_CHOICES = ("no", "always", "on-failure")
NETWORK_ONLINE = "network-online.target"
# [Install] directives a generated unit cannot carry over.
_UNPORTABLE_INSTALL = ("Also", "Alias", "RequiredBy", "DefaultInstance")
DEFAULT_WANTED_BY = "multi-user.target"
# A stuck oneshot stays "activating" and silently stops its timer from firing.
DEFAULT_TIMER_TIMEOUT = "1h"
ACTIVE_STATES = ("active", "activating", "reloading")
# systemd.time(7): a bare number of seconds, or numbers each with their unit.
_TIMESPAN_RE = re.compile(
    r"\d+|(?:\d+ *(?:usec|us|msec|ms|seconds|second|sec|s|minutes|minute|min|m"
    r"|hours|hour|hr|h|days|day|d|weeks|week|w|months|month|M|years|year|y) *)+",
    re.ASCII,
)
# Characters of a calendar event; systemd-analyze checks the expression itself.
_CALENDAR_RE = re.compile(r"[A-Za-z0-9*][A-Za-z0-9 ,:*./~+_-]*")
_TIMER_LEFT = "warning: {path} is left as is, not managed by this tool"
_INVALID_SPAN = "invalid time span (example: 5min): {value}"
_INVALID_CALENDAR = "invalid calendar expression (example: hourly): {value}"

# Properties read with `systemctl show`, the machine-readable interface.
_PROPERTIES = (
    "LoadState",
    "ActiveState",
    "SubState",
    "UnitFileState",
    "Result",
    "MainPID",
    "ExecMainStatus",
    "NRestarts",
    "ActiveEnterTimestamp",
    "FragmentPath",
    "DropInPaths",
)
_TIMER_PROPERTIES = (
    "ActiveState",
    "SubState",
    "UnitFileState",
    "NextElapseUSecRealtime",
    "NextElapseUSecMonotonic",
    "LastTriggerUSec",
)


class ExitCode(IntEnum):
    OK = 0
    USAGE = 1
    NOT_FOUND = 2
    SYSTEMD_FAILURE = 3
    PERMISSION = 4


class CliError(Exception):
    """An error reported to the user with a stable exit code."""

    def __init__(self, code: ExitCode, kind: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.kind = kind
        self.message = message


@dataclass
class Context:
    unit_dir: Path
    services_dir: Path


def _t(text: str) -> str:
    return i18n.get_text(text)


def _err(text: str) -> None:
    print(text, file=sys.stderr)


class _Parser(argparse.ArgumentParser):
    """ArgumentParser whose usage errors exit with code 1, not argparse's 2."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(ExitCode.USAGE, f"{self.prog}: error: {message}\n")


def default_services_dir() -> Path:
    """Directory of the JSON service configurations.

    Under sudo this is the invoking user's directory, not root's, so a service
    created with ``sudo systemd-manager create`` is still seen by an
    unprivileged ``list``/``status``.
    """
    home = Path.home()
    sudo_user = os.environ.get("SUDO_USER")
    if os.geteuid() == 0 and sudo_user:
        try:
            home = Path(pwd.getpwnam(sudo_user).pw_dir)
        except KeyError:
            pass
    return home / ".config" / "systemd-manager" / "services"


def _service_name(value: str) -> str:
    name = value.removesuffix(".service")
    if not is_valid_service_name(name):
        raise argparse.ArgumentTypeError(
            _t("invalid service name: {name}").format(name=value)
        )
    return name


def _literal(value: str) -> str:
    """Reject ``%``: systemd would expand it as a specifier (systemd.unit(5))."""
    if "%" in value:
        raise argparse.ArgumentTypeError(
            _t("'%' is not allowed here (systemd specifier): {value}").format(
                value=value
            )
        )
    return value


def _env_pair(value: str) -> tuple[str, str]:
    key, sep, val = value.partition("=")
    if not sep or not key:
        raise argparse.ArgumentTypeError(
            _t("expected KEY=VALUE, got: {value}").format(value=value)
        )
    return key, val


def _timespan(value: str) -> str:
    if not _TIMESPAN_RE.fullmatch(value) or not re.search(r"[1-9]", value):
        raise argparse.ArgumentTypeError(_t(_INVALID_SPAN).format(value=value))
    return value


def _calendar(value: str) -> str:
    if not _CALENDAR_RE.fullmatch(value):
        raise argparse.ArgumentTypeError(_t(_INVALID_CALENDAR).format(value=value))
    return value


def _systemctl(*args: str) -> str:
    """Run systemctl without a shell; raise CliError(3) on failure."""
    try:
        result = subprocess.run(
            ["systemctl", *args], capture_output=True, text=True, check=True
        )
    except FileNotFoundError as e:
        raise CliError(
            ExitCode.SYSTEMD_FAILURE, "systemd_failure", _t("systemctl not found")
        ) from e
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or "").strip() or f"exit {e.returncode}"
        raise CliError(
            ExitCode.SYSTEMD_FAILURE,
            "systemd_failure",
            _t("systemctl {args} failed: {detail}").format(
                args=" ".join(args), detail=detail
            ),
        ) from e
    return result.stdout


def _unit_properties(
    name: str, suffix: str = "service", properties: Sequence[str] = _PROPERTIES
) -> dict[str, str]:
    output = _systemctl(
        "show", f"{name}.{suffix}", "--property=" + ",".join(properties)
    )
    props: dict[str, str] = {}
    for line in output.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            props[key] = value
    return props


def _int_or_none(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _timer_record(name: str, ctx: Context) -> dict[str, Any] | None:
    if not (ctx.unit_dir / f"{name}.timer").exists():
        return None
    props = _unit_properties(name, "timer", _TIMER_PROPERTIES)
    monotonic = props.get("NextElapseUSecMonotonic")
    return {
        "unit": f"{name}.timer",
        "active_state": props.get("ActiveState") or "unknown",
        "sub_state": props.get("SubState") or "unknown",
        "unit_file_state": props.get("UnitFileState") or None,
        "next_run": props.get("NextElapseUSecRealtime") or None,
        # Time since boot, set instead of next_run for --every timers.
        "next_run_monotonic": (
            monotonic if monotonic not in (None, "", "0", "infinity") else None
        ),
        "last_run": props.get("LastTriggerUSec") or None,
    }


def _status_record(name: str, ctx: Context) -> dict[str, Any]:
    props = _unit_properties(name)
    main_pid = _int_or_none(props.get("MainPID"))
    return {
        "name": name,
        "unit": f"{name}.service",
        "managed": (ctx.services_dir / f"{name}.json").is_file(),
        "load_state": props.get("LoadState") or "unknown",
        "active_state": props.get("ActiveState") or "unknown",
        "sub_state": props.get("SubState") or "unknown",
        "unit_file_state": props.get("UnitFileState") or None,
        "result": props.get("Result") or None,
        "main_pid": main_pid or None,
        "exec_main_status": _int_or_none(props.get("ExecMainStatus")),
        "n_restarts": _int_or_none(props.get("NRestarts")),
        "active_since": props.get("ActiveEnterTimestamp") or None,
        "timer": _timer_record(name, ctx),
    }


def _not_found(name: str) -> CliError:
    return CliError(
        ExitCode.NOT_FOUND,
        "not_found",
        _t("service not found: {name}").format(name=name),
    )


def _require_loaded(name: str) -> None:
    if _unit_properties(name).get("LoadState", "not-found") == "not-found":
        raise _not_found(name)


def _require_root() -> None:
    if os.geteuid() != 0:
        raise CliError(
            ExitCode.PERMISSION,
            "permission_denied",
            _t("root privileges required (run with sudo)"),
        )


def _require_yes(args: argparse.Namespace) -> None:
    if not args.yes:
        raise CliError(
            ExitCode.USAGE,
            "confirmation_required",
            _t("refusing to run without --yes (non-interactive mode)"),
        )


def _check_timer_options(args: argparse.Namespace) -> None:
    """Refuse options a timer-run oneshot cannot honour (systemd.service(5))."""
    if not (args.every or args.calendar):
        if args.timeout:
            raise CliError(
                ExitCode.USAGE,
                "invalid_config",
                _t("--timeout requires --every or --calendar"),
            )
        return
    conflicts = [
        option
        for option, used in (
            ("--screen", args.screen),
            ("--restart always", args.restart == "always"),
            ("--wanted-by", args.wanted_by),
        )
        if used
    ]
    if conflicts:
        raise CliError(
            ExitCode.USAGE,
            "invalid_config",
            _t("a timer cannot be combined with {options}").format(
                options=", ".join(conflicts)
            ),
        )


def _check_syntax(kind: str, value: str, message: str) -> None:
    """Ask systemd itself; only reached on install, as a dry-run calls nothing."""
    try:
        subprocess.run(
            ["systemd-analyze", kind, value],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as e:
        raise CliError(
            ExitCode.SYSTEMD_FAILURE,
            "systemd_failure",
            _t("systemd-analyze not found"),
        ) from e
    except subprocess.CalledProcessError as e:
        raise CliError(
            ExitCode.USAGE, "invalid_config", _t(message).format(value=value)
        ) from e


def _build_service(args: argparse.Namespace) -> ServiceModel:
    service = ServiceModel(args.name)
    service.unit.description = args.description or args.name
    if args.after:
        service.unit.after = list(args.after)
        if NETWORK_ONLINE in args.after:
            # After= only orders; Wants= pulls the target in (systemd.special(7)).
            service.unit.wants = [NETWORK_ONLINE]
    service.service.user = args.user
    service.service.working_directory = args.workdir or ""
    service.service.exec_start = (
        build_screen_command(screen_session_name(args.name), args.exec)
        if args.screen
        else args.exec
    )
    service.service.restart = args.restart
    service.service.restart_sec = args.restart_sec
    service.service.environment = dict(args.env) if args.env else None
    # RemainAfterExit=yes would keep a cleanly exited process "active" and stop
    # Restart= from relaunching it.
    service.service.remain_after_exit = False
    service.timer.every = args.every or ""
    service.timer.on_calendar = args.calendar or ""
    if service.has_timer:
        # The timer is what gets enabled; the service only runs when it fires.
        service.service.type = "oneshot"
        service.timer.timeout = args.timeout or DEFAULT_TIMER_TIMEOUT
    else:
        service.install.wanted_by = [args.wanted_by or DEFAULT_WANTED_BY]
    return service


def _render_units(service: ServiceModel) -> str:
    """The unit file, preceded by a header per file when there are two."""
    unit_text = service.to_systemd_file()
    if not service.has_timer:
        return unit_text
    return (
        f"# {service.name}.service\n{unit_text}\n"
        f"# {service.name}.timer\n{service.to_timer_file()}"
    )


def _unportable_install(unit_path: Path) -> list[str]:
    """Old [Install] directives that adopting would silently drop."""
    section = ""
    found: list[str] = []
    wanted_by: list[str] = []
    for raw in unit_path.read_text(errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("["):
            section = line
        elif section == "[Install]":
            key, _, value = line.partition("=")
            if key.strip() == "WantedBy":
                wanted_by += value.split()
            elif key.strip() in _UNPORTABLE_INSTALL:
                found.append(key.strip())
    # --wanted-by only takes one target.
    return found + ["WantedBy"] * (len(wanted_by) > 1)


def _unit_exists(unit_path: Path, props: dict[str, str]) -> bool:
    return (
        unit_path.exists()
        or unit_path.is_symlink()
        or props.get("LoadState", "not-found") != "not-found"
    )


def _check_replaceable(name: str, unit_path: Path, props: dict[str, str]) -> None:
    """Refuse anything but a regular unit file in the unit directory."""
    fragment = props.get("FragmentPath")
    # A symlink would be written through (a masked unit points to /dev/null), and
    # a unit loaded from elsewhere (package, /run) is not the file replaced here.
    if (
        unit_path.is_symlink()
        or not unit_path.is_file()
        or props.get("LoadState") == "masked"
        or (fragment and fragment != str(unit_path))
    ):
        raise CliError(
            ExitCode.USAGE,
            "not_adoptable",
            _t("{name} cannot be adopted: not a regular unit file in {path}").format(
                name=name, path=unit_path.parent
            ),
        )
    unportable = _unportable_install(unit_path)
    if unportable:
        raise CliError(
            ExitCode.USAGE,
            "not_adoptable",
            _t(
                "{name} cannot be adopted: [Install] would lose {directives}; "
                "remove them from the unit first"
            ).format(name=name, directives=", ".join(sorted(set(unportable)))),
        )


def _check_adoptable(
    name: str, unit_path: Path, config: Path, props: dict[str, str]
) -> None:
    if config.is_file():
        raise CliError(
            ExitCode.USAGE,
            "already_managed",
            _t("service {name} is already managed; remove it first").format(name=name),
        )
    if not _unit_exists(unit_path, props):
        raise _not_found(name)
    _check_replaceable(name, unit_path, props)


def _backup_unit(unit_path: Path) -> Path:
    """Copy a unit aside, keeping its mode; systemd ignores this file suffix."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = unit_path.with_name(f"{unit_path.name}.adopted-{stamp}")
    shutil.copy2(unit_path, backup)
    return backup


def _replace_file(path: Path, text: str) -> None:
    """Write ``path`` atomically: a failure leaves the previous content intact."""
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        with tmp.open("w") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


@dataclass
class _Adopted:
    """A unit file about to be replaced, and what it takes to hand it back."""

    path: Path
    backup: Path | None
    enabled: bool


def _backup_adopted(path: Path, props: dict[str, str]) -> _Adopted:
    if not path.exists():
        return _Adopted(path, None, False)
    backup = _backup_unit(path)
    _err(_t("previous unit saved to {path}").format(path=backup))
    return _Adopted(path, backup, props.get("UnitFileState") == "enabled")


def _restore_file(backup: Path, path: Path) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        shutil.copy2(backup, tmp)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _undo_adoption(adopted: list[_Adopted], config: Path) -> None:
    """Hand the previous units back after a failed install, as far as possible."""
    try:
        config.unlink(missing_ok=True)
        for unit in adopted:
            if unit.backup:
                _restore_file(unit.backup, unit.path)
            else:
                unit.path.unlink(missing_ok=True)
        _systemctl("daemon-reload")
        for unit in adopted:
            if unit.enabled:
                _systemctl("enable", unit.path.name)
    except (OSError, CliError) as e:
        _err(_t("warning: {message}").format(message=str(e)))
    else:
        _err(_t("previous unit restored"))


def _require_unit_loads(unit_name: str) -> None:
    """A unit can be enabled yet be rejected at start: check what systemd loaded."""
    name, _, suffix = unit_name.rpartition(".")
    state = _unit_properties(name, suffix).get("LoadState")
    if state != "loaded":
        raise CliError(
            ExitCode.SYSTEMD_FAILURE,
            "invalid_unit",
            _t("systemd rejects the new unit of {name} ({state})").format(
                name=unit_name, state=state
            ),
        )


def _warn_adopted(name: str, props: dict[str, str]) -> None:
    if props.get("ActiveState") in ACTIVE_STATES:
        _err(
            _t(
                "warning: {name} is still running its old configuration; restart it"
            ).format(name=name)
        )
    if props.get("DropInPaths"):
        _err(
            _t("warning: these drop-ins still apply to {name}: {paths}").format(
                name=name, paths=props["DropInPaths"]
            )
        )


def cmd_create(args: argparse.Namespace, ctx: Context) -> int:
    _check_timer_options(args)
    check_host = not args.dry_run
    result = ServiceValidator().validate_service_config(
        {
            "name": args.name,
            "command": args.exec,
            "working_directory": args.workdir or "",
            "restart": args.restart,
            "restart_sec": str(args.restart_sec),
            "user": args.user,
        },
        check_host=check_host,
    )
    errors = list(result.errors)
    if args.screen and check_host and not Path(SCREEN_BIN).exists():
        errors.append(_t("GNU Screen is not installed: {path}").format(path=SCREEN_BIN))
    for warning in result.warnings:
        _err(_t("warning: {message}").format(message=_t(warning)))
    for error in errors:
        _err(_t("error: {message}").format(message=_t(error)))
    if errors:
        raise CliError(
            ExitCode.USAGE, "invalid_config", _t("invalid service configuration")
        )

    service = _build_service(args)
    try:
        rendered = _render_units(service)
    except ValueError as e:
        raise CliError(ExitCode.USAGE, "invalid_config", _t(str(e))) from e

    if args.dry_run:
        sys.stdout.write(rendered)
        return ExitCode.OK

    _require_yes(args)
    _require_root()
    if args.calendar:
        _check_syntax("calendar", args.calendar, _INVALID_CALENDAR)
    for span in (args.every, args.timeout):
        if span:
            _check_syntax("timespan", span, _INVALID_SPAN)
    unit_path = ctx.unit_dir / f"{args.name}.service"
    timer_path = ctx.unit_dir / f"{args.name}.timer"
    config = ctx.services_dir / f"{args.name}.json"
    props = _unit_properties(args.name)
    timer_props = _unit_properties(args.name, "timer") if service.has_timer else {}
    if args.adopt:
        _check_adoptable(args.name, unit_path, config, props)
        if service.has_timer and props.get("ActiveState") in ACTIVE_STATES:
            # A timer cannot start a unit that is already active: it would keep
            # running its old configuration and every firing would be a no-op.
            raise CliError(
                ExitCode.USAGE,
                "not_adoptable",
                _t(
                    "{name} is active and a timer could not run it; stop it first"
                ).format(name=args.name),
            )
        if service.has_timer and _unit_exists(timer_path, timer_props):
            _check_replaceable(f"{args.name}.timer", timer_path, timer_props)
    elif _unit_exists(unit_path, props) or (
        service.has_timer and _unit_exists(timer_path, timer_props)
    ):
        hint = (
            "a unit named {name} already exists; remove it first"
            if config.is_file()
            else "a unit named {name} already exists; --adopt takes it over"
        )
        raise CliError(
            ExitCode.USAGE, "already_exists", _t(hint).format(name=args.name)
        )

    adopted: list[_Adopted] = []
    if args.adopt:
        adopted.append(_backup_adopted(unit_path, props))
        if service.has_timer:
            adopted.append(_backup_adopted(timer_path, timer_props))
    written = [(unit_path, service.to_systemd_file())]
    if service.has_timer:
        written.append((timer_path, service.to_timer_file()))
    try:
        service.save_to_json(str(config))
        for unit in adopted:
            if unit.backup:
                # While the old [Install] section is still there, so that its
                # symlinks do not outlive it.
                _systemctl("disable", unit.path.name)
        for path, text in written:
            _replace_file(path, text)
        _systemctl("daemon-reload")
        for unit in adopted:
            _require_unit_loads(unit.path.name)
        _systemctl("enable", written[-1][0].name)
    except (OSError, ValueError, CliError) as e:
        if adopted:
            _undo_adoption(adopted, config)
        if isinstance(e, CliError):
            raise
        # save_to_json wraps OSError in ValueError; keep the permission case.
        denied = isinstance(e, PermissionError) or isinstance(
            e.__cause__, PermissionError
        )
        code = ExitCode.PERMISSION if denied else ExitCode.SYSTEMD_FAILURE
        raise CliError(code, "write_failed", _t(str(e))) from e
    if args.adopt:
        _warn_adopted(args.name, props)
    if not service.has_timer and timer_path.exists():
        _err(_t(_TIMER_LEFT).format(path=timer_path))
    if service.has_timer:
        _err(
            _t("timer of {name} installed and enabled; `start {name}` arms it").format(
                name=args.name
            )
        )
    else:
        _err(_t("service {name} installed and enabled").format(name=args.name))
    return ExitCode.OK


def cmd_action(args: argparse.Namespace, ctx: Context) -> int:
    _require_loaded(args.name)
    _require_root()
    config = ctx.services_dir / f"{args.name}.json"
    units = timer_action_units(args.command, args.name, config, ctx.unit_dir)
    _systemctl(args.command, *(units or [f"{args.name}.service"]))
    _err(_t("{action}: {name} done").format(action=args.command, name=args.name))
    return ExitCode.OK


def cmd_run(args: argparse.Namespace, ctx: Context) -> int:
    """Run the service now, without touching its timer; waits for a oneshot."""
    _require_loaded(args.name)
    _require_root()
    _systemctl("start", f"{args.name}.service")
    _err(_t("{action}: {name} done").format(action=args.command, name=args.name))
    return ExitCode.OK


_STATUS_LABELS = (
    ("Service", "unit"),
    ("Managed by systemd-manager", "managed"),
    ("Load state", "load_state"),
    ("Active state", "active_state"),
    ("Sub state", "sub_state"),
    ("Unit file state", "unit_file_state"),
    ("Main PID", "main_pid"),
    ("Restarts", "n_restarts"),
    ("Active since", "active_since"),
)


def cmd_status(args: argparse.Namespace, ctx: Context) -> int:
    record = _status_record(args.name, ctx)
    if record["load_state"] == "not-found":
        raise _not_found(args.name)
    if args.json:
        print(json.dumps(record))
    else:
        for label, key in _STATUS_LABELS:
            print(f"{_t(label)}: {record[key]}")
        timer = record["timer"]
        if timer:
            next_run = timer["next_run"] or timer["next_run_monotonic"]
            print(f"{_t('Timer')}: {timer['active_state']}")
            print(f"{_t('Next run')}: {next_run}")
            print(f"{_t('Last run')}: {timer['last_run']}")
    return ExitCode.OK


def cmd_list(args: argparse.Namespace, ctx: Context) -> int:
    names = (
        sorted(
            path.stem
            for path in ctx.services_dir.glob("*.json")
            if is_valid_service_name(path.stem)
        )
        if ctx.services_dir.is_dir()
        else []
    )
    records = [_status_record(name, ctx) for name in names]
    if args.json:
        print(json.dumps({"services": records}))
    elif not records:
        _err(_t("no service managed by systemd-manager"))
    else:
        for record in records:
            print(
                "\t".join(
                    str(record[key])
                    for key in ("name", "active_state", "sub_state", "unit_file_state")
                )
            )
    return ExitCode.OK


def cmd_show(args: argparse.Namespace, ctx: Context) -> int:
    config = ctx.services_dir / f"{args.name}.json"
    if not config.is_file():
        raise _not_found(args.name)
    try:
        rendered = _render_units(ServiceModel.load_from_json(str(config)))
    except ValueError as e:
        raise CliError(ExitCode.USAGE, "invalid_config", _t(str(e))) from e
    sys.stdout.write(rendered)
    return ExitCode.OK


def cmd_remove(args: argparse.Namespace, ctx: Context) -> int:
    _require_yes(args)
    config = ctx.services_dir / f"{args.name}.json"
    unit_path = ctx.unit_dir / f"{args.name}.service"
    if not config.is_file():
        # Only services created by this tool are removed.
        if unit_path.exists() or unit_path.is_symlink():
            raise CliError(
                ExitCode.NOT_FOUND,
                "not_managed",
                _t(
                    "{name} is not managed by this tool, nothing removed; "
                    "create --adopt takes it over"
                ).format(name=args.name),
            )
        raise _not_found(args.name)
    _require_root()
    try:
        # First, so that it cannot fire while the service is going away.
        reload_needed = remove_managed_timer(args.name, config, ctx.unit_dir)
        if unit_path.exists():
            _systemctl("stop", f"{args.name}.service")
            _systemctl("disable", f"{args.name}.service")
            unit_path.unlink()
            reload_needed = True
        if reload_needed:
            _systemctl("daemon-reload")
        config.unlink()
    except subprocess.CalledProcessError as e:
        raise CliError(
            ExitCode.SYSTEMD_FAILURE,
            "systemd_failure",
            _t("systemctl {args} failed: {detail}").format(
                args=" ".join(e.cmd[1:]),
                detail=(e.stderr or "").strip() or f"exit {e.returncode}",
            ),
        ) from e
    except PermissionError as e:
        raise CliError(ExitCode.PERMISSION, "permission_denied", str(e)) from e
    except OSError as e:
        raise CliError(ExitCode.SYSTEMD_FAILURE, "remove_failed", str(e)) from e
    timer_path = ctx.unit_dir / f"{args.name}.timer"
    if timer_path.exists():
        _err(_t(_TIMER_LEFT).format(path=timer_path))
    _err(_t("service {name} removed").format(name=args.name))
    return ExitCode.OK


Handler = Callable[[argparse.Namespace, Context], int]


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog=PROG,
        description=_t("Manage systemd services non-interactively."),
        epilog=_t(
            "Exit codes: 0 success, 1 usage error, 2 service not found, "
            "3 systemd failure, 4 insufficient privileges. "
            "Without arguments, the interactive menu opens."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    create = sub.add_parser("create", help=_t("create and install a service"))
    create.add_argument("--name", required=True, type=_service_name)
    create.add_argument(
        "--exec", required=True, help=_t("absolute command to run (ExecStart)")
    )
    create.add_argument(
        "--user", required=True, type=_literal, help=_t("user running the service")
    )
    create.add_argument(
        "--workdir", type=_literal, help=_t("absolute working directory")
    )
    create.add_argument(
        "--description", type=_literal, help=_t("defaults to the service name")
    )
    create.add_argument("--restart", choices=RESTART_CHOICES, default="no")
    create.add_argument(
        "--restart-sec", type=int, default=0, help=_t("delay before restart (s)")
    )
    create.add_argument(
        "--after",
        action="append",
        type=_literal,
        help=_t("ordering dependency (repeatable)"),
    )
    create.add_argument(
        "--wanted-by",
        type=_literal,
        help=_t("defaults to {target}").format(target=DEFAULT_WANTED_BY),
    )
    schedule = create.add_mutually_exclusive_group()
    schedule.add_argument(
        "--every",
        type=_timespan,
        metavar="SPAN",
        help=_t("run periodically through a timer (example: 5min)"),
    )
    schedule.add_argument(
        "--calendar",
        type=_calendar,
        metavar="EXPR",
        help=_t("run on a schedule through a timer (example: hourly)"),
    )
    create.add_argument(
        "--timeout",
        type=_timespan,
        metavar="SPAN",
        help=_t("kill a timer-run service after SPAN (default: {span})").format(
            span=DEFAULT_TIMER_TIMEOUT
        ),
    )
    create.add_argument(
        "--env",
        action="append",
        type=_env_pair,
        metavar="KEY=VALUE",
        help=_t("environment variable (repeatable)"),
    )
    create.add_argument(
        "--screen", action="store_true", help=_t("run inside a GNU Screen session")
    )
    create.add_argument(
        "--dry-run",
        action="store_true",
        help=_t("print the unit to stdout; install nothing, call nothing"),
    )
    create.add_argument(
        "--adopt",
        action="store_true",
        help=_t("take over an existing unmanaged unit (a copy is kept)"),
    )
    create.add_argument("--yes", action="store_true", help=_t("skip confirmation"))
    create.set_defaults(handler=cmd_create)

    for action in ("start", "stop", "restart", "enable", "disable"):
        p = sub.add_parser(action, help=_t("systemctl {action}").format(action=action))
        p.add_argument("name", type=_service_name)
        p.set_defaults(handler=cmd_action)

    run = sub.add_parser("run", help=_t("run the service once, now"))
    run.add_argument("name", type=_service_name)
    run.set_defaults(handler=cmd_run)

    status = sub.add_parser("status", help=_t("show the state of a service"))
    status.add_argument("name", type=_service_name)
    status.add_argument("--json", action="store_true", help=_t("JSON output"))
    status.set_defaults(handler=cmd_status)

    list_ = sub.add_parser("list", help=_t("list services managed by this tool"))
    list_.add_argument("--json", action="store_true", help=_t("JSON output"))
    list_.set_defaults(handler=cmd_list)

    show = sub.add_parser("show", help=_t("print the generated unit file"))
    show.add_argument("name", type=_service_name)
    show.set_defaults(handler=cmd_show)

    remove = sub.add_parser("remove", help=_t("stop, disable and delete a service"))
    remove.add_argument("name", type=_service_name)
    remove.add_argument("--yes", action="store_true", help=_t("required"))
    remove.set_defaults(handler=cmd_remove)

    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    unit_dir: Path = SYSTEMD_UNIT_DIR,
    services_dir: Path | None = None,
) -> int:
    """Parse ``argv``, run the command and return its exit code."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else ExitCode.USAGE
        if code != ExitCode.OK and "--json" in (argv if argv is not None else sys.argv):
            _print_json_error(
                CliError(ExitCode.USAGE, "usage", _t("invalid arguments"))
            )
        return code

    ctx = Context(
        unit_dir=unit_dir, services_dir=services_dir or default_services_dir()
    )
    handler: Handler = args.handler
    try:
        return int(handler(args, ctx))
    except PermissionError as e:
        error = CliError(ExitCode.PERMISSION, "permission_denied", str(e))
    except OSError as e:
        error = CliError(ExitCode.SYSTEMD_FAILURE, "os_error", str(e))
    except CliError as e:
        error = e
    _err(_t("error: {message}").format(message=error.message))
    if getattr(args, "json", False):
        _print_json_error(error)
    return int(error.code)


def _print_json_error(error: CliError) -> None:
    print(
        json.dumps(
            {
                "error": {
                    "code": int(error.code),
                    "kind": error.kind,
                    "message": error.message,
                }
            }
        )
    )
