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

    def save_to_json(self, filepath: str):
        """
        Save configuration to JSON file
        
        Args:
            filepath (str): Path where to save the JSON file
        """
        data = {
            'name': self.name,
            'unit': self.unit.__dict__,
            'service': self.service.__dict__,
            'install': self.install.__dict__
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def load_from_json(cls, filepath: str) -> 'ServiceModel':
        """
        Load configuration from JSON file
        
        Args:
            filepath (str): Path to the JSON configuration file
            
        Returns:
            ServiceModel: Loaded service model instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
            
            # Migrate old configurations
            if 'service' in data and 'start_limit_interval' in data['service']:
                # Move start_limit_interval to unit section
                if 'unit' not in data:
                    data['unit'] = {}
                data['unit']['start_limit_interval'] = data['service'].pop('start_limit_interval')
            
            if 'service' in data and 'start_limit_burst' in data['service']:
                # Move start_limit_burst to unit section
                if 'unit' not in data:
                    data['unit'] = {}
                data['unit']['start_limit_burst'] = data['service'].pop('start_limit_burst')
            
            # Create service
            service = cls(data['name'])
            
            # Load sections with default value handling
            if 'unit' in data:
                service.unit = UnitSection(**data['unit'])
            if 'service' in data:
                service.service = ServiceSection(**data['service'])
            if 'install' in data:
                service.install = InstallSection(**data['install'])
                
            return service

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