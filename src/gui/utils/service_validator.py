import os
import re
from typing import Dict, List, Optional, Tuple
import subprocess
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """
    Data class representing the result of a service validation.
    
    Attributes:
        is_valid (bool): Whether the service configuration is valid
        errors (List[str]): List of validation errors
        warnings (List[str]): List of validation warnings
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class ServiceValidator:
    """
    Validator class for systemd service configurations.
    
    This class provides methods to validate various aspects of a systemd service
    configuration including service name, command, working directory, and user settings.
    
    Attributes:
        errors (List[str]): List of validation errors
        warnings (List[str]): List of validation warnings
    """
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_service_config(self, config: Dict) -> ValidationResult:

        self.errors = []
        self.warnings = []

        self._validate_service_name(config.get('name', ''))

        self._validate_command(config.get('command', ''))

        self._validate_working_directory(config.get('working_directory', ''))

        self._validate_restart_config(config.get('restart', 'no'),
                                   config.get('restart_sec', '0'),
                                   config.get('max_restarts', '3'))

        self._validate_user(config.get('user', ''))

        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors.copy(),
            warnings=self.warnings.copy()
        )

    def _validate_service_name(self, name: str) -> None:

        if not name:
            self.errors.append("Le nom du service est requis")
            return

        if len(name) > 255:
            self.errors.append("Le nom du service est trop long (maximum 255 caractères)")
        
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9-_]*$', name):
            self.errors.append("Le nom du service doit commencer par une lettre et ne contenir que des lettres, chiffres, tirets et underscores")
        
        if os.path.exists(f"/etc/systemd/system/{name}.service"):
            self.warnings.append(f"Un service nommé '{name}' existe déjà")

    def _validate_command(self, command: str) -> None:

        if not command:
            self.errors.append("La commande est requise")
            return

        if len(command) > 1024:
            self.errors.append("La commande est trop longue (maximum 1024 caractères)")

        cmd_parts = command.split()
        if not cmd_parts:
            self.errors.append("La commande ne peut pas être vide")
            return

        executable = cmd_parts[0]

        if not os.path.isabs(executable):
            self.errors.append("L'exécutable doit être spécifié avec un chemin absolu")
            return

        if not os.path.exists(executable):
            self.errors.append(f"L'exécutable '{executable}' n'existe pas")
        elif not os.path.isfile(executable):
            self.errors.append(f"'{executable}' n'est pas un fichier")
        elif not os.access(executable, os.X_OK):
            if not executable.endswith(('.sh', '.py', '.bash', '.js')):
                self.errors.append(f"'{executable}' n'a pas les permissions d'exécution")

    def _validate_working_directory(self, directory: str) -> None:

        if not directory:
            return 

        if len(directory) > 4096:
            self.errors.append("Le chemin du répertoire est trop long (maximum 4096 caractères)")
            return

        if not os.path.isabs(directory):
            self.errors.append("Le répertoire de travail doit être un chemin absolu")
            return

        if not os.path.exists(directory):
            self.errors.append(f"Le répertoire '{directory}' n'existe pas")
        elif not os.path.isdir(directory):
            self.errors.append(f"'{directory}' n'est pas un répertoire")
        else:

            if not os.access(directory, os.R_OK):
                self.warnings.append(f"Le répertoire '{directory}' n'est pas lisible")
            if not os.access(directory, os.W_OK):
                self.warnings.append(f"Le répertoire '{directory}' n'est pas accessible en écriture")
            if not os.access(directory, os.X_OK):
                self.warnings.append(f"Le répertoire '{directory}' n'est pas accessible en exécution")

    def _validate_restart_config(self, restart: str, restart_sec: str, max_restarts: str) -> None:

        valid_restart_values = ['no', 'always', 'on-failure', 'on-abnormal', 'on-abort', 'on-watchdog']
        if restart not in valid_restart_values:
            self.errors.append(f"Valeur de redémarrage invalide. Valeurs autorisées : {', '.join(valid_restart_values)}")

        try:
            restart_sec_val = int(restart_sec)
            if restart_sec_val < 0:
                self.errors.append("Le délai de redémarrage ne peut pas être négatif")
            elif restart_sec_val > 300:
                self.warnings.append("Un délai de redémarrage supérieur à 5 minutes pourrait être problématique")
        except ValueError:
            self.errors.append("Le délai de redémarrage doit être un nombre entier")

        try:
            max_restarts_val = int(max_restarts)
            if max_restarts_val < 0:
                self.errors.append("Le nombre maximum de redémarrages ne peut pas être négatif")
            elif max_restarts_val == 0:
                self.warnings.append("Un nombre de redémarrages de 0 désactivera tout redémarrage automatique")
            elif max_restarts_val > 100:
                self.warnings.append("Un nombre élevé de redémarrages pourrait indiquer un problème")
        except ValueError:
            self.errors.append("Le nombre maximum de redémarrages doit être un nombre entier")

    def _validate_user(self, user: str) -> None:

        if not user:
            self.errors.append("L'utilisateur est requis")
            return

        try:
            subprocess.run(['id', user], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            self.errors.append(f"L'utilisateur '{user}' n'existe pas dans le système")

    def _command_exists_in_path(self, command: str) -> bool:

        try:
            subprocess.run(['which', command], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def analyze_service_status(self, service_name: str) -> Tuple[str, List[str]]:

        try:

            status_output = subprocess.run(
                ['systemctl', 'status', f"{service_name}.service"],
                capture_output=True,
                text=True
            )

            journal_output = subprocess.run(
                ['journalctl', '-u', f"{service_name}.service", '-n', '50', '--no-pager'],
                capture_output=True,
                text=True
            )

            status = self._parse_service_status(status_output.stdout)
            errors = self._analyze_service_logs(journal_output.stdout)
            
            return status, errors

        except subprocess.CalledProcessError as e:
            return "error", [f"Erreur lors de l'analyse du service: {str(e)}"]

    def _parse_service_status(self, status_output: str) -> str:

        if "Active: inactive" in status_output or "Active: dead" in status_output or "Stopped" in status_output:
            return "inactive"
        elif "Active: active (running)" in status_output:
            return "active"
        elif "Active: failed" in status_output:
            return "failed"
        else:
            return "unknown"

    def _analyze_service_logs(self, logs: str) -> List[str]:

        errors = []
 
        error_patterns = [
            (r"(segmentation fault)", "Erreur de segmentation détectée"),
            (r"(permission denied)", "Erreur de permission"),
            (r"(failed to start)", "Échec du démarrage du service"),
            (r"(cannot allocate memory)", "Erreur de mémoire"),
            (r"(timeout)", "Timeout détecté"),
            (r"(core dumped)", "Crash du programme détecté"),
            (r"(failed to bind to address)", "Erreur de binding d'adresse"),
            (r"(file not found)", "Fichier non trouvé"),
            (r"(configuration error)", "Erreur de configuration")
        ]

        for pattern, message in error_patterns:
            if re.search(pattern, logs, re.IGNORECASE):
                errors.append(message)

        return errors
