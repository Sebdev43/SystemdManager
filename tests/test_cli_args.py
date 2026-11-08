"""Tests for the non-interactive command line (src/cli/cli_args.py).

subprocess is always faked and every path points to a temporary directory:
no test touches /etc/systemd/system or needs privileges.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.cli import cli_args
from src.cli.cli_args import ExitCode, build_parser

LOADED = {
    "LoadState": "loaded",
    "ActiveState": "active",
    "SubState": "running",
    "UnitFileState": "enabled",
    "Result": "success",
    "MainPID": "4242",
    "ExecMainStatus": "0",
    "NRestarts": "3",
    "ActiveEnterTimestamp": "Sun 2026-11-01 10:00:00 CET",
}
NOT_FOUND = {
    "LoadState": "not-found",
    "ActiveState": "inactive",
    "SubState": "dead",
    "MainPID": "0",
}

PROXIMA_UNIT = """\
[Unit]
Description=proxima-test
After=network-online.target
Wants=network-online.target
StartLimitBurst=5
StartLimitIntervalSec=10

[Service]
Type=simple
User=seb43
WorkingDirectory=/home/seb43/proxima-node
ExecStart=/home/seb43/proxima-node/bin/proxima
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

PROXIMA_ARGS = [
    "create",
    "--name",
    "proxima-test",
    "--exec",
    "/home/seb43/proxima-node/bin/proxima",
    "--workdir",
    "/home/seb43/proxima-node",
    "--user",
    "seb43",
    "--restart",
    "always",
    "--restart-sec",
    "10",
    "--after",
    "network-online.target",
]


class FakeRun:
    """Stand-in for subprocess.run that records systemctl calls."""

    def __init__(
        self,
        props: dict[str, str] | None = None,
        fail_on: str | None = None,
        missing: bool = False,
        fail_once: str | None = None,
        props_after_reload: dict[str, str] | None = None,
        timer_props: dict[str, str] | None = None,
    ) -> None:
        self.props = LOADED if props is None else props
        self.fail_on = fail_on
        self.missing = missing
        self.fail_once = fail_once
        self.props_after_reload = props_after_reload
        self.timer_props = timer_props  # until the next daemon-reload
        self.calls: list[list[str]] = []

    def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
        assert isinstance(cmd, list)
        assert kwargs.get("check") is True
        assert not kwargs.get("shell")
        self.calls.append(cmd)
        if self.missing:
            raise FileNotFoundError(cmd[0])
        if cmd[0] == "systemd-analyze" and self.fail_on == "calendar":
            raise subprocess.CalledProcessError(1, cmd, stderr="boom")
        if cmd[0] == "systemctl" and cmd[1] == self.fail_on:
            raise subprocess.CalledProcessError(1, cmd, stderr="boom")
        if cmd[0] == "systemctl" and cmd[1] == self.fail_once:
            self.fail_once = None
            raise subprocess.CalledProcessError(1, cmd, stderr="boom")
        if cmd[:2] == ["systemctl", "daemon-reload"]:
            self.timer_props = None
            if self.props_after_reload:
                self.props, self.props_after_reload = self.props_after_reload, None
        if cmd[:2] == ["systemctl", "show"]:
            props = self.props
            if self.timer_props is not None and cmd[2].endswith(".timer"):
                props = self.timer_props
            out = "".join(f"{k}={v}\n" for k, v in props.items())
            return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    @property
    def verbs(self) -> list[str]:
        return [c[1] for c in self.calls if c[0] == "systemctl"]


@pytest.fixture
def dirs(tmp_path: Path) -> dict[str, Path]:
    unit_dir = tmp_path / "units"
    services_dir = tmp_path / "services"
    unit_dir.mkdir()
    services_dir.mkdir()
    return {"unit_dir": unit_dir, "services_dir": services_dir}


def run(
    argv: list[str],
    dirs: dict[str, Path],
    fake: FakeRun | None = None,
    root: bool = True,
) -> int:
    fake = fake or FakeRun()
    with (
        patch.object(cli_args.subprocess, "run", fake),
        patch.object(cli_args.os, "geteuid", return_value=0 if root else 1000),
    ):
        return cli_args.main(argv, **dirs)


def add_config(dirs: dict[str, Path], name: str = "proxima-test") -> Path:
    from src.models.service_model import ServiceModel

    service = ServiceModel(name)
    service.unit.description = "Proxima"
    service.service.exec_start = "/opt/proxima/bin/proxima"
    service.service.user = "seb43"
    service.service.remain_after_exit = False
    service.install.wanted_by = ["multi-user.target"]
    path = dirs["services_dir"] / f"{name}.json"
    service.save_to_json(str(path))
    return path


# --- argument parsing ------------------------------------------------------


def test_create_defaults() -> None:
    args = build_parser().parse_args(
        ["create", "--name", "a", "--exec", "/x", "--user", "u"]
    )
    assert args.handler is cli_args.cmd_create
    assert args.restart == "no"
    assert args.restart_sec == 0
    assert args.after is None
    assert args.env is None
    assert args.wanted_by is None
    assert args.workdir is None and args.description is None
    assert not (args.screen or args.dry_run or args.yes)


def test_create_all_options() -> None:
    args = build_parser().parse_args(
        PROXIMA_ARGS
        + ["--after", "b.target", "--env", "A=1", "--env", "B=x=y", "--screen"]
        + ["--wanted-by", "default.target", "--description", "d", "--dry-run", "--yes"]
    )
    assert args.after == ["network-online.target", "b.target"]
    assert args.env == [("A", "1"), ("B", "x=y")]
    assert args.restart == "always" and args.restart_sec == 10
    assert args.screen and args.dry_run and args.yes
    assert args.wanted_by == "default.target"


@pytest.mark.parametrize("action", ["start", "stop", "restart", "enable", "disable"])
def test_action_parsing(action: str) -> None:
    args = build_parser().parse_args([action, "proxima-test.service"])
    assert args.handler is cli_args.cmd_action
    assert args.command == action
    assert args.name == "proxima-test"  # .service suffix stripped


@pytest.mark.parametrize(
    ("argv", "handler"),
    [
        (["status", "x"], cli_args.cmd_status),
        (["list"], cli_args.cmd_list),
        (["show", "x"], cli_args.cmd_show),
        (["remove", "x"], cli_args.cmd_remove),
    ],
)
def test_other_commands_parsing(argv: list[str], handler: object) -> None:
    args = build_parser().parse_args(argv)
    assert args.handler is handler


def test_option_defaults() -> None:
    parser = build_parser()
    assert parser.parse_args(["status", "x"]).json is False
    assert parser.parse_args(["list"]).json is False
    assert parser.parse_args(["remove", "x"]).yes is False


def test_json_and_yes_flags() -> None:
    parser = build_parser()
    assert parser.parse_args(["status", "x", "--json"]).json
    assert parser.parse_args(["list", "--json"]).json
    assert parser.parse_args(["remove", "x", "--yes"]).yes


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["bogus"],
        ["create", "--exec", "/x", "--user", "u"],  # missing --name
        [
            "create",
            "--name",
            "a",
            "--exec",
            "/x",
            "--user",
            "u",
            "--restart",
            "sometimes",
        ],
        [
            "create",
            "--name",
            "a",
            "--exec",
            "/x",
            "--user",
            "u",
            "--restart-sec",
            "ten",
        ],
        ["create", "--name", "a", "--exec", "/x", "--user", "u", "--env", "NOEQUAL"],
        ["create", "--name", "../etc/passwd", "--exec", "/x", "--user", "u"],
        ["start"],
        ["status", "bad name"],
        ["list", "extra"],
    ],
)
def test_invalid_arguments_exit_1(
    argv: list[str], dirs: dict[str, Path], capsys
) -> None:
    fake = FakeRun()
    assert run(argv, dirs, fake) == ExitCode.USAGE
    assert fake.calls == []
    assert capsys.readouterr().out == ""


def test_help_exits_0(dirs: dict[str, Path], capsys) -> None:
    assert run(["--help"], dirs) == ExitCode.OK
    assert "systemd-manager" in capsys.readouterr().out


# --- create ----------------------------------------------------------------


def test_create_dry_run_unit_content(dirs: dict[str, Path], capsys) -> None:
    fake = FakeRun()
    assert run(PROXIMA_ARGS + ["--dry-run"], dirs, fake, root=False) == ExitCode.OK
    assert capsys.readouterr().out == PROXIMA_UNIT
    assert fake.calls == []  # no systemctl, no `id`
    assert list(dirs["unit_dir"].iterdir()) == []
    assert list(dirs["services_dir"].iterdir()) == []


def test_create_dry_run_env_and_screen(dirs: dict[str, Path], capsys) -> None:
    argv = PROXIMA_ARGS + ["--env", 'MSG=a "b" 50%', "--screen", "--dry-run"]
    assert run(argv, dirs, root=False) == ExitCode.OK
    out = capsys.readouterr().out
    assert 'Environment="MSG=a \\"b\\" 50%%"\n' in out
    assert (
        "ExecStart=/usr/bin/screen -DmS service_proxima-test "
        "/home/seb43/proxima-node/bin/proxima\n"
    ) in out
    assert "ExecStop=/usr/bin/screen -S service_proxima-test -X quit\n" in out
    assert "RemainAfterExit" not in out


@pytest.mark.parametrize(
    "extra",
    [
        ["--exec", "relative/bin"],
        ["--workdir", "relative"],
        ["--env", "1BAD=x"],
        ["--description", "a\nExecStartPre=/bin/evil"],
        ["--exec", "/bin/foo \\"],  # trailing backslash would splice next line
        ["--description", "50%"],
        ["--after", "%n.target"],
    ],
)
def test_create_dry_run_invalid_config_exit_1(
    extra: list[str], dirs: dict[str, Path], capsys
) -> None:
    assert run(PROXIMA_ARGS + extra + ["--dry-run"], dirs) == ExitCode.USAGE
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err


def test_create_requires_yes(dirs: dict[str, Path]) -> None:
    fake = FakeRun()
    with patch.object(cli_args.ServiceValidator, "_validate_user"):
        assert run(_local_create_args(), dirs, fake) == ExitCode.USAGE
    assert fake.calls == []
    assert list(dirs["unit_dir"].iterdir()) == []


def test_create_requires_root(dirs: dict[str, Path]) -> None:
    fake = FakeRun()
    with patch.object(cli_args.ServiceValidator, "_validate_user"):
        argv = _local_create_args() + ["--yes"]
        assert run(argv, dirs, fake, root=False) == ExitCode.PERMISSION
    assert list(dirs["unit_dir"].iterdir()) == []


def test_create_installs(dirs: dict[str, Path]) -> None:
    fake = FakeRun(props=NOT_FOUND)
    with patch.object(cli_args.ServiceValidator, "_validate_user"):
        assert run(_local_create_args() + ["--yes"], dirs, fake) == ExitCode.OK
    unit = (dirs["unit_dir"] / "local-test.service").read_text()
    assert "ExecStart=/bin/true\n" in unit
    assert (dirs["services_dir"] / "local-test.json").is_file()
    assert fake.verbs == ["show", "daemon-reload", "enable"]


def test_create_refuses_existing_unit(dirs: dict[str, Path]) -> None:
    fake = FakeRun(props=LOADED)
    with patch.object(cli_args.ServiceValidator, "_validate_user"):
        assert run(_local_create_args() + ["--yes"], dirs, fake) == ExitCode.USAGE
    assert fake.verbs == ["show"]
    assert list(dirs["unit_dir"].iterdir()) == []


def test_create_systemctl_failure_exit_3(dirs: dict[str, Path]) -> None:
    fake = FakeRun(props=NOT_FOUND, fail_on="daemon-reload")
    with patch.object(cli_args.ServiceValidator, "_validate_user"):
        argv = _local_create_args() + ["--yes"]
        assert run(argv, dirs, fake) == ExitCode.SYSTEMD_FAILURE


def _local_create_args() -> list[str]:
    return ["create", "--name", "local-test", "--exec", "/bin/true", "--user", "root"]


# --- start / stop / restart / enable / disable ------------------------------


@pytest.mark.parametrize("action", ["start", "stop", "restart", "enable", "disable"])
def test_action_success(action: str, dirs: dict[str, Path]) -> None:
    fake = FakeRun()
    assert run([action, "proxima-test"], dirs, fake) == ExitCode.OK
    assert fake.calls[-1] == ["systemctl", action, "proxima-test.service"]


def test_action_not_found_exit_2(dirs: dict[str, Path]) -> None:
    fake = FakeRun(props=NOT_FOUND)
    assert run(["start", "ghost"], dirs, fake) == ExitCode.NOT_FOUND
    assert fake.verbs == ["show"]


def test_action_not_root_exit_4(dirs: dict[str, Path]) -> None:
    fake = FakeRun()
    assert run(["stop", "proxima-test"], dirs, fake, root=False) == ExitCode.PERMISSION
    assert "stop" not in fake.verbs


def test_action_failure_exit_3(dirs: dict[str, Path], capsys) -> None:
    fake = FakeRun(fail_on="restart")
    assert run(["restart", "proxima-test"], dirs, fake) == ExitCode.SYSTEMD_FAILURE
    assert "boom" in capsys.readouterr().err


def test_systemctl_missing_exit_3(dirs: dict[str, Path]) -> None:
    assert run(["start", "x"], dirs, FakeRun(missing=True)) == ExitCode.SYSTEMD_FAILURE


# --- status ----------------------------------------------------------------


def test_status_json_exact_shape(dirs: dict[str, Path], capsys) -> None:
    add_config(dirs)
    assert run(["status", "proxima-test", "--json"], dirs, root=False) == ExitCode.OK
    out = capsys.readouterr().out
    assert out.count("\n") == 1  # one single JSON document
    assert json.loads(out) == {
        "name": "proxima-test",
        "unit": "proxima-test.service",
        "managed": True,
        "load_state": "loaded",
        "active_state": "active",
        "sub_state": "running",
        "unit_file_state": "enabled",
        "result": "success",
        "main_pid": 4242,
        "exec_main_status": 0,
        "n_restarts": 3,
        "active_since": "Sun 2026-11-01 10:00:00 CET",
        "timer": None,
    }


def test_status_json_inactive_nulls(dirs: dict[str, Path], capsys) -> None:
    props = {
        "LoadState": "loaded",
        "ActiveState": "failed",
        "SubState": "failed",
        "MainPID": "0",
        "NRestarts": "",
        "ActiveEnterTimestamp": "",
    }
    assert run(["status", "x", "--json"], dirs, FakeRun(props=props)) == ExitCode.OK
    data = json.loads(capsys.readouterr().out)
    assert data["managed"] is False
    assert data["active_state"] == "failed"
    assert data["main_pid"] is None
    assert data["n_restarts"] is None
    assert data["active_since"] is None


def test_status_text(dirs: dict[str, Path], capsys) -> None:
    assert run(["status", "proxima-test"], dirs) == ExitCode.OK
    captured = capsys.readouterr()
    assert "running" in captured.out
    assert captured.err == ""


def test_status_not_found_json_error(dirs: dict[str, Path], capsys) -> None:
    fake = FakeRun(props=NOT_FOUND)
    assert run(["status", "ghost", "--json"], dirs, fake) == ExitCode.NOT_FOUND
    captured = capsys.readouterr()
    error = json.loads(captured.out)["error"]
    assert error["code"] == 2 and error["kind"] == "not_found"
    assert captured.err


def test_status_systemd_failure_json_error(dirs: dict[str, Path], capsys) -> None:
    fake = FakeRun(fail_on="show")
    assert run(["status", "x", "--json"], dirs, fake) == ExitCode.SYSTEMD_FAILURE
    assert json.loads(capsys.readouterr().out)["error"]["code"] == 3


# --- list ------------------------------------------------------------------


def test_list_json(dirs: dict[str, Path], capsys) -> None:
    add_config(dirs, "b-node")
    add_config(dirs, "a-node")
    (dirs["services_dir"] / "not valid.json").write_text("{}")
    assert run(["list", "--json"], dirs, root=False) == ExitCode.OK
    data = json.loads(capsys.readouterr().out)
    assert list(data) == ["services"]
    assert [s["name"] for s in data["services"]] == ["a-node", "b-node"]
    assert all(s["managed"] and s["active_state"] == "active" for s in data["services"])


def test_list_json_empty(dirs: dict[str, Path], capsys) -> None:
    assert run(["list", "--json"], dirs) == ExitCode.OK
    assert json.loads(capsys.readouterr().out) == {"services": []}


def test_list_missing_dir(tmp_path: Path, capsys) -> None:
    dirs = {"unit_dir": tmp_path, "services_dir": tmp_path / "absent"}
    assert run(["list", "--json"], dirs) == ExitCode.OK
    assert json.loads(capsys.readouterr().out) == {"services": []}


# --- show ------------------------------------------------------------------


def test_show_prints_unit(dirs: dict[str, Path], capsys) -> None:
    add_config(dirs)
    fake = FakeRun()
    assert run(["show", "proxima-test"], dirs, fake, root=False) == ExitCode.OK
    out = capsys.readouterr().out
    assert out.startswith("[Unit]\nDescription=Proxima\n")
    assert "ExecStart=/opt/proxima/bin/proxima\n" in out
    assert fake.calls == []


def test_show_not_found(dirs: dict[str, Path]) -> None:
    assert run(["show", "ghost"], dirs) == ExitCode.NOT_FOUND


def test_show_invalid_config_exit_1(dirs: dict[str, Path]) -> None:
    (dirs["services_dir"] / "broken.json").write_text("{not json")
    assert run(["show", "broken"], dirs) == ExitCode.USAGE


# --- remove ----------------------------------------------------------------


def test_remove_requires_yes(dirs: dict[str, Path]) -> None:
    config = add_config(dirs)
    fake = FakeRun()
    assert run(["remove", "proxima-test"], dirs, fake) == ExitCode.USAGE
    assert config.exists() and fake.calls == []


def test_remove_not_managed_exit_2(dirs: dict[str, Path]) -> None:
    (dirs["unit_dir"] / "ssh.service").write_text("[Unit]\n")
    fake = FakeRun()
    assert run(["remove", "ssh", "--yes"], dirs, fake) == ExitCode.NOT_FOUND
    assert (dirs["unit_dir"] / "ssh.service").exists() and fake.calls == []


def test_remove_requires_root(dirs: dict[str, Path]) -> None:
    config = add_config(dirs)
    assert (
        run(["remove", "proxima-test", "--yes"], dirs, root=False)
        == ExitCode.PERMISSION
    )
    assert config.exists()


def test_remove_success(dirs: dict[str, Path]) -> None:
    config = add_config(dirs)
    unit = dirs["unit_dir"] / "proxima-test.service"
    unit.write_text("[Unit]\n")
    fake = FakeRun()
    assert run(["remove", "proxima-test", "--yes"], dirs, fake) == ExitCode.OK
    assert not unit.exists() and not config.exists()
    assert fake.verbs == ["stop", "disable", "daemon-reload"]


def test_remove_stop_failure_keeps_files(dirs: dict[str, Path]) -> None:
    config = add_config(dirs)
    unit = dirs["unit_dir"] / "proxima-test.service"
    unit.write_text("[Unit]\n")
    fake = FakeRun(fail_on="stop")
    assert (
        run(["remove", "proxima-test", "--yes"], dirs, fake) == ExitCode.SYSTEMD_FAILURE
    )
    assert unit.exists() and config.exists()


# --- entry point -----------------------------------------------------------


def test_main_dispatches_arguments_without_menu(capsys) -> None:
    import src.main as entry

    with (
        patch.object(sys, "argv", ["systemd-manager", "list", "--json"]),
        patch.object(cli_args, "main", return_value=0) as cli_main,
        patch.object(entry, "print_banner") as banner,
        patch.object(entry.questionary, "select") as select,
        patch.object(entry.signal, "signal"),
        pytest.raises(SystemExit) as exc,
    ):
        entry.main()
    assert exc.value.code == 0
    cli_main.assert_called_once_with(["list", "--json"])
    banner.assert_not_called()
    select.assert_not_called()


def test_main_without_arguments_opens_menu() -> None:
    import src.main as entry

    with (
        patch.object(sys, "argv", ["systemd-manager"]),
        patch.object(entry, "print_banner") as banner,
        patch.object(entry.questionary, "select") as select,
        pytest.raises(SystemExit),
    ):
        select.return_value.ask.return_value = entry.i18n.get_text("❌ Quitter")
        entry.main()
    banner.assert_called_once()
    select.assert_called_once()


def test_exec_percent_kept_as_specifier(dirs: dict[str, Path], capsys) -> None:
    argv = PROXIMA_ARGS + ["--exec", "/usr/bin/date +%%Y", "--dry-run"]
    assert run(argv, dirs) == ExitCode.OK
    assert "ExecStart=/usr/bin/date +%%Y\n" in capsys.readouterr().out


def test_usage_error_with_json_emits_json(dirs: dict[str, Path], capsys) -> None:
    assert run(["status", "bad name", "--json"], dirs) == ExitCode.USAGE
    error = json.loads(capsys.readouterr().out)["error"]
    assert error["code"] == 1 and error["kind"] == "usage"


def test_show_malformed_environment_exit_1(dirs: dict[str, Path]) -> None:
    config = add_config(dirs)
    data = json.loads(config.read_text())
    data["service"]["environment"] = "A=1"
    config.write_text(json.dumps(data))
    assert run(["show", "proxima-test"], dirs) == ExitCode.USAGE


def test_create_screen_missing_exit_1(dirs: dict[str, Path]) -> None:
    fake = FakeRun(props=NOT_FOUND)
    with patch.object(cli_args, "SCREEN_BIN", "/nonexistent/screen"):
        argv = _local_create_args() + ["--screen", "--yes"]
        assert run(argv, dirs, fake) == ExitCode.USAGE
    assert list(dirs["unit_dir"].iterdir()) == []


def test_create_json_permission_denied_exit_4(dirs: dict[str, Path]) -> None:
    denied = ValueError("denied")
    denied.__cause__ = PermissionError("denied")
    fake = FakeRun(props=NOT_FOUND)
    with patch.object(cli_args.ServiceModel, "save_to_json", side_effect=denied):
        argv = _local_create_args() + ["--yes"]
        assert run(argv, dirs, fake) == ExitCode.PERMISSION
    assert "daemon-reload" not in fake.verbs


def test_list_text(dirs: dict[str, Path], capsys) -> None:
    add_config(dirs, "a-node")
    assert run(["list"], dirs) == ExitCode.OK
    assert capsys.readouterr().out == "a-node\tactive\trunning\tenabled\n"


def test_services_dir_follows_sudo_user(monkeypatch, tmp_path: Path) -> None:
    import pwd

    monkeypatch.setenv("SUDO_USER", "seb43")
    entry = pwd.struct_passwd(("seb43", "x", 1000, 1000, "", str(tmp_path), "/bin/sh"))
    with (
        patch.object(cli_args.os, "geteuid", return_value=0),
        patch.object(cli_args.pwd, "getpwnam", return_value=entry),
    ):
        assert cli_args.default_services_dir() == (
            tmp_path / ".config" / "systemd-manager" / "services"
        )
    with patch.object(cli_args.os, "geteuid", return_value=1000):
        assert cli_args.default_services_dir() == (
            Path.home() / ".config" / "systemd-manager" / "services"
        )


# create --adopt


def add_unit(dirs: dict[str, Path], text: str = "[Service]\nExecStart=/old\n") -> Path:
    path = dirs["unit_dir"] / "proxima-test.service"
    path.write_text(text)
    path.chmod(0o640)
    return path


ADOPT_ARGS = [*PROXIMA_ARGS, "--exec", sys.executable, "--workdir", "/tmp"]
HAND_WRITTEN = {
    **LOADED,
    "FragmentPath": "",
    "DropInPaths": "",
}


def test_adopt_replaces_unit_and_keeps_a_copy(dirs: dict[str, Path], capsys) -> None:
    unit = add_unit(dirs)
    fake = FakeRun(props={**HAND_WRITTEN, "FragmentPath": str(unit)})
    assert run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.OK
    assert f"ExecStart={sys.executable}" in unit.read_text()
    assert (dirs["services_dir"] / "proxima-test.json").is_file()
    backups = list(dirs["unit_dir"].glob("proxima-test.service.adopted-*"))
    assert len(backups) == 1
    assert backups[0].read_text() == "[Service]\nExecStart=/old\n"
    assert backups[0].stat().st_mode & 0o777 == 0o640
    assert fake.verbs == ["show", "disable", "daemon-reload", "show", "enable"]
    assert not [c for c in fake.calls if c[1] in ("stop", "start", "restart")]
    err = capsys.readouterr().err
    assert str(backups[0]) in err
    assert "redémarrez" in err  # the service is running its old configuration


def test_adopt_warns_about_drop_ins(dirs: dict[str, Path], capsys) -> None:
    add_unit(dirs)
    fake = FakeRun(props={**HAND_WRITTEN, "DropInPaths": "/etc/x.d/a.conf"})
    assert run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.OK
    assert "/etc/x.d/a.conf" in capsys.readouterr().err


def test_adopt_then_remove_unblocks_the_deadlock(dirs: dict[str, Path]) -> None:
    unit = add_unit(dirs)
    assert (
        run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, FakeRun(props=HAND_WRITTEN)) == 0
    )
    assert run(["remove", "proxima-test", "--yes"], dirs) == ExitCode.OK
    assert not unit.exists()


def test_adopt_requires_yes_and_root(dirs: dict[str, Path]) -> None:
    unit = add_unit(dirs)
    before = unit.read_text()
    assert run([*ADOPT_ARGS, "--adopt"], dirs) == ExitCode.USAGE
    assert (
        run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, root=False) == ExitCode.PERMISSION
    )
    assert unit.read_text() == before


def test_adopt_dry_run_touches_nothing(dirs: dict[str, Path], capsys) -> None:
    unit = add_unit(dirs)
    fake = FakeRun()
    argv = [*PROXIMA_ARGS, "--adopt", "--dry-run"]
    assert run(argv, dirs, fake, root=False) == ExitCode.OK
    assert fake.calls == []
    assert capsys.readouterr().out == PROXIMA_UNIT
    assert "/old" in unit.read_text()
    assert len(list(dirs["unit_dir"].iterdir())) == 1


def test_adopt_nothing_to_adopt_exit_2(dirs: dict[str, Path]) -> None:
    fake = FakeRun(props=NOT_FOUND)
    assert run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.NOT_FOUND
    assert fake.verbs == ["show"]
    assert list(dirs["unit_dir"].iterdir()) == []


def test_adopt_refuses_already_managed(dirs: dict[str, Path], capsys) -> None:
    unit = add_unit(dirs)
    add_config(dirs)
    fake = FakeRun(props=HAND_WRITTEN)
    assert run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.USAGE
    assert "/old" in unit.read_text()
    assert fake.verbs == ["show"]


@pytest.mark.parametrize("target", ["/dev/null", "/nonexistent/dangling"])
def test_adopt_refuses_symlink_and_never_writes_through(
    dirs: dict[str, Path], tmp_path: Path, target: str
) -> None:
    link = dirs["unit_dir"] / "proxima-test.service"
    link.symlink_to(target)
    fake = FakeRun(props={**HAND_WRITTEN, "LoadState": "masked"})
    assert run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.USAGE
    assert link.is_symlink() and str(link.readlink()) == target
    assert fake.verbs == ["show"]


def test_adopt_refuses_symlink_to_a_real_file(
    dirs: dict[str, Path], tmp_path: Path
) -> None:
    real = tmp_path / "real.service"
    real.write_text("original")
    (dirs["unit_dir"] / "proxima-test.service").symlink_to(real)
    fake = FakeRun(props=HAND_WRITTEN)
    assert run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.USAGE
    assert real.read_text() == "original"


def test_adopt_refuses_package_unit_without_file(dirs: dict[str, Path]) -> None:
    fake = FakeRun(
        props={**HAND_WRITTEN, "FragmentPath": "/usr/lib/systemd/system/x.service"}
    )
    assert run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.USAGE
    assert list(dirs["unit_dir"].iterdir()) == []


@pytest.mark.parametrize(
    "install",
    [
        "Also=x.socket",
        "Alias=y.service",
        "RequiredBy=z.target",
        "DefaultInstance=a",
        "WantedBy=a.target b.target",
        "WantedBy=a.target\nWantedBy=b.target",
    ],
)
def test_adopt_refuses_install_it_would_lose(
    dirs: dict[str, Path], install: str, capsys
) -> None:
    unit = add_unit(dirs, f"[Service]\nExecStart=/old\n[Install]\n{install}\n")
    fake = FakeRun(props=HAND_WRITTEN)
    assert run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.USAGE
    assert fake.verbs == ["show"]
    assert "/old" in unit.read_text()
    assert install.split("=")[0] in capsys.readouterr().err


@pytest.mark.parametrize(
    "text",
    [
        "[Service]\nExecStart=/old\nAlias=not-in-install\n",
        "[Service]\nExecStart=/old\n[Install]\n# Also=x.socket\nWantedBy=a.target\n",
    ],
)
def test_adopt_accepts_install_it_keeps(dirs: dict[str, Path], text: str) -> None:
    add_unit(dirs, text)
    fake = FakeRun(props=HAND_WRITTEN)
    assert run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.OK


@pytest.mark.parametrize(
    "fake_kwargs",
    [
        {"fail_once": "daemon-reload"},
        {"fail_once": "enable"},
        {"props_after_reload": {**LOADED, "LoadState": "bad-setting"}},
    ],
)
def test_adopt_late_failure_restores_previous_unit(
    dirs: dict[str, Path], fake_kwargs: dict[str, Any], capsys
) -> None:
    unit = add_unit(dirs)
    fake = FakeRun(props=HAND_WRITTEN, **fake_kwargs)
    code = run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake)
    assert code == ExitCode.SYSTEMD_FAILURE
    assert unit.read_text() == "[Service]\nExecStart=/old\n"
    assert unit.stat().st_mode & 0o777 == 0o640
    assert not (dirs["services_dir"] / "proxima-test.json").exists()
    assert fake.verbs[-2:] == ["daemon-reload", "enable"]
    assert not list(dirs["unit_dir"].glob(".*"))
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "restaurée" in captured.err


def test_adopt_rollback_failure_is_reported(dirs: dict[str, Path], capsys) -> None:
    add_unit(dirs)
    fake = FakeRun(props=HAND_WRITTEN, fail_on="enable")
    code = run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake)
    assert code == ExitCode.SYSTEMD_FAILURE
    err = capsys.readouterr().err
    assert err.count("boom") == 2
    assert "restaurée" not in err


def test_adopt_refuses_shadowed_file(dirs: dict[str, Path]) -> None:
    unit = add_unit(dirs)
    fake = FakeRun(
        props={**HAND_WRITTEN, "FragmentPath": "/run/systemd/system/x.service"}
    )
    assert run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.USAGE
    assert "/old" in unit.read_text()


def test_adopt_disable_failure_restores_state(dirs: dict[str, Path]) -> None:
    unit = add_unit(dirs)
    fake = FakeRun(props=HAND_WRITTEN, fail_on="disable")
    code = run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake)
    assert code == ExitCode.SYSTEMD_FAILURE
    assert "/old" in unit.read_text()
    assert not (dirs["services_dir"] / "proxima-test.json").exists()
    assert fake.verbs == ["show", "disable", "daemon-reload", "enable"]


def test_adopt_write_failure_restores_state(dirs: dict[str, Path]) -> None:
    unit = add_unit(dirs)
    fake = FakeRun(props=HAND_WRITTEN)
    with patch.object(cli_args.os, "replace", side_effect=OSError("disk full")):
        code = run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake)
    assert code == ExitCode.SYSTEMD_FAILURE
    assert "/old" in unit.read_text()
    assert not (dirs["services_dir"] / "proxima-test.json").exists()
    assert fake.verbs == ["show", "disable"]
    assert not list(dirs["unit_dir"].glob(".*"))


def test_adopt_does_not_re_enable_a_disabled_unit_on_failure(
    dirs: dict[str, Path],
) -> None:
    add_unit(dirs)
    fake = FakeRun(
        props={**HAND_WRITTEN, "UnitFileState": "disabled"}, fail_on="disable"
    )
    run([*ADOPT_ARGS, "--adopt", "--yes"], dirs, fake)
    assert fake.verbs == ["show", "disable", "daemon-reload"]


def test_create_existing_unit_hints_adopt(dirs: dict[str, Path], capsys) -> None:
    add_unit(dirs)
    assert run([*ADOPT_ARGS, "--yes"], dirs) == ExitCode.USAGE
    assert "--adopt" in capsys.readouterr().err


def test_create_managed_unit_hints_remove(dirs: dict[str, Path], capsys) -> None:
    add_unit(dirs)
    add_config(dirs)
    assert run([*ADOPT_ARGS, "--yes"], dirs) == ExitCode.USAGE
    assert "--adopt" not in capsys.readouterr().err


def test_create_never_writes_through_dangling_symlink(
    dirs: dict[str, Path], tmp_path: Path
) -> None:
    target = tmp_path / "elsewhere.service"
    (dirs["unit_dir"] / "proxima-test.service").symlink_to(target)
    fake = FakeRun(props=NOT_FOUND)
    assert run([*ADOPT_ARGS, "--yes"], dirs, fake) == ExitCode.USAGE
    assert not target.exists()


def test_remove_unmanaged_unit_exit_2_keeps_it(dirs: dict[str, Path], capsys) -> None:
    unit = add_unit(dirs)
    fake = FakeRun()
    assert run(["remove", "proxima-test", "--yes"], dirs, fake) == ExitCode.NOT_FOUND
    assert unit.exists()
    assert fake.calls == []
    assert "--adopt" in capsys.readouterr().err


# Timers

HAND_PROBE = {**HAND_WRITTEN, "ActiveState": "inactive", "SubState": "dead"}

PROBE_ARGS = ["create", "--name", "sonde", "--exec", "/bin/true", "--user", "root"]

PROBE_SERVICE = """\
[Unit]
Description=sonde
StartLimitBurst=5
StartLimitIntervalSec=10

[Service]
Type=oneshot
User=root
ExecStart=/bin/true
Restart=no
TimeoutStartSec=1h

[Install]
"""

PROBE_DRY_RUN = (
    "# sonde.service\n"
    + PROBE_SERVICE
    + """
# sonde.timer
[Unit]
Description=Timer for sonde

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
"""
)


def add_timer_config(dirs: dict[str, Path], name: str = "sonde") -> None:
    from src.models.service_model import ServiceModel

    service = ServiceModel(name)
    service.service.exec_start = "/bin/true"
    service.timer.every = "5min"
    service.save_to_json(str(dirs["services_dir"] / f"{name}.json"))
    (dirs["unit_dir"] / f"{name}.service").write_text("[Service]\n")
    (dirs["unit_dir"] / f"{name}.timer").write_text("[Timer]\n")


def files(dirs: dict[str, Path]) -> list[str]:
    return sorted(path.name for path in dirs["unit_dir"].iterdir())


@pytest.mark.parametrize(
    "span", ["5min", "1h 30min", "90", "2 weeks", "1d12h", "10s", "500ms"]
)
def test_every_accepts_time_spans(span: str) -> None:
    args = build_parser().parse_args([*PROBE_ARGS, "--every", span])
    assert args.every == span


@pytest.mark.parametrize(
    "span",
    ["", "0", "0min", "5 lightyears", "min", "-5min", "5min\nExecStart=/x", "5%n"],
)
def test_every_rejects_invalid_spans(dirs: dict[str, Path], span: str) -> None:
    assert run([*PROBE_ARGS, f"--every={span}", "--dry-run"], dirs) == ExitCode.USAGE


@pytest.mark.parametrize(
    "expr",
    ["hourly", "*-*-* 03:00:00", "Mon..Fri 08:00", "*:0/5", "*-*-* 03:00 Europe/Paris"],
)
def test_calendar_accepts_expressions(expr: str) -> None:
    args = build_parser().parse_args([*PROBE_ARGS, "--calendar", expr])
    assert args.calendar == expr


@pytest.mark.parametrize("expr", ["", "-1", "daily\nExecStart=/x", "%n", 'daily"'])
def test_calendar_rejects_invalid_characters(dirs: dict[str, Path], expr: str) -> None:
    assert run([*PROBE_ARGS, f"--calendar={expr}", "--dry-run"], dirs) == ExitCode.USAGE


def test_every_and_calendar_are_exclusive(dirs: dict[str, Path]) -> None:
    argv = [*PROBE_ARGS, "--every", "5min", "--calendar", "hourly", "--dry-run"]
    assert run(argv, dirs) == ExitCode.USAGE


def test_timer_dry_run_exact_output_calls_nothing(
    dirs: dict[str, Path], capsys
) -> None:
    fake = FakeRun()
    argv = [*PROBE_ARGS, "--every", "5min", "--dry-run"]
    assert run(argv, dirs, fake, root=False) == ExitCode.OK
    assert fake.calls == []
    assert capsys.readouterr().out == PROBE_DRY_RUN
    assert files(dirs) == []


def test_calendar_dry_run_is_persistent(dirs: dict[str, Path], capsys) -> None:
    fake = FakeRun()
    argv = [*PROBE_ARGS, "--calendar", "hourly", "--dry-run"]
    assert run(argv, dirs, fake, root=False) == ExitCode.OK
    assert fake.calls == []
    out = capsys.readouterr().out
    assert "OnCalendar=hourly\nPersistent=true\n" in out
    assert "OnBootSec" not in out


@pytest.mark.parametrize(
    "extra",
    [["--screen"], ["--restart", "always"], ["--wanted-by", "default.target"]],
)
def test_timer_refuses_incompatible_options(
    dirs: dict[str, Path], extra: list[str]
) -> None:
    argv = [*PROBE_ARGS, "--every", "5min", *extra, "--dry-run"]
    assert run(argv, dirs) == ExitCode.USAGE


def test_timer_allows_restart_on_failure(dirs: dict[str, Path], capsys) -> None:
    argv = [*PROBE_ARGS, "--every", "5min", "--restart", "on-failure", "--dry-run"]
    assert run(argv, dirs) == ExitCode.OK
    assert "Restart=on-failure" in capsys.readouterr().out


def test_no_timer_output_has_no_header(dirs: dict[str, Path], capsys) -> None:
    assert run([*PROXIMA_ARGS, "--dry-run"], dirs) == ExitCode.OK
    assert capsys.readouterr().out == PROXIMA_UNIT


def test_timer_install_enables_only_the_timer(dirs: dict[str, Path], capsys) -> None:
    fake = FakeRun(props=NOT_FOUND)
    assert run([*PROBE_ARGS, "--every", "5min", "--yes"], dirs, fake) == ExitCode.OK
    assert files(dirs) == ["sonde.service", "sonde.timer"]
    assert fake.verbs == ["show", "show", "daemon-reload", "enable"]
    assert fake.calls[-1] == ["systemctl", "enable", "sonde.timer"]
    assert "Type=oneshot" in (dirs["unit_dir"] / "sonde.service").read_text()
    assert "WantedBy" not in (dirs["unit_dir"] / "sonde.service").read_text()
    assert capsys.readouterr().out == ""


def test_calendar_install_is_checked_by_systemd(dirs: dict[str, Path]) -> None:
    fake = FakeRun(props=NOT_FOUND)
    argv = [*PROBE_ARGS, "--calendar", "hourly", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.OK
    assert ["systemd-analyze", "calendar", "hourly"] in fake.calls


def test_span_install_is_checked_by_systemd(dirs: dict[str, Path], capsys) -> None:
    fake = FakeRun(props=NOT_FOUND)
    argv = [*PROBE_ARGS, "--every", "5min", "--timeout", "30s", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.OK
    assert ["systemd-analyze", "timespan", "5min"] in fake.calls
    assert ["systemd-analyze", "timespan", "30s"] in fake.calls
    assert "TimeoutStartSec=30s" in (dirs["unit_dir"] / "sonde.service").read_text()


def test_span_refused_by_systemd_installs_nothing(dirs: dict[str, Path]) -> None:
    fake = FakeRun(props=NOT_FOUND, fail_on="calendar")
    argv = [*PROBE_ARGS, "--every", "99999999999y", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.USAGE
    assert files(dirs) == []


def test_every_rejects_non_ascii_digits(dirs: dict[str, Path]) -> None:
    argv = [*PROBE_ARGS, "--every=٥min", "--dry-run"]
    assert run(argv, dirs) == ExitCode.USAGE


def test_timeout_requires_a_timer(dirs: dict[str, Path]) -> None:
    assert run([*PROBE_ARGS, "--timeout", "5min", "--dry-run"], dirs) == ExitCode.USAGE


def test_no_timeout_without_timer(dirs: dict[str, Path], capsys) -> None:
    assert run([*PROBE_ARGS, "--dry-run"], dirs) == ExitCode.OK
    assert "TimeoutStartSec" not in capsys.readouterr().out


def test_invalid_calendar_installs_nothing(dirs: dict[str, Path]) -> None:
    fake = FakeRun(props=NOT_FOUND, fail_on="calendar")
    argv = [*PROBE_ARGS, "--calendar", "nope", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.USAGE
    assert files(dirs) == []
    assert fake.verbs == []
    assert not (dirs["services_dir"] / "sonde.json").exists()


def test_missing_systemd_analyze_exit_3(dirs: dict[str, Path]) -> None:
    fake = FakeRun(missing=True)
    argv = [*PROBE_ARGS, "--calendar", "hourly", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.SYSTEMD_FAILURE
    assert files(dirs) == []


def test_timer_requires_yes_and_root(dirs: dict[str, Path]) -> None:
    fake = FakeRun(props=NOT_FOUND)
    argv = [*PROBE_ARGS, "--every", "5min"]
    assert run(argv, dirs, fake) == ExitCode.USAGE
    assert run([*argv, "--yes"], dirs, fake, root=False) == ExitCode.PERMISSION
    assert files(dirs) == []
    assert fake.verbs == []


def test_timer_refuses_existing_timer_file(dirs: dict[str, Path]) -> None:
    (dirs["unit_dir"] / "sonde.timer").write_text("hand")
    fake = FakeRun(props=NOT_FOUND)
    assert run([*PROBE_ARGS, "--every", "5min", "--yes"], dirs, fake) == ExitCode.USAGE
    assert (dirs["unit_dir"] / "sonde.timer").read_text() == "hand"
    assert files(dirs) == ["sonde.timer"]


def test_plain_create_ignores_an_unrelated_timer(dirs: dict[str, Path], capsys) -> None:
    (dirs["unit_dir"] / "sonde.timer").write_text("hand")
    fake = FakeRun(props=NOT_FOUND)
    assert run([*PROBE_ARGS, "--yes"], dirs, fake) == ExitCode.OK
    assert (dirs["unit_dir"] / "sonde.timer").read_text() == "hand"
    assert fake.calls[-1] == ["systemctl", "enable", "sonde.service"]
    assert "sonde.timer" in capsys.readouterr().err


def add_hand_probe(
    dirs: dict[str, Path], timer: str | None = "[Timer]\nOnCalendar=daily\n"
) -> None:
    (dirs["unit_dir"] / "sonde.service").write_text("[Service]\nExecStart=/old\n")
    if timer is not None:
        (dirs["unit_dir"] / "sonde.timer").write_text(timer)


def test_adopt_takes_over_service_and_timer(dirs: dict[str, Path]) -> None:
    add_hand_probe(dirs)
    fake = FakeRun(props=HAND_PROBE)
    argv = [*PROBE_ARGS, "--every", "5min", "--adopt", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.OK
    assert "OnBootSec=5min" in (dirs["unit_dir"] / "sonde.timer").read_text()
    assert len(list(dirs["unit_dir"].glob("sonde.service.adopted-*"))) == 1
    backups = list(dirs["unit_dir"].glob("sonde.timer.adopted-*"))
    assert len(backups) == 1
    assert "OnCalendar=daily" in backups[0].read_text()
    disabled = [c[2] for c in fake.calls if c[1] == "disable"]
    assert disabled == ["sonde.service", "sonde.timer"]
    assert fake.calls[-1] == ["systemctl", "enable", "sonde.timer"]


@pytest.mark.parametrize("state", ["active", "activating", "reloading"])
def test_adopt_with_timer_refuses_active_service(
    dirs: dict[str, Path], state: str, capsys
) -> None:
    add_hand_probe(dirs, timer=None)
    fake = FakeRun(props={**HAND_PROBE, "ActiveState": state})
    argv = [*PROBE_ARGS, "--every", "5min", "--adopt", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.USAGE
    assert fake.verbs == ["show", "show"]
    assert files(dirs) == ["sonde.service"]
    assert not (dirs["services_dir"] / "sonde.json").exists()


def test_adopt_service_with_new_timer_rolls_it_back(dirs: dict[str, Path]) -> None:
    add_hand_probe(dirs, timer=None)
    fake = FakeRun(props=HAND_PROBE, fail_once="enable", timer_props=NOT_FOUND)
    argv = [*PROBE_ARGS, "--every", "5min", "--adopt", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.SYSTEMD_FAILURE
    assert not (dirs["unit_dir"] / "sonde.timer").exists()
    assert "/old" in (dirs["unit_dir"] / "sonde.service").read_text()
    assert not (dirs["services_dir"] / "sonde.json").exists()
    assert fake.calls[-1] == ["systemctl", "enable", "sonde.service"]


def test_adopt_rolls_back_both_units(dirs: dict[str, Path]) -> None:
    add_hand_probe(dirs)
    fake = FakeRun(props=HAND_PROBE, fail_once="enable")
    argv = [*PROBE_ARGS, "--every", "5min", "--adopt", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.SYSTEMD_FAILURE
    assert "OnCalendar=daily" in (dirs["unit_dir"] / "sonde.timer").read_text()
    assert "/old" in (dirs["unit_dir"] / "sonde.service").read_text()
    enabled = [c[2] for c in fake.calls if c[1] == "enable"]
    assert enabled == ["sonde.timer", "sonde.service", "sonde.timer"]


def test_adopt_refuses_symlinked_timer(dirs: dict[str, Path], tmp_path: Path) -> None:
    add_hand_probe(dirs, timer=None)
    real = tmp_path / "real.timer"
    real.write_text("original")
    (dirs["unit_dir"] / "sonde.timer").symlink_to(real)
    fake = FakeRun(props=HAND_PROBE)
    argv = [*PROBE_ARGS, "--every", "5min", "--adopt", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.USAGE
    assert real.read_text() == "original"
    assert fake.verbs == ["show", "show"]
    assert "/old" in (dirs["unit_dir"] / "sonde.service").read_text()


def test_adopt_refuses_timer_install_it_would_lose(dirs: dict[str, Path]) -> None:
    add_hand_probe(dirs, timer="[Timer]\nOnCalendar=daily\n[Install]\nAlso=x.service\n")
    fake = FakeRun(props=HAND_PROBE)
    argv = [*PROBE_ARGS, "--every", "5min", "--adopt", "--yes"]
    assert run(argv, dirs, fake) == ExitCode.USAGE
    assert not list(dirs["unit_dir"].glob("*.adopted-*"))


def test_adopt_without_timer_leaves_hand_timer_and_warns(
    dirs: dict[str, Path], capsys
) -> None:
    add_hand_probe(dirs)
    fake = FakeRun(props=HAND_PROBE)
    assert run([*PROBE_ARGS, "--adopt", "--yes"], dirs, fake) == ExitCode.OK
    assert "OnCalendar=daily" in (dirs["unit_dir"] / "sonde.timer").read_text()
    assert not list(dirs["unit_dir"].glob("sonde.timer.adopted-*"))
    assert "sonde.timer" in capsys.readouterr().err


@pytest.mark.parametrize(
    "action,units",
    [
        ("start", ["sonde.timer"]),
        ("restart", ["sonde.timer"]),
        ("enable", ["sonde.timer"]),
        ("disable", ["sonde.timer"]),
        ("stop", ["sonde.timer", "sonde.service"]),
    ],
)
def test_actions_drive_the_timer(
    dirs: dict[str, Path], action: str, units: list[str]
) -> None:
    add_timer_config(dirs)
    fake = FakeRun()
    assert run([action, "sonde"], dirs, fake) == ExitCode.OK
    assert fake.calls[-1] == ["systemctl", action, *units]


def test_action_ignores_a_hand_written_timer(dirs: dict[str, Path]) -> None:
    add_config(dirs, "sonde")
    (dirs["unit_dir"] / "sonde.timer").write_text("hand")
    fake = FakeRun()
    assert run(["start", "sonde"], dirs, fake) == ExitCode.OK
    assert fake.calls[-1] == ["systemctl", "start", "sonde.service"]


def test_run_starts_the_service_not_the_timer(dirs: dict[str, Path]) -> None:
    add_timer_config(dirs)
    fake = FakeRun()
    assert run(["run", "sonde"], dirs, fake) == ExitCode.OK
    assert fake.calls[-1] == ["systemctl", "start", "sonde.service"]


def test_run_exit_codes(dirs: dict[str, Path]) -> None:
    assert run(["run", "sonde"], dirs, FakeRun(props=NOT_FOUND)) == ExitCode.NOT_FOUND
    assert run(["run", "sonde"], dirs, root=False) == ExitCode.PERMISSION
    assert (
        run(["run", "sonde"], dirs, FakeRun(fail_on="start"))
        == ExitCode.SYSTEMD_FAILURE
    )


TIMER_PROPS = {
    **LOADED,
    "ActiveState": "active",
    "SubState": "waiting",
    "NextElapseUSecRealtime": "Fri 2026-11-06 07:00:00 UTC",
    "NextElapseUSecMonotonic": "0",
    "LastTriggerUSec": "Fri 2026-11-06 06:00:00 UTC",
}


def test_status_json_has_timer_record(dirs: dict[str, Path], capsys) -> None:
    add_timer_config(dirs)
    assert run(["status", "sonde", "--json"], dirs, FakeRun(props=TIMER_PROPS)) == 0
    record = json.loads(capsys.readouterr().out)
    assert record["timer"] == {
        "unit": "sonde.timer",
        "active_state": "active",
        "sub_state": "waiting",
        "unit_file_state": "enabled",
        "next_run": "Fri 2026-11-06 07:00:00 UTC",
        "next_run_monotonic": None,
        "last_run": "Fri 2026-11-06 06:00:00 UTC",
    }


def test_status_json_monotonic_next_run(dirs: dict[str, Path], capsys) -> None:
    add_timer_config(dirs)
    props = {
        **TIMER_PROPS,
        "NextElapseUSecRealtime": "",
        "NextElapseUSecMonotonic": "59min 15s",
        "LastTriggerUSec": "",
    }
    assert run(["status", "sonde", "--json"], dirs, FakeRun(props=props)) == 0
    timer = json.loads(capsys.readouterr().out)["timer"]
    assert timer["next_run"] is None
    assert timer["next_run_monotonic"] == "59min 15s"
    assert timer["last_run"] is None


def test_status_json_stopped_timer_has_no_next_run(
    dirs: dict[str, Path], capsys
) -> None:
    add_timer_config(dirs)
    props = {
        **TIMER_PROPS,
        "ActiveState": "inactive",
        "NextElapseUSecRealtime": "",
        "NextElapseUSecMonotonic": "infinity",
    }
    assert run(["status", "sonde", "--json"], dirs, FakeRun(props=props)) == 0
    timer = json.loads(capsys.readouterr().out)["timer"]
    assert timer["next_run"] is None
    assert timer["next_run_monotonic"] is None


def test_status_text_shows_timer(dirs: dict[str, Path], capsys) -> None:
    add_timer_config(dirs)
    assert run(["status", "sonde"], dirs, FakeRun(props=TIMER_PROPS)) == 0
    assert "07:00:00" in capsys.readouterr().out


def test_list_json_has_timer(dirs: dict[str, Path], capsys) -> None:
    add_timer_config(dirs)
    assert run(["list", "--json"], dirs, FakeRun(props=TIMER_PROPS)) == 0
    assert json.loads(capsys.readouterr().out)["services"][0]["timer"]["unit"] == (
        "sonde.timer"
    )


def test_show_prints_both_units(dirs: dict[str, Path], capsys) -> None:
    fake = FakeRun(props=NOT_FOUND)
    assert run([*PROBE_ARGS, "--every", "5min", "--yes"], dirs, fake) == 0
    capsys.readouterr()
    assert run(["show", "sonde"], dirs) == ExitCode.OK
    assert capsys.readouterr().out == PROBE_DRY_RUN


def test_remove_deletes_the_managed_timer_first(dirs: dict[str, Path]) -> None:
    add_timer_config(dirs)
    fake = FakeRun()
    assert run(["remove", "sonde", "--yes"], dirs, fake) == ExitCode.OK
    assert files(dirs) == []
    assert not (dirs["services_dir"] / "sonde.json").exists()
    assert fake.calls == [
        ["systemctl", "stop", "sonde.timer"],
        ["systemctl", "disable", "sonde.timer"],
        ["systemctl", "stop", "sonde.service"],
        ["systemctl", "disable", "sonde.service"],
        ["systemctl", "daemon-reload"],
    ]


def test_remove_leaves_a_hand_written_timer(dirs: dict[str, Path]) -> None:
    add_config(dirs, "sonde")
    (dirs["unit_dir"] / "sonde.service").write_text("[Service]\n")
    (dirs["unit_dir"] / "sonde.timer").write_text("hand")
    assert run(["remove", "sonde", "--yes"], dirs) == ExitCode.OK
    assert files(dirs) == ["sonde.timer"]


def test_remove_timer_failure_exit_3_keeps_config(dirs: dict[str, Path]) -> None:
    add_timer_config(dirs)
    fake = FakeRun(fail_on="stop")
    assert run(["remove", "sonde", "--yes"], dirs, fake) == ExitCode.SYSTEMD_FAILURE
    assert (dirs["services_dir"] / "sonde.json").exists()
    assert (dirs["unit_dir"] / "sonde.timer").exists()


def test_remove_with_corrupt_config_keeps_timer(dirs: dict[str, Path], capsys) -> None:
    (dirs["services_dir"] / "sonde.json").write_text("{not json")
    (dirs["unit_dir"] / "sonde.service").write_text("[Service]\n")
    (dirs["unit_dir"] / "sonde.timer").write_text("hand")
    assert run(["remove", "sonde", "--yes"], dirs) == ExitCode.OK
    assert files(dirs) == ["sonde.timer"]
    assert "sonde.timer" in capsys.readouterr().err


def test_timer_survives_json_round_trip(tmp_path: Path) -> None:
    from src.models.service_model import ServiceModel

    service = ServiceModel("sonde")
    service.timer.on_calendar = "hourly"
    path = tmp_path / "sonde.json"
    service.save_to_json(str(path))
    loaded = ServiceModel.load_from_json(str(path))
    assert loaded.has_timer
    assert loaded.to_timer_file() == service.to_timer_file()


def test_json_without_timer_is_unchanged(tmp_path: Path) -> None:
    from src.models.service_model import ServiceModel

    assert "timer" not in ServiceModel("x").to_json()
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"name": "x", "service": {"exec_start": "/bin/true"}}))
    assert not ServiceModel.load_from_json(str(path)).has_timer


def test_timer_file_rejects_injected_directive() -> None:
    from src.models.service_model import ServiceModel

    service = ServiceModel("x")
    service.timer.every = "5min\nExecStart=/evil"
    with pytest.raises(ValueError):
        service.to_timer_file()


def wizard(tmp_path: Path) -> Any:
    from types import SimpleNamespace

    return SimpleNamespace(services_dir=str(tmp_path))


def test_interactive_delete_removes_managed_timer(tmp_path: Path) -> None:
    from src.cli import cli_controller

    with (
        patch.object(cli_controller.questionary, "confirm") as confirm,
        patch.object(cli_controller, "remove_managed_timer") as remover,
        patch.object(cli_controller.subprocess, "run"),
    ):
        confirm.return_value.ask.return_value = True
        cli_controller.CLIController.delete_service(wizard(tmp_path), "sonde")
    remover.assert_called_once_with("sonde", tmp_path / "sonde.json")


def test_interactive_delete_stops_if_the_timer_cannot_go(tmp_path: Path) -> None:
    from src.cli import cli_controller

    (tmp_path / "sonde.json").write_text("{}")
    error = subprocess.CalledProcessError(1, ["systemctl"])
    with (
        patch.object(cli_controller.questionary, "confirm") as confirm,
        patch.object(cli_controller, "remove_managed_timer", side_effect=error),
        patch.object(cli_controller.subprocess, "run") as systemctl,
    ):
        confirm.return_value.ask.return_value = True
        cli_controller.CLIController.delete_service(wizard(tmp_path), "sonde")
    systemctl.assert_not_called()
    assert (tmp_path / "sonde.json").exists()


@pytest.mark.parametrize(
    "action,units",
    [
        ("stop", ["sonde.timer", "sonde.service"]),
        ("start", ["sonde.timer"]),
        ("restart", ["sonde.timer"]),
    ],
)
def test_interactive_actions_drive_the_timer(
    tmp_path: Path, action: str, units: list[str]
) -> None:
    from unittest.mock import MagicMock

    from src.cli import cli_controller

    def fake_run(cmd: list[str], **kwargs: Any) -> MagicMock:
        # The timer is active when stopping it, inactive when starting it.
        inactive = cmd[1] == "is-active" and action == "start"
        return MagicMock(returncode=1 if inactive else 0, stdout="")

    method = getattr(cli_controller.CLIController, f"{action}_service")
    with (
        patch.object(cli_controller, "timer_action_units", return_value=units),
        patch.object(cli_controller.subprocess, "run", side_effect=fake_run) as run_,
        patch.object(cli_controller.questionary, "confirm") as confirm,
    ):
        confirm.return_value.ask.return_value = False
        method(wizard(tmp_path), "sonde")
    run_.assert_any_call(["systemctl", action, *units])


@pytest.fixture
def gui_controller() -> Any:
    import importlib
    from types import ModuleType
    from unittest.mock import MagicMock

    # src.gui's __init__ imports the whole Tk application: bypass it.
    package = ModuleType("src.gui")
    package.__path__ = [str(Path(cli_args.__file__).parents[1] / "gui")]
    stubs = {"customtkinter": MagicMock(), "src.gui": package}
    with patch.dict(sys.modules, stubs):
        sys.modules.pop("src.gui.gui_controller", None)
        yield importlib.import_module("src.gui.gui_controller")


def test_gui_delete_removes_managed_timer(tmp_path: Path, gui_controller: Any) -> None:
    with (
        patch.object(gui_controller, "remove_managed_timer") as remover,
        patch.object(gui_controller.subprocess, "run"),
    ):
        gui_controller.GUIController.delete_service(wizard(tmp_path), "sonde")
    remover.assert_called_once_with("sonde", tmp_path / "sonde.json")


def test_gui_edit_keeps_the_timer(tmp_path: Path, gui_controller: Any) -> None:
    from src.models.service_model import ServiceModel

    service = ServiceModel("sonde")
    service.timer.every = "5min"
    service.save_to_json(str(tmp_path / "sonde.json"))
    fake = wizard(tmp_path)
    fake.get_service_status = lambda name: {}
    loaded = gui_controller.GUIController.load_service(fake, "sonde")
    assert loaded.has_timer
    assert loaded.to_json()["timer"]["every"] == "5min"


@pytest.mark.parametrize(
    "action,units",
    [
        ("stop", ["sonde.timer", "sonde.service"]),
        ("start", ["sonde.timer"]),
        ("restart", ["sonde.timer"]),
    ],
)
def test_gui_buttons_drive_the_timer(
    tmp_path: Path, gui_controller: Any, action: str, units: list[str]
) -> None:
    cls = gui_controller.GUIController
    fake = wizard(tmp_path)
    fake._action_units = lambda a, n: cls._action_units(fake, a, n)
    with (
        patch.object(gui_controller, "timer_action_units", return_value=units),
        patch.object(gui_controller.subprocess, "run") as run_,
    ):
        assert getattr(cls, f"{action}_service")(fake, "sonde") is True
    run_.assert_called_once_with(["systemctl", action, *units], check=True)


def test_gui_buttons_without_timer_use_the_service(
    tmp_path: Path, gui_controller: Any
) -> None:
    cls = gui_controller.GUIController
    fake = wizard(tmp_path)
    fake._action_units = lambda a, n: cls._action_units(fake, a, n)
    with patch.object(gui_controller.subprocess, "run") as run_:
        assert cls.stop_service(fake, "plain") is True
    run_.assert_called_once_with(["systemctl", "stop", "plain.service"], check=True)


def test_gui_status_reads_active_state(gui_controller: Any) -> None:
    out = "ActiveState=active\nSubState=waiting\nLoadState=loaded\n"
    done = subprocess.CompletedProcess([], 0, stdout=out)
    with patch.object(gui_controller.subprocess, "run", return_value=done) as run_:
        status = gui_controller.GUIController.get_service_status(None, "sonde", "timer")
    assert status == {"active": "active", "sub": "waiting", "load": "loaded"}
    assert run_.call_args.args[0][:3] == ["systemctl", "show", "sonde.timer"]


@pytest.mark.parametrize("managed,expected", [(True, "timer"), (False, "service")])
def test_gui_list_shows_the_timer_state(
    tmp_path: Path, gui_controller: Any, managed: bool, expected: str
) -> None:
    from src.models.service_model import ServiceModel

    ServiceModel("sonde").save_to_json(str(tmp_path / "sonde.json"))
    fake = wizard(tmp_path)
    fake.get_service_status = lambda name, suffix="service": {"active": suffix}
    with patch.object(gui_controller, "has_managed_timer", return_value=managed):
        [service] = gui_controller.GUIController.get_services(fake)
    assert service.status["active"] == expected
    assert bool(service.status.get("timer")) is managed


@pytest.fixture
def service_list(gui_controller: Any) -> Any:
    import importlib
    from types import ModuleType
    from unittest.mock import MagicMock

    tk = ModuleType("tkinter")
    tk.messagebox = MagicMock()  # type: ignore[attr-defined]
    ctk = ModuleType("customtkinter")
    ctk.CTkFrame = object  # type: ignore[attr-defined]
    stubs = {
        "tkinter": tk,
        "tkinter.messagebox": tk.messagebox,  # type: ignore[attr-defined]
        "customtkinter": ctk,
    }
    with patch.dict(sys.modules, stubs):
        for name in ("src.gui.frames", "src.gui.frames.service_list"):
            sys.modules.pop(name, None)
        yield importlib.import_module("src.gui.frames.service_list")


@pytest.mark.parametrize("succeeded", [True, False])
def test_gui_action_reports_failure(service_list: Any, succeeded: bool) -> None:
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    frame = SimpleNamespace(
        selected_service=SimpleNamespace(name="sonde"),
        show_success=MagicMock(),
        show_error=MagicMock(),
        refresh_services=MagicMock(),
    )
    service_list.ServiceListFrame._run_action(frame, lambda name: succeeded, "ok", "ko")
    assert frame.show_success.called is succeeded
    assert frame.show_error.called is not succeeded
    frame.refresh_services.assert_called_once()
