import os
import json
import subprocess
from typing import List, Optional
from src.models.service_model import ServiceModel
import customtkinter  # Ajouter cet import en haut du fichier

class GUIController:
    def __init__(self):
        """Initialise le contrôleur GUI"""
        self.services_dir = os.path.expanduser("~/.config/systemd-manager/services")
        self.setup_directories()
        self.current_theme = "dark"  # Initialisation du thème par défaut
        
    def setup_directories(self):
        """Crée les dossiers nécessaires s'ils n'existent pas"""
        if not os.path.exists(self.services_dir):
            os.makedirs(self.services_dir)

    def get_services(self) -> List[ServiceModel]:
        """Récupère la liste des services depuis notre configuration"""
        services = []
        
        try:
            # Parcourir les fichiers JSON dans le dossier services
            for filename in os.listdir(self.services_dir):
                if filename.endswith('.json'):
                    service_path = os.path.join(self.services_dir, filename)
                    try:
                        # Charger le fichier JSON
                        with open(service_path, 'r') as f:
                            service_data = json.load(f)
                            
                        # Créer le modèle de service
                        service_name = os.path.splitext(filename)[0]
                        service = ServiceModel(service_name)
                        
                        # Charger les données du JSON dans le modèle
                        if isinstance(service_data, dict):
                            # Charger les sections si elles existent
                            if 'Unit' in service_data:
                                service.unit.__dict__.update(service_data['Unit'])
                            if 'Service' in service_data:
                                service.service.__dict__.update(service_data['Service'])
                            if 'Install' in service_data:
                                service.install.__dict__.update(service_data['Install'])
                        
                        # Récupérer le statut actuel du service
                        status = self.get_service_status(service_name)
                        service.status = status
                        
                        services.append(service)
                    except Exception as e:
                        print(f"Erreur lors du chargement du service {filename}: {e}")
            
            return services
        except Exception as e:
            print(f"Erreur lors de la lecture du dossier services : {e}")
            return []

    def get_service_status(self, service_name: str) -> dict:
        """Récupère le statut d'un service"""
        try:
            result = subprocess.run(
                ["systemctl", "show", f"{service_name}.service", "--property=ActiveState,SubState,LoadState"],
                capture_output=True,
                text=True,
                check=True
            )
            
            status = {}
            for line in result.stdout.splitlines():
                if '=' in line:
                    key, value = line.split('=', 1)
                    status[key.lower()] = value
            
            return {
                "active": status.get('activestate', 'unknown'),
                "sub": status.get('substate', 'unknown'),
                "load": status.get('loadstate', 'unknown')
            }
        except subprocess.CalledProcessError:
            return {
                "active": "unknown",
                "sub": "unknown",
                "load": "unknown"
            }

    def start_service(self, service_name: str) -> bool:
        """Démarre un service"""
        try:
            subprocess.run(
                ["systemctl", "start", f"{service_name}.service"],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def stop_service(self, service_name: str) -> bool:
        """Arrête un service"""
        try:
            subprocess.run(
                ["systemctl", "stop", f"{service_name}.service"],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def restart_service(self, service_name: str) -> bool:
        """Redémarre un service"""
        try:
            subprocess.run(
                ["systemctl", "restart", f"{service_name}.service"],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def check_sudo(self) -> bool:
        """Vérifie si l'utilisateur a les droits sudo"""
        return subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True
        ).returncode == 0

    def save_service(self, service: ServiceModel) -> bool:
        """Sauvegarde un service"""
        try:
            # Créer le fichier de configuration du service
            service_path = os.path.join(self.services_dir, f"{service.name}.json")
            
            # Préparer les données à sauvegarder
            service_data = {
                'Unit': service.unit.__dict__,
                'Service': service.service.__dict__,
                'Install': service.install.__dict__
            }
            
            # Sauvegarder dans notre dossier de configuration
            with open(service_path, 'w') as f:
                json.dump(service_data, f, indent=4)
            
            # Créer le fichier systemd
            systemd_path = f"/etc/systemd/system/{service.name}.service"
            systemd_content = []
            
            # Section Unit
            systemd_content.append("[Unit]")
            if service.unit.description:
                systemd_content.append(f"Description={service.unit.description}")
            if hasattr(service.unit, 'start_limit_burst') and service.unit.start_limit_burst:
                systemd_content.append(f"StartLimitBurst={service.unit.start_limit_burst}")
            
            # Section Service
            systemd_content.append("\n[Service]")
            if service.service.type:
                systemd_content.append(f"Type={service.service.type}")
            if service.service.user:
                systemd_content.append(f"User={service.service.user}")
            if service.service.working_directory:
                systemd_content.append(f"WorkingDirectory={service.service.working_directory}")
            if service.service.exec_start:
                systemd_content.append(f"ExecStart={service.service.exec_start}")
            if service.service.restart:
                systemd_content.append(f"Restart={service.service.restart}")
            if service.service.restart_sec:
                systemd_content.append(f"RestartSec={service.service.restart_sec}")
            if hasattr(service.service, 'start_limit_burst') and service.service.start_limit_burst:
                systemd_content.append(f"StartLimitBurst={service.service.start_limit_burst}")
            if service.service.start_sec:
                systemd_content.append(f"TimeoutStartSec={service.service.start_sec}")
            if service.service.remain_after_exit:
                systemd_content.append("RemainAfterExit=yes")
            
            # Section Install
            systemd_content.append("\n[Install]")
            if service.install.wanted_by:
                systemd_content.append(f"WantedBy={','.join(service.install.wanted_by)}")
            
            # Écrire le fichier systemd avec sudo
            with open("/tmp/service.tmp", 'w') as f:
                f.write("\n".join(systemd_content))
            
            subprocess.run(["sudo", "mv", "/tmp/service.tmp", systemd_path], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du service : {e}")
            return False

    def call_refresh_if_exists(self, widget):
        """Appelle la méthode refresh() sur un widget si elle existe
        
        Args:
            widget: Le widget à rafraîchir
            
        Returns:
            bool: True si le refresh a été effectué, False sinon
        """
        try:
            # Vérifie si le widget existe toujours dans l'interface
            if not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
                return False
            
            # Vérifie si la méthode refresh existe
            if not hasattr(widget, 'refresh'):
                return False
            
            # Vérifie si refresh est bien une méthode callable
            if not callable(widget.refresh):
                return False
            
            # Appelle la méthode refresh
            widget.refresh()
            return True
            
        except Exception as e:
            print(f"Erreur lors du refresh du widget : {e}")
            return False

    def toggle_theme(self):
        """Bascule entre le mode clair et sombre"""
        if self.current_theme == "dark":
            customtkinter.set_appearance_mode("light")
            self.current_theme = "light"
        else:
            customtkinter.set_appearance_mode("dark")
            self.current_theme = "dark"
        return self.current_theme
