"""Tests for unified systemd unit-file generation (ServiceModel.to_systemd_file).

Both the CLI and the GUI now render through this single method, so these tests
lock the directive set and formatting. Dependency-free (no GUI imports).
"""

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
