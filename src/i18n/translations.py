"""
Module de gestion des traductions pour SystemdManager
"""

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
                "Service name without .service extension\nExample: my-app": "Le nom du service sans l'extension .service\nExemple: mon-app",
                "Short description of the service\nExample: System monitoring service": "Description courte du service\nExemple: Service de monitoring système",
                "Service Type": "Type de service",
                "Available service types:": "Types de service disponibles :",
                "Main process stays in foreground": "Process principal reste au premier plan",
                "Process detaches to background": "Process se détache en arrière-plan",
                "Runs once and stops": "S'exécute une fois et s'arrête",
                "Like simple, but with notifications": "Comme simple, mais avec notifications",
                "Execution Configuration": "Configuration d'exécution",
                "User": "Utilisateur",
                "User who runs the service\nCurrent user by default, root for system services": "Utilisateur qui exécute le service\nUtilisateur actuel par défaut, root pour les services système",
                "Working Directory": "Dossier de travail",
                "Directory where the service runs\nAbsolute path required. Example: /home/user/app": "Dossier où le service s'exécute\nChemin absolu requis. Exemple: /home/user/app",
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
                "Working directory must be an absolute path": "Le dossier de travail doit être un chemin absolu",
                "Working directory does not exist": "Le dossier de travail n'existe pas",
                "Command to execute is required": "La commande à exécuter est requise",
                
                # Édition de service
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
                "Service name without .service extension\nExample: my-app": "Service name without .service extension\nExample: my-app",
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
                "Working directory must be an absolute path": "Working directory must be an absolute path",
                "Working directory does not exist": "Working directory does not exist",
                "Command to execute is required": "Command to execute is required",
                
                # Service editing
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
        """Change la langue courante"""
        if locale in self.translations:
            self.current_locale = locale

    def get_text(self, text: str) -> str:
        """Traduit un texte dans la langue courante"""
        return self.translations[self.current_locale].get(text, text)

# Instance globale pour l'internationalisation
i18n = I18n()

# Fonction helper pour la traduction
def _(text: str) -> str:
    """Fonction de traduction"""
    return i18n.get_text(text)
