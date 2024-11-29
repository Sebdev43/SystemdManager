
class I18n:
    def __init__(self):
        self.current_locale = "fr"
        self.translations = {
            "fr": {
                # Barre latérale
                "📋 Services": "📋 Services",
                "➕ New Service": "➕ Nouveau Service",
                "🔄 Refresh": "🔄 Actualiser",
                "🎨 Theme": "🎨 Thème",
                "Dark mode": "Mode sombre",
                
                # Boutons principaux
                "Start": "Démarrer",
                "Stop": "Arrêter",
                "Restart": "Redémarrer",
                "Edit": "Éditer",
                "Logs": "Journaux",
                "Delete": "Supprimer",
                "Create": "Créer",
                "Cancel": "Annuler",
                "Save": "Sauvegarder",
                
                # Labels et titres
                "Name": "Nom",
                "Description": "Description",
                "Status": "Statut",
                "Services systemd": "Services systemd",
                "Creation of a new service": "Création d'un nouveau service",
                "Unit": "Unité",
                "Service": "Service",
                "Install": "Installation",
                "No description": "Aucune",
                
                # Statuts
                "active": "actif",
                "inactive": "inactif",
                "failed": "échec",
                "unknown": "inconnu",
                
                # Formulaire de création
                "Enter the name of your service (without .service)": "Entrez le nom de votre service (sans .service)",
                "Enter a description for your service": "Entrez une description pour votre service",
                "Enter the command to execute": "Entrez la commande à exécuter",
                "Enter the working directory (optional)": "Entrez le répertoire de travail (optionnel)",
                "Enter the user to run the service (optional)": "Entrez l'utilisateur pour exécuter le service (optionnel)",
                "Enter the group to run the service (optional)": "Entrez le groupe pour exécuter le service (optionnel)",
                "Basic Information": "Informations de base",
                "Service Name *": "Nom du service *",
                "Service name without .service extension\nExample: my-app": "Nom du service sans l'extension .service\nExemple : mon-service",
                "Short description of the service\nExample: System monitoring service": "Brève description du service\nExemple : Service de surveillance système",
                "Service Type": "Type de service",
                "Available service types:": "Types de service disponibles :",
                "Main process stays in foreground": "Le processus principal reste au premier plan",
                "Process detaches to background": "Le processus se détache en arrière-plan",
                "Runs once and stops": "S'exécute une fois puis s'arrête",
                "Like simple, but with notifications": "Comme simple, mais avec notifications",
                "Execution Configuration": "Configuration d'exécution",
                "User": "Utilisateur",
                "User who runs the service\nCurrent user by default, root for system services": "Utilisateur qui exécute le service\nUtilisateur actuel par défaut, root pour les services système",
                "Working Directory": "Répertoire de travail",
                "Directory where the service runs\nAbsolute path required. Example: /home/user/app": "Répertoire où s'exécute le service\nChemin absolu requis. Exemple : /home/utilisateur/app",
                "Manual Input": "Saisie manuelle",
                "Select Executable": "Sélection d'un exécutable",
                "Command to execute": "Commande à exécuter",
                "Full command with arguments": "Commande complète avec arguments",
                "Arguments": "Arguments",
                "Optional arguments": "Arguments optionnels",
                "Use screen": "Utiliser screen",
                "Restart Configuration": "Configuration du redémarrage",
                "Restart Policy": "Politique de redémarrage",
                "No restart": "Pas de redémarrage",
                "Always": "Toujours",
                "On failure": "Sur échec",
                "On failure or signal": "Sur échec ou signal",
                "Restart delay (seconds)": "Délai de redémarrage (secondes)",
                "Maximum restarts": "Nombre maximum de redémarrages",
                "Start delay (seconds)": "Délai de démarrage (secondes)",
                "Start service after saving": "Démarrer après la sauvegarde",
                "Create Service": "Créer le service",
                "Cancel": "Annuler",
                
                # Messages d'erreur et validation
                "Service name is required": "Le nom du service est requis",
                "Description is too long (maximum 256 characters)": "La description est trop longue (maximum 256 caractères)",
                "Number cannot be negative": "Le nombre ne peut pas être négatif",
                "A value of 0 will disable all restarts": "Un nombre de 0 désactivera tout redémarrage",
                "High number could indicate a problem": "Un nombre élevé pourrait indiquer un problème",
                "Must be an integer": "Doit être un nombre entier",
                "Interval cannot be negative": "L'intervalle ne peut pas être négatif",
                "Interval > 5 min could be problematic": "Un intervalle > 5 min pourrait être problématique",
                "User is required": "L'utilisateur est requis",
                "User '%s' does not exist": "L'utilisateur '%s' n'existe pas",
                "Must be an absolute path": "Doit être un chemin absolu",
                "Directory does not exist": "Le répertoire n'existe pas",
                "Not a directory": "N'est pas un répertoire",
                "Insufficient permissions": "Permissions insuffisantes",
                "Command is required": "La commande est requise",
                "Command is too long": "Commande trop longue",
                "❌ ": "❌ ",
                "⚠️ ": "⚠️ ",
                
                # Messages de notification
                "Error creating notification: ": "Erreur lors de la création de la notification : ",
                "Creating notification widget...": "Création du widget de notification...",
                "Notification created and positioned": "Notification créée et positionnée",
                "Error displaying notification: ": "Erreur lors de l'affichage de la notification : ",
                
                # Liste des services
                "Name": "Nom",
                "Description": "Description",
                "Status": "Statut",
                "Start": "Démarrer",
                "Stop": "Arrêter",
                "Restart": "Redémarrer",
                "Edit": "Éditer",
                "Logs": "Journaux",
                "Delete": "Supprimer",
                "No description": "Aucune description",
                "unknown": "inconnu",
                
                # Messages de confirmation
                "Delete service?": "Supprimer le service ?",
                "Are you sure you want to delete the service '%s'?": "Êtes-vous sûr de vouloir supprimer le service '%s' ?",
                "This action cannot be undone.": "Cette action ne peut pas être annulée.",
                
                # Messages d'erreur et de succès
                "Error starting service": "Erreur lors du démarrage du service",
                "Error stopping service": "Erreur lors de l'arrêt du service",
                "Error restarting service": "Erreur lors du redémarrage du service",
                "Error deleting service": "Erreur lors de la suppression du service",
                "Service started successfully": "Service démarré avec succès",
                "Service stopped successfully": "Service arrêté avec succès",
                "Service restarted successfully": "Service redémarré avec succès",
                "Service deleted successfully": "Service supprimé avec succès",
                
                # États des services
                "active": "actif",
                "inactive": "inactif",
                "failed": "échec",
                "unknown": "inconnu",
                
                # Messages système
                "System error": "Erreur système",
                "Permission denied": "Permission refusée",
                "Service not found": "Service introuvable",
                "Invalid service configuration": "Configuration de service invalide",
                
                # Types de notification
                "info": "information",
                "success": "succès",
                "error": "erreur",
                
                # Textes d'aide sous les champs
                "Service name without .service extension\nExample: my-app": "Nom du service sans l'extension .service\nExemple : mon-service",
                "Short description of the service\nExample: System monitoring service": "Brève description du service\nExemple : Service de surveillance système",
                "Directory where the service runs\nAbsolute path required. Example: /home/user/app": "Répertoire où s'exécute le service\nChemin absolu requis. Exemple : /home/utilisateur/app",
                "User who runs the service\nCurrent user by default, root for system services": "Utilisateur qui exécute le service\nUtilisateur actuel par défaut, root pour les services système",
                "Command to execute\nExample: /usr/bin/python3 script.py": "Commande à exécuter\nExemple : /usr/bin/python3 script.py",
                "Full command with arguments\nExample: /usr/bin/python3 script.py --config config.ini": "Commande complète avec arguments\nExemple : /usr/bin/python3 script.py --config config.ini",
                "Optional arguments\nExample: --config config.ini": "Arguments optionnels\nExemple : --config config.ini",
                "Wait time in seconds before restarting\n0 = immediate restart": "Temps d'attente en secondes avant redémarrage\n0 = redémarrage immédiat",
                "Wait time in seconds before starting after boot\n0 = immediate start": "Temps d'attente en secondes avant démarrage après boot\n0 = démarrage immédiat",
                "Maximum number of restarts allowed in 5 minutes\nDefault: 3": "Nombre maximum de redémarrages autorisés en 5 minutes\nPar défaut : 3",

                # Types de service
                "Available service types:": "Types de service disponibles :",
                "• simple: Main process stays in foreground": "• simple : Le processus principal reste au premier plan",
                "• forking: Process detaches to background": "• forking : Le processus se détache en arrière-plan",
                "• oneshot: Runs once and stops": "• oneshot : S'exécute une fois puis s'arrête",
                "• notify: Like simple, but with notifications": "• notify : Comme simple, mais avec notifications",

                # Fenêtre des logs
                "Period": "Période",
                "Lines": "Lignes",
                "Auto-update": "Mise à jour automatique",
                "Refresh": "Actualiser",
                "Close": "Fermer",
                "No logs available for this period": "Aucun log disponible pour cette période",
                "Error retrieving logs: ": "Erreur lors de la récupération des logs : ",

                # Politiques de redémarrage
                "Restart policies:": "Politiques de redémarrage :",
                "• no: No automatic restart": "• non : Pas de redémarrage automatique",
                "• always: Restarts after normal stop or error": "• toujours : Redémarre après arrêt normal ou erreur",
                "• on-failure: Restarts only on error": "• sur-erreur : Redémarre uniquement sur erreur",
                "• on-abnormal: Restarts on error or signal": "• sur-anormal : Redémarre sur erreur ou signal",
                "• on-abort: Restarts if process is aborted": "• sur-interruption : Redémarre si le processus est interrompu",

                # Messages d'aide pour les placeholders
                "Enter service name...": "Entrez le nom du service...",
                "Enter service description...": "Entrez la description du service...",
                "Enter command...": "Entrez la commande...",
                "Enter working directory...": "Entrez le répertoire de travail...",
                "Enter arguments...": "Entrez les arguments...",
                "Full command (e.g.: /usr/bin/python3 script.py)": "Commande complète (ex : /usr/bin/python3 script.py)",
                "Select working directory first": "Sélectionnez d'abord un répertoire de travail",

                # Édition de service
                "Edit service": "Édition du service",
                "Description:": "Description :",
                "Number of restarts allowed:": "Nombre de redémarrages autorisés :",
                "Interval (seconds):": "Intervalle (secondes) :",
                "User:": "Utilisateur :",
                "Working directory:": "Dossier de travail :",
                "Execution command:": "Commande d'exécution :",
                "Restart policy:": "Politique de redémarrage :",
                "No automatic restart": "Pas de redémarrage automatique",
                "Always restart": "Redémarre toujours",
                "Restart on error": "Redémarre sur erreur",
                "Restart on error or signal": "Redémarre sur erreur ou signal",
                "Restart delay (seconds):": "Délai de redémarrage (secondes) :",
                "Start with:": "Démarrer avec :",
                "Normal startup": "Démarrage normal",
                "Graphical interface": "Interface graphique",
                "After network": "Après le réseau",
                "Restart limits": "Limites de redémarrage",
                "Maximum number:": "Nombre maximum :",
                "Maximum number of restarts allowed in the interval\nDefault: 5": "Nombre maximum de redémarrages autorisés dans l'intervalle\nPar défaut : 5",
                "Interval (s):": "Intervalle (s) :",
                "Time interval in seconds for restart limit\nDefault: 10": "Intervalle de temps en secondes pour la limite de redémarrage\nPar défaut : 10",
                "Type:": "Type :",
                "Command:": "Commande :",
                "Restart:": "Redémarrage :",
                "Delay (s):": "Délai (s) :",
                "Time in seconds to wait before restart\nDefault: 1": "Temps d'attente en secondes avant redémarrage\nPar défaut : 1",
                
                # Fenêtre des logs
                "Period": "Période",
                "Lines": "Lignes",
                "Auto-update": "Mise à jour automatique",
                "No logs available for this period": "Aucun log disponible pour cette période",
                "Error retrieving logs: ": "Erreur lors de la récupération des logs : ",
                "Close": "Fermer",
                
                # Directory chooser dialog
                "Select Working Directory": "Sélection du dossier de travail",
                "Current Directory:": "Dossier actuel :",
                "Go": "Aller",
                "The specified directory does not exist.": "Le dossier spécifié n'existe pas.",
                "The specified path is not a directory.": "Le chemin spécifié n'est pas un dossier.",
                "You don't have permission to access this directory.": "Vous n'avez pas les permissions pour accéder à ce dossier.",
                "Error validating directory: ": "Erreur lors de la validation du dossier : ",
                "Select": "Sélectionner",
                "Cancel": "Annuler",
                "Error accessing directory: ": "Erreur lors de l'accès au dossier : ",

                # Sections
                "Basic Information": "Informations de base",
                "Execution Configuration": "Configuration d'exécution",
                "Advanced Options": "Options avancées",

                # Champs et labels
                "Command *": "Commande *",
                "Executable *": "Exécutable *",
                "Arguments": "Arguments",
                "Restart": "Redémarrage",
                "Restart Delay (sec)": "Délai de redémarrage (sec)",
                "Start Delay after boot (sec)": "Délai de démarrage après boot (sec)",
                "Maximum number of restarts": "Nombre maximum de redémarrages",

                # Placeholders et textes d'aide
                "Full command (e.g.: /usr/bin/python3 script.py)": "Commande complète (ex : /usr/bin/python3 script.py)",
                "Select working directory first": "Sélectionnez d'abord un répertoire de travail",
                "Optional arguments\nExample: --config config.ini": "Arguments optionnels\nExemple : --config config.ini",
                "Command to execute\nExample: /usr/bin/python3 script.py": "Commande à exécuter\nExemple : /usr/bin/python3 script.py",
                "Command to execute\nExample: /usr/bin/python3 /home/user/app/main.py": "Commande à exécuter\nExemple : /usr/bin/python3 /home/utilisateur/app/main.py",
                "Wait time in seconds before restarting\n0 = immediate restart": "Temps d'attente en secondes avant redémarrage\n0 = redémarrage immédiat",
                "Wait time in seconds before starting after boot\n0 = immediate start": "Temps d'attente en secondes avant démarrage après boot\n0 = démarrage immédiat",
                "Maximum number of restarts allowed in 5 minutes\nDefault: 3": "Nombre maximum de redémarrages autorisés en 5 minutes\nPar défaut : 3",
                "Use screen to run the service in a virtual terminal": "Utiliser screen pour exécuter le service dans un terminal virtuel",

                # Options de type de service
                "Available service types:": "Types de service disponibles :",
                "• simple": "• simple : Processus principal au premier plan",
                "• forking": "• forking : Processus se détache en arrière-plan",
                "• oneshot": "• oneshot : S'exécute une fois puis s'arrête",
                "• notify": "• notify : Comme simple, mais avec notifications",

                # Options de redémarrage
                "Restart policies:": "Politiques de redémarrage :",
                "• no": "• non : Pas de redémarrage automatique",
                "• always": "• toujours : Redémarre après arrêt normal ou erreur",
                "• on-failure": "• sur-erreur : Redémarre uniquement sur erreur",
                "• on-abnormal": "• sur-anormal : Redémarre sur erreur ou signal",
                "• on-abort": "• sur-interruption : Redémarre si le processus est interrompu",
            },
            "en": {
                # Sidebar
                "📋 Services": "📋 Services",
                "➕ New Service": "➕ New Service",
                "🔄 Refresh": "🔄 Refresh",
                "🎨 Theme": "🎨 Theme",
                "Dark mode": "Dark mode",
                
                # Main buttons
                "Start": "Start",
                "Stop": "Stop",
                "Restart": "Restart",
                "Edit": "Edit",
                "Logs": "Logs",
                "Delete": "Delete",
                "Create": "Create",
                "Cancel": "Cancel",
                "Save": "Save",
                
                # Labels and titles
                "Name": "Name",
                "Description": "Description",
                "Status": "Status",
                "Services systemd": "Systemd Services",
                "Creation of a new service": "Creation of a new service",
                "Unit": "Unit",
                "Service": "Service",
                "Install": "Install",
                "No description": "No description",
                
                # Status
                "active": "active",
                "inactive": "inactive",
                "failed": "failed",
                "unknown": "unknown",
                
                # Creation form
                "Enter the name of your service (without .service)": "Enter the name of your service (without .service)",
                "Enter a description for your service": "Enter a description for your service",
                "Enter the command to execute": "Enter the command to execute",
                "Enter the working directory (optional)": "Enter the working directory (optional)",
                "Enter the user to run the service (optional)": "Enter the user to run the service (optional)",
                "Enter the group to run the service (optional)": "Enter the group to run the service (optional)",
                "Basic Information": "Basic Information",
                "Service Name *": "Service Name *",
                "Service name without .service extension\nExample: my-app": "Service name without .service extension\nExample: my-service",
                "Short description of the service\nExample: System monitoring service": "Short description of the service\nExample: System monitoring service",
                "Service Type": "Service Type",
                "Available service types:": "Available service types:",
                "Main process stays in foreground": "Main process stays in foreground",
                "Process detaches to background": "Process detaches to background",
                "Runs once and stops": "Runs once and stops",
                "Like simple, but with notifications": "Like simple, but with notifications",
                "Execution Configuration": "Execution Configuration",
                "User": "User",
                "User who runs the service\nCurrent user by default, root for system services": "User who runs the service\nCurrent user by default, root for system services",
                "Working Directory": "Working Directory",
                "Directory where the service runs\nAbsolute path required. Example: /home/user/app": "Directory where the service runs\nAbsolute path required. Example: /home/user/app",
                "Manual Input": "Manual Input",
                "Select Executable": "Select Executable",
                "Command to execute": "Command to execute",
                "Full command with arguments": "Full command with arguments",
                "Arguments": "Arguments",
                "Optional arguments": "Optional arguments",
                "Use screen": "Use screen",
                "Restart Configuration": "Restart Configuration",
                "Restart Policy": "Restart Policy",
                "No restart": "No restart",
                "Always": "Always",
                "On failure": "On failure",
                "On failure or signal": "On failure or signal",
                "Restart delay (seconds)": "Restart delay (seconds)",
                "Maximum restarts": "Maximum restarts",
                "Start delay (seconds)": "Start delay (seconds)",
                "Start service after saving": "Start service after saving",
                "Create Service": "Create Service",
                "Cancel": "Cancel",
                # Messages d'erreur et validation
                "Service name is required": "Service name is required",
                "Description is too long (maximum 256 characters)": "Description is too long (maximum 256 characters)",
                "Number cannot be negative": "Number cannot be negative",
                "A value of 0 will disable all restarts": "A value of 0 will disable all restarts",
                "High number could indicate a problem": "High number could indicate a problem",
                "Must be an integer": "Must be an integer",
                "Interval cannot be negative": "Interval cannot be negative",
                "Interval > 5 min could be problematic": "Interval > 5 min could be problematic",
                "User is required": "User is required",
                "User '%s' does not exist": "User '%s' does not exist",
                "Must be an absolute path": "Must be an absolute path",
                "Directory does not exist": "Directory does not exist",
                "Not a directory": "Not a directory",
                "Insufficient permissions": "Insufficient permissions",
                "Command is required": "Command is required",
                "Command is too long": "Command is too long",
                "❌ ": "❌ ",
                "⚠️ ": "⚠️ ",
               
                # Service editing
                "Edit service": "Edit service",
                "Description:": "Description:",
                "Number of restarts allowed:": "Number of restarts allowed:",
                "Interval (seconds):": "Interval (seconds):",
                "User:": "User:",
                "Working directory:": "Working directory:",
                "Execution command:": "Execution command:",
                "Restart policy:": "Restart policy:",
                "No automatic restart": "No automatic restart",
                "Always restart": "Always restart",
                "Restart on error": "Restart on error",
                "Restart on error or signal": "Restart on error or signal",
                "Restart delay (seconds):": "Restart delay (seconds):",
                "Start with:": "Start with:",
                "Normal startup": "Normal startup",
                "Graphical interface": "Graphical interface",
                "After network": "After network",
                "Restart limits": "Restart limits",
                "Maximum number:": "Maximum number:",
                "Maximum number of restarts allowed in the interval\nDefault: 5": "Maximum number of restarts allowed in the interval\nDefault: 5",
                "Interval (s):": "Interval (s):",
                "Time interval in seconds for restart limit\nDefault: 10": "Time interval in seconds for restart limit\nDefault: 10",
                "Type:": "Type:",
                "Command:": "Command:",
                "Restart:": "Restart:",
                "Delay (s):": "Delay (s):",
                "Time in seconds to wait before restart\nDefault: 1": "Time in seconds to wait before restart\nDefault: 1",
                
                # Fenêtre des logs
                "Period": "Period",
                "Lines": "Lines",
                "Auto-update": "Auto-update",
                "Refresh": "Refresh",
                "Close": "Close",
                "No logs available for this period": "No logs available for this period",
                "Error retrieving logs: ": "Error retrieving logs: ",
                "Close": "Close",
                
                # Directory chooser dialog
                "Select Working Directory": "Select Working Directory",
                "Current Directory:": "Current Directory:",
                "Go": "Go",
                "The specified directory does not exist.": "The specified directory does not exist.",
                "The specified path is not a directory.": "The specified path is not a directory.",
                "You don't have permission to access this directory.": "You don't have permission to access this directory.",
                "Error validating directory: ": "Error validating directory: ",
                "Select": "Select",
                "Cancel": "Cancel",
                "Error accessing directory: ": "Error accessing directory: ",
            }
        }

    def set_locale(self, locale: str):

        if locale in self.translations:
            self.current_locale = locale

    def get_text(self, text: str) -> str:

        return self.translations[self.current_locale].get(text, text)

i18n = I18n()

def _(text: str) -> str:
    """Fonction de traduction"""
    return i18n.get_text(text)
