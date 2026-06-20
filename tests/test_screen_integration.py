"""Tests for GNU Screen + systemd integration.

Covers the pure helpers in ``src/models/screen.py`` and the screen-aware
rendering in ``ServiceModel.to_systemd_file``. These tests are dependency-free
(no GUI/questionary imports) so they run in any environment.
"""

from src.models.screen import (
    SCREEN_BIN,
    build_screen_command,
    is_screen_command,
    normalize_screen_command,
    screen_session_from_command,
    screen_session_name,
    screen_stop_command,
)
from src.models.service_model import ServiceModel

# --- helper unit tests -----------------------------------------------------


def test_screen_session_name_prefixes_service():
    assert screen_session_name("myapp") == "service_myapp"


def test_build_screen_command_uses_non_forking_and_absolute_path():
    cmd = build_screen_command("service_myapp", "/usr/bin/python3 app.py")
    assert cmd == "/usr/bin/screen -DmS service_myapp /usr/bin/python3 app.py"
    assert "-DmS" in cmd
    assert "-dmS" not in cmd
    assert cmd.startswith(SCREEN_BIN)


def test_screen_stop_command():
    assert screen_stop_command("service_myapp") == (
        "/usr/bin/screen -S service_myapp -X quit"
    )


def test_is_screen_command_true_for_absolute_and_bare():
    assert is_screen_command("/usr/bin/screen -DmS s cmd")
    assert is_screen_command("screen -DmS s cmd")


def test_is_screen_command_false_for_non_screen():
    assert not is_screen_command("/usr/bin/python3 app.py")
    # No false positive on a substring match (e.g. "screensaver").
    assert not is_screen_command("/usr/bin/screensaver --run")


def test_screen_session_from_command_parses_all_forms():
    assert (
        screen_session_from_command("/usr/bin/screen -DmS service_a /bin/x")
        == "service_a"
    )
    assert (
        screen_session_from_command("/usr/bin/screen -dmS service_b /bin/x")
        == "service_b"
    )
    assert (
        screen_session_from_command("/usr/bin/screen -S service_c -X quit")
        == "service_c"
    )


def test_screen_session_from_command_none_when_absent():
    assert screen_session_from_command("/usr/bin/python3 app.py") is None


def test_normalize_rewrites_legacy_forking_flag():
    assert (
        normalize_screen_command("/usr/bin/screen -dmS service_a cmd")
        == "/usr/bin/screen -DmS service_a cmd"
    )


def test_normalize_leaves_non_forking_unchanged():
    cmd = "/usr/bin/screen -DmS service_a cmd"
    assert normalize_screen_command(cmd) == cmd


# --- to_systemd_file rendering tests ---------------------------------------


def _screen_service(name: str = "myapp") -> ServiceModel:
    service = ServiceModel(name)
    service.unit.description = "My app"
    service.service.working_directory = "/opt/app"
    service.service.user = "appuser"
    service.service.exec_start = build_screen_command(
        screen_session_name(name), "/usr/bin/python3 app.py"
    )
    service.install.wanted_by = ["multi-user.target"]
    return service


def test_to_systemd_file_screen_service_renders_correctly():
    out = _screen_service("myapp").to_systemd_file()
    assert "ExecStart=/usr/bin/screen -DmS service_myapp" in out
    assert "Type=simple" in out
    assert "ExecStop=/usr/bin/screen -S service_myapp -X quit" in out
    # RemainAfterExit must NOT be set for screen services.
    assert "RemainAfterExit" not in out
    # The forking flag must never leak into the rendered unit.
    assert "-dmS" not in out


def test_to_systemd_file_screen_forces_simple_even_if_forking_chosen():
    service = _screen_service("myapp")
    service.service.type = "forking"
    out = service.to_systemd_file()
    assert "Type=simple" in out
    assert "Type=forking" not in out


def test_to_systemd_file_normalizes_legacy_dms_screen_command():
    service = _screen_service("legacy")
    # Simulate an old saved config that stored the forking flag.
    service.service.exec_start = (
        "/usr/bin/screen -dmS service_legacy /usr/bin/python3 app.py"
    )
    out = service.to_systemd_file()
    assert "ExecStart=/usr/bin/screen -DmS service_legacy" in out
    assert "-dmS" not in out
    assert "ExecStop=/usr/bin/screen -S service_legacy -X quit" in out


def test_to_systemd_file_non_screen_service_behavior_unchanged():
    service = ServiceModel("plain")
    service.unit.description = "Plain"
    service.service.working_directory = "/opt/app"
    service.service.exec_start = "app.py"
    service.service.user = "appuser"
    service.install.wanted_by = ["multi-user.target"]
    out = service.to_systemd_file()
    # Non-screen services keep RemainAfterExit and gain no ExecStop/screen.
    assert "RemainAfterExit=true" in out
    assert "ExecStop" not in out
    assert "screen" not in out
    # Absolute-path join still applied for non-screen commands.
    assert "ExecStart=/opt/app/app.py" in out


# --- hardening tests (adversarial review fixes) ----------------------------


def test_is_screen_command_false_when_screen_is_only_an_argument():
    # "screen" appearing as an argument must not classify the command.
    assert not is_screen_command("/bin/cat screen")
    assert not is_screen_command("/usr/bin/mybackup --dest /opt/screen")
    assert not is_screen_command("echo screen")


def test_is_screen_command_false_without_named_session():
    # screen is the program but no -DmS/-dmS/-S names a session.
    assert not is_screen_command("/usr/bin/screen -dm mycmd")
    assert not is_screen_command("/usr/bin/screen mycmd")


def test_screen_session_parsing_anchored_to_program_token():
    # A stray -S in a wrapper before screen must not be read as the session.
    assert screen_session_from_command("sudo -S screen -DmS realsession cmd") is None
    # Options before screen's own -DmS are skipped correctly.
    assert screen_session_from_command("/usr/bin/screen -L -DmS sess cmd") == "sess"


def test_normalize_preserves_significant_whitespace():
    cmd = '/usr/bin/screen -DmS s bash -c "echo a   b"'
    # No -dmS to rewrite, and the triple space inside quotes is preserved.
    assert normalize_screen_command(cmd) == cmd
    legacy = '/usr/bin/screen -dmS s bash -c "echo a   b"'
    assert normalize_screen_command(legacy) == (
        '/usr/bin/screen -DmS s bash -c "echo a   b"'
    )


def test_to_systemd_file_screen_as_argument_not_treated_as_screen():
    service = ServiceModel("plain")
    service.unit.description = "Plain"
    service.service.working_directory = "/opt/app"
    service.service.type = "forking"
    service.service.exec_start = "mytool --log screen"
    service.install.wanted_by = ["multi-user.target"]
    out = service.to_systemd_file()
    # Not a screen service: user Type kept, RemainAfterExit present, no ExecStop.
    assert "Type=forking" in out
    assert "RemainAfterExit=true" in out
    assert "ExecStop" not in out
