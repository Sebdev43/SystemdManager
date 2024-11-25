import os
import sys
import json
import signal
import questionary
from typing import Optional, List
from src.models.service_model import ServiceModel, UnitSection, ServiceSection, InstallSection
import subprocess
from datetime import datetime

class CLIController:
    def __init__(self):
        # Configuration de questionary pour ne pas intercepter Ctrl+C
        questionary.prompts.confirm.kbi_handler = lambda: None
        questionary.prompts.select.kbi_handler = lambda: None
        questionary.prompts.text.kbi_handler = lambda: None
        
        # Configuration du gestionnaire de signal au niveau de la classe
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.services_dir = os.path.expanduser("~/.config/systemd-manager/services")
        self.logs_dir = os.path.expanduser("~/.config/systemd-manager/logs")
        self.setup_directories()

    def setup_directories(self):
        """Crée les dossiers nécessaires"""
        for directory in [self.services_dir, self.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def ensure_config_dir(self):
        """Crée le dossier de configuration s'il n'existe pas"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def check_sudo(self) -> bool:
        """Vérifie si l'utilisateur a les droits sudo"""
        return os.geteuid() == 0

    def request_sudo(self, action: str):
        """Demande les droits sudo si nécessaire"""
        if not self.check_sudo():
            print(f"⚠️  Droits administrateur requis pour {action}")
            sys.exit("📌 Relancez avec sudo")

    def main_menu(self):
        """Menu principal de l'interface CLI"""
        while True:
            print("\n🚀 Gestionnaire de services systemd")
            action = questionary.select(
                "Que souhaitez-vous faire ?",
                choices=[
                    "📝 Créer un nouveau service",
                    "⚙️  Gérer les services existants",
                    "❌ Quitter"
                ]
            ).ask()

            if action == "📝 Créer un nouveau service":
                self.create_service()
            elif action == "⚙️  Gérer les services existants":
                self.manage_services()
            else:
                sys.exit("Au revoir ! 👋")

    def create_service(self):
        """Assistant de création de service"""
        try:
            print("\n📝 Création d'un nouveau service systemd")
            print("Utilisez ↩️  pour revenir en arrière à tout moment\n")
            
            # Définition des étapes du flux
            current_step = 0
            service = None
            
            # Liste des étapes dans l'ordre avec leurs descriptions
            steps = [
                (self.get_service_name, "Nom du service"),
                (self.get_service_description, "Description"),
                (self.get_service_type, "Type de service"),
                (self.get_user_config, "Configuration utilisateur"),
                (self.get_working_directory, "Dossier de travail"),
                (self.get_exec_command, "Commande d'exécution")
            ]
            
            # Barre de progression
            total_steps = len(steps)
            
            while current_step < total_steps:
                # Affichage de la progression
                print(f"\n🔄 Étape {current_step + 1}/{total_steps}: {steps[current_step][1]}")
                
                # Si on commence, on crée le service
                if current_step == 0:
                    result = steps[current_step][0]()
                    if result:
                        service = ServiceModel(result)
                        print(f"✅ Service '{result}' initialisé")
                        current_step += 1
                    else:
                        print("❌ Le nom du service est requis")
                    continue

                # Exécution de l'étape courante
                try:
                    if current_step == 5:  # Pour get_exec_command
                        result = steps[current_step][0](service)
                    else:
                        result = steps[current_step][0]()
                    
                    if result is None:  # L'utilisateur veut revenir en arrière
                        print("↩️  Retour à l'étape précédente")
                        current_step = max(0, current_step - 1)
                        continue
                    
                    # Mise à jour du modèle selon l'étape
                    if current_step == 1:  # Description
                        service.unit.description = result
                        print("✅ Description ajoutée")
                    elif current_step == 2:  # Type de service
                        service.service.type = result
                        print(f"✅ Type de service défini: {result}")
                    elif current_step == 3:  # Utilisateur
                        service.service.user = result[0]
                        print(f"✅ Utilisateur configuré: {result[0]}")
                    elif current_step == 4:  # Dossier de travail
                        service.service.working_directory = result
                        print(f"✅ Dossier de travail défini: {result}")
                    elif current_step == 5:  # Commande d'exécution
                        service.service.exec_start = result
                        print("✅ Commande d'exécution configurée")
                    
                    # Passage à l'étape suivante
                    current_step += 1
                    
                except Exception as e:
                    print(f"❌ Erreur lors de l'étape {steps[current_step][1]}: {str(e)}")
                    if not questionary.confirm("Voulez-vous réessayer ?").ask():
                        return None

            print("\n✨ Configuration de base terminée")
            # Configuration finale et sauvegarde
            return self.finalize_service(service)

        except KeyboardInterrupt:
            print("\n\n👋 Au revoir !")
            sys.exit(0)

    def finalize_service(self, service: ServiceModel):
        """Finalise la configuration du service"""
        print("\n🔧 Configuration finale du service")
        
        # Configuration du redémarrage
        restart_options = {
            "no": {
                "description": "Pas de redémarrage automatique",
                "detail": "Le service ne redémarre pas automatiquement"
            },
            "always": {
                "description": "Redémarre toujours",
                "detail": "Redémarre après un arrêt normal ou une erreur"
            },
            "on-failure": {
                "description": "Redémarre sur erreur",
                "detail": "Redémarre uniquement en cas d'erreur (code de sortie non nul)"
            },
            "on-abnormal": {
                "description": "Redémarre sur anomalie",
                "detail": "Redémarre sur erreur ou signal (crash, kill)"
            }
        }

        # Création des choix pour questionary
        restart_choices = [
            f"{key} - {value['description']}" for key, value in restart_options.items()
        ] + ["↩️  Retour", "❌ Quitter"]

        print("\n📋 Configuration du redémarrage :")
        for key, value in restart_options.items():
            print(f"  • {key}: {value['detail']}")

        choice = questionary.select(
            "Choisissez la politique de redémarrage :",
            choices=restart_choices
        ).ask()

        if choice == "❌ Quitter":
            if questionary.confirm("Voulez-vous vraiment quitter ?").ask():
                sys.exit("Au revoir ! 👋")
            return self.finalize_service(service)
        elif choice == "↩️  Retour":
            return None

        service.service.restart = choice.split(" - ")[0]

        # Configuration du délai de redémarrage
        print("\n⏱️  Configuration des délais")
        restart_sec = questionary.text(
            "Délai avant redémarrage (en secondes) :",
            instruction="Entrez un nombre de secondes (défaut: 1)",
            validate=lambda text: text.isdigit() or text == "",
            default="1"
        ).ask()
        
        if restart_sec:
            service.service.restart_sec = restart_sec

        # Configuration du délai de démarrage
        start_delay = questionary.text(
            "Délai de démarrage après le boot (en secondes) :",
            instruction="Entrez un nombre de secondes (0 pour démarrer immédiatement)",
            validate=lambda text: text.isdigit(),
            default="0"
        ).ask()

        if start_delay and int(start_delay) > 0:
            service.unit.after = ["time-sync.target"]
            service.service.exec_start_pre = f"/bin/sleep {start_delay}"

        # Configuration des limites de redémarrage
        if service.service.restart != "no":
            print("\n🔄 Configuration des limites de redémarrage")
            start_limit = questionary.text(
                "Nombre maximum de redémarrages en 5 minutes :",
                instruction="Entrez un nombre (défaut: 3)",
                validate=lambda text: text.isdigit() or text == "",
                default="3"
            ).ask()
            
            if start_limit:
                service.service.start_limit_interval = 300
                service.service.start_limit_burst = int(start_limit)

        # Important: définir WantedBy pour l'installation
        service.install.wanted_by = ["multi-user.target"]

        print("\n✅ Configuration finale terminée")

        # Installation et démarrage
        if questionary.confirm("Voulez-vous installer le service maintenant ?").ask():
            self.request_sudo("installer le service")
            success = self.install_service(service)
            
            if success and questionary.confirm("Voulez-vous démarrer le service maintenant ?").ask():
                print("\n📋 Démarrage du service...")
                start_result = subprocess.run(['systemctl', 'start', service.name], capture_output=True, text=True)
                
                if start_result.returncode == 0:
                    # Vérification du statut
                    status_result = subprocess.run(['systemctl', 'is-active', service.name], capture_output=True, text=True)
                    
                    if status_result.stdout.strip() == 'active':
                        print("\n✨ Service démarré avec succès !")
                        print("👋 Au revoir !")
                        sys.exit(0)
                    else:
                        print("\n⚠️ Le service est installé mais n'est pas actif")
                        print("📜 Consultation des logs d'erreur :")
                        os.system(f"journalctl -u {service.name} -n 50 --no-pager")
                else:
                    print("\n❌ Erreur lors du démarrage du service")
                    print("📜 Consultation des logs d'erreur :")
                    os.system(f"journalctl -u {service.name} -n 50 --no-pager")
            
    def install_service(self, service: ServiceModel):
        """Installe un service dans systemd"""
        service_path = f"/etc/systemd/system/{service.name}.service"
        
        # Écriture du fichier service
        with open(service_path, 'w') as f:
            f.write(service.to_systemd_file())
        
        # Sauvegarde de la configuration en JSON dans le dossier services_dir
        json_path = os.path.join(self.services_dir, f"{service.name}.json")
        service.save_to_json(json_path)
        
        # Rechargement et activation
        os.system("systemctl daemon-reload")
        os.system(f"systemctl enable {service.name}")
        print(f"✅ Service {service.name} installé")
        return True

    def manage_services(self):
        """Gestion des services existants"""
        while True:
            # Liste tous les fichiers JSON dans le dossier services
            services = [f for f in os.listdir(self.services_dir) if f.endswith('.json')]
            
            if not services:
                print("❌ Aucun service trouvé")
                return

            # Ajouter les options de navigation
            choices = services + ["↩️  Retour", "❌ Quitter"]
            
            service_choice = questionary.select(
                "Choisissez un service :",
                choices=choices
            ).ask()

            # Gestion du retour et de la sortie
            if service_choice == "❌ Quitter":
                if questionary.confirm("Voulez-vous vraiment quitter ?").ask():
                    sys.exit("Au revoir ! 👋")
                continue
            elif service_choice == "↩️  Retour":
                return

            # Menu des actions pour le service sélectionné
            actions = [
                "▶️  Démarrer",
                "⏹️  Arrêter",
                "🔄 Redémarrer",
                "📊 Voir le statut",
                "📜 Voir les logs",
                "✏️  Modifier",
                "🗑️  Supprimer",
                "↩️  Retour",
                "❌ Quitter"
            ]

            action = questionary.select(
                "Action :",
                choices=actions
            ).ask()

            # Gestion du retour et de la sortie dans le sous-menu
            if action == "❌ Quitter":
                if questionary.confirm("Voulez-vous vraiment quitter ?").ask():
                    sys.exit("Au revoir ! 👋")
                continue
            elif action == "↩️  Retour":
                continue

            # Récupérer le nom du service sans l'extension .json
            service_name = service_choice.replace('.json', '')

            # Exécuter l'action choisie
            if action == "▶️  Démarrer":
                self.start_service(service_name)
            elif action == "⏹️  Arrêter":
                self.stop_service(service_name)
            elif action == "🔄 Redémarrer":
                self.restart_service(service_name)
            elif action == "📊 Voir le statut":
                os.system(f"systemctl status {service_name}")
            elif action == "📜 Voir les logs":
                os.system(f"journalctl -u {service_name} -n 50 --no-pager")
            elif action == "✏️  Modifier":
                self.edit_service(service_name)
            elif action == "🗑️  Supprimer":
                self.delete_service(service_name)

    def edit_service(self, service_name: str):
        """Modifie un service existant"""
        config_path = os.path.join(self.services_dir, f"{service_name}.json")
        service = ServiceModel.load_from_json(config_path)
        
        while True:
            # Menu principal d'édition
            section = questionary.select(
                "Quelle section voulez-vous modifier ?",
                choices=[
                    "📋 Section [Unit] - Description et dépendances",
                    "⚙️  Section [Service] - Configuration du service",
                    "🔌 Section [Install] - Installation et démarrage",
                    "💾 Sauvegarder et appliquer les modifications",
                    "↩️  Retour sans sauvegarder",
                    "❌ Quitter"
                ]
            ).ask()

            if section == "❌ Quitter":
                if questionary.confirm("Voulez-vous vraiment quitter sans sauvegarder ?").ask():
                    sys.exit("Au revoir ! 👋")
                continue
            elif section == "↩️  Retour sans sauvegarder":
                return
            elif section == "💾 Sauvegarder et appliquer les modifications":
                self.save_service_changes(service)
                return

            if "Unit" in section:
                self.edit_unit_section(service)
            elif "Service" in section:
                self.edit_service_section(service)
            elif "Install" in section:
                self.edit_install_section(service)

    def edit_unit_section(self, service: ServiceModel):
        """Édite la section [Unit]"""
        while True:
            choice = questionary.select(
                "Que voulez-vous modifier ?",
                choices=[
                    "📝 Description",
                    "⏱️  Limites de redémarrage",
                    "🔄 Dépendances (after, requires, wants)",
                    "↩️  Retour"
                ]
            ).ask()

            if choice == "↩️  Retour":
                break
            elif choice == "📝 Description":
                service.unit.description = questionary.text(
                    "Nouvelle description :",
                    default=service.unit.description
                ).ask()
            elif choice == "⏱️  Limites de redémarrage":
                service.unit.start_limit_burst = int(questionary.text(
                    "Nombre de redémarrages autorisés :",
                    default=str(service.unit.start_limit_burst),
                    validate=lambda text: text.isdigit()
                ).ask())
                service.unit.start_limit_interval = int(questionary.text(
                    "Intervalle en secondes :",
                    default=str(service.unit.start_limit_interval),
                    validate=lambda text: text.isdigit()
                ).ask())

    def edit_service_section(self, service: ServiceModel):
        """Édite la section [Service]"""
        while True:
            choice = questionary.select(
                "Que voulez-vous modifier ?",
                choices=[
                    "👤 Utilisateur",
                    "📂 Dossier de travail",
                    "⚡ Commande d'exécution",
                    "🔄 Politique de redémarrage",
                    "⏱️  Délai de redémarrage",
                    "🛡️  Options de sécurité",
                    "↩️  Retour"
                ]
            ).ask()

            if choice == "↩️  Retour":
                break
            elif choice == "👤 Utilisateur":
                user = self.get_user_config()
                if user:
                    service.service.user = user[0]
            elif choice == "📂 Dossier de travail":
                dir_path = self.browse_directory(service.service.working_directory)
                if dir_path:
                    service.service.working_directory = dir_path
            elif choice == "⚡ Commande d'exécution":
                cmd = self.get_exec_command(service)
                if cmd:
                    service.service.exec_start = cmd
            elif choice == "🔄 Politique de redémarrage":
                restart_choices = [
                    "no - Pas de redémarrage automatique",
                    "always - Redémarre toujours",
                    "on-failure - Redémarre sur erreur",
                    "on-abnormal - Redémarre sur erreur ou signal"
                ]
                choice = questionary.select(
                    "Politique de redémarrage :",
                    choices=restart_choices
                ).ask()
                service.service.restart = choice.split(" - ")[0]
            elif choice == "⏱️  Délai de redémarrage":
                restart_sec = questionary.text(
                    "Délai avant redémarrage (en secondes) :",
                    validate=lambda text: text.isdigit(),
                    default=str(service.service.restart_sec)
                ).ask()
                service.service.restart_sec = int(restart_sec)

    def edit_install_section(self, service: ServiceModel):
        """Édite la section [Install]"""
        while True:
            choice = questionary.select(
                "Que voulez-vous modifier ?",
                choices=[
                    "🎯 WantedBy (quand démarrer)",
                    "↩️  Retour"
                ]
            ).ask()

            if choice == "↩️  Retour":
                break
            elif choice == "🎯 WantedBy":
                targets = [
                    "multi-user.target - Démarrage normal",
                    "graphical.target - Interface graphique",
                    "network-online.target - Après le réseau"
                ]
                choice = questionary.select(
                    "Quand démarrer le service :",
                    choices=targets
                ).ask()
                service.install.wanted_by = [choice.split(" - ")[0]]

    def save_service_changes(self, service: ServiceModel):
        """Sauvegarde et applique les modifications du service"""
        try:
            # 1. Arrêter le service
            print(f"📥 Arrêt du service {service.name}...")
            os.system(f"systemctl stop {service.name}")
            
            # 2. Sauvegarder les fichiers
            service_path = f"/etc/systemd/system/{service.name}.service"
            with open(service_path, 'w') as f:
                f.write(service.to_systemd_file())
                
            json_path = os.path.join(self.services_dir, f"{service.name}.json")
            service.save_to_json(json_path)
            
            # 3. Recharger et redémarrer
            os.system("systemctl daemon-reload")
            os.system(f"systemctl restart {service.name}")
            
            print(f"✅ Service {service.name} mis à jour et redémarré")
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde : {e}")

    def delete_service(self, service_name: str):
        """Supprime un service"""
        if questionary.confirm(f"Êtes-vous sûr de vouloir supprimer {service_name} ?").ask():
            # 1. Arrêter le service
            print(f"📥 Arrêt du service {service_name}...")
            os.system(f"systemctl stop {service_name}")
            
            # 2. Désactiver le service
            print(f"🔌 Désactivation du service {service_name}...")
            os.system(f"systemctl disable {service_name}")
            
            # 3. Supprimer le fichier service
            service_path = f"/etc/systemd/system/{service_name}.service"
            if os.path.exists(service_path):
                os.remove(service_path)
                print(f"🗑️  Fichier service supprimé : {service_path}")
            
            # 4. Supprimer le fichier JSON
            json_path = os.path.join(self.services_dir, f"{service_name}.json")
            if os.path.exists(json_path):
                os.remove(json_path)
                print(f"🗑️  Configuration supprimée : {json_path}")
            
            # 5. Recharger systemd
            os.system("systemctl daemon-reload")
            print(f"✅ Service {service_name} complètement supprimé")


    def get_system_users(self) -> List[str]:
        """Récupère la liste des utilisateurs du système"""
        users = []
        try:
            with open('/etc/passwd', 'r') as f:
                for line in f:
                    user_info = line.strip().split(':')
                    # Filtrer les utilisateurs système (UID >= 1000) et exclure nobody
                    if (len(user_info) >= 3 and 
                        user_info[2].isdigit() and 
                        int(user_info[2]) >= 1000 and 
                        user_info[0] != 'nobody'):
                        users.append(user_info[0])
            return sorted(users)
        except Exception as e:
            print(f"⚠️  Erreur lors de la lecture des utilisateurs: {e}")
            return []

    def get_user_config(self) -> Optional[tuple]:
        """Assistant pour la configuration de l'utilisateur"""
        try:
            # Liste des choix (uniquement root et l'utilisateur courant)
            current_user = os.getenv('SUDO_USER', os.getenv('USER'))
            choices = ["root", current_user]
            
            choice = self.handle_step_navigation(
                "Sélectionnez l'utilisateur qui exécutera le service :",
                sorted(set(choices))  # Supprime les doublons et trie
            )
            
            if choice is None:
                return None
            
            return choice, ""  # Retourne (user, group)
            
        except Exception as e:
            print(f"⚠️  Erreur lors de la configuration utilisateur: {e}")
            return None

    def browse_directory(self, start_path: str = "/"):
        """Assistant de navigation dans les dossiers"""
        current_path = start_path
        
        while True:
            try:
                # Ne liste que les dossiers, pas les fichiers
                items = [".."] + sorted([
                    f"📁 {d}"
                    for d in os.listdir(current_path)
                    if os.path.isdir(os.path.join(current_path, d))
                    and not d.startswith('.')  # Cache les dossiers cachés
                ])
                
                print(f"\nDossier actuel : {current_path}")
                choice = questionary.select(
                    "Sélectionnez un dossier :",
                    choices=items + [
                        "✅ Sélectionner ce dossier",
                        "↩️  Retour",
                        "❌ Quitter"
                    ]
                ).ask()
                
                if choice == "❌ Quitter":
                    sys.exit("Au revoir ! 👋")
                elif choice == "↩️  Retour":
                    return None
                elif choice == "✅ Sélectionner ce dossier":
                    return current_path
                elif choice == "..":
                    if current_path != "/":  # Empêche de remonter au-delà de la racine
                        current_path = os.path.dirname(current_path)
                else:
                    # Enlève l'emoji et navigue vers le dossier sélectionné
                    folder_name = choice[2:]
                    current_path = os.path.join(current_path, folder_name)
                    
            except PermissionError:
                print("⚠️  Accès refusé à ce dossier")
                current_path = os.path.dirname(current_path)

    def check_screen_installed(self) -> bool:
        """Vérifie si screen est installé"""
        try:
            result = subprocess.run(['which', 'screen'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception:
            return False

    def get_exec_command(self, service: ServiceModel = None):
        """Assistant pour la configuration de la commande d'exécution"""
        try:
            base_command = None
            
            # Choix de la méthode
            method = questionary.select(
                "Comment souhaitez-vous spécifier la commande ?",
                choices=[
                    "📂 Sélectionner un fichier exécutable",
                    "⌨️  Saisir la commande manuellement",
                    "↩️  Retour",
                    "❌ Quitter"
                ]
            ).ask()

            if method == "❌ Quitter":
                if questionary.confirm("Voulez-vous vraiment quitter ?").ask():
                    sys.exit("Au revoir ! 👋")
                return self.get_exec_command(service)
            elif method == "↩️  Retour":
                return None

            # Obtention de la commande selon la méthode
            if method == "📂 Sélectionner un fichier exécutable":
                working_dir = service.service.working_directory
                executables = []
                try:
                    print(f"\n🔍 Recherche des fichiers exécutables dans : {working_dir}")
                    for item in os.listdir(working_dir):
                        full_path = os.path.join(working_dir, item)
                        if os.path.isfile(full_path):
                            if os.access(full_path, os.X_OK):
                                executables.append(item)
                            elif item.endswith(('.sh', '.py', '.bash', '.js')):
                                executables.append(item)
                except Exception as e:
                    print(f"⚠️  Erreur lors de la lecture du dossier: {e}")
                    return None

                if not executables:
                    print(f"⚠️  Aucun fichier exécutable trouvé dans {working_dir}")
                    return None

                choice = questionary.select(
                    "Sélectionnez le fichier à exécuter :",
                    choices=executables + ["↩️  Retour", "❌ Quitter"]
                ).ask()

                if choice == "❌ Quitter":
                    if questionary.confirm("Voulez-vous vraiment quitter ?").ask():
                        sys.exit("Au revoir ! 👋")
                    return self.get_exec_command(service)
                elif choice == "↩️  Retour":
                    return None

                base_command = choice
                
                # Demande d'arguments pour l'exécutable
                if questionary.confirm("Voulez-vous ajouter des arguments ?").ask():
                    args = questionary.text(
                        "Arguments additionnels :",
                        instruction="Ex: --port 8080 --config config.json"
                    ).ask()
                    base_command = f"{base_command} {args}"

            else:  # Saisie manuelle
                base_command = questionary.text(
                    "📝 Commande complète :",
                    instruction="Ex: python3 script.py ou ./executable --arg"
                ).ask()

                if not base_command:
                    return self.get_exec_command(service)

            # Vérification de screen après avoir obtenu la commande
            screen_available = self.check_screen_installed()
            
            if screen_available:
                use_screen = questionary.confirm(
                    "Voulez-vous exécuter cette commande dans un screen ?",
                    default=False
                ).ask()
                
                if use_screen:
                    screen_name = f"service_{service.name}"
                    service.service.type = "forking"
                    service.service.remain_after_exit = True
                    # Correction du format de la commande screen
                    return f"/usr/bin/screen -dmS {screen_name} {os.path.join(service.service.working_directory, base_command)}"

            return base_command

        except Exception as e:
            print(f"⚠️  Erreur: {e}")
            return None

    def configure_timer(self):
        """Configuration du timer pour le service"""
        use_timer = questionary.confirm("Voulez-vous configurer un timer ?").ask()
        
        if not use_timer:
            return None
        
        timer_type = questionary.select(
            "Type de timer :",
            choices=[
                "Délai après le démarrage",
                "Intervalle régulier",
                "Heure spécifique"
            ]
        ).ask()
        
        if timer_type == "Délai après le démarrage":
            seconds = questionary.text(
                "Délai en secondes :",
                validate=lambda text: text.isdigit()
            ).ask()
            return f"OnBootSec={seconds}s"
        elif timer_type == "Intervalle régulier":
            seconds = questionary.text(
                "Intervalle en secondes :",
                validate=lambda text: text.isdigit()
            ).ask()
            return f"OnUnitActiveSec={seconds}s"
        else:
            time = questionary.text(
                "Heure (format HH:MM) :",
                validate=lambda text: len(text.split(':')) == 2
            ).ask()
            return f"OnCalendar=*-*-* {time}:00"

    def save_service_config(self, service: ServiceModel):
        """Sauvegarde la configuration du service"""
        config_path = os.path.join(self.services_dir, f"{service.name}.json")
        service.save_to_json(config_path)
        
        # Log de l'action
        log_path = os.path.join(self.logs_dir, f"{service.name}.log")
        with open(log_path, 'a') as f:
            f.write(f"{datetime.now()}: Service configuration saved\n")
    
    def get_service_status(self, service_name: str) -> dict:
        """Récupère le statut complet d'un service"""
        status = {
            'active': subprocess.getoutput(f"systemctl is-active {service_name}"),
            'enabled': subprocess.getoutput(f"systemctl is-enabled {service_name}"),
            'status': subprocess.getoutput(f"systemctl status {service_name}"),
            'config': os.path.join(self.services_dir, f"{service_name}.json"),
            'log': os.path.join(self.logs_dir, f"{service_name}.log")
        }
        return status

    def signal_handler(self, sig, frame):
        """Gestionnaire unifié pour Ctrl+C"""
        print("\n\n👋 Au revoir !")
        sys.exit(0)

    def handle_navigation_choice(self, choice: str, return_callback=None):
        """Gestion générique des choix de navigation"""
        if choice == "❌ Quitter":
            if questionary.confirm("Êtes-vous sûr de vouloir quitter ?").ask():
                sys.exit("Au revoir ! 👋")
            return False
        elif choice == "↩️  Retour" and return_callback:
            return_callback()
            return False
        return True

    def validate_service_name(self, name: str) -> bool:
        """Valide le nom du service"""
        if not name:
            return False
        # Vérifie que le nom ne contient que des caractères valides
        return all(c.isalnum() or c in '-_' for c in name)

    def get_service_name(self):
        """Assistant pour obtenir le nom du service"""
        while True:
            print("\n📝 Création d'un nouveau service")
            name = questionary.text(
                "Nom du service",
                instruction="Entrez un nom (lettres, chiffres, - et _ uniquement)\n'b' pour retour, 'q' pour quitter"
            ).ask()
            
            if not name:
                continue
            elif name.lower() == 'q':
                if questionary.confirm("Voulez-vous vraiment quitter ?").ask():
                    sys.exit("Au revoir ! 👋")
            elif name.lower() == 'b':
                return None
            elif self.validate_service_name(name):
                return name
            else:
                print("❌ Nom invalide. Utilisez uniquement des lettres, chiffres, - et _")

    def get_service_description(self):
        """Assistant pour obtenir la description du service"""
        print("\n📝 Description du service")
        description = questionary.text(
            "Description",
            instruction="Décrivez brièvement le service\n'b' pour retour, 'q' pour quitter"
        ).ask()
        
        if description.lower() == 'q':
            if questionary.confirm("Voulez-vous vraiment quitter ?").ask():
                sys.exit("Au revoir ! ")
            return self.get_service_description()
        elif description.lower() == 'b':
            return None
        return description

    def handle_step_navigation(self, question_text: str, choices: list) -> Optional[str]:
        """Méthode générique pour gérer la navigation dans les étapes"""
        nav_choices = choices + [
            "↩️  'b' pour retour",
            "❌ 'q' pour quitter"
        ]
        
        choice = questionary.select(
            question_text,
            choices=nav_choices
        ).ask()
        
        if choice == "❌ 'q' pour quitter":
            if questionary.confirm("Voulez-vous vraiment quitter ?").ask():
                sys.exit("Au revoir ! 👋")
            return self.handle_step_navigation(question_text, choices)
        
        elif choice == "↩️  'b' pour retour":
            return None
        
        return choice

    def get_service_type(self) -> Optional[str]:
        """Assistant pour la sélection du type de service"""
        print("\n🔧 Configuration du type de service")
        service_types = [
            "📦 simple - Le processus reste au premier plan",
            "🔄 forking - Le processus se détache en arrière-plan (recommandé si vous utilisez screen)",
            "⚡ oneshot - S'exécute une fois et s'arrête",
            "🔔 notify - Comme simple mais notifie quand il est prêt"
        ]
        
        choice = questionary.select(
            "Type de service",
            choices=service_types + ["↩️  Retour", "❌ Quitter"]
        ).ask()
        
        if choice == "❌ Quitter":
            if questionary.confirm("Voulez-vous vraiment quitter ?").ask():
                sys.exit("Au revoir ! 👋")
            return self.get_service_type()
        elif choice == "↩️  Retour":
            return None
        
        return choice.split(" - ")[0].split(" ")[1]

    def get_working_directory(self):
        """Assistant pour la sélection du dossier de travail"""
        while True:
            choices = [
                "📂 Parcourir les dossiers",
                "📝 Saisir le chemin manuellement",
                "🔙 Retour",
                "❌ Quitter"
            ]
            
            choice = questionary.select(
                "Comment souhaitez-vous définir le dossier de travail ?",
                choices=choices
            ).ask()
            
            if choice == "📂 Parcourir les dossiers":
                directory = self.browse_directory()
                if directory:
                    return directory
            
            elif choice == "📝 Saisir le chemin manuellement":
                directory = questionary.text(
                    "Entrez le chemin complet du dossier de travail :"
                ).ask()
                
                if not directory:
                    continue
                
                # Convertir le chemin en absolu
                directory = os.path.expanduser(directory)
                directory = os.path.abspath(directory)
                
                if not os.path.exists(directory):
                    print(f"⚠️  Le dossier {directory} n'existe pas")
                    continue
                
                if not os.path.isdir(directory):
                    print(f"⚠️  {directory} n'est pas un dossier")
                    continue
                
                return directory
            
            elif choice == "🔙 Retour":
                return None
            
            else:
                sys.exit("Au revoir ! 👋")

    def stop_service(self, service_name: str):
        """Arrête un service"""
        try:
            # Vérifier si le service est actif
            status = os.system(f"systemctl is-active --quiet {service_name}")
            
            if status != 0:
                print(f"⚠️  Le service {service_name} n'est pas actif")
                return
            
            print(f"📥 Arrêt du service {service_name}...")
            
            # Arrêter le service
            if os.system(f"systemctl stop {service_name}") == 0:
                print(f"✅ Service {service_name} arrêté avec succès")
                
                # Afficher le statut après l'arrêt
                print("\n📊 Statut actuel du service :")
                os.system(f"systemctl status {service_name}")
            else:
                print(f"❌ Erreur lors de l'arrêt du service {service_name}")
                
                # Afficher les logs en cas d'erreur
                print("\n📜 Derniers logs du service :")
                os.system(f"journalctl -u {service_name} -n 20 --no-pager")
            
        except Exception as e:
            print(f"❌ Erreur inattendue : {e}")

    def start_service(self, service_name: str):
        """Démarre un service"""
        try:
            # Vérifier si le service n'est pas déjà actif
            status = os.system(f"systemctl is-active --quiet {service_name}")
            
            if status == 0:
                print(f"⚠️  Le service {service_name} est déjà actif")
                return
            
            print(f"🚀 Démarrage du service {service_name}...")
            
            # Démarrer le service
            if os.system(f"systemctl start {service_name}") == 0:
                print(f"✅ Service {service_name} démarré avec succès")
                
                # Afficher le statut après le démarrage
                print("\n📊 Statut actuel du service :")
                os.system(f"systemctl status {service_name}")
                
                # Afficher les logs de démarrage
                print("\n📜 Logs de démarrage :")
                os.system(f"journalctl -u {service_name} -n 20 --no-pager")
            else:
                print(f"❌ Erreur lors du démarrage du service {service_name}")
                
                # Afficher les logs en cas d'erreur
                print("\n📜 Logs d'erreur :")
                os.system(f"journalctl -u {service_name} -n 50 --no-pager")
            
        except Exception as e:
            print(f"❌ Erreur inattendue : {e}")

    def restart_service(self, service_name: str):
        """Redémarre un service"""
        try:
            print(f"🔄 Redémarrage du service {service_name}...")
            
            # Redémarrer le service
            if os.system(f"systemctl restart {service_name}") == 0:
                print(f"✅ Service {service_name} redémarré avec succès")
                
                # Afficher le statut après le redémarrage
                print("\n📊 Statut actuel du service :")
                os.system(f"systemctl status {service_name}")
                
                # Afficher les logs de démarrage
                print("\n📜 Logs de redémarrage :")
                os.system(f"journalctl -u {service_name} -n 20 --no-pager")
            else:
                print(f"❌ Erreur lors du redémarrage du service {service_name}")
                
                # Afficher plus de logs en cas d'erreur
                print("\n📜 Logs d'erreur détaillés :")
                os.system(f"journalctl -u {service_name} -n 50 --no-pager")
                
                # Vérifier l'état du service
                print("\n🔍 État détaillé du service :")
                os.system(f"systemctl status {service_name} --no-pager")
                
        except Exception as e:
            print(f"❌ Erreur inattendue : {e}")