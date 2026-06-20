import json
import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.cli.cli_controller import CLIController
from src.models.service_model import ServiceModel


def test_setup_directories(cli_controller, temp_dir):

    assert os.path.exists(cli_controller.services_dir)
    assert os.path.exists(cli_controller.logs_dir)


def test_check_sudo():

    controller = CLIController()
    with patch("os.geteuid", return_value=0):
        assert controller.check_sudo()
    with patch("os.geteuid", return_value=1000):
        assert not controller.check_sudo()


def test_request_sudo():

    controller = CLIController()
    with patch("os.geteuid", return_value=1000):
        with pytest.raises(SystemExit):
            controller.request_sudo("test")


def test_get_system_users():

    controller = CLIController()

    passwd_content = (
        "root:x:0:0:root:/root:/bin/bash\n"
        "user1:x:1000:1000:User One:/home/user1:/bin/bash\n"
        "user2:x:1001:1001:User Two:/home/user2:/bin/bash\n"
        "nobody:x:65534:65534:Nobody:/:/usr/sbin/nologin\n"
    )

    mock_file = mock_open(read_data=passwd_content)

    with patch("builtins.open", mock_file):
        users = controller.get_system_users()
        print(f"\nUtilisateurs trouvés : {users}")
        assert isinstance(users, list)
        assert len(users) == 2
        assert users == ["user1", "user2"]


def test_get_service_type():

    controller = CLIController()
    with patch("questionary.select") as mock_select:
        mock_select.return_value.ask.return_value = (
            " simple - Le processus reste au premier plan"
        )
        assert controller.get_service_type() == "simple"

        mock_select.return_value.ask.return_value = " forking - Le processus se détache en arrière-plan (recommandé si vous utilisez screen)"
        assert controller.get_service_type() == "forking"


@patch("questionary.text")
def test_get_service_name(mock_text, cli_controller):

    mock_text.return_value.ask.return_value = "test-service"
    assert cli_controller.get_service_name() == "test-service"

    mock_text.return_value.ask.return_value = "b"
    assert cli_controller.get_service_name() is None


@patch("questionary.text")
def test_get_service_description(mock_text, cli_controller):

    mock_text.return_value.ask.return_value = "Service de test"
    assert cli_controller.get_service_description() == "Service de test"


def test_validate_service_name(cli_controller):

    assert cli_controller.validate_service_name("test-service") is True
    assert cli_controller.validate_service_name("my_service") is True

    assert cli_controller.validate_service_name("") is False
    assert cli_controller.validate_service_name("test@service") is False
    assert cli_controller.validate_service_name("test service") is False


@patch("subprocess.run")
def test_service_operations(mock_run, cli_controller):

    def result(code):
        return MagicMock(returncode=code)

    # start: is-active -> inactive (1) so it proceeds; start -> success (0).
    mock_run.side_effect = [result(1), result(0), result(0), result(0)]
    cli_controller.start_service("test-service")
    mock_run.assert_any_call(["systemctl", "is-active", "--quiet", "test-service"])
    mock_run.assert_any_call(["systemctl", "start", "test-service"])
    # status uses --no-pager so no interactive pager (Ctrl+C would otherwise
    # reach the parent's SIGINT handler and exit the whole app).
    mock_run.assert_any_call(["systemctl", "status", "test-service", "--no-pager"])

    mock_run.reset_mock()
    # stop: is-active -> active (0) so it proceeds; stop -> success (0).
    mock_run.side_effect = [result(0), result(0), result(0)]
    cli_controller.stop_service("test-service")
    mock_run.assert_any_call(["systemctl", "stop", "test-service"])

    mock_run.reset_mock()
    mock_run.side_effect = [result(0), result(0), result(0)]
    cli_controller.restart_service("test-service")
    mock_run.assert_any_call(["systemctl", "restart", "test-service"])


@patch("subprocess.run")
def test_get_service_status_uses_no_shell_list_args(mock_run, cli_controller):
    mock_run.return_value = MagicMock(stdout="active\n")
    status = cli_controller.get_service_status("test-service")
    list_args = [call.args[0] for call in mock_run.call_args_list]
    # No shell: the service name is passed as a separate list element.
    assert ["systemctl", "is-active", "test-service"] in list_args
    assert ["systemctl", "is-enabled", "test-service"] in list_args
    assert status["active"] == "active"


@patch("questionary.confirm")
def test_handle_navigation_choice(mock_confirm, cli_controller):

    mock_confirm.return_value.ask.return_value = False
    result = cli_controller.handle_navigation_choice("↩️  Retour", lambda: None)
    assert not result

    result = cli_controller.handle_navigation_choice("Option 1")
    assert result


@patch("questionary.select")
@patch("questionary.text")
def test_get_working_directory(mock_text, mock_select, cli_controller, temp_dir):

    mock_select.return_value.ask.return_value = "📝 Saisir le chemin manuellement"
    mock_text.return_value.ask.return_value = temp_dir
    assert cli_controller.get_working_directory() == temp_dir


def test_service_model_migration():

    old_config = {
        "name": "test-service",
        "unit": {"description": "Service de test"},
        "service": {
            "type": "simple",
            "start_limit_interval": 300,
            "start_limit_burst": 5,
        },
        "install": {"wanted_by": ["multi-user.target"]},
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        json.dump(old_config, temp_file)

    try:
        service = ServiceModel.load_from_json(temp_file.name)

        assert service.unit.start_limit_interval == 300
        assert service.unit.start_limit_burst == 5
        assert not hasattr(service.service, "start_limit_interval")
        assert not hasattr(service.service, "start_limit_burst")

        assert service.name == "test-service"
        assert service.unit.description == "Service de test"
        assert service.service.type == "simple"
        assert service.install.wanted_by == ["multi-user.target"]
    finally:
        os.unlink(temp_file.name)


@patch("questionary.select")
@patch("questionary.text")
def test_edit_service_restart_limits(mock_text, mock_select, cli_controller):

    service = ServiceModel("test-service")

    # Current edit_unit_section flow: separate interval + burst options.
    mock_select.return_value.ask.side_effect = [
        "⏰ Délai avant redémarrage",  # EDIT_START_LIMIT_INTERVAL
        "🔄 Nombre de redémarrages",  # EDIT_START_LIMIT_BURST
        "↩️  Retour",  # BACK
    ]
    mock_text.return_value.ask.side_effect = ["300", "10"]

    cli_controller.edit_unit_section(service)

    assert service.unit.start_limit_interval == 300
    assert service.unit.start_limit_burst == 10


@patch("questionary.select")
@patch("questionary.text")
def test_edit_service_restart_delay(mock_text, mock_select, cli_controller):

    service = ServiceModel("test-service")

    mock_select.return_value.ask.side_effect = ["⏱️  Délai de redémarrage", "↩️  Retour"]
    mock_text.return_value.ask.return_value = "30"

    cli_controller.edit_service_section(service)

    assert service.service.restart_sec == 30
