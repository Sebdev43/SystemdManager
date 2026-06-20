from dataclasses import dataclass
from typing import List, Optional
import json
import sys
import os
import re

from src.models.screen import (
    is_screen_command,
    normalize_screen_command,
    screen_session_from_command,
    screen_stop_command,
)

# A service name is interpolated into systemd unit-file paths and systemctl
# commands downstream, so a name loaded from an untrusted JSON file is held to
# a strict charset (must start alphanumeric; no path separators, '..',
# whitespace or shell metacharacters).
_VALID_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._@-]*$")


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
        if self.unit.after:
            content += f"After={' '.join(self.unit.after)}\n"
        if self.unit.start_limit_burst:
            content += f"StartLimitBurst={self.unit.start_limit_burst}\n"
        if self.unit.start_limit_interval:
            # StartLimitIntervalSec is the current name (renamed from the
            # legacy alias StartLimitInterval in systemd v229); StartLimit*
            # directives belong in [Unit]. A plain integer means seconds.
            content += f"StartLimitIntervalSec={self.unit.start_limit_interval}\n"

        content += "\n[Service]\n"

        # A service launched through GNU Screen must use the non-forking -DmS
        # form with Type=simple so systemd keeps tracking the live process
        # (see src/models/screen.py for the rationale and references).
        screen_mode = is_screen_command(self.service.exec_start)
        session = (
            screen_session_from_command(self.service.exec_start)
            if screen_mode
            else None
        )
        if screen_mode:
            content += "Type=simple\n"

        # Service options correction
        for key, value in vars(self.service).items():
            if not value:
                continue
            if key == "exec_start":
                if screen_mode:
                    # Keep the screen command verbatim but normalise a legacy
                    # forking -dmS flag to the non-forking -DmS form.
                    content += f"ExecStart={normalize_screen_command(value)}\n"
                else:
                    # Use absolute path for other commands
                    full_path = os.path.join(
                        self.service.working_directory, value
                    )
                    content += f"ExecStart={full_path}\n"
            elif key == "type":
                # Type for screen services is forced to simple above.
                if not screen_mode:
                    content += f"Type={value}\n"
            elif key == "exec_stop":
                content += f"ExecStop={value}\n"
            elif key == "working_directory":
                content += f"WorkingDirectory={value}\n"
            elif key == "user":
                content += f"User={value}\n"
            elif key == "group":
                content += f"Group={value}\n"
            elif key == "restart":
                content += f"Restart={value}\n"
            elif key == "restart_sec":
                content += f"RestartSec={value}\n"
            elif key == "remain_after_exit":
                # RemainAfterExit must not be set for screen services: with
                # -DmS systemd already tracks the live process.
                if not screen_mode:
                    content += f"RemainAfterExit={str(value).lower()}\n"

        # Clean shutdown for screen sessions (Arch Wiki canonical pattern).
        if screen_mode and session and not self.service.exec_stop:
            content += f"ExecStop={screen_stop_command(session)}\n"

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
        except (OSError, ValueError) as e:
            # ValueError covers json.JSONDecodeError and UnicodeDecodeError
            # (non-UTF-8 file content).
            raise ValueError(
                f"Erreur lors du chargement du service depuis {filepath}: {e}"
            ) from e

        if not isinstance(data, dict):
            raise ValueError(
                f"Configuration de service invalide dans {filepath}: "
                "objet JSON attendu"
            )

        # Prefer the stored service name, but only when it is a safe string;
        # otherwise fall back to the (filesystem-derived) file name, which is
        # the trusted source the loader used previously.
        fallback_name = os.path.splitext(os.path.basename(filepath))[0]
        raw_name = data.get('name')
        if isinstance(raw_name, str) and raw_name:
            if not _VALID_NAME_RE.match(raw_name):
                raise ValueError(
                    f"Nom de service invalide dans {filepath}: {raw_name!r}"
                )
            service_name = raw_name
        else:
            service_name = fallback_name
        service = cls(service_name)

        # [Unit] section
        unit_data = data.get('unit', {})
        if isinstance(unit_data, dict):
            for key, value in unit_data.items():
                if hasattr(service.unit, key):
                    setattr(service.unit, key, value)

        # [Service] section
        service_data = data.get('service', {})
        if isinstance(service_data, dict):
            for key, value in service_data.items():
                # Backward-compat: StartLimit* used to live under [Service];
                # systemd (and this model) keep them under [Unit].
                if key in ('start_limit_interval', 'start_limit_burst'):
                    setattr(service.unit, key, value)
                elif hasattr(service.service, key):
                    setattr(service.service, key, value)

        # [Install] section
        install_data = data.get('install', {})
        if isinstance(install_data, dict):
            for key, value in install_data.items():
                if hasattr(service.install, key):
                    setattr(service.install, key, value)

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

    def save_to_json(self, filepath: str) -> None:
        """
        Sauvegarde la configuration du service dans un fichier JSON
        
        Args:
            filepath (str): Chemin du fichier où sauvegarder la configuration
        """
        data = self.to_json()

        # Create the parent directory only when the path has one (a bare
        # filename yields '' and os.makedirs('') raises FileNotFoundError).
        parent = os.path.dirname(filepath)
        try:
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
        except OSError as e:
            raise ValueError(
                f"Erreur lors de la sauvegarde dans {filepath}: {e}"
            ) from e