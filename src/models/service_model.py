from dataclasses import dataclass
from typing import List, Optional
import json
import sys
import os

@dataclass
class UnitSection:
    """[Unit] Section - General service information"""
    description: str = ""  # Simple service description
    documentation: str = ""  # Documentation links
    
    # Service startup
    after: List[str] = None  # Services that must start BEFORE this service
    before: List[str] = None  # Services that must start AFTER this service
    requires: List[str] = None  # REQUIRED services for operation
    wants: List[str] = None  # RECOMMENDED but not required services
    
    # Error handling behavior
    on_failure: str = "none"  # Action on failure (none, reboot, restart)
    start_limit_burst: int = 5  # Number of allowed restarts
    start_limit_interval: int = 10  # Period to count restarts (in seconds)

@dataclass
class ServiceSection:
    """[Service] Section - How the service should operate"""
    # Service type
    type: str = "simple"  # How systemd handles the service
    
    # User and permissions
    user: str = ""
    group: str = ""
    
    # Execution commands
    working_directory: str = ""
    environment: dict = None
    exec_start: str = ""
    exec_stop: str = ""
    exec_reload: str = ""
    
    # Restart behavior
    restart: str = "no"
    restart_sec: int = 0
    
    # Security
    nice: int = 0
    memory_limit: str = ""
    cpu_quota: int = 100
    
    # Screen support
    remain_after_exit: bool = True

@dataclass
class InstallSection:
    """[Install] Section - When and how the service should be activated"""
    wanted_by: List[str] = None  
    
    required_by: List[str] = None  
    also: List[str] = None  

class ServiceModel:
    """
    Complete systemd service model
    
    This class represents a systemd service configuration with all its sections
    and provides methods to convert between systemd and JSON formats.
    
    Attributes:
        name (str): Service name
        unit (UnitSection): Unit section configuration
        service (ServiceSection): Service section configuration
        install (InstallSection): Install section configuration
    """
    def __init__(self, name: str):
        """
        Initialize a new service model
        
        Args:
            name (str): Name of the service
        """
        self.name = name
        self.unit = UnitSection()
        self.service = ServiceSection()
        self.install = InstallSection()
        
    def to_systemd_file(self) -> str:
        """
        Convert the model to systemd file format
        
        Returns:
            str: Service configuration in systemd format
        """
        content = "[Unit]\n"
        content += f"Description={self.unit.description}\n"
        
        # Add non-empty Unit options
        if self.unit.start_limit_burst:
            content += f"StartLimitBurst={self.unit.start_limit_burst}\n"
        if self.unit.start_limit_interval:
            content += f"StartLimitInterval={self.unit.start_limit_interval}\n"

        content += "\n[Service]\n"
        # Service options correction
        for key, value in vars(self.service).items():
            if value:
                if key == "exec_start":
                    if "screen" in value:
                        # Screen format correction
                        content += f"ExecStart={value}\n"
                    else:
                        # Use absolute path for other commands
                        full_path = os.path.join(self.service.working_directory, value)
                        content += f"ExecStart={full_path}\n"
                elif key == "type":
                    content += f"Type={value}\n"
                elif key == "working_directory":
                    content += f"WorkingDirectory={value}\n"
                elif key == "user":
                    content += f"User={value}\n"
                elif key == "restart":
                    content += f"Restart={value}\n"
                elif key == "remain_after_exit":
                    content += f"RemainAfterExit={str(value).lower()}\n"

        content += "\n[Install]\n"
        if self.install.wanted_by:
            content += f"WantedBy={' '.join(self.install.wanted_by)}\n"

        return content

    def to_json(self) -> dict:
        """
        Convertit le modèle en dictionnaire pour la sérialisation JSON
        """
        return {
            "name": self.name,  # Ajout du champ name
            "unit": self.unit.__dict__,
            "service": self.service.__dict__,
            "install": self.install.__dict__
        }

    @classmethod
    def load_from_json(cls, filepath: str) -> 'ServiceModel':
        """
        Load configuration from JSON file
        
        Args:
            filepath (str): Path to the JSON configuration file
            
        Returns:
            ServiceModel: Loaded service model instance
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Utiliser le nom du fichier comme nom du service
            service_name = os.path.splitext(os.path.basename(filepath))[0]
            service = cls(service_name)
            
            # Charger la section Unit
            if isinstance(data.get('unit', {}), dict):
                for key, value in data['unit'].items():
                    if hasattr(service.unit, key):
                        setattr(service.unit, key, value)
            
            # Charger la section Service
            if isinstance(data.get('service', {}), dict):
                for key, value in data['service'].items():
                    if hasattr(service.service, key):
                        setattr(service.service, key, value)
            
            # Charger la section Install
            if isinstance(data.get('install', {}), dict):
                for key, value in data['install'].items():
                    if hasattr(service.install, key):
                        setattr(service.install, key, value)
            
            return service
        
        except Exception as e:
            raise Exception(f"Erreur lors du chargement du service depuis {filepath}: {str(e)}")

    def handle_input(self, value: str, previous_step: callable = None):
        """
        Handle standard user input
        
        Args:
            value (str): User input value
            previous_step (callable, optional): Callback for previous step
            
        Returns:
            str: Processed input value
        """
        if value.lower() == 'q':
            sys.exit("Goodbye!")
        elif value.lower() == 'b' and previous_step:
            previous_step()
        return value

    def save_to_json(self, filepath: str) -> None:
        """
        Sauvegarde la configuration du service dans un fichier JSON
        
        Args:
            filepath (str): Chemin du fichier où sauvegarder la configuration
        """
        try:
            # Conversion du modèle en dictionnaire
            data = self.to_json()
            
            # Création du dossier parent si nécessaire
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Sauvegarde dans le fichier JSON avec indentation pour la lisibilité
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde dans {filepath}: {str(e)}")