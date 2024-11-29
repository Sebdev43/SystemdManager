import pytest
import os
import json
from unittest.mock import patch, MagicMock, mock_open
from src.cli.cli_controller import CLIController
from src.models.service_model import ServiceModel
import tempfile

def test_setup_directories(cli_controller, temp_dir):

    assert os.path.exists(cli_controller.services_dir)
    assert os.path.exists(cli_controller.logs_dir)

def test_check_sudo():

    controller = CLIController()
    with patch('os.geteuid', return_value=0):
        assert controller.check_sudo() == True
    with patch('os.geteuid', return_value=1000):
        assert controller.check_sudo() == False

def test_request_sudo():

    controller = CLIController()
    with patch('os.geteuid', return_value=1000):
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

    with patch('builtins.open', mock_file):
        users = controller.get_system_users()
        print(f"\nUtilisateurs trouvés : {users}")
        assert isinstance(users, list)
        assert len(users) == 2  
        assert users == ['user1', 'user2']  

def test_get_service_type():

    controller = CLIController()
    with patch('questionary.select') as mock_select:
        mock_select.return_value.ask.return_value = " simple - Le processus reste au premier plan"
        assert controller.get_service_type() == "simple"
        
        mock_select.return_value.ask.return_value = " forking - Le processus se détache en arrière-plan (recommandé si vous utilisez screen)"
        assert controller.get_service_type() == "forking"

@patch('questionary.text')
def test_get_service_name(mock_text, cli_controller):

    mock_text.return_value.ask.return_value = "test-service"
    assert cli_controller.get_service_name() == "test-service"

    mock_text.return_value.ask.return_value = "b"
    assert cli_controller.get_service_name() is None

@patch('questionary.text')
def test_get_service_description(mock_text, cli_controller):

    mock_text.return_value.ask.return_value = "Service de test"
    assert cli_controller.get_service_description() == "Service de test"

def test_validate_service_name(cli_controller):

    assert cli_controller.validate_service_name("test-service") is True
    assert cli_controller.validate_service_name("my_service") is True

    assert cli_controller.validate_service_name("") is False
    assert cli_controller.validate_service_name("test@service") is False
    assert cli_controller.validate_service_name("test service") is False

@patch('os.system')
def test_service_operations(mock_system, cli_controller):

    mock_system.side_effect = [1, 0]  
    cli_controller.start_service("test-service")
    mock_system.assert_any_call("systemctl is-active --quiet test-service")
    mock_system.assert_any_call("systemctl start test-service")

    mock_system.reset_mock()
    mock_system.side_effect = [0]  
    cli_controller.stop_service("test-service")
    mock_system.assert_any_call("systemctl stop test-service")

    mock_system.reset_mock()
    cli_controller.restart_service("test-service")
    mock_system.assert_any_call("systemctl restart test-service")

@patch('questionary.confirm')
def test_handle_navigation_choice(mock_confirm, cli_controller):

    mock_confirm.return_value.ask.return_value = False
    result = cli_controller.handle_navigation_choice("↩️  Retour", lambda: None)
    assert result == False

    result = cli_controller.handle_navigation_choice("Option 1")
    assert result == True

@patch('questionary.select')
@patch('questionary.text')
def test_get_working_directory(mock_text, mock_select, cli_controller, temp_dir):

    mock_select.return_value.ask.return_value = "📝 Saisir le chemin manuellement"
    mock_text.return_value.ask.return_value = temp_dir
    assert cli_controller.get_working_directory() == temp_dir

def test_service_model_migration():

    old_config = {
        'name': 'test-service',
        'unit': {
            'description': 'Service de test'
        },
        'service': {
            'type': 'simple',
            'start_limit_interval': 300,
            'start_limit_burst': 5
        },
        'install': {
            'wanted_by': ['multi-user.target']
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        json.dump(old_config, temp_file)
    
    try:

        service = ServiceModel.load_from_json(temp_file.name)

        assert service.unit.start_limit_interval == 300
        assert service.unit.start_limit_burst == 5
        assert not hasattr(service.service, 'start_limit_interval')
        assert not hasattr(service.service, 'start_limit_burst')

        assert service.name == 'test-service'
        assert service.unit.description == 'Service de test'
        assert service.service.type == 'simple'
        assert service.install.wanted_by == ['multi-user.target']
    finally:

        os.unlink(temp_file.name)

@patch('questionary.select')
@patch('questionary.text')
def test_edit_service_restart_limits(mock_text, mock_select, cli_controller):

    service = ServiceModel("test-service")

    mock_select.return_value.ask.side_effect = ["⏱️  Limites de redémarrage", "↩️  Retour"]
    mock_text.return_value.ask.side_effect = ["10", "300"] 

    cli_controller.edit_unit_section(service)

    assert service.unit.start_limit_burst == 10
    assert service.unit.start_limit_interval == 300

@patch('questionary.select')
@patch('questionary.text')
def test_edit_service_restart_delay(mock_text, mock_select, cli_controller):

    service = ServiceModel("test-service")

    mock_select.return_value.ask.side_effect = ["⏱️  Délai de redémarrage", "↩️  Retour"]
    mock_text.return_value.ask.return_value = "30"

    cli_controller.edit_service_section(service)

    assert service.service.restart_sec == 30
