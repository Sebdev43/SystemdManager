import pytest
import os
import json
from src.models.service_model import ServiceModel, UnitSection, ServiceSection, InstallSection

def test_service_model_creation(basic_service):
    """Test la création basique d'un service"""
    assert basic_service.name == "test-service"
    assert basic_service.unit.description == "Service de test"
    assert basic_service.service.working_directory == "/tmp"
    assert basic_service.service.exec_start == "/usr/bin/python3 app.py"
    assert basic_service.service.user == "testuser"
    assert basic_service.install.wanted_by == ["multi-user.target"]

def test_service_sections():
    """Test la création des différentes sections"""
    service = ServiceModel("test")
    assert isinstance(service.unit, UnitSection)
    assert isinstance(service.service, ServiceSection)
    assert isinstance(service.install, InstallSection)

def test_systemd_format(basic_service):
    """Test la conversion au format systemd"""
    output = basic_service.to_systemd_file()
    assert "[Unit]" in output
    assert "Description=Service de test" in output
    assert "[Service]" in output
    assert "ExecStart=/usr/bin/python3 app.py" in output
    assert "User=testuser" in output
    assert "WorkingDirectory=/tmp" in output
    assert "[Install]" in output
    assert "WantedBy=multi-user.target" in output

def test_json_serialization(basic_service, temp_dir):
    """Test la sérialisation/désérialisation JSON"""
    json_path = os.path.join(temp_dir, "service.json")
    basic_service.save_to_json(json_path)
    
    loaded_service = ServiceModel.load_from_json(json_path)
    assert loaded_service.name == basic_service.name
    assert loaded_service.unit.description == basic_service.unit.description
    assert loaded_service.service.working_directory == basic_service.service.working_directory
    assert loaded_service.service.exec_start == basic_service.service.exec_start
    assert loaded_service.service.user == basic_service.service.user
    assert loaded_service.install.wanted_by == basic_service.install.wanted_by

def test_service_validation():
    """Test la validation des paramètres du service"""
    service = ServiceModel("test")
    
    # Test des valeurs par défaut
    assert service.service.type == "simple"
    assert service.service.restart == "no"
    assert service.service.restart_sec == 0
    assert service.service.nice == 0
    assert service.service.cpu_quota == 100
    assert service.service.remain_after_exit == True

    # Test des listes optionnelles
    assert service.unit.after is None
    assert service.unit.before is None
    assert service.unit.requires is None
    assert service.unit.wants is None
    assert service.install.wanted_by is None
    assert service.install.required_by is None
    assert service.install.also is None

@pytest.mark.parametrize("name,expected", [
    ("my-service", "my-service"),
    ("My Service", "My Service"),
    ("my_service!", "my_service!"),
    ("my.service", "my.service"),
    ("MY_SERVICE_123", "MY_SERVICE_123")
])
def test_service_name_sanitization(name, expected):
    """Test la sanitization du nom du service"""
    service = ServiceModel(name)
    assert service.name == expected
