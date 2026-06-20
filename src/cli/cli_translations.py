"""
Module de traductions pour l'interface CLI dans SystemdManager
"""

import json
import os


# Clés de traduction
class TranslationKeys:
    # Messages de base
    WELCOME = "WELCOME"
    MAIN_MENU = "MAIN_MENU"
    CREATE_SERVICE = "CREATE_SERVICE"
    EDIT_SERVICE = "EDIT_SERVICE"
    DELETE_SERVICE = "DELETE_SERVICE"
    VIEW_SERVICE = "VIEW_SERVICE"
    EXIT = "EXIT"
    SELECT_ACTION = "SELECT_ACTION"
    GOODBYE = "GOODBYE"
    CREATE_NEW_SERVICE_SYSTEMD = "CREATE_NEW_SERVICE_SYSTEMD"
    EXEC_COMMAND_CONFIGURED = "EXEC_COMMAND_CONFIGURED"
    START_DELAY = "START_DELAY"
    START_DELAY_SET = "START_DELAY_SET"
    MAX_RESTARTS = "MAX_RESTARTS"
    CONFIGURE_FINAL_SERVICE = "CONFIGURE_FINAL_SERVICE"
    MAX_RESTARTS_SET = "MAX_RESTARTS_SET"

    # Messages d'erreur et d'administration
    ADMIN_RIGHTS_REQUIRED = "ADMIN_RIGHTS_REQUIRED"
    RELAUNCH_WITH_SUDO = "RELAUNCH_WITH_SUDO"
    INSTALLATION_ERROR = "INSTALLATION_ERROR"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
    ERROR_READING_USERS = "ERROR_READING_USERS"
    ERROR_USER_CONFIGURATION = "ERROR_USER_CONFIGURATION"
    ERROR_DURING_STEP = "ERROR_DURING_STEP"
    ERROR_SAVING = "ERROR_SAVING"
    ERROR_STARTING_SERVICE = "ERROR_STARTING_SERVICE"
    ERROR_STOPPING_SERVICE = "ERROR_STOPPING_SERVICE"
    ERROR_RESTARTING_SERVICE = "ERROR_RESTARTING_SERVICE"
    SERVICE_FILE_CREATED = "SERVICE_FILE_CREATED"
    SYSTEMD_RELOADED = "SYSTEMD_RELOADED"
    SERVICE_ENABLED_ON_BOOT = "SERVICE_ENABLED_ON_BOOT"
    WANT_TO_START_SERVICE_NOW = "WANT_TO_START_SERVICE_NOW"
    SERVICE_RUNNING = "SERVICE_RUNNING"
    SERVICE_INSTALLED_BUT_NOT_ACTIVE = "SERVICE_INSTALLED_BUT_NOT_ACTIVE"
    INSTALL_SERVICE_ACTION = "INSTALL_SERVICE_ACTION"

    # Messages de validation
    SERVICE_NAME_VALIDATION = "SERVICE_NAME_VALIDATION"
    SERVICE_NAME_MIN_LENGTH = "SERVICE_NAME_MIN_LENGTH"
    SERVICE_NAME_NO_NUMBER_START = "SERVICE_NAME_NO_NUMBER_START"
    SERVICE_ALREADY_EXISTS = "SERVICE_ALREADY_EXISTS"

    # Interface principale
    MAIN_TITLE = "MAIN_TITLE"
    WHAT_DO_YOU_WANT_TO_DO = "WHAT_DO_YOU_WANT_TO_DO"
    CREATE_NEW_SERVICE = "CREATE_NEW_SERVICE"
    MANAGE_EXISTING_SERVICES = "MANAGE_EXISTING_SERVICES"
    LANGUAGE = "LANGUAGE"
    QUIT = "QUIT"
    CHOOSE_LANGUAGE = "CHOOSE_LANGUAGE"
    FRENCH = "FRENCH"
    ENGLISH = "ENGLISH"

    # Configuration du service
    SERVICE_NAME = "SERVICE_NAME"
    DESCRIPTION = "DESCRIPTION"
    SERVICE_TYPE = "SERVICE_TYPE"
    USER_CONFIGURATION = "USER_CONFIGURATION"
    WORKING_DIRECTORY = "WORKING_DIRECTORY"
    EXECUTION_COMMAND = "EXECUTION_COMMAND"
    CONFIGURE_SERVICE_TYPE = "CONFIGURE_SERVICE_TYPE"
    SIMPLE_TYPE = "SIMPLE_TYPE"
    FORKING_TYPE = "FORKING_TYPE"
    ONESHOT_TYPE = "ONESHOT_TYPE"
    NOTIFY_TYPE = "NOTIFY_TYPE"

    # Messages de progression
    PROGRESS_STEP = "PROGRESS_STEP"
    USE_BACK_TO_GO_BACK = "USE_BACK_TO_GO_BACK"
    BACK_TO_PREVIOUS_STEP = "BACK_TO_PREVIOUS_STEP"
    MSG_NO_SERVICES = "MSG_NO_SERVICES"
    MSG_CHOOSE_SERVICE = "MSG_CHOOSE_SERVICE"
    MSG_CHOOSE_ACTION = "MSG_CHOOSE_ACTION"
    BACK = "BACK"

    # Actions sur les services
    START_SERVICE = "START_SERVICE"
    STOP_SERVICE = "STOP_SERVICE"
    RESTART_SERVICE = "RESTART_SERVICE"
    VIEW_STATUS = "VIEW_STATUS"
    VIEW_LOGS = "VIEW_LOGS"
    EDIT_SERVICE_ACTION = "EDIT_SERVICE_ACTION"
    DELETE_SERVICE_ACTION = "DELETE_SERVICE_ACTION"

    # Messages de succès
    SERVICE_INITIALIZED = "SERVICE_INITIALIZED"
    DESCRIPTION_ADDED = "DESCRIPTION_ADDED"
    SERVICE_TYPE_SET = "SERVICE_TYPE_SET"
    USER_CONFIGURED = "USER_CONFIGURED"
    WORKING_DIRECTORY_SET = "WORKING_DIRECTORY_SET"
    FINAL_CONFIGURATION_COMPLETED = "FINAL_CONFIGURATION_COMPLETED"
    SERVICE_UPDATED_AND_RESTARTED = "SERVICE_UPDATED_AND_RESTARTED"
    SERVICE_DELETED = "SERVICE_DELETED"
    SERVICE_STARTED_SUCCESSFULLY = "SERVICE_STARTED_SUCCESSFULLY"
    SERVICE_STOPPED_SUCCESSFULLY = "SERVICE_STOPPED_SUCCESSFULLY"
    SERVICE_RESTARTED_SUCCESSFULLY = "SERVICE_RESTARTED_SUCCESSFULLY"
    SERVICE_NAME_REQUIRED = "SERVICE_NAME_REQUIRED"

    # Instructions et messages pour le nom du service
    ENTER_SERVICE_NAME_INSTRUCTION = "ENTER_SERVICE_NAME_INSTRUCTION"
    ENTER_SERVICE_DESCRIPTION_INSTRUCTION = "ENTER_SERVICE_DESCRIPTION_INSTRUCTION"
    CONFIRM_QUIT = "CONFIRM_QUIT"
    INVALID_NAME = "INVALID_NAME"
    SELECT_USER_TO_RUN_SERVICE = "SELECT_USER_TO_RUN_SERVICE"

    # Messages pour le dossier de travail
    BROWSE_DIRECTORIES = "BROWSE_DIRECTORIES"
    ENTER_PATH_MANUALLY = "ENTER_PATH_MANUALLY"
    DEFINE_WORKING_DIRECTORY = "DEFINE_WORKING_DIRECTORY"
    ENTER_FULL_DIRECTORY_PATH = "ENTER_FULL_DIRECTORY_PATH"
    DIRECTORY_DOES_NOT_EXIST = "DIRECTORY_DOES_NOT_EXIST"
    NOT_A_DIRECTORY = "NOT_A_DIRECTORY"

    # Messages pour la navigation des dossiers
    CURRENT_DIRECTORY = "CURRENT_DIRECTORY"
    SELECT_DIRECTORY = "SELECT_DIRECTORY"
    SELECT_THIS_DIRECTORY = "SELECT_THIS_DIRECTORY"

    # Messages pour la commande d'exécution
    SPECIFY_COMMAND_METHOD = "SPECIFY_COMMAND_METHOD"
    SELECT_EXECUTABLE_FILE = "SELECT_EXECUTABLE_FILE"
    ENTER_COMMAND_MANUALLY = "ENTER_COMMAND_MANUALLY"
    SEARCH_EXECUTABLE_FILES = "SEARCH_EXECUTABLE_FILES"
    ERROR_READING_DIRECTORY = "ERROR_READING_DIRECTORY"
    NO_EXECUTABLE_FILES_FOUND = "NO_EXECUTABLE_FILES_FOUND"
    ENTER_EXECUTION_COMMAND = "ENTER_EXECUTION_COMMAND"
    EXAMPLE_COMMAND = "EXAMPLE_COMMAND"
    RUN_SERVICE_IN_SCREEN = "RUN_SERVICE_IN_SCREEN"

    # Autres messages
    QUIT_WITHOUT_SAVING = "QUIT_WITHOUT_SAVING"
    WANT_TO_RETRY = "WANT_TO_RETRY"
    SAVE_CONFIGURATION = "SAVE_CONFIGURATION"
    CONFIGURATION_SAVED = "CONFIGURATION_SAVED"
    WANT_TO_INSTALL_SERVICE_NOW = "WANT_TO_INSTALL_SERVICE_NOW"
    SERVICE_INSTALLED_SUCCESSFULLY = "SERVICE_INSTALLED_SUCCESSFULLY"
    SERVICE_ALREADY_ACTIVE = "SERVICE_ALREADY_ACTIVE"
    SERVICE_NOT_ACTIVE = "SERVICE_NOT_ACTIVE"
    CHECKING_LOGS = "CHECKING_LOGS"
    LAST_SERVICE_LOGS = "LAST_SERVICE_LOGS"
    INVALID_INPUT_FOR_START_DELAY = "INVALID_INPUT_FOR_START_DELAY"
    INVALID_INPUT_FOR_MAX_RESTARTS = "INVALID_INPUT_FOR_MAX_RESTARTS"
    WANT_TO_QUIT = "WANT_TO_QUIT"
    YES = "YES"
    NO = "NO"
    ARE_YOU_SURE_YOU_WANT_TO_DELETE = "ARE_YOU_SURE_YOU_WANT_TO_DELETE"
    SERVICE_STOPPED = "SERVICE_STOPPED"
    SERVICE_DISABLED = "SERVICE_DISABLED"
    SERVICE_FILE_DELETED = "SERVICE_FILE_DELETED"
    CONFIGURATION_DELETED = "CONFIGURATION_DELETED"
    SERVICE_FULLY_DELETED = "SERVICE_FULLY_DELETED"

    # Édition des sections
    WHICH_SECTION_TO_EDIT = "WHICH_SECTION_TO_EDIT"
    SECTION_UNIT = "SECTION_UNIT"
    SECTION_SERVICE = "SECTION_SERVICE"
    SECTION_INSTALL = "SECTION_INSTALL"
    SAVE_AND_APPLY_CHANGES = "SAVE_AND_APPLY_CHANGES"

    # Modifications des sections
    WHAT_DO_YOU_WANT_TO_MODIFY = "WHAT_DO_YOU_WANT_TO_MODIFY"
    DOCUMENTATION = "DOCUMENTATION"
    START_LIMIT_INTERVAL = "START_LIMIT_INTERVAL"
    START_LIMIT_BURST = "START_LIMIT_BURST"
    USER = "USER"
    GROUP = "GROUP"
    EXEC_START = "EXEC_START"
    EXEC_STOP = "EXEC_STOP"
    RESTART_POLICY = "RESTART_POLICY"
    RESTART_SEC = "RESTART_SEC"
    MAX_RESTARTS_ALLOWED = "MAX_RESTARTS_ALLOWED"

    # Politique de redémarrage
    CHOOSE_RESTART_POLICY = "CHOOSE_RESTART_POLICY"

    # Entrées invalides
    INVALID_INPUT = "INVALID_INPUT"

    # Autres
    RETRY = "RETRY"
    RETOUR = "RETOUR"
    EXITING = "EXITING"

    # Instructions pour quitter ou revenir
    ENTER_B_TO_GO_BACK = "ENTER_B_TO_GO_BACK"
    ENTER_Q_TO_QUIT = "ENTER_Q_TO_QUIT"
    BACK = "BACK"
    QUIT = "QUIT"

    # Messages pour le timer (si nécessaire)
    CONFIGURE_TIMER = "CONFIGURE_TIMER"
    TIMER_TYPE = "TIMER_TYPE"
    DELAY_AFTER_BOOT = "DELAY_AFTER_BOOT"
    REGULAR_INTERVAL = "REGULAR_INTERVAL"
    SPECIFIC_TIME = "SPECIFIC_TIME"
    DELAY_IN_SECONDS = "DELAY_IN_SECONDS"
    INTERVAL_IN_SECONDS = "INTERVAL_IN_SECONDS"
    TIME_IN_HH_MM = "TIME_IN_HH_MM"
    INVALID_TIME_FORMAT = "INVALID_TIME_FORMAT"
    ON_BOOT_SEC = "ON_BOOT_SEC"
    ON_UNIT_ACTIVE_SEC = "ON_UNIT_ACTIVE_SEC"
    ON_CALENDAR = "ON_CALENDAR"

    # Confirmation
    CONFIRMATION = "CONFIRMATION"
    ARE_YOU_SURE = "ARE_YOU_SURE"

    # Clés pour les options de redémarrage
    RESTART_NO_KEY = "RESTART_NO_KEY"
    RESTART_ALWAYS_KEY = "RESTART_ALWAYS_KEY"
    RESTART_ON_FAILURE_KEY = "RESTART_ON_FAILURE_KEY"
    RESTART_ON_ABNORMAL_KEY = "RESTART_ON_ABNORMAL_KEY"

    # Messages supplémentaires
    RESTART_LIMIT_CONFIGURATION = "RESTART_LIMIT_CONFIGURATION"
    MAX_RESTARTS_IN_INTERVAL = "MAX_RESTARTS_IN_INTERVAL"
    ENTER_NUMBER_DEFAULT = "ENTER_NUMBER_DEFAULT"
    RESTART_DELAY_BETWEEN_ATTEMPTS = "RESTART_DELAY_BETWEEN_ATTEMPTS"
    ENTER_SECONDS_DEFAULT = "ENTER_SECONDS_DEFAULT"

    # Nouvelles clés manquantes
    SERVICE_INSTALLED_BUT_NOT_ACTIVE = "SERVICE_INSTALLED_BUT_NOT_ACTIVE"
    INSTALL_SERVICE_ACTION = "INSTALL_SERVICE_ACTION"
    SERVICE_FILE_CREATED = "SERVICE_FILE_CREATED"
    SYSTEMD_RELOADED = "SYSTEMD_RELOADED"
    SERVICE_ENABLED_ON_BOOT = "SERVICE_ENABLED_ON_BOOT"
    WANT_TO_START_SERVICE_NOW = "WANT_TO_START_SERVICE_NOW"
    SERVICE_RUNNING = "SERVICE_RUNNING"
    SERVICE_NAME_REQUIRED = "SERVICE_NAME_REQUIRED"
    SERVICE_WORKING_DIRECTORY = "SERVICE_WORKING_DIRECTORY"

    # Options de redémarrage
    RESTART_NO = "RESTART_NO"
    RESTART_NO_DESCRIPTION = "RESTART_NO_DESCRIPTION"
    RESTART_ALWAYS = "RESTART_ALWAYS"
    RESTART_ALWAYS_DESCRIPTION = "RESTART_ALWAYS_DESCRIPTION"
    RESTART_ON_FAILURE = "RESTART_ON_FAILURE"
    RESTART_ON_FAILURE_DESCRIPTION = "RESTART_ON_FAILURE_DESCRIPTION"
    RESTART_ON_ABNORMAL = "RESTART_ON_ABNORMAL"
    RESTART_ON_ABNORMAL_DESCRIPTION = "RESTART_ON_ABNORMAL_DESCRIPTION"

    # Options de redémarrage (nouvelles clés pour les détails)
    RESTART_NO_DETAIL = "RESTART_NO_DETAIL"
    RESTART_ALWAYS_DETAIL = "RESTART_ALWAYS_DETAIL"
    RESTART_ON_FAILURE_DETAIL = "RESTART_ON_FAILURE_DETAIL"
    RESTART_ON_ABNORMAL_DETAIL = "RESTART_ON_ABNORMAL_DETAIL"

    # Configuration du redémarrage
    RESTART_CONFIGURATION = "RESTART_CONFIGURATION"
    RESTART_CONFIGURATION_TITLE = "🔄 Restart Options Configuration"
    RESTART_CONFIGURATION_DESCRIPTION = (
        "Configure how the service should behave when it stops"
    )

    # Configuration des redémarrages
    RESTART_POLICY_ABNORMAL = "RESTART_POLICY_ABNORMAL"
    RESTART_LIMITS_CONFIG = "RESTART_LIMITS_CONFIG"
    MAX_RESTARTS_IN_INTERVAL = "MAX_RESTARTS_IN_INTERVAL"
    ENTER_NUMBER_DEFAULT = "ENTER_NUMBER_DEFAULT"

    # Ajouter ces clés
    EDIT_USER = "EDIT_USER"
    EDIT_GROUP = "EDIT_GROUP"
    EDIT_WORKING_DIR = "EDIT_WORKING_DIR"
    EDIT_SERVICE_TYPE = "EDIT_SERVICE_TYPE"
    EDIT_START_COMMAND = "EDIT_START_COMMAND"
    EDIT_STOP_COMMAND = "EDIT_STOP_COMMAND"
    EDIT_RESTART_POLICY = "EDIT_RESTART_POLICY"
    EDIT_RESTART_DELAY = "EDIT_RESTART_DELAY"
    EDIT_MAX_RESTARTS = "EDIT_MAX_RESTARTS"

    # Politiques de redémarrage
    RESTART_POLICY_NO = "RESTART_POLICY_NO"
    RESTART_POLICY_ALWAYS = "RESTART_POLICY_ALWAYS"
    RESTART_POLICY_ON_FAILURE = "RESTART_POLICY_ON_FAILURE"
    RESTART_POLICY_ON_ABNORMAL = "RESTART_POLICY_ON_ABNORMAL"
    RESTART_POLICY_ON_ABORT = "RESTART_POLICY_ON_ABORT"
    RESTART_POLICY_ON_WATCHDOG = "RESTART_POLICY_ON_WATCHDOG"

    # Options d'édition
    EDIT_USER = "👤 Utilisateur"
    EDIT_GROUP = "👥 Groupe"
    EDIT_WORKING_DIR = "📂 Dossier de travail"
    EDIT_SERVICE_TYPE = "⚡ Type de service"
    EDIT_START_COMMAND = "🚀 Commande de démarrage"
    EDIT_STOP_COMMAND = "🛑 Commande d'arrêt"
    EDIT_RESTART_POLICY = "🔄 Politique de redémarrage"
    EDIT_RESTART_DELAY = "⏱️  Délai de redémarrage"
    EDIT_MAX_RESTARTS = "🔄 Nombre maximum de redémarrages"

    # Restart configuration
    RESTART_POLICY_TITLE = "🔄 Restart Policy Configuration"
    RESTART_POLICY_DESCRIPTION = "Choose how the service should restart"
    RESTART_LIMITS_TITLE = "🔄 Restart Limits Configuration"
    RESTART_LIMITS_MAX_RESTARTS = "Maximum number of restarts in 5 minutes:"
    RESTART_LIMITS_DELAY = "Delay between restart attempts (in seconds):"
    RESTART_LIMITS_DEFAULT = "Enter a number (default: {default})"
    FINAL_CONFIG_COMPLETED = "✨ Final configuration completed"

    # Configuration des redémarrages
    RESTART_POLICY_TITLE = "RESTART_POLICY_TITLE"
    RESTART_POLICY_DESCRIPTION = "RESTART_POLICY_DESCRIPTION"
    RESTART_LIMITS_TITLE = "RESTART_LIMITS_TITLE"
    RESTART_LIMITS_MAX_RESTARTS = "RESTART_LIMITS_MAX_RESTARTS"
    RESTART_LIMITS_DELAY = "RESTART_LIMITS_DELAY"
    RESTART_LIMITS_DEFAULT = "RESTART_LIMITS_DEFAULT"
    RESTART_POLICY_NO = "RESTART_POLICY_NO"
    RESTART_POLICY_ALWAYS = "RESTART_POLICY_ALWAYS"
    RESTART_POLICY_ON_FAILURE = "RESTART_POLICY_ON_FAILURE"
    RESTART_POLICY_ON_ABNORMAL = "RESTART_POLICY_ON_ABNORMAL"

    # Ajouter ces nouvelles clés
    EDIT_SECTION_TITLE = "EDIT_SECTION_TITLE"
    EDIT_SECTION_UNIT = "EDIT_SECTION_UNIT"
    EDIT_SECTION_SERVICE = "EDIT_SECTION_SERVICE"
    EDIT_SECTION_INSTALL = "EDIT_SECTION_INSTALL"
    EDIT_SAVE_CHANGES = "EDIT_SAVE_CHANGES"
    EDIT_DESCRIPTION = "EDIT_DESCRIPTION"
    EDIT_DOCUMENTATION = "EDIT_DOCUMENTATION"
    EDIT_START_LIMIT_INTERVAL = "EDIT_START_LIMIT_INTERVAL"
    EDIT_START_LIMIT_BURST = "EDIT_START_LIMIT_BURST"
    EDIT_CURRENT_VALUE = "EDIT_CURRENT_VALUE"
    EDIT_ENTER_NEW_VALUE = "EDIT_ENTER_NEW_VALUE"
    EDIT_URLS_SPACE_SEPARATED = "EDIT_URLS_SPACE_SEPARATED"
    EDIT_RESTART_INTERVAL = "EDIT_RESTART_INTERVAL"
    EDIT_RESTART_ATTEMPTS = "EDIT_RESTART_ATTEMPTS"

    # Section Install
    EDIT_WANTED_BY = "EDIT_WANTED_BY"
    EDIT_REQUIRED_BY = "EDIT_REQUIRED_BY"
    EDIT_ALSO = "EDIT_ALSO"
    EDIT_WANTED_BY_PROMPT = "EDIT_WANTED_BY_PROMPT"
    EDIT_REQUIRED_BY_PROMPT = "EDIT_REQUIRED_BY_PROMPT"
    EDIT_ALSO_PROMPT = "EDIT_ALSO_PROMPT"

    # Suppression de service
    CONFIRM_DELETE_SERVICE = "CONFIRM_DELETE_SERVICE"
    STOPPING_SERVICE = "STOPPING_SERVICE"
    DISABLING_SERVICE = "DISABLING_SERVICE"
    SERVICE_FILE_DELETED = "SERVICE_FILE_DELETED"
    CONFIG_FILE_DELETED = "CONFIG_FILE_DELETED"
    SERVICE_DELETED = "SERVICE_DELETED"


# Dictionnaire de traduction français
cli_translations_fr = {
    # Configuration des redémarrages
    TranslationKeys.RESTART_POLICY_TITLE: "🔄 Configuration de la politique de redémarrage",
    TranslationKeys.RESTART_POLICY_DESCRIPTION: "Choisissez comment le service doit redémarrer",
    TranslationKeys.RESTART_LIMITS_TITLE: "🔄 Configuration des limites de redémarrage",
    TranslationKeys.RESTART_LIMITS_MAX_RESTARTS: "Nombre maximum de redémarrages en 5 minutes :",
    TranslationKeys.RESTART_LIMITS_DELAY: "Délai entre les tentatives de redémarrage (en secondes) :",
    TranslationKeys.RESTART_LIMITS_DEFAULT: "Entrez un nombre (défaut: {default})",
    TranslationKeys.RESTART_POLICY_NO: "Ne pas redémarrer",
    TranslationKeys.RESTART_POLICY_ALWAYS: "Toujours redémarrer",
    TranslationKeys.RESTART_POLICY_ON_FAILURE: "Redémarrer en cas d'échec",
    TranslationKeys.RESTART_POLICY_ON_ABNORMAL: "Redémarrer en cas d'anomalie",
    TranslationKeys.WELCOME: "Bienvenue dans SystemdManager",
    TranslationKeys.MAIN_MENU: "Menu principal",
    TranslationKeys.CREATE_SERVICE: "📝 Créer un nouveau service",
    TranslationKeys.EDIT_SERVICE: "Modifier le service",
    TranslationKeys.DELETE_SERVICE: "Supprimer le service",
    TranslationKeys.VIEW_SERVICE: "Voir le service",
    TranslationKeys.EXIT: "Quitter",
    TranslationKeys.SELECT_ACTION: "Sélectionnez une action",
    TranslationKeys.GOODBYE: "Au revoir ! 👋",
    TranslationKeys.CREATE_NEW_SERVICE_SYSTEMD: "📝 Création d'un nouveau service systemd",
    TranslationKeys.EXEC_COMMAND_CONFIGURED: "✅ Commande d'exécution configurée",
    TranslationKeys.START_DELAY: "⏰ Délai de démarrage (en secondes)",
    TranslationKeys.START_DELAY_SET: "✅ Délai de démarrage défini à {delay} secondes",
    TranslationKeys.MAX_RESTARTS: "🔄 Nombre maximum de redémarrages",
    TranslationKeys.CONFIGURE_FINAL_SERVICE: "🔧 Configuration finale du service",
    TranslationKeys.MAX_RESTARTS_SET: "✅ Nombre maximum de redémarrages défini à {restarts}",
    # Messages d'erreur et d'administration
    TranslationKeys.ADMIN_RIGHTS_REQUIRED: "⚠️  Droits administrateur requis pour",
    TranslationKeys.RELAUNCH_WITH_SUDO: "📌 Relancez avec sudo",
    TranslationKeys.INSTALLATION_ERROR: "❌ Erreur lors de l'installation :",
    TranslationKeys.UNEXPECTED_ERROR: " Erreur inattendue :",
    TranslationKeys.ERROR_READING_USERS: "Erreur lors de la lecture des utilisateurs :",
    TranslationKeys.ERROR_USER_CONFIGURATION: "Erreur lors de la configuration utilisateur :",
    TranslationKeys.ERROR_DURING_STEP: "❌ Erreur lors de l'étape",
    TranslationKeys.ERROR_SAVING: "❌ Erreur lors de la sauvegarde :",
    TranslationKeys.ERROR_STARTING_SERVICE: "❌ Erreur lors du démarrage du service",
    TranslationKeys.ERROR_STOPPING_SERVICE: "❌ Erreur lors de l'arrêt du service",
    TranslationKeys.ERROR_RESTARTING_SERVICE: "❌ Erreur lors du redémarrage du service",
    TranslationKeys.SERVICE_FILE_CREATED: "✅ Fichier service créé",
    TranslationKeys.SYSTEMD_RELOADED: "✅ Configuration systemd rechargée",
    TranslationKeys.SERVICE_ENABLED_ON_BOOT: "✅ Service activé au démarrage",
    TranslationKeys.WANT_TO_START_SERVICE_NOW: "Voulez-vous démarrer le service maintenant ?",
    TranslationKeys.SERVICE_RUNNING: "Service en cours d'exécution",
    TranslationKeys.SERVICE_INSTALLED_BUT_NOT_ACTIVE: "Le service est installé mais n'est pas actif",
    TranslationKeys.INSTALL_SERVICE_ACTION: "installer le service",
    TranslationKeys.SERVICE_NAME_REQUIRED: "❌ Le nom du service est requis.",
    # Messages de validation
    TranslationKeys.SERVICE_NAME_VALIDATION: "Le nom du service ne peut contenir que des lettres, chiffres, tirets et underscores",
    TranslationKeys.SERVICE_NAME_MIN_LENGTH: "Le nom du service doit faire au moins 1 caractère",
    TranslationKeys.SERVICE_NAME_NO_NUMBER_START: "Le nom du service ne doit pas commencer par un chiffre",
    TranslationKeys.SERVICE_ALREADY_EXISTS: "Un service avec ce nom existe déjà",
    # Interface principale
    TranslationKeys.MAIN_TITLE: "🚀 Gestionnaire de services systemd",
    TranslationKeys.WHAT_DO_YOU_WANT_TO_DO: "Que souhaitez-vous faire ?",
    TranslationKeys.CREATE_NEW_SERVICE: "📝 Créer un nouveau service",
    TranslationKeys.MANAGE_EXISTING_SERVICES: "⚙️  Gérer les services existants",
    TranslationKeys.LANGUAGE: "🌍 Langue",
    TranslationKeys.QUIT: "❌ Quitter",
    TranslationKeys.CHOOSE_LANGUAGE: "🌍 Choisissez votre langue",
    TranslationKeys.FRENCH: "🇫🇷 Français",
    TranslationKeys.ENGLISH: "🇬🇧 Anglais",
    # Configuration du service
    TranslationKeys.SERVICE_NAME: "Nom du service",
    TranslationKeys.DESCRIPTION: "Description",
    TranslationKeys.SERVICE_TYPE: "Type de service",
    TranslationKeys.USER_CONFIGURATION: "Configuration utilisateur",
    TranslationKeys.WORKING_DIRECTORY: "Dossier de travail",
    TranslationKeys.EXECUTION_COMMAND: "Commande d'exécution",
    TranslationKeys.CONFIGURE_SERVICE_TYPE: "⚡ Configuration du type de service",
    TranslationKeys.SIMPLE_TYPE: "simple - Le processus reste au premier plan (recommandé, y compris pour screen via -DmS)",
    TranslationKeys.FORKING_TYPE: "forking - Le processus se détache en arrière-plan",
    TranslationKeys.ONESHOT_TYPE: "oneshot - S'exécute une fois et s'arrête",
    TranslationKeys.NOTIFY_TYPE: "notify - Comme simple mais notifie quand il est prêt",
    # Messages de progression
    TranslationKeys.PROGRESS_STEP: "🔄 Étape {step}/{total}: {name}",
    TranslationKeys.USE_BACK_TO_GO_BACK: "Utilisez ↩️  pour revenir en arrière à tout moment",
    TranslationKeys.BACK_TO_PREVIOUS_STEP: "↩️  Retour à l'étape précédente",
    TranslationKeys.MSG_NO_SERVICES: "Aucun service disponible",
    TranslationKeys.MSG_CHOOSE_SERVICE: "Choisissez un service",
    TranslationKeys.MSG_CHOOSE_ACTION: "Choisissez une action",
    TranslationKeys.BACK: "↩️  Retour",
    # Actions sur les services
    TranslationKeys.START_SERVICE: "🚀 Démarrer",
    TranslationKeys.STOP_SERVICE: "🛑 Arrêter",
    TranslationKeys.RESTART_SERVICE: "🔄 Redémarrer",
    TranslationKeys.VIEW_STATUS: "📊 Voir le statut",
    TranslationKeys.VIEW_LOGS: "📜 Voir les logs",
    TranslationKeys.EDIT_SERVICE_ACTION: "📝 Modifier",
    TranslationKeys.DELETE_SERVICE_ACTION: "🗑️  Supprimer",
    # Messages de succès
    TranslationKeys.SERVICE_INITIALIZED: "✅ Service '{name}' initialisé",
    TranslationKeys.DESCRIPTION_ADDED: "✅ Description ajoutée",
    TranslationKeys.SERVICE_TYPE_SET: "✅ Type de service défini : {result}",
    TranslationKeys.USER_CONFIGURED: "✅ Utilisateur configuré : {user}",
    TranslationKeys.WORKING_DIRECTORY_SET: "✅ Dossier de travail défini : {directory}",
    TranslationKeys.FINAL_CONFIGURATION_COMPLETED: "✅ Configuration finale terminée",
    TranslationKeys.SERVICE_UPDATED_AND_RESTARTED: "✅ Service {name} mis à jour et redémarré",
    TranslationKeys.SERVICE_DELETED: "✅ Service {name} complètement supprimé",
    TranslationKeys.SERVICE_STARTED_SUCCESSFULLY: "✅ Service {name} démarré avec succès",
    TranslationKeys.SERVICE_STOPPED_SUCCESSFULLY: "✅ Service {name} arrêté avec succès",
    TranslationKeys.SERVICE_RESTARTED_SUCCESSFULLY: "✅ Service {name} redémarré avec succès",
    # Instructions et messages pour le nom du service
    TranslationKeys.ENTER_SERVICE_NAME_INSTRUCTION: "Entrez un nom (lettres, chiffres, - et _ uniquement)\n'b' pour revenir en arrière, 'q' pour quitter",
    TranslationKeys.ENTER_SERVICE_DESCRIPTION_INSTRUCTION: "Décrivez brièvement le service\n'b' pour revenir, 'q' pour quitter",
    TranslationKeys.CONFIRM_QUIT: "Êtes-vous sûr de vouloir quitter ?",
    TranslationKeys.INVALID_NAME: "❌ Nom invalide. Utilisez uniquement des lettres, des chiffres, - et _",
    TranslationKeys.SELECT_USER_TO_RUN_SERVICE: "Sélectionnez l'utilisateur qui exécutera le service :",
    # Messages pour le dossier de travail
    TranslationKeys.BROWSE_DIRECTORIES: "📂 Parcourir les dossiers",
    TranslationKeys.ENTER_PATH_MANUALLY: "📝 Saisir le chemin manuellement",
    TranslationKeys.DEFINE_WORKING_DIRECTORY: "Comment souhaitez-vous définir le dossier de travail ?",
    TranslationKeys.ENTER_FULL_DIRECTORY_PATH: "Entrez le chemin complet du dossier de travail :",
    TranslationKeys.DIRECTORY_DOES_NOT_EXIST: "Le dossier {directory} n'existe pas",
    TranslationKeys.NOT_A_DIRECTORY: "{directory} n'est pas un dossier",
    # Messages pour la navigation des dossiers
    TranslationKeys.CURRENT_DIRECTORY: "Dossier actuel :",
    TranslationKeys.SELECT_DIRECTORY: "Sélectionnez un dossier :",
    TranslationKeys.SELECT_THIS_DIRECTORY: "✅ Sélectionner ce dossier",
    # Messages pour la commande d'exécution
    TranslationKeys.SPECIFY_COMMAND_METHOD: "Comment souhaitez-vous spécifier la commande ?",
    TranslationKeys.SELECT_EXECUTABLE_FILE: "📂 Sélectionner un fichier exécutable",
    TranslationKeys.ENTER_COMMAND_MANUALLY: "📝 Saisir la commande manuellement",
    TranslationKeys.SEARCH_EXECUTABLE_FILES: "🔍 Recherche des fichiers exécutables dans :",
    TranslationKeys.ERROR_READING_DIRECTORY: "Erreur lors de la lecture du dossier",
    TranslationKeys.NO_EXECUTABLE_FILES_FOUND: "Aucun fichier exécutable trouvé dans",
    TranslationKeys.ENTER_EXECUTION_COMMAND: "Entrez la commande d'exécution :",
    TranslationKeys.EXAMPLE_COMMAND: "Exemple : python3 script.py ou ./executable",
    TranslationKeys.RUN_SERVICE_IN_SCREEN: "Voulez-vous exécuter ce service dans screen ?",
    # Autres messages
    TranslationKeys.QUIT_WITHOUT_SAVING: "Quitter sans sauvegarder",
    TranslationKeys.WANT_TO_RETRY: "Voulez-vous réessayer ?",
    TranslationKeys.SAVE_CONFIGURATION: "Sauvegarde de la configuration",
    TranslationKeys.CONFIGURATION_SAVED: "✅ Configuration sauvegardée",
    TranslationKeys.WANT_TO_INSTALL_SERVICE_NOW: "Voulez-vous installer le service maintenant ?",
    TranslationKeys.SERVICE_INSTALLED_SUCCESSFULLY: "✅ Service installé avec succès",
    TranslationKeys.SERVICE_ALREADY_ACTIVE: "⚠️  Le service {name} est déjà actif",
    TranslationKeys.SERVICE_NOT_ACTIVE: "⚠️  Le service est installé mais n'est pas actif",
    TranslationKeys.CHECKING_LOGS: "📜 Consultation des logs :",
    TranslationKeys.LAST_SERVICE_LOGS: "📜 Derniers logs du service :",
    TranslationKeys.INVALID_INPUT_FOR_START_DELAY: "Entrée invalide pour le délai de démarrage.",
    TranslationKeys.INVALID_INPUT_FOR_MAX_RESTARTS: "Entrée invalide pour le nombre maximum de redémarrages.",
    TranslationKeys.WANT_TO_QUIT: "Voulez-vous vraiment quitter ?",
    TranslationKeys.YES: "Oui",
    TranslationKeys.NO: "Non",
    TranslationKeys.ARE_YOU_SURE_YOU_WANT_TO_DELETE: "Êtes-vous sûr de vouloir supprimer {name} ?",
    TranslationKeys.SERVICE_STOPPED: "📥 Arrêt du service {name}...",
    TranslationKeys.SERVICE_DISABLED: "🔌 Désactivation du service {name}...",
    TranslationKeys.SERVICE_FILE_DELETED: "🗑️  Fichier service supprimé : {path}",
    TranslationKeys.CONFIGURATION_DELETED: "🗑️  Configuration supprimée : {path}",
    TranslationKeys.SERVICE_FULLY_DELETED: "✅ Service {name} complètement supprimé",
    # Édition des sections
    TranslationKeys.WHICH_SECTION_TO_EDIT: "Quelle section voulez-vous modifier ?",
    TranslationKeys.SECTION_UNIT: "📋 Section [Unit] - Description et dépendances",
    TranslationKeys.SECTION_SERVICE: "⚙️  Section [Service] - Configuration du service",
    TranslationKeys.SECTION_INSTALL: "🔌 Section [Install] - Installation et démarrage",
    TranslationKeys.SAVE_AND_APPLY_CHANGES: "💾 Sauvegarder et appliquer les modifications",
    # Modifications des sections
    TranslationKeys.WHAT_DO_YOU_WANT_TO_MODIFY: "Que souhaitez-vous modifier ?",
    TranslationKeys.DESCRIPTION: "📝 Description",
    TranslationKeys.DOCUMENTATION: "📚 Documentation",
    TranslationKeys.START_LIMIT_INTERVAL: "⏰ Délai avant redémarrage",
    TranslationKeys.START_LIMIT_BURST: "🔄 Nombre de redémarrages",
    TranslationKeys.USER: "👤 Utilisateur",
    TranslationKeys.GROUP: "👥 Groupe",
    TranslationKeys.WORKING_DIRECTORY: "📂 Dossier de travail",
    TranslationKeys.SERVICE_TYPE: "⚡ Type de service",
    TranslationKeys.EXEC_START: "🚀 Commande de démarrage",
    TranslationKeys.EXEC_STOP: "🛑 Commande d'arrêt",
    TranslationKeys.RESTART_POLICY: "🔄 Politique de redémarrage",
    TranslationKeys.RESTART_SEC: "⏱️  Délai de redémarrage",
    TranslationKeys.MAX_RESTARTS_ALLOWED: "🔄 Nombre maximum de redémarrages",
    # Politique de redémarrage
    TranslationKeys.CHOOSE_RESTART_POLICY: "Choisissez la politique de redémarrage :",
    # Entrées invalides
    TranslationKeys.INVALID_INPUT: "Entrée invalide.",
    # Autres
    TranslationKeys.RETRY: "Réessayer",
    TranslationKeys.RETOUR: "Retour",
    TranslationKeys.EXITING: "Au revoir ! 👋",
    # Instructions pour quitter ou revenir
    TranslationKeys.ENTER_B_TO_GO_BACK: "'b' pour revenir",
    TranslationKeys.ENTER_Q_TO_QUIT: "'q' pour quitter",
    # Messages pour le timer (si nécessaire)
    TranslationKeys.CONFIGURE_TIMER: "Voulez-vous configurer un timer ?",
    TranslationKeys.TIMER_TYPE: "Type de timer :",
    TranslationKeys.DELAY_AFTER_BOOT: "Délai après le démarrage",
    TranslationKeys.REGULAR_INTERVAL: "Intervalle régulier",
    TranslationKeys.SPECIFIC_TIME: "Heure spécifique",
    TranslationKeys.DELAY_IN_SECONDS: "Délai en secondes :",
    TranslationKeys.INTERVAL_IN_SECONDS: "Intervalle en secondes :",
    TranslationKeys.TIME_IN_HH_MM: "Heure (format HH:MM) :",
    TranslationKeys.INVALID_TIME_FORMAT: "Format de temps invalide.",
    TranslationKeys.ON_BOOT_SEC: "OnBootSec={seconds}s",
    TranslationKeys.ON_UNIT_ACTIVE_SEC: "OnUnitActiveSec={seconds}s",
    TranslationKeys.ON_CALENDAR: "OnCalendar=*-*-* {time}:00",
    # Confirmation
    TranslationKeys.CONFIRMATION: "Confirmation",
    TranslationKeys.ARE_YOU_SURE: "Êtes-vous sûr ?",
    TranslationKeys.YES: "Oui",
    TranslationKeys.NO: "Non",
    # Clés pour les options de redémarrage
    TranslationKeys.RESTART_NO_KEY: "non",
    TranslationKeys.RESTART_ALWAYS_KEY: "toujours",
    TranslationKeys.RESTART_ON_FAILURE_KEY: "en cas d'échec",
    TranslationKeys.RESTART_ON_ABNORMAL_KEY: "en cas d'anomalie",
    # Messages supplémentaires
    TranslationKeys.RESTART_LIMIT_CONFIGURATION: "🔄 Configuration des limites de redémarrage",
    TranslationKeys.MAX_RESTARTS_IN_INTERVAL: "Nombre maximum de redémarrages en 5 minutes :",
    TranslationKeys.ENTER_NUMBER_DEFAULT: "Entrez un nombre (défaut: {default})",
    TranslationKeys.RESTART_DELAY_BETWEEN_ATTEMPTS: "Délai entre les tentatives de redémarrage (en secondes) :",
    TranslationKeys.ENTER_SECONDS_DEFAULT: "Entrez un nombre de secondes (défaut: {default})",
    # Options de redémarrage
    TranslationKeys.RESTART_NO: "Ne pas redémarrer",
    TranslationKeys.RESTART_NO_DESCRIPTION: "Le service ne redémarre jamais automatiquement",
    TranslationKeys.RESTART_ALWAYS: "Toujours redémarrer",
    TranslationKeys.RESTART_ALWAYS_DESCRIPTION: "Le service redémarre toujours automatiquement",
    TranslationKeys.RESTART_ON_FAILURE: "Redémarrer sur échec",
    TranslationKeys.RESTART_ON_FAILURE_DESCRIPTION: "Le service redémarre uniquement en cas d'échec",
    TranslationKeys.RESTART_ON_ABNORMAL: "Redémarrer sur anomalie",
    TranslationKeys.RESTART_ON_ABNORMAL_DESCRIPTION: "Le service redémarre en cas d'arrêt anormal",
    # Détails des options de redémarrage
    TranslationKeys.RESTART_NO_DETAIL: "Le service ne redémarre jamais automatiquement.",
    TranslationKeys.RESTART_ALWAYS_DETAIL: "Le service redémarre toujours automatiquement.",
    TranslationKeys.RESTART_ON_FAILURE_DETAIL: "Le service redémarre uniquement en cas d'échec.",
    TranslationKeys.RESTART_ON_ABNORMAL_DETAIL: "Le service redémarre en cas d'arrêt anormal.",
    # Configuration du redémarrage
    TranslationKeys.RESTART_CONFIGURATION: "Configuration du redémarrage",
    TranslationKeys.RESTART_CONFIGURATION_TITLE: "🔄 Restart Options Configuration",
    TranslationKeys.RESTART_CONFIGURATION_DESCRIPTION: "Configurez comment le service doit se comporter en cas d'arrêt",
    # Configuration des redémarrages
    TranslationKeys.RESTART_POLICY_ABNORMAL: "en cas d'anomalie - Redémarrer sur arrêt anormal",
    TranslationKeys.RESTART_LIMITS_CONFIG: "🔄 Configuration des limites de redémarrage",
    TranslationKeys.MAX_RESTARTS_IN_INTERVAL: "Nombre maximum de redémarrages en 5 minutes :",
    TranslationKeys.ENTER_NUMBER_DEFAULT: "Entrez un nombre (défaut: {default})",
    # Politiques de redémarrage
    TranslationKeys.RESTART_POLICY_NO: "Ne pas redémarrer",
    TranslationKeys.RESTART_POLICY_ALWAYS: "Toujours redémarrer",
    TranslationKeys.RESTART_POLICY_ON_FAILURE: "Redémarrer en cas d'échec",
    TranslationKeys.RESTART_POLICY_ON_ABNORMAL: "Redémarrer en cas d'anomalie",
    TranslationKeys.RESTART_POLICY_ON_ABORT: "Redémarrer en cas d'arrêt",
    TranslationKeys.RESTART_POLICY_ON_WATCHDOG: "Redémarrer sur watchdog",
    # Options d'édition
    TranslationKeys.EDIT_USER: "👤 Utilisateur",
    TranslationKeys.EDIT_GROUP: "👥 Groupe",
    TranslationKeys.EDIT_WORKING_DIR: "📂 Dossier de travail",
    TranslationKeys.EDIT_SERVICE_TYPE: "⚡ Type de service",
    TranslationKeys.EDIT_START_COMMAND: "🚀 Commande de démarrage",
    TranslationKeys.EDIT_STOP_COMMAND: "🛑 Commande d'arrêt",
    TranslationKeys.EDIT_RESTART_POLICY: "🔄 Politique de redémarrage",
    TranslationKeys.EDIT_RESTART_DELAY: "⏱️  Délai de redémarrage",
    TranslationKeys.EDIT_MAX_RESTARTS: "🔄 Nombre maximum de redémarrages",
    # Ajouter ces traductions françaises
    TranslationKeys.EDIT_SECTION_TITLE: "Quelle section voulez-vous modifier ?",
    TranslationKeys.EDIT_SECTION_UNIT: "📋 Section [Unit] - Description et dépendances",
    TranslationKeys.EDIT_SECTION_SERVICE: "⚙️  Section [Service] - Configuration du service",
    TranslationKeys.EDIT_SECTION_INSTALL: "🔌 Section [Install] - Installation et démarrage",
    TranslationKeys.EDIT_SAVE_CHANGES: "💾 Sauvegarder et appliquer les modifications",
    TranslationKeys.EDIT_DESCRIPTION: "📝 Description",
    TranslationKeys.EDIT_DOCUMENTATION: "📚 Documentation",
    TranslationKeys.EDIT_START_LIMIT_INTERVAL: "⏰ Délai avant redémarrage",
    TranslationKeys.EDIT_START_LIMIT_BURST: "🔄 Nombre de redémarrages",
    TranslationKeys.EDIT_CURRENT_VALUE: "Valeur actuelle : {value}",
    TranslationKeys.EDIT_ENTER_NEW_VALUE: "Nouvelle valeur :",
    TranslationKeys.EDIT_URLS_SPACE_SEPARATED: "Documentation (URLs, séparées par des espaces) :",
    TranslationKeys.EDIT_RESTART_INTERVAL: "Délai avant redémarrage (en secondes) :",
    TranslationKeys.EDIT_RESTART_ATTEMPTS: "Nombre de redémarrages autorisés :",
    TranslationKeys.EDIT_WANTED_BY: "🎯 WantedBy (Démarrage automatique)",
    TranslationKeys.EDIT_REQUIRED_BY: "⚡ RequiredBy (Dépendances)",
    TranslationKeys.EDIT_ALSO: "➕ Also (Services additionnels)",
    TranslationKeys.EDIT_WANTED_BY_PROMPT: "Cibles qui démarrent ce service (ex: multi-user.target) :",
    TranslationKeys.EDIT_REQUIRED_BY_PROMPT: "Services qui requièrent ce service :",
    TranslationKeys.EDIT_ALSO_PROMPT: "Services à installer en même temps :",
    # Suppression de service
    TranslationKeys.CONFIRM_DELETE_SERVICE: "⚠️  Êtes-vous sûr de vouloir supprimer {name} ?",
    TranslationKeys.STOPPING_SERVICE: "🛑 Arrêt du service {name}...",
    TranslationKeys.DISABLING_SERVICE: "🔌 Désactivation du service {name}...",
    TranslationKeys.SERVICE_FILE_DELETED: "🗑️  Fichier service supprimé : {path}",
    TranslationKeys.CONFIG_FILE_DELETED: "🗑️  Fichier de configuration supprimé : {path}",
    TranslationKeys.SERVICE_DELETED: "✅ Service {name} complètement supprimé",
}

# Dictionnaire de traduction anglais
cli_translations_en = {
    # Restart configuration
    TranslationKeys.RESTART_POLICY_TITLE: "🔄 Restart Policy Configuration",
    TranslationKeys.RESTART_POLICY_DESCRIPTION: "Choose how the service should restart",
    TranslationKeys.RESTART_LIMITS_TITLE: "🔄 Restart Limits Configuration",
    TranslationKeys.RESTART_LIMITS_MAX_RESTARTS: "Maximum number of restarts in 5 minutes:",
    TranslationKeys.RESTART_LIMITS_DELAY: "Delay between restart attempts (in seconds):",
    TranslationKeys.RESTART_LIMITS_DEFAULT: "Enter a number (default: {default})",
    TranslationKeys.RESTART_POLICY_NO: "No restart",
    TranslationKeys.RESTART_POLICY_ALWAYS: "Always restart",
    TranslationKeys.RESTART_POLICY_ON_FAILURE: "Restart on failure",
    TranslationKeys.RESTART_POLICY_ON_ABNORMAL: "Restart on abnormal",
    # Messages de base en anglais
    TranslationKeys.WELCOME: "Welcome to SystemdManager",
    TranslationKeys.MAIN_MENU: "Main menu",
    TranslationKeys.CREATE_SERVICE: "📝 Create new service",
    TranslationKeys.EDIT_SERVICE: "Edit service",
    TranslationKeys.DELETE_SERVICE: "Delete service",
    TranslationKeys.VIEW_SERVICE: "View service",
    TranslationKeys.EXIT: "Exit",
    TranslationKeys.SELECT_ACTION: "Select an action",
    TranslationKeys.GOODBYE: "Goodbye! 👋",
    TranslationKeys.CREATE_NEW_SERVICE_SYSTEMD: "📝 Creating new systemd service",
    TranslationKeys.EXEC_COMMAND_CONFIGURED: "✅ Execution command configured",
    TranslationKeys.START_DELAY: "⏰ Start delay (in seconds)",
    TranslationKeys.START_DELAY_SET: "✅ Start delay set to {delay} seconds",
    TranslationKeys.MAX_RESTARTS: "🔄 Maximum number of restarts",
    TranslationKeys.CONFIGURE_FINAL_SERVICE: "🔧 Final service configuration",
    TranslationKeys.MAX_RESTARTS_SET: "✅ Maximum number of restarts set to {restarts}",
    # Configuration des redémarrages en anglais
    TranslationKeys.RESTART_POLICY_ABNORMAL: "on abnormal - Restart on abnormal exit",
    TranslationKeys.RESTART_LIMITS_CONFIG: "🔄 Restart Limits Configuration",
    TranslationKeys.MAX_RESTARTS_IN_INTERVAL: "Maximum number of restarts in 5 minutes:",
    TranslationKeys.ENTER_NUMBER_DEFAULT: "Enter a number (default: {default})",
    # Politiques de redémarrage en anglais
    TranslationKeys.RESTART_POLICY_NO: "No restart",
    TranslationKeys.RESTART_POLICY_ALWAYS: "Always restart",
    TranslationKeys.RESTART_POLICY_ON_FAILURE: "Restart on failure",
    TranslationKeys.RESTART_POLICY_ON_ABNORMAL: "Restart on abnormal",
    TranslationKeys.RESTART_POLICY_ON_ABORT: "Restart on abort",
    TranslationKeys.RESTART_POLICY_ON_WATCHDOG: "Restart on watchdog",
    # Options d'édition en anglais
    TranslationKeys.EDIT_USER: "👤 User",
    TranslationKeys.EDIT_GROUP: "👥 Group",
    TranslationKeys.EDIT_WORKING_DIR: "📂 Working directory",
    TranslationKeys.EDIT_SERVICE_TYPE: "⚡ Service type",
    TranslationKeys.EDIT_START_COMMAND: "🚀 Start command",
    TranslationKeys.EDIT_STOP_COMMAND: "🛑 Stop command",
    TranslationKeys.EDIT_RESTART_POLICY: "🔄 Restart policy",
    TranslationKeys.EDIT_RESTART_DELAY: "⏱️  Restart delay",
    TranslationKeys.EDIT_MAX_RESTARTS: "🔄 Maximum number of restarts",
    # Configuration du redémarrage en anglais
    TranslationKeys.RESTART_CONFIGURATION: "Restart Configuration",
    TranslationKeys.RESTART_CONFIGURATION_TITLE: "🔄 Restart Options Configuration",
    TranslationKeys.RESTART_CONFIGURATION_DESCRIPTION: "Configure how the service should behave when it stops",
    # Détails des options de redémarrage en anglais
    TranslationKeys.RESTART_NO_DETAIL: "The service never restarts automatically.",
    TranslationKeys.RESTART_ALWAYS_DETAIL: "The service always restarts automatically.",
    TranslationKeys.RESTART_ON_FAILURE_DETAIL: "The service restarts only on failure.",
    TranslationKeys.RESTART_ON_ABNORMAL_DETAIL: "The service restarts on abnormal exit.",
    # Ajouter ces traductions anglaises
    TranslationKeys.EDIT_SECTION_TITLE: "Which section do you want to modify?",
    TranslationKeys.EDIT_SECTION_UNIT: "📋 [Unit] Section - Description and dependencies",
    TranslationKeys.EDIT_SECTION_SERVICE: "⚙️  [Service] Section - Service configuration",
    TranslationKeys.EDIT_SECTION_INSTALL: "🔌 [Install] Section - Installation and startup",
    TranslationKeys.EDIT_SAVE_CHANGES: "💾 Save and apply changes",
    TranslationKeys.EDIT_DESCRIPTION: "📝 Description",
    TranslationKeys.EDIT_DOCUMENTATION: "📚 Documentation",
    TranslationKeys.EDIT_START_LIMIT_INTERVAL: "⏰ Restart delay",
    TranslationKeys.EDIT_START_LIMIT_BURST: "🔄 Number of restarts",
    TranslationKeys.EDIT_CURRENT_VALUE: "Current value: {value}",
    TranslationKeys.EDIT_ENTER_NEW_VALUE: "New value:",
    TranslationKeys.EDIT_URLS_SPACE_SEPARATED: "Documentation (URLs, space separated):",
    TranslationKeys.EDIT_RESTART_INTERVAL: "Restart delay (in seconds):",
    TranslationKeys.EDIT_RESTART_ATTEMPTS: "Number of allowed restarts:",
    TranslationKeys.EDIT_WANTED_BY: "🎯 WantedBy (Auto-start)",
    TranslationKeys.EDIT_REQUIRED_BY: "⚡ RequiredBy (Dependencies)",
    TranslationKeys.EDIT_ALSO: "➕ Also (Additional services)",
    TranslationKeys.EDIT_WANTED_BY_PROMPT: "Targets that start this service (e.g., multi-user.target):",
    TranslationKeys.EDIT_REQUIRED_BY_PROMPT: "Services that require this service:",
    TranslationKeys.EDIT_ALSO_PROMPT: "Services to install alongside:",
    # Service deletion
    TranslationKeys.CONFIRM_DELETE_SERVICE: "⚠️  Are you sure you want to delete {name}?",
    TranslationKeys.STOPPING_SERVICE: "🛑 Stopping service {name}...",
    TranslationKeys.DISABLING_SERVICE: "🔌 Disabling service {name}...",
    TranslationKeys.SERVICE_FILE_DELETED: "🗑️  Service file deleted: {path}",
    TranslationKeys.CONFIG_FILE_DELETED: "🗑️  Configuration file deleted: {path}",
    TranslationKeys.SERVICE_DELETED: "✅ Service {name} completely deleted",
}


class CLITranslations:
    def __init__(self):
        self.current_locale = "fr"
        self.config_dir = os.path.expanduser("~/.config/systemd-manager")
        self.config_file = os.path.join(self.config_dir, "cli_config.json")
        self.translations = cli_translations_fr
        self.load_config()

    def load_config(self):
        """Charge la configuration de langue"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.current_locale = config.get("language", "fr")
                    self.translations = (
                        cli_translations_en
                        if self.current_locale == "en"
                        else cli_translations_fr
                    )
            except (OSError, json.JSONDecodeError):
                self.current_locale = "fr"

    def save_config(self):
        """Sauvegarde la configuration de langue"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        with open(self.config_file, "w") as f:
            json.dump({"language": self.current_locale}, f)

    def set_locale(self, locale):
        """Définit la langue courante"""
        if locale in ["fr", "en"]:
            self.current_locale = locale
            self.translations = (
                cli_translations_en if locale == "en" else cli_translations_fr
            )
            self.save_config()

    def get_text(self, key):
        """Obtient le texte traduit pour une clé donnée"""
        return self.translations.get(key, key)


# Instance globale pour l'utilisation dans l'application
cli_translations = CLITranslations()
