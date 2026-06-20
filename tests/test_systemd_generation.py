"""Tests for unified systemd unit-file generation (ServiceModel.to_systemd_file).

Both the CLI and the GUI now render through this single method, so these tests
lock the directive set and formatting. Dependency-free (no GUI imports).
"""

import pytest

from src.models.service_model import ServiceModel


def _service() -> ServiceModel:
    service = ServiceModel("web")
    service.unit.description = "Web app"
    service.service.type = "simple"
    service.service.user = "appuser"
    service.service.working_directory = "/opt/web"
    service.service.exec_start = "app.py"
    service.install.wanted_by = ["multi-user.target"]
    return service


def test_restart_sec_emitted_only_when_positive():
    service = _service()
    service.service.restart = "on-failure"
    service.service.restart_sec = 0
    assert "RestartSec" not in service.to_systemd_file()
    service.service.restart_sec = 5
    assert "RestartSec=5" in service.to_systemd_file()


def test_group_emitted_when_set():
    service = _service()
    assert "Group=" not in service.to_systemd_file()
    service.service.group = "webgroup"
    assert "Group=webgroup" in service.to_systemd_file()


def test_after_is_space_joined():
    service = _service()
    service.unit.after = ["network.target", "postgresql.service"]
    assert "After=network.target postgresql.service" in service.to_systemd_file()


def test_start_limit_uses_current_directive_name():
    service = _service()
    service.unit.start_limit_interval = 30
    out = service.to_systemd_file()
    assert "StartLimitIntervalSec=30" in out
    # The legacy bare name must no longer be emitted.
    assert "StartLimitInterval=" not in out


def test_wanted_by_space_joined():
    service = _service()
    service.install.wanted_by = ["multi-user.target", "graphical.target"]
    out = service.to_systemd_file()
    assert "WantedBy=multi-user.target graphical.target" in out
    wanted_by_line = out.split("WantedBy=")[1].splitlines()[0]
    assert "," not in wanted_by_line


def test_full_non_screen_render_has_all_sections_and_fields():
    service = _service()
    service.unit.after = ["network.target"]
    service.service.group = "appgroup"
    service.service.restart = "always"
    service.service.restart_sec = 3
    service.unit.start_limit_burst = 4
    service.unit.start_limit_interval = 20
    out = service.to_systemd_file()
    for expected in [
        "[Unit]",
        "Description=Web app",
        "After=network.target",
        "StartLimitBurst=4",
        "StartLimitIntervalSec=20",
        "[Service]",
        "Type=simple",
        "User=appuser",
        "Group=appgroup",
        "WorkingDirectory=/opt/web",
        "ExecStart=/opt/web/app.py",
        "Restart=always",
        "RestartSec=3",
        "RemainAfterExit=true",
        "[Install]",
        "WantedBy=multi-user.target",
    ]:
        assert expected in out, f"missing directive: {expected}"


# --- directive-injection hardening (newline rejection) ---------------------


@pytest.mark.parametrize("payload", ["app\nUser=root", "app\rUser=root"])
def test_newline_in_exec_start_is_rejected(payload):
    service = _service()
    service.service.exec_start = payload
    with pytest.raises(ValueError):
        service.to_systemd_file()


def test_newline_in_description_is_rejected():
    service = _service()
    service.unit.description = "ok\nExecStart=/evil"
    with pytest.raises(ValueError):
        service.to_systemd_file()


def test_newline_in_user_is_rejected():
    service = _service()
    service.service.user = "root\nGroup=wheel"
    with pytest.raises(ValueError):
        service.to_systemd_file()


def test_newline_in_after_element_is_rejected():
    service = _service()
    service.unit.after = ["network.target\nExecStartPre=/evil"]
    with pytest.raises(ValueError):
        service.to_systemd_file()


def test_newline_in_wanted_by_element_is_rejected():
    service = _service()
    service.install.wanted_by = ["multi-user.target\nAlias=evil"]
    with pytest.raises(ValueError):
        service.to_systemd_file()


def test_clean_values_still_render_after_hardening():
    service = _service()
    out = service.to_systemd_file()
    assert "User=appuser" in out
    assert "ExecStart=/opt/web/app.py" in out


def test_newline_in_numeric_unit_field_is_rejected():
    # A corrupted JSON can set an int-typed field to a string (load_from_json
    # does not coerce); int() must fail-fast on an embedded newline.
    service = _service()
    service.unit.start_limit_burst = "5\nExecStartPre=/bin/evil"
    with pytest.raises(ValueError):
        service.to_systemd_file()


def test_newline_in_restart_sec_is_rejected():
    service = _service()
    service.service.restart = "always"
    service.service.restart_sec = "3\nUser=root"
    with pytest.raises(ValueError):
        service.to_systemd_file()


def test_newline_in_remain_after_exit_is_rejected():
    service = _service()
    service.service.remain_after_exit = "true\nExecStop=/bin/evil"
    with pytest.raises(ValueError):
        service.to_systemd_file()
