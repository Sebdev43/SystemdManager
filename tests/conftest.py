import pytest
import os
import tempfile
import shutil
from src.models.service_model import ServiceModel

@pytest.fixture
def temp_dir():

    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def basic_service():

    service = ServiceModel("test-service")
    service.unit.description = "Service de test"
    service.service.working_directory = "/tmp"
    service.service.exec_start = "/usr/bin/python3 app.py"
    service.service.user = "testuser"
    service.install.wanted_by = ["multi-user.target"]
    return service

@pytest.fixture
def cli_controller(temp_dir):

    from src.cli.cli_controller import CLIController
    controller = CLIController()
    controller.services_dir = os.path.join(temp_dir, "services")
    controller.logs_dir = os.path.join(temp_dir, "logs")
    controller.setup_directories()
    return controller
