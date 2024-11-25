from dataclasses import dataclass
from typing import List, Optional
import json
import sys
import os

@dataclass
class UnitSection:
    """Section [Unit] - Informations générales sur le service"""
    description: str = ""  # Description simple du service
    documentation: str = ""  # Liens vers la documentation
    
    # Démarrage du service
    after: List[str] = None  # Services qui doivent démarrer AVANT ce service
    before: List[str] = None  # Services qui doivent démarrer APRÈS ce service
    requires: List[str] = None  # Services OBLIGATOIRES pour le fonctionnement
    wants: List[str] = None  # Services RECOMMANDÉS mais non obligatoires
    
    # Comportement en cas d'erreur
    on_failure: str = "none"  # Action en cas d'échec (none, reboot, restart)
    start_limit_burst: int = 5  # Nombre de redémarrages autorisés
    start_limit_interval: int = 10  # Période pour compter les redémarrages (en secondes)

@dataclass
class ServiceSection:
    """Section [Service] - Comment le service doit fonctionner"""
    # Type de service
    type: str = "simple"  # Comment systemd gère le service
    
    # Utilisateur et permissions
    user: str = ""
    group: str = ""
    
    # Commandes d'exécution
    working_directory: str = ""
    environment: dict = None
    exec_start: str = ""
    exec_stop: str = ""
    exec_reload: str = ""
    
    # Redémarrage
    restart: str = "no"
    restart_sec: int = 0
    
    # Sécurité
    nice: int = 0
    memory_limit: str = ""
    cpu_quota: int = 100
    
    # Ajout pour screen
    remain_after_exit: bool = True

@dataclass
class InstallSection:
    """Section [Install] - Quand et comment le service doit être activé"""
    wanted_by: List[str] = None  # Quand le service doit démarrer:
    # - multi-user.target: démarrage normal
    # - graphical.target: démarrage avec interface graphique
    # - network-online.target: après le réseau
    
    required_by: List[str] = None  # Services qui ont BESOIN de ce service
    also: List[str] = None  # Services à activer en même temps

class ServiceModel:
    """Modèle complet d'un service systemd"""
    def __init__(self, name: str):
        self.name = name
        self.unit = UnitSection()
        self.service = ServiceSection()
        self.install = InstallSection()
        
    def to_systemd_file(self) -> str:
        """Convertit le modèle en fichier systemd"""
        content = "[Unit]\n"
        content += f"Description={self.unit.description}\n"
        
        # Ajoute les options Unit non vides
        if self.unit.start_limit_burst:
            content += f"StartLimitBurst={self.unit.start_limit_burst}\n"
        if self.unit.start_limit_interval:
            content += f"StartLimitInterval={self.unit.start_limit_interval}\n"

        content += "\n[Service]\n"
        # Correction des options Service
        for key, value in vars(self.service).items():
            if value:
                if key == "exec_start":
                    if "screen" in value:
                        # Correction du format pour screen
                        content += f"ExecStart={value}\n"
                    else:
                        # Pour les autres commandes, utiliser le chemin absolu
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
        """Sauvegarde la configuration en JSON"""
        with open(filepath, 'w') as f:
            json.dump({
                'name': self.name,
                'unit': vars(self.unit),
                'service': vars(self.service),
                'install': vars(self.install)
            }, f, indent=4)

    @classmethod
    def load_from_json(cls, filepath: str) -> 'ServiceModel':
        """Charge la configuration depuis un JSON"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
            # Migration des anciennes configurations
            if 'service' in data and 'start_limit_interval' in data['service']:
                # Déplacer start_limit_interval vers la section unit
                if 'unit' not in data:
                    data['unit'] = {}
                data['unit']['start_limit_interval'] = data['service'].pop('start_limit_interval')
            
            if 'service' in data and 'start_limit_burst' in data['service']:
                # Déplacer start_limit_burst vers la section unit
                if 'unit' not in data:
                    data['unit'] = {}
                data['unit']['start_limit_burst'] = data['service'].pop('start_limit_burst')
            
            # Création du service
            service = cls(data['name'])
            
            # Chargement des sections avec gestion des valeurs par défaut
            if 'unit' in data:
                service.unit = UnitSection(**data['unit'])
            if 'service' in data:
                service.service = ServiceSection(**data['service'])
            if 'install' in data:
                service.install = InstallSection(**data['install'])
                
            return service

    def handle_input(self, value: str, previous_step: callable = None):
        """Gère les entrées utilisateur standard"""
        if value.lower() == 'q':
            sys.exit("Au revoir ! 👋")
        elif value.lower() == 'b' and previous_step:
            previous_step()
        return value