import pytest
import os
import json
from unittest.mock import patch, MagicMock, mock_open
from src.cli.cli_controller import CLIController
from src.models.service_model import ServiceModel
import tempfile

def test_setup_directories(cli_controller, temp_dir):
    """Test la création des répertoires nécessaires"""
    assert os.path.exists(cli_controller.services_dir)
    assert os.path.exists(cli_controller.logs_dir)

def test_check_sudo():
    """Test la vérification des droits sudo"""
    controller = CLIController()
    with patch('os.geteuid', return_value=0):
        assert controller.check_sudo() == True
    with patch('os.geteuid', return_value=1000):
        assert controller.check_sudo() == False

def test_request_sudo():
    """Test la demande de droits sudo"""
    controller = CLIController()
    with patch('os.geteuid', return_value=1000):
        with pytest.raises(SystemExit):
            controller.request_sudo("test")

def test_get_system_users():
    """Test la récupération des utilisateurs système"""
    controller = CLIController()
    
    # Préparer le contenu du fichier
    passwd_content = (
        "root:x:0:0:root:/root:/bin/bash\n"  # UID < 1000, devrait être filtré
        "user1:x:1000:1000:User One:/home/user1:/bin/bash\n"  # UID = 1000, devrait être inclus
        "user2:x:1001:1001:User Two:/home/user2:/bin/bash\n"  # UID > 1000, devrait être inclus
        "nobody:x:65534:65534:Nobody:/:/usr/sbin/nologin\n"  # nobody, devrait être filtré
    )
    
    # Créer un mock pour la fonction open
    mock_file = mock_open(read_data=passwd_content)
    
    # Patcher la fonction open
    with patch('builtins.open', mock_file):
        users = controller.get_system_users()
        print(f"\nUtilisateurs trouvés : {users}")
        assert isinstance(users, list)
        assert len(users) == 2  # Seulement user1 et user2 devraient être inclus
        assert users == ['user1', 'user2']  # La liste devrait être triée

def test_get_service_type():
    """Test la sélection du type de service"""
    controller = CLIController()
    with patch('questionary.select') as mock_select:
        mock_select.return_value.ask.return_value = " simple - Le processus reste au premier plan"
        assert controller.get_service_type() == "simple"
        
        mock_select.return_value.ask.return_value = " forking - Le processus se détache en arrière-plan (recommandé si vous utilisez screen)"
        assert controller.get_service_type() == "forking"

@patch('questionary.text')
def test_get_service_name(mock_text, cli_controller):
    """Test la saisie du nom du service"""
    # Test avec un nom valide
    mock_text.return_value.ask.return_value = "test-service"
    assert cli_controller.get_service_name() == "test-service"
    
    # Test avec retour
    mock_text.return_value.ask.return_value = "b"
    assert cli_controller.get_service_name() is None

@patch('questionary.text')
def test_get_service_description(mock_text, cli_controller):
    """Test la saisie de la description du service"""
    mock_text.return_value.ask.return_value = "Service de test"
    assert cli_controller.get_service_description() == "Service de test"

def test_validate_service_name(cli_controller):
    """Test la validation du nom du service"""
    # Noms valides
    assert cli_controller.validate_service_name("test-service") is True
    assert cli_controller.validate_service_name("my_service") is True
    
    # Noms invalides
    assert cli_controller.validate_service_name("") is False
    assert cli_controller.validate_service_name("test@service") is False
    assert cli_controller.validate_service_name("test service") is False

@patch('os.system')
def test_service_operations(mock_system, cli_controller):
    """Test les opérations sur les services"""
    # Test du démarrage
    mock_system.side_effect = [1, 0]  # is-active retourne 1 (inactif), start retourne 0
    cli_controller.start_service("test-service")
    mock_system.assert_any_call("systemctl is-active --quiet test-service")
    mock_system.assert_any_call("systemctl start test-service")
    
    # Test de l'arrêt
    mock_system.reset_mock()
    mock_system.side_effect = [0]  # is-active retourne 0 (actif)
    cli_controller.stop_service("test-service")
    mock_system.assert_any_call("systemctl stop test-service")
    
    # Test du redémarrage
    mock_system.reset_mock()
    cli_controller.restart_service("test-service")
    mock_system.assert_any_call("systemctl restart test-service")

@patch('questionary.confirm')
def test_handle_navigation_choice(mock_confirm, cli_controller):
    """Test la gestion des choix de navigation"""
    # Test du retour
    mock_confirm.return_value.ask.return_value = False
    result = cli_controller.handle_navigation_choice("↩️  Retour", lambda: None)
    assert result == False
    
    # Test de la sélection d'une option normale
    result = cli_controller.handle_navigation_choice("Option 1")
    assert result == True

@patch('questionary.select')
@patch('questionary.text')
def test_get_working_directory(mock_text, mock_select, cli_controller, temp_dir):
    """Test la sélection du dossier de travail"""
    # Test avec saisie manuelle d'un chemin valide
    mock_select.return_value.ask.return_value = "📝 Saisir le chemin manuellement"
    mock_text.return_value.ask.return_value = temp_dir
    assert cli_controller.get_working_directory() == temp_dir

def test_service_model_migration():
    """Test la migration des anciennes configurations"""
    # Ancien format avec start_limit_interval dans service
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
    
    # Créer un fichier temporaire avec l'ancienne configuration
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        json.dump(old_config, temp_file)
    
    try:
        # Charger le service depuis le fichier
        service = ServiceModel.load_from_json(temp_file.name)
        
        # Vérifier que les paramètres ont été migrés correctement
        assert service.unit.start_limit_interval == 300
        assert service.unit.start_limit_burst == 5
        assert not hasattr(service.service, 'start_limit_interval')
        assert not hasattr(service.service, 'start_limit_burst')
        
        # Vérifier que les autres paramètres sont conservés
        assert service.name == 'test-service'
        assert service.unit.description == 'Service de test'
        assert service.service.type == 'simple'
        assert service.install.wanted_by == ['multi-user.target']
    finally:
        # Nettoyer le fichier temporaire
        os.unlink(temp_file.name)

@patch('questionary.select')
@patch('questionary.text')
def test_edit_service_restart_limits(mock_text, mock_select, cli_controller):
    """Test l'édition des limites de redémarrage"""
    # Créer un service de test
    service = ServiceModel("test-service")
    
    # Simuler les choix de l'utilisateur
    mock_select.return_value.ask.side_effect = ["⏱️  Limites de redémarrage", "↩️  Retour"]
    mock_text.return_value.ask.side_effect = ["10", "300"]  # burst puis interval
    
    # Appeler la méthode d'édition
    cli_controller.edit_unit_section(service)
    
    # Vérifier que les valeurs ont été mises à jour
    assert service.unit.start_limit_burst == 10
    assert service.unit.start_limit_interval == 300

@patch('questionary.select')
@patch('questionary.text')
def test_edit_service_restart_delay(mock_text, mock_select, cli_controller):
    """Test l'édition du délai de redémarrage"""
    # Créer un service de test
    service = ServiceModel("test-service")
    
    # Simuler les choix de l'utilisateur
    mock_select.return_value.ask.side_effect = ["⏱️  Délai de redémarrage", "↩️  Retour"]
    mock_text.return_value.ask.return_value = "30"
    
    # Appeler la méthode d'édition
    cli_controller.edit_service_section(service)
    
    # Vérifier que la valeur a été mise à jour
    assert service.service.restart_sec == 30
