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
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
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

PROG = "systemd-manager"
SYSTEMD_UNIT_DIR = Path("/etc/systemd/system")
RESTART_CHOICES = ("no", "always", "on-failure")
NETWORK_ONLINE = "network-online.target"

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


def _unit_properties(name: str) -> dict[str, str]:
    output = _systemctl(
        "show", f"{name}.service", "--property=" + ",".join(_PROPERTIES)
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
    service.install.wanted_by = [args.wanted_by]
    return service


def cmd_create(args: argparse.Namespace, ctx: Context) -> int:
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
        unit_text = service.to_systemd_file()
    except ValueError as e:
        raise CliError(ExitCode.USAGE, "invalid_config", _t(str(e))) from e

    if args.dry_run:
        sys.stdout.write(unit_text)
        return ExitCode.OK

    _require_yes(args)
    _require_root()
    unit_path = ctx.unit_dir / f"{args.name}.service"
    loaded = _unit_properties(args.name).get("LoadState", "not-found")
    if unit_path.exists() or loaded != "not-found":
        raise CliError(
            ExitCode.USAGE,
            "already_exists",
            _t("a unit named {name} already exists; remove it first").format(
                name=args.name
            ),
        )

    try:
        service.save_to_json(str(ctx.services_dir / f"{args.name}.json"))
        unit_path.write_text(unit_text)
    except (OSError, ValueError) as e:
        # save_to_json wraps OSError in ValueError; keep the permission case.
        denied = isinstance(e, PermissionError) or isinstance(
            e.__cause__, PermissionError
        )
        code = ExitCode.PERMISSION if denied else ExitCode.SYSTEMD_FAILURE
        raise CliError(code, "write_failed", _t(str(e))) from e
    _systemctl("daemon-reload")
    _systemctl("enable", f"{args.name}.service")
    _err(_t("service {name} installed and enabled").format(name=args.name))
    return ExitCode.OK


def cmd_action(args: argparse.Namespace, ctx: Context) -> int:
    _require_loaded(args.name)
    _require_root()
    _systemctl(args.command, f"{args.name}.service")
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
        unit_text = ServiceModel.load_from_json(str(config)).to_systemd_file()
    except ValueError as e:
        raise CliError(ExitCode.USAGE, "invalid_config", _t(str(e))) from e
    sys.stdout.write(unit_text)
    return ExitCode.OK


def cmd_remove(args: argparse.Namespace, ctx: Context) -> int:
    _require_yes(args)
    config = ctx.services_dir / f"{args.name}.json"
    if not config.is_file():
        # Only services created by this tool are removed.
        raise _not_found(args.name)
    _require_root()
    unit_path = ctx.unit_dir / f"{args.name}.service"
    try:
        if unit_path.exists():
            _systemctl("stop", f"{args.name}.service")
            _systemctl("disable", f"{args.name}.service")
            unit_path.unlink()
            _systemctl("daemon-reload")
        config.unlink()
    except PermissionError as e:
        raise CliError(ExitCode.PERMISSION, "permission_denied", str(e)) from e
    except OSError as e:
        raise CliError(ExitCode.SYSTEMD_FAILURE, "remove_failed", str(e)) from e
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
    create.add_argument("--wanted-by", type=_literal, default="multi-user.target")
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
    create.add_argument("--yes", action="store_true", help=_t("skip confirmation"))
    create.set_defaults(handler=cmd_create)

    for action in ("start", "stop", "restart", "enable", "disable"):
        p = sub.add_parser(action, help=_t("systemctl {action}").format(action=action))
        p.add_argument("name", type=_service_name)
        p.set_defaults(handler=cmd_action)

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
