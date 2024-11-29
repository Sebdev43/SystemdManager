import os
import sys
import json
import signal
import questionary
from typing import Optional, List
from src.models.service_model import ServiceModel, UnitSection, ServiceSection, InstallSection
import subprocess
from datetime import datetime
from src.cli.cli_translations import cli_translations, TranslationKeys

"""
CLI Controller for SystemD Service Manager

This module provides a command-line interface to manage systemd services.
It allows users to create, edit, delete and monitor systemd services through
an interactive CLI built with questionary.

Classes:
    CLIController: Main controller class handling all CLI operations

Features:
- Create new systemd services with step-by-step wizard
- Manage existing services (start, stop, restart)
- Edit service configurations
- Monitor service status and logs
- Multi-language support (English/French)
- Screen session support
- Sudo rights management
"""

class CLIController:
    """
    Main controller class for the CLI interface.
    
    Handles all CLI operations including service creation, management,
    and configuration. Provides an interactive interface using questionary.

    Attributes:
        services_dir (str): Directory path for storing service configurations
        logs_dir (str): Directory path for storing service logs
    """

    def __init__(self):
        """
        Initialize the CLI controller with necessary configurations.
        Sets up signal handlers and required directories.
        """
        questionary.prompts.confirm.kbi_handler = lambda: None
        questionary.prompts.select.kbi_handler = lambda: None
        questionary.prompts.text.kbi_handler = lambda: None
        
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.services_dir = os.path.expanduser("~/.config/systemd-manager/services")
        self.logs_dir = os.path.expanduser("~/.config/systemd-manager/logs")
        self.setup_directories()

    def setup_directories(self):
        """
        Create necessary directories for storing service configurations and logs.
        Creates ~/.config/systemd-manager/services and ~/.config/systemd-manager/logs
        """
        for directory in [self.services_dir, self.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def ensure_config_dir(self):
        """
        Ensure the configuration directory exists.
        Creates it if it doesn't exist.
        """
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def check_sudo(self) -> bool:
        """
        Check if the current user has sudo privileges.

        Returns:
            bool: True if user has sudo rights, False otherwise
        """
        return os.geteuid() == 0

    def request_sudo(self, action: str):
        """
        Request sudo privileges for a specific action.
        Exits the program if sudo rights are not available.

        Args:
            action (str): Description of the action requiring sudo rights
        """
        if not self.check_sudo():
            print(f"{cli_translations.get_text(TranslationKeys.ADMIN_RIGHTS_REQUIRED)} {action}")
            sys.exit(cli_translations.get_text(TranslationKeys.RELAUNCH_WITH_SUDO))

    def main_menu(self):
        """
        Display and handle the main menu of the CLI interface.
        Provides options to create new services, manage existing ones,
        change language, or quit.
        """
        while True:
            print("\n" + cli_translations.get_text(TranslationKeys.MAIN_TITLE))
            action = questionary.select(
                cli_translations.get_text(TranslationKeys.WHAT_DO_YOU_WANT_TO_DO),
                choices=[
                    cli_translations.get_text(TranslationKeys.CREATE_NEW_SERVICE),
                    cli_translations.get_text(TranslationKeys.MANAGE_EXISTING_SERVICES),
                    cli_translations.get_text(TranslationKeys.LANGUAGE),
                    cli_translations.get_text(TranslationKeys.QUIT)
                ]
            ).ask()

            if action == cli_translations.get_text(TranslationKeys.CREATE_NEW_SERVICE):
                self.create_service()
            elif action == cli_translations.get_text(TranslationKeys.MANAGE_EXISTING_SERVICES):
                self.manage_services()
            elif action == cli_translations.get_text(TranslationKeys.LANGUAGE):
                self.change_language()
            else:
                sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))

    def create_service(self):
        """
        Guide the user through the service creation process.
        Implements a step-by-step wizard for configuring all service parameters.
        Handles navigation between steps and input validation.
        """
        try:
            print("\n" + cli_translations.get_text(TranslationKeys.CREATE_NEW_SERVICE_SYSTEMD))
            print(cli_translations.get_text(TranslationKeys.USE_BACK_TO_GO_BACK) + "\n")
            
            current_step = 0
            service = None
            
            steps = [
                (self.get_service_name, cli_translations.get_text(TranslationKeys.SERVICE_NAME)),
                (self.get_service_description, cli_translations.get_text(TranslationKeys.DESCRIPTION)),
                (self.get_service_type, cli_translations.get_text(TranslationKeys.SERVICE_TYPE)),
                (self.get_user_config, cli_translations.get_text(TranslationKeys.USER_CONFIGURATION)),
                (self.get_working_directory, cli_translations.get_text(TranslationKeys.WORKING_DIRECTORY)),
                (self.get_exec_command, cli_translations.get_text(TranslationKeys.EXECUTION_COMMAND)),
                (self.get_start_delay, cli_translations.get_text(TranslationKeys.START_DELAY))
            ]
            
            total_steps = len(steps)
            
            while current_step < total_steps:
                print(f"\n" + cli_translations.get_text(TranslationKeys.PROGRESS_STEP).format(
                    step=current_step + 1,
                    total=total_steps,
                    name=steps[current_step][1]
                ))
                
                if current_step == 0:
                    result = steps[current_step][0]()
                    if result:
                        service = ServiceModel(result)
                        print(cli_translations.get_text(TranslationKeys.SERVICE_INITIALIZED).format(name=result))
                        current_step += 1
                    else:
                        print(cli_translations.get_text(TranslationKeys.SERVICE_NAME_REQUIRED))
                    continue

                try:
                    if current_step == 5:
                        result = steps[current_step][0](service)
                    else:
                        result = steps[current_step][0]()
                    
                    if result is None:
                        print(cli_translations.get_text(TranslationKeys.BACK_TO_PREVIOUS_STEP))
                        current_step = max(0, current_step - 1)
                        continue
                    
                    if current_step == 1:
                        service.unit.description = result
                        print(cli_translations.get_text(TranslationKeys.DESCRIPTION_ADDED))
                    elif current_step == 2:
                        service.service.type = result
                        print(cli_translations.get_text(TranslationKeys.SERVICE_TYPE_SET).format(result=result))
                    elif current_step == 3:
                        service.service.user = result[0]
                        print(cli_translations.get_text(TranslationKeys.USER_CONFIGURED).format(user=result[0]))
                    elif current_step == 4:
                        service.service.working_directory = result
                        print(cli_translations.get_text(TranslationKeys.WORKING_DIRECTORY_SET).format(directory=result))
                    elif current_step == 5:
                        service.service.exec_start = result
                        print(cli_translations.get_text(TranslationKeys.EXEC_COMMAND_CONFIGURED))
                    elif current_step == 6:
                        service.unit.start_limit_interval = int(result)
                        print(cli_translations.get_text(TranslationKeys.START_DELAY_SET).format(delay=result))
                    
                    current_step += 1
                    
                except Exception as e:
                    print(f"{cli_translations.get_text(TranslationKeys.ERROR_DURING_STEP)} {steps[current_step][1]}: {str(e)}")
                    if not questionary.confirm(cli_translations.get_text(TranslationKeys.WANT_TO_RETRY)).ask():
                        return None

            print("\n✨ " + cli_translations.get_text(TranslationKeys.FINAL_CONFIGURATION_COMPLETED))
            return self.finalize_service(service)

        except KeyboardInterrupt:
            print("\n\n👋 " + cli_translations.get_text(TranslationKeys.GOODBYE))
            sys.exit(0)

    def finalize_service(self, service: ServiceModel):
        """
        Complete the service configuration process.
        Configure restart policies, limits, and install the service.

        Args:
            service (ServiceModel): The service model to finalize

        Returns:
            ServiceModel: The finalized service model, or None if cancelled
        """
        print("\n" + cli_translations.get_text(TranslationKeys.CONFIGURE_FINAL_SERVICE))
        
        restart_options = {
            "no": {
                "description": cli_translations.get_text(TranslationKeys.RESTART_NO),
                "detail": cli_translations.get_text(TranslationKeys.RESTART_NO_DETAIL)
            },
            "always": {
                "description": cli_translations.get_text(TranslationKeys.RESTART_ALWAYS),
                "detail": cli_translations.get_text(TranslationKeys.RESTART_ALWAYS_DETAIL)
            },
            "on-failure": {
                "description": cli_translations.get_text(TranslationKeys.RESTART_ON_FAILURE),
                "detail": cli_translations.get_text(TranslationKeys.RESTART_ON_FAILURE_DETAIL)
            },
            "on-abnormal": {
                "description": cli_translations.get_text(TranslationKeys.RESTART_ON_ABNORMAL),
                "detail": cli_translations.get_text(TranslationKeys.RESTART_ON_ABNORMAL_DETAIL)
            }
        }

        restart_choices = [
            f"{key} - {value['description']}" for key, value in restart_options.items()
        ] + [cli_translations.get_text(TranslationKeys.BACK), cli_translations.get_text(TranslationKeys.QUIT)]

        print("\n" + cli_translations.get_text(TranslationKeys.RESTART_CONFIGURATION))
        for key, value in restart_options.items():
            print(f"  • {key}: {value['detail']}")

        choice = questionary.select(
            cli_translations.get_text(TranslationKeys.CHOOSE_RESTART_POLICY),
            choices=restart_choices
        ).ask()

        if choice == cli_translations.get_text(TranslationKeys.QUIT):
            if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
            return self.finalize_service(service)
        elif choice == cli_translations.get_text(TranslationKeys.BACK):
            return None

        service.service.restart = choice.split(" - ")[0]

        if service.service.restart != "no":
            print("\n" + cli_translations.get_text(TranslationKeys.RESTART_LIMITS_TITLE))
            start_limit = questionary.text(
                cli_translations.get_text(TranslationKeys.RESTART_LIMITS_MAX_RESTARTS),
                default="3",
                validate=lambda v: v.isdigit() and int(v) >= 0,
                instruction=cli_translations.get_text(TranslationKeys.RESTART_LIMITS_DEFAULT).format(default="3")
            ).ask()

            if start_limit:
                service.unit.start_limit_burst = int(start_limit)
                service.unit.start_limit_interval = 300

            restart_delay = questionary.text(
                cli_translations.get_text(TranslationKeys.RESTART_LIMITS_DELAY),
                default="5",
                validate=lambda v: v.isdigit() and int(v) >= 0,
                instruction=cli_translations.get_text(TranslationKeys.RESTART_LIMITS_DEFAULT).format(default="5")
            ).ask()
            if restart_delay:
                service.service.restart_sec = int(restart_delay)

        service.install.wanted_by = ["multi-user.target"]

        print("\n" + cli_translations.get_text(TranslationKeys.FINAL_CONFIGURATION_COMPLETED))
        
        print("\n💾 " + cli_translations.get_text(TranslationKeys.SAVE_CONFIGURATION))
        try:
            self.save_service_config(service)
            print(cli_translations.get_text(TranslationKeys.CONFIGURATION_SAVED))
        except Exception as e:
            print(cli_translations.get_text(TranslationKeys.ERROR_SAVING) + f" {str(e)}")
            return None

        if questionary.confirm(cli_translations.get_text(TranslationKeys.WANT_TO_INSTALL_SERVICE_NOW)).ask():
            try:
                self.install_service(service)
                print(cli_translations.get_text(TranslationKeys.SERVICE_INSTALLED_SUCCESSFULLY))
            except Exception as e:
                print(cli_translations.get_text(TranslationKeys.INSTALLATION_ERROR) + f" {str(e)}")
                return None

        return service

    def install_service(self, service: ServiceModel):
        """
        Install a service into systemd.
        Creates service file, enables it, and optionally starts it.

        Args:
            service (ServiceModel): The service model to install

        Returns:
            bool: True if installation successful, False otherwise
        """
        service_path = f"/etc/systemd/system/{service.name}.service"
        
        self.request_sudo(cli_translations.get_text("installer le service"))
        
        try:
            with open(service_path, 'w') as f:
                f.write(service.to_systemd_file())
            print(cli_translations.get_text("✅ Fichier service créé"))
            
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            print(cli_translations.get_text("✅ Configuration systemd rechargée"))
            
            if service.install.wanted_by:
                subprocess.run(['systemctl', 'enable', service.name], check=True)
                print(cli_translations.get_text("✅ Service activé au démarrage"))
            
            if questionary.confirm(cli_translations.get_text("Voulez-vous démarrer le service maintenant ?")).ask():
                subprocess.run(['systemctl', 'start', service.name], check=True)
                print(cli_translations.get_text("✅ Service démarré"))
                
                status = subprocess.run(['systemctl', 'is-active', service.name], 
                                     capture_output=True, text=True).stdout.strip()
                if status == 'active':
                    print("✨ " + cli_translations.get_text("Service en cours d'exécution"))
                else:
                    print("⚠️  " + cli_translations.get_text("Le service est installé mais n'est pas actif"))
                    print("📜 " + cli_translations.get_text("Consultation des logs :"))
                    os.system(f"journalctl -u {service.name} -n 50 --no-pager")

            return True

        except subprocess.CalledProcessError as e:
            print(cli_translations.get_text(TranslationKeys.INSTALLATION_ERROR) + f" {str(e)}")
            return False
        except Exception as e:
            print(cli_translations.get_text(TranslationKeys.UNEXPECTED_ERROR) + f" {str(e)}")
            return False

    def manage_services(self):
        """
        Display and handle the service management interface.
        Allows users to select and manage existing services through
        various operations like start, stop, restart, edit, etc.
        """
        while True:
            services = [f for f in os.listdir(self.services_dir) if f.endswith('.json')]
            
            if not services:
                print(cli_translations.get_text(TranslationKeys.MSG_NO_SERVICES))
                return

            choices = services + [
                cli_translations.get_text(TranslationKeys.BACK),
                cli_translations.get_text(TranslationKeys.QUIT)
            ]
            
            service_choice = questionary.select(
                cli_translations.get_text(TranslationKeys.MSG_CHOOSE_SERVICE),
                choices=choices
            ).ask()

            if service_choice == cli_translations.get_text(TranslationKeys.QUIT):
                if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                    sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
                continue
            elif service_choice == cli_translations.get_text(TranslationKeys.BACK):
                return

            action_keys = {
                "start": TranslationKeys.START_SERVICE,
                "stop": TranslationKeys.STOP_SERVICE,
                "restart": TranslationKeys.RESTART_SERVICE,
                "status": TranslationKeys.VIEW_STATUS,
                "logs": TranslationKeys.VIEW_LOGS,
                "edit": TranslationKeys.EDIT_SERVICE_ACTION,
                "delete": TranslationKeys.DELETE_SERVICE_ACTION,
                "back": TranslationKeys.BACK,
                "quit": TranslationKeys.QUIT
            }
            
            actions = [cli_translations.get_text(key) for key in action_keys.values()]
            
            action = questionary.select(
                cli_translations.get_text(TranslationKeys.MSG_CHOOSE_ACTION),
                choices=actions
            ).ask()

            service_name = service_choice.replace('.json', '')

            if action == cli_translations.get_text(TranslationKeys.START_SERVICE):
                self.start_service(service_name)
            elif action == cli_translations.get_text(TranslationKeys.STOP_SERVICE):
                self.stop_service(service_name)
            elif action == cli_translations.get_text(TranslationKeys.RESTART_SERVICE):
                self.restart_service(service_name)
            elif action == cli_translations.get_text(TranslationKeys.VIEW_STATUS):
                os.system(f"systemctl status {service_name}")
            elif action == cli_translations.get_text(TranslationKeys.VIEW_LOGS):
                os.system(f"journalctl -u {service_name} -n 50 --no-pager")
            elif action == cli_translations.get_text(TranslationKeys.EDIT_SERVICE_ACTION):
                self.edit_service(service_name)
            elif action == cli_translations.get_text(TranslationKeys.DELETE_SERVICE_ACTION):
                self.delete_service(service_name)

    def edit_service(self, service_name: str):
        """
        Edit an existing service configuration.
        Provides interface to modify Unit, Service, and Install sections.

        Args:
            service_name (str): Name of the service to edit
        """
        config_path = os.path.join(self.services_dir, f"{service_name}.json")
        service = ServiceModel.load_from_json(config_path)
        
        sections = {
            "unit": cli_translations.get_text(TranslationKeys.EDIT_SECTION_UNIT),
            "service": cli_translations.get_text(TranslationKeys.EDIT_SECTION_SERVICE),
            "install": cli_translations.get_text(TranslationKeys.EDIT_SECTION_INSTALL),
            "save": cli_translations.get_text(TranslationKeys.EDIT_SAVE_CHANGES),
            "back": cli_translations.get_text(TranslationKeys.BACK),
            "quit": cli_translations.get_text(TranslationKeys.QUIT)
        }
        
        while True:
            section_choices = list(sections.values())
            section = questionary.select(
                cli_translations.get_text(TranslationKeys.EDIT_SECTION_TITLE),
                choices=section_choices
            ).ask()

            if section == cli_translations.get_text(TranslationKeys.QUIT):
                if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                    sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
                continue
            elif section == cli_translations.get_text(TranslationKeys.BACK):
                return

            if section == sections["unit"]:
                self.edit_unit_section(service)
            elif section == sections["service"]:
                self.edit_service_section(service)
            elif section == sections["install"]:
                self.edit_install_section(service)
            elif section == sections["save"]:
                self.save_service_changes(service)
                return

    def save_service_changes(self, service: ServiceModel):
        """
        Save and apply changes made to a service configuration.
        Updates both the service file and JSON configuration.

        Args:
            service (ServiceModel): The modified service model to save
        """
        try:
            print(f"📥 " + cli_translations.get_text("Arrêt du service {name}...").format(name=service.name))
            
            os.system(f"systemctl stop {service.name}")
            
            service_path = f"/etc/systemd/system/{service.name}.service"
            with open(service_path, 'w') as f:
                f.write(service.to_systemd_file())
                
            json_path = os.path.join(self.services_dir, f"{service.name}.json")
            service.save_to_json(json_path)
            
            os.system("systemctl daemon-reload")
            os.system(f"systemctl restart {service.name}")
            
            print(cli_translations.get_text(TranslationKeys.SERVICE_UPDATED_AND_RESTARTED).format(name=service.name))
            
        except Exception as e:
            print(cli_translations.get_text(TranslationKeys.ERROR_SAVING) + f" {e}")

    def delete_service(self, service_name: str):
        """
        Delete a service completely from the system.
        Stops, disables, and removes all service files and configurations.

        Args:
            service_name (str): Name of the service to delete
        """
        if questionary.confirm(
            cli_translations.get_text(TranslationKeys.CONFIRM_DELETE_SERVICE).format(name=service_name)
        ).ask():
            print(cli_translations.get_text(TranslationKeys.STOPPING_SERVICE).format(name=service_name))
            
            os.system(f"systemctl stop {service_name}")
            
            print(cli_translations.get_text(TranslationKeys.DISABLING_SERVICE).format(name=service_name))
            os.system(f"systemctl disable {service_name}")
            
            service_path = f"/etc/systemd/system/{service_name}.service"
            if os.path.exists(service_path):
                os.remove(service_path)
                print(cli_translations.get_text(TranslationKeys.SERVICE_FILE_DELETED).format(path=service_path))
            
            json_path = os.path.join(self.services_dir, f"{service_name}.json")
            if os.path.exists(json_path):
                os.remove(json_path)
                print(cli_translations.get_text(TranslationKeys.CONFIG_FILE_DELETED).format(path=json_path))
            
            os.system("systemctl daemon-reload")
            print(cli_translations.get_text(TranslationKeys.SERVICE_DELETED).format(name=service_name))

    def get_system_users(self) -> List[str]:
        """
        Get list of system users with UID >= 1000.
        Excludes system users and 'nobody'.

        Returns:
            List[str]: List of valid system usernames
        """
        users = []
        try:
            with open('/etc/passwd', 'r') as f:
                for line in f:
                    user_info = line.strip().split(':')
                    if (len(user_info) >= 3 and 
                        user_info[2].isdigit() and 
                        int(user_info[2]) >= 1000 and 
                        user_info[0] != 'nobody'):
                        users.append(user_info[0])
            return sorted(users)
        except Exception as e:
            print(f"⚠️  " + cli_translations.get_text(TranslationKeys.ERROR_READING_USERS) + f" {e}")
            return []

    def get_user_config(self) -> Optional[tuple]:
        """
        Guide user through service user configuration.
        Allows selection between root and current user.

        Returns:
            Optional[tuple]: Tuple of (username, group) or None if cancelled
        """
        try:
            current_user = os.getenv('SUDO_USER', os.getenv('USER'))
            choices = ["root", current_user]
            
            choice = self.handle_step_navigation(
                cli_translations.get_text(TranslationKeys.SELECT_USER_TO_RUN_SERVICE),
                sorted(set(choices))
            )
            if choice is None:
                return None
            
            return choice, ""
            
        except Exception as e:
            print(f"⚠️  " + cli_translations.get_text(TranslationKeys.ERROR_USER_CONFIGURATION) + f" {e}")
            return None

    def browse_directory(self, start_path: str = "/"):
        """
        Provide interactive directory browser interface.
        Allows navigation through filesystem to select working directory.

        Args:
            start_path (str): Initial directory path to start browsing from

        Returns:
            Optional[str]: Selected directory path or None if cancelled
        """
        current_path = start_path
        
        while True:
            try:
                items = [".."] + sorted([
                    f"📁 {d}"
                    for d in os.listdir(current_path)
                    if os.path.isdir(os.path.join(current_path, d))
                    and not d.startswith('.')
                ])
                
                print(f"\n{cli_translations.get_text(TranslationKeys.CURRENT_DIRECTORY)} {current_path}")
                choice = questionary.select(
                    cli_translations.get_text(TranslationKeys.SELECT_DIRECTORY),
                    choices=items + [
                        cli_translations.get_text(TranslationKeys.SELECT_THIS_DIRECTORY),
                        cli_translations.get_text(TranslationKeys.BACK),
                        cli_translations.get_text(TranslationKeys.QUIT)
                    ]
                ).ask()
                
                if choice == cli_translations.get_text(TranslationKeys.QUIT):
                    sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
                elif choice == cli_translations.get_text(TranslationKeys.BACK):
                    return None
                elif choice == cli_translations.get_text(TranslationKeys.SELECT_THIS_DIRECTORY):
                    return current_path
                elif choice == "..":
                    if current_path != "/":
                        current_path = os.path.dirname(current_path)
                else:
                    folder_name = choice[2:]
                    current_path = os.path.join(current_path, folder_name)
                    
            except PermissionError:
                print("⚠️  Accès refusé à ce dossier")
                current_path = os.path.dirname(current_path)

    def check_screen_installed(self) -> bool:
        """
        Check if GNU Screen is installed on the system.

        Returns:
            bool: True if screen is installed, False otherwise
        """
        try:
            result = subprocess.run(['which', 'screen'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception:
            return False

    def get_exec_command(self, service: ServiceModel = None):
        """
        Guide user through execution command configuration.
        Allows selecting executable file or manual command entry.
        Supports GNU Screen integration if available.

        Args:
            service (ServiceModel, optional): Service model for context

        Returns:
            Optional[str]: Configured execution command or None if cancelled
        """
        try:
            base_command = None
            
            method = questionary.select(
                cli_translations.get_text(TranslationKeys.SPECIFY_COMMAND_METHOD),
                choices=[
                    cli_translations.get_text(TranslationKeys.SELECT_EXECUTABLE_FILE),
                    cli_translations.get_text(TranslationKeys.ENTER_COMMAND_MANUALLY),
                    cli_translations.get_text(TranslationKeys.BACK),
                    cli_translations.get_text(TranslationKeys.QUIT)
                ]
            ).ask()

            if method == cli_translations.get_text(TranslationKeys.QUIT):
                if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                    sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
                return self.get_exec_command(service)
            elif method == cli_translations.get_text(TranslationKeys.BACK):
                return None

            if method == cli_translations.get_text(TranslationKeys.SELECT_EXECUTABLE_FILE):
                working_dir = service.service.working_directory
                executables = []
                try:
                    print(f"\n{cli_translations.get_text(TranslationKeys.SEARCH_EXECUTABLE_FILES)} {working_dir}")
                    for item in os.listdir(working_dir):
                        full_path = os.path.join(working_dir, item)
                        if os.path.isfile(full_path):
                            if os.access(full_path, os.X_OK):
                                executables.append(item)
                            elif item.endswith(('.sh', '.py', '.bash', '.js')):
                                executables.append(item)
                except Exception as e:
                    print(f"⚠️  {cli_translations.get_text(TranslationKeys.ERROR_READING_DIRECTORY)}: {e}")
                    return None

                if not executables:
                    print(f"⚠️  {cli_translations.get_text(TranslationKeys.NO_EXECUTABLE_FILES_FOUND)} {working_dir}")
                    return None

                executables += [
                    cli_translations.get_text(TranslationKeys.BACK),
                    cli_translations.get_text(TranslationKeys.QUIT)
                ]

                choice = questionary.select(
                    cli_translations.get_text(TranslationKeys.SELECT_EXECUTABLE_FILE),
                    choices=executables
                ).ask()

                if choice == cli_translations.get_text(TranslationKeys.QUIT):
                    if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                        sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
                    return self.get_exec_command(service)
                elif choice == cli_translations.get_text(TranslationKeys.BACK):
                    return None

                base_command = choice

            elif method == cli_translations.get_text(TranslationKeys.ENTER_COMMAND_MANUALLY):
                base_command = questionary.text(
                    cli_translations.get_text(TranslationKeys.ENTER_EXECUTION_COMMAND),
                    instruction=cli_translations.get_text(TranslationKeys.EXAMPLE_COMMAND)
                ).ask()

                if not base_command:
                    return None

            if self.check_screen_installed():
                use_screen = questionary.confirm(
                    cli_translations.get_text(TranslationKeys.RUN_SERVICE_IN_SCREEN)
                ).ask()
                
                if use_screen:
                    screen_name = service.name if service else "my_service"
                    base_command = f"screen -dmS {screen_name} {base_command}"

            return base_command

        except Exception as e:
            print(f"⚠️  Erreur lors de la configuration de la commande: {e}")
            return None

    def configure_timer(self):
        """
        Configure systemd timer settings for the service.
        Allows setting up delayed start, intervals, or specific times.

        Returns:
            Optional[str]: Timer configuration string or None if cancelled
        """
        use_timer = questionary.confirm(cli_translations.get_text("Voulez-vous configurer un timer ?")).ask()
        
        if not use_timer:
            return None
        
        timer_type = questionary.select(
            cli_translations.get_text("Type de timer :"),
            choices=[
                cli_translations.get_text("Délai après le démarrage"),
                cli_translations.get_text("Intervalle régulier"),
                cli_translations.get_text("Heure spécifique")
            ]
        ).ask()
        
        if timer_type == cli_translations.get_text("Délai après le démarrage"):
            seconds = questionary.text(
                cli_translations.get_text("Délai en secondes :"),
                validate=lambda text: text.isdigit()
            ).ask()
            return f"OnBootSec={seconds}s"
        elif timer_type == cli_translations.get_text("Intervalle régulier"):
            seconds = questionary.text(
                cli_translations.get_text("Intervalle en secondes :"),
                validate=lambda text: text.isdigit()
            ).ask()
            return f"OnUnitActiveSec={seconds}s"
        else:
            time = questionary.text(
                cli_translations.get_text("Heure (format HH:MM) :"),
                validate=lambda text: len(text.split(':')) == 2
            ).ask()
            return f"OnCalendar=*-*-* {time}:00"

    def save_service_config(self, service: ServiceModel):
        """
        Save service configuration to JSON file.
        Also logs the save action with timestamp.

        Args:
            service (ServiceModel): Service model to save
        """
        config_path = os.path.join(self.services_dir, f"{service.name}.json")
        service.save_to_json(config_path)
        
        log_path = os.path.join(self.logs_dir, f"{service.name}.log")
        with open(log_path, 'a') as f:
            f.write(f"{datetime.now()}: Service configuration saved\n")
    
    def get_service_status(self, service_name: str) -> dict:
        """
        Get comprehensive status information for a service.

        Args:
            service_name (str): Name of the service to check

        Returns:
            dict: Dictionary containing service status information
        """
        status = {
            'active': subprocess.getoutput(f"systemctl is-active {service_name}"),
            'enabled': subprocess.getoutput(f"systemctl is-enabled {service_name}"),
            'status': subprocess.getoutput(f"systemctl status {service_name}"),
            'config': os.path.join(self.services_dir, f"{service_name}.json"),
            'log': os.path.join(self.logs_dir, f"{service_name}.log")
        }
        return status

    def signal_handler(self, sig, frame):
        """
        Handle system signals (SIGINT, SIGTERM).
        Ensures clean exit when user interrupts program.

        Args:
            sig: Signal number
            frame: Current stack frame
        """
        print("\n\n👋 " + cli_translations.get_text(TranslationKeys.GOODBYE))
        sys.exit(0)

    def handle_navigation_choice(self, choice: str, return_callback=None):
        """
        Handle navigation choices in menus.
        Manages quit and back operations consistently.

        Args:
            choice (str): User's choice
            return_callback (callable, optional): Callback for 'back' action

        Returns:
            bool: True to continue, False to go back
        """
        if choice == cli_translations.get_text(TranslationKeys.QUIT):
            if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
            return False
        elif choice == cli_translations.get_text(TranslationKeys.BACK) and return_callback:
            return_callback()
            return False
        return True

    def validate_service_name(self, name: str) -> bool:
        """
        Validate service name format.
        Ensures name contains only alphanumeric characters, hyphens, and underscores.

        Args:
            name (str): Service name to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not name:
            return False
        return all(c.isalnum() or c in '-_' for c in name)

    def get_service_name(self):
        """
        Guide user through service name input.
        Validates input and handles navigation options.

        Returns:
            Optional[str]: Valid service name or None if cancelled
        """
        while True:
            print("\n" + cli_translations.get_text(TranslationKeys.CREATE_NEW_SERVICE))
            name = questionary.text(
                cli_translations.get_text(TranslationKeys.SERVICE_NAME),
                instruction=cli_translations.get_text(TranslationKeys.ENTER_SERVICE_NAME_INSTRUCTION)
            ).ask()
            
            if not name:
                continue
            elif name.lower() == 'q':
                if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                    sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
            elif name.lower() == 'b':
                return None
            elif self.validate_service_name(name):
                return name
            else:
                print(cli_translations.get_text(TranslationKeys.INVALID_NAME))

    def get_service_description(self):
        """
        Guide user through service description input.
        Handles navigation options.

        Returns:
            Optional[str]: Service description or None if cancelled
        """
        print("\n" + cli_translations.get_text(TranslationKeys.DESCRIPTION))
        description = questionary.text(
            cli_translations.get_text(TranslationKeys.DESCRIPTION),
            instruction=cli_translations.get_text(TranslationKeys.ENTER_SERVICE_DESCRIPTION_INSTRUCTION)
        ).ask()
        
        if description.lower() == 'q':
            if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
            return self.get_service_description()
        elif description.lower() == 'b':
            return None
        return description

    def handle_step_navigation(self, question_text: str, choices: list) -> Optional[str]:
        """
        Handle navigation in multi-step processes.
        Provides consistent navigation options across different steps.

        Args:
            question_text (str): Question to display
            choices (list): List of available choices

        Returns:
            Optional[str]: Selected choice or None if cancelled/back
        """
        nav_choices = choices + [
            cli_translations.get_text(TranslationKeys.BACK),
            cli_translations.get_text(TranslationKeys.QUIT)
        ]
        
        choice = questionary.select(
            question_text,
            choices=nav_choices
        ).ask()
        
        if choice == cli_translations.get_text(TranslationKeys.QUIT):
            if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
            return self.handle_step_navigation(question_text, choices)
        
        elif choice == cli_translations.get_text(TranslationKeys.BACK):
            return None
        
        return choice

    def get_service_type(self) -> Optional[str]:
        """
        Guide user through service type selection.
        Provides detailed descriptions for each service type.

        Returns:
            Optional[str]: Selected service type or None if cancelled
        """
        print("\n" + cli_translations.get_text(TranslationKeys.CONFIGURE_SERVICE_TYPE))
        service_types = [
            cli_translations.get_text(TranslationKeys.SIMPLE_TYPE),
            cli_translations.get_text(TranslationKeys.FORKING_TYPE),
            cli_translations.get_text(TranslationKeys.ONESHOT_TYPE),
            cli_translations.get_text(TranslationKeys.NOTIFY_TYPE)
        ]
        
        choice = questionary.select(
            cli_translations.get_text(TranslationKeys.SERVICE_TYPE),
            choices=service_types + [cli_translations.get_text(TranslationKeys.BACK), cli_translations.get_text(TranslationKeys.QUIT)]
        ).ask()
        
        if choice == cli_translations.get_text(TranslationKeys.QUIT):
            if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
            return self.get_service_type()
        elif choice == cli_translations.get_text(TranslationKeys.BACK):
            return None
        
        return choice.split(" - ")[0].strip()

    def get_working_directory(self):
        """
        Guide user through working directory selection.
        Allows browsing or manual path entry.

        Returns:
            Optional[str]: Selected working directory path or None if cancelled
        """
        while True:
            choices = [
                cli_translations.get_text(TranslationKeys.BROWSE_DIRECTORIES),
                cli_translations.get_text(TranslationKeys.ENTER_PATH_MANUALLY),
                cli_translations.get_text(TranslationKeys.BACK),
                cli_translations.get_text(TranslationKeys.QUIT)
            ]
            
            choice = questionary.select(
                cli_translations.get_text(TranslationKeys.DEFINE_WORKING_DIRECTORY),
                choices=choices
            ).ask()
            
            if choice == cli_translations.get_text(TranslationKeys.BROWSE_DIRECTORIES):
                directory = self.browse_directory()
                if directory:
                    return directory
            
            elif choice == cli_translations.get_text(TranslationKeys.ENTER_PATH_MANUALLY):
                directory = questionary.text(
                    cli_translations.get_text(TranslationKeys.ENTER_FULL_DIRECTORY_PATH)
                ).ask()
                
                if not directory:
                    continue
                
                directory = os.path.expanduser(directory)
                directory = os.path.abspath(directory)
                
                if not os.path.exists(directory):
                    print(f"⚠️  " + cli_translations.get_text("Le dossier {directory} n'existe pas").format(directory=directory))
                    continue
                
                if not os.path.isdir(directory):
                    print(f"⚠️  " + cli_translations.get_text("{directory} n'est pas un dossier").format(directory=directory))
                    continue
                
                return directory
            
            elif choice == cli_translations.get_text(TranslationKeys.BACK):
                return None
            
            else:
                sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))

    def stop_service(self, service_name: str):
        """
        Stop a running service.
        Checks service status and displays relevant logs.

        Args:
            service_name (str): Name of the service to stop
        """
        try:
            status = os.system(f"systemctl is-active --quiet {service_name}")
            
            if status != 0:
                print(f"⚠️  " + cli_translations.get_text("Le service {name} n'est pas actif").format(name=service_name))
                return
            
            print(f"📥 " + cli_translations.get_text("Arrêt du service {name}...").format(name=service_name))
            
            if os.system(f"systemctl stop {service_name}") == 0:
                print(cli_translations.get_text(TranslationKeys.SERVICE_STOPPED_SUCCESSFULLY).format(name=service_name))
                
                print("\n📊 " + cli_translations.get_text("Statut actuel du service :"))
                os.system(f"systemctl status {service_name}")
            else:
                print(cli_translations.get_text(TranslationKeys.ERROR_STOPPING_SERVICE) + f" {service_name}")
                
                print("\n📜 " + cli_translations.get_text("Derniers logs du service :"))
                os.system(f"journalctl -u {service_name} -n 20 --no-pager")
            
        except Exception as e:
            print(cli_translations.get_text(TranslationKeys.UNEXPECTED_ERROR) + f" {e}")

    def start_service(self, service_name: str):
        """
        Start a stopped service.
        Checks service status and displays relevant logs.

        Args:
            service_name (str): Name of the service to start
        """
        try:
            status = os.system(f"systemctl is-active --quiet {service_name}")
            
            if status == 0:
                print(f"⚠️  " + cli_translations.get_text("Le service {name} est déjà actif").format(name=service_name))
                return
            
            print(f"🚀 " + cli_translations.get_text("Démarrage du service {name}...").format(name=service_name))
            
            if os.system(f"systemctl start {service_name}") == 0:
                print(cli_translations.get_text(TranslationKeys.SERVICE_STARTED_SUCCESSFULLY).format(name=service_name))
                
                print("\n📊 " + cli_translations.get_text("Statut actuel du service :"))
                os.system(f"systemctl status {service_name}")
                
                print("\n📜 " + cli_translations.get_text("Logs de démarrage :"))
                os.system(f"journalctl -u {service_name} -n 20 --no-pager")
            else:
                print(cli_translations.get_text(TranslationKeys.ERROR_STARTING_SERVICE) + f" {service_name}")
                
                print("\n📜 " + cli_translations.get_text("Logs d'erreur :"))
                os.system(f"journalctl -u {service_name} -n 50 --no-pager")
            
        except Exception as e:
            print(cli_translations.get_text(TranslationKeys.UNEXPECTED_ERROR) + f" {e}")

    def restart_service(self, service_name: str):
        """
        Restart a service.
        Performs full restart and displays status and logs.

        Args:
            service_name (str): Name of the service to restart
        """
        try:
            print(f"🔄 " + cli_translations.get_text("Redémarrage du service {name}...").format(name=service_name))
            
            if os.system(f"systemctl restart {service_name}") == 0:
                print(cli_translations.get_text(TranslationKeys.SERVICE_RESTARTED_SUCCESSFULLY).format(name=service_name))
                
                print("\n📊 " + cli_translations.get_text("Statut actuel du service :"))
                os.system(f"systemctl status {service_name}")
                
                print("\n📜 " + cli_translations.get_text("Logs de redémarrage :"))
                os.system(f"journalctl -u {service_name} -n 20 --no-pager")
            else:
                print(cli_translations.get_text(TranslationKeys.ERROR_RESTARTING_SERVICE) + f" {service_name}")
                
                print("\n📜 " + cli_translations.get_text("Logs d'erreur détaillés :"))
                os.system(f"journalctl -u {service_name} -n 50 --no-pager")
                
                print("\n🔍 " + cli_translations.get_text("État détaillé du service :"))
                os.system(f"systemctl status {service_name} --no-pager")
                
        except Exception as e:
            print(cli_translations.get_text(TranslationKeys.UNEXPECTED_ERROR) + f" {e}")

    def change_language(self):
        """
        Change the language of the CLI interface.
        Allows switching between English and French.

        Returns:
            None
        """
        french_choice = cli_translations.get_text(TranslationKeys.FRENCH)
        english_choice = cli_translations.get_text(TranslationKeys.ENGLISH)
        
        choices = [french_choice, english_choice]
        choice = questionary.select(
            cli_translations.get_text(TranslationKeys.CHOOSE_LANGUAGE),
            choices=choices
        ).ask()
        
        if choice == french_choice:
            cli_translations.set_locale("fr")
        else:
            cli_translations.set_locale("en")
        
        return self.main_menu()

    def edit_unit_section(self, service: ServiceModel):
        """
        Edit the Unit section of a service configuration.
        Provides interface to modify description, documentation, and start limits.

        Args:
            service (ServiceModel): The service model to edit
        """
        while True:
            choices = [
                cli_translations.get_text(TranslationKeys.EDIT_DESCRIPTION),
                cli_translations.get_text(TranslationKeys.EDIT_DOCUMENTATION),
                cli_translations.get_text(TranslationKeys.EDIT_START_LIMIT_INTERVAL),
                cli_translations.get_text(TranslationKeys.EDIT_START_LIMIT_BURST),
                cli_translations.get_text(TranslationKeys.BACK),
                cli_translations.get_text(TranslationKeys.QUIT)
            ]

            choice = questionary.select(
                cli_translations.get_text(TranslationKeys.WHAT_DO_YOU_WANT_TO_MODIFY),
                choices=choices
            ).ask()

            if choice == cli_translations.get_text(TranslationKeys.QUIT):
                if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                    sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
                continue
            elif choice == cli_translations.get_text(TranslationKeys.BACK):
                return

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_DESCRIPTION):
                print(cli_translations.get_text(TranslationKeys.EDIT_CURRENT_VALUE).format(
                    value=service.unit.description))
                description = questionary.text(
                    cli_translations.get_text(TranslationKeys.EDIT_ENTER_NEW_VALUE),
                    default=service.unit.description
                ).ask()
                if description:
                    service.unit.description = description

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_DOCUMENTATION):
                print(cli_translations.get_text(TranslationKeys.EDIT_CURRENT_VALUE).format(
                    value=service.unit.documentation))
                documentation = questionary.text(
                    cli_translations.get_text(TranslationKeys.EDIT_URLS_SPACE_SEPARATED),
                    default=service.unit.documentation
                ).ask()
                if documentation:
                    service.unit.documentation = documentation

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_START_LIMIT_INTERVAL):
                print(cli_translations.get_text(TranslationKeys.EDIT_CURRENT_VALUE).format(
                    value=service.unit.start_limit_interval))
                interval = questionary.text(
                    cli_translations.get_text(TranslationKeys.EDIT_RESTART_INTERVAL),
                    default=str(service.unit.start_limit_interval),
                    validate=lambda v: v.isdigit() and int(v) >= 0
                ).ask()
                if interval and interval.isdigit():
                    service.unit.start_limit_interval = int(interval)

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_START_LIMIT_BURST):
                print(cli_translations.get_text(TranslationKeys.EDIT_CURRENT_VALUE).format(
                    value=service.unit.start_limit_burst))
                burst = questionary.text(
                    cli_translations.get_text(TranslationKeys.EDIT_RESTART_ATTEMPTS),
                    default=str(service.unit.start_limit_burst),
                    validate=lambda v: v.isdigit() and int(v) >= 0
                ).ask()
                if burst and burst.isdigit():
                    service.unit.start_limit_burst = int(burst)

    def edit_service_section(self, service: ServiceModel):
        """
        Edit the Service section of a service configuration.
        Provides interface to modify user, group, working directory,
        service type, start command, stop command, restart policy,
        and restart delay.

        Args:
            service (ServiceModel): The service model to edit
        """
        while True:
            choices = [
                cli_translations.get_text(TranslationKeys.EDIT_USER),
                cli_translations.get_text(TranslationKeys.EDIT_GROUP),
                cli_translations.get_text(TranslationKeys.EDIT_WORKING_DIR),
                cli_translations.get_text(TranslationKeys.EDIT_SERVICE_TYPE),
                cli_translations.get_text(TranslationKeys.EDIT_START_COMMAND),
                cli_translations.get_text(TranslationKeys.EDIT_STOP_COMMAND),
                cli_translations.get_text(TranslationKeys.EDIT_RESTART_POLICY),
                cli_translations.get_text(TranslationKeys.EDIT_RESTART_DELAY),
                cli_translations.get_text(TranslationKeys.EDIT_MAX_RESTARTS),
                cli_translations.get_text(TranslationKeys.BACK),
                cli_translations.get_text(TranslationKeys.QUIT)
            ]

            choice = questionary.select(
                cli_translations.get_text("Que souhaitez-vous modifier ?"),
                choices=choices
            ).ask()

            if choice == cli_translations.get_text(TranslationKeys.QUIT):
                sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
            elif choice == cli_translations.get_text(TranslationKeys.BACK):
                return

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_USER):
                user = questionary.text(
                    cli_translations.get_text("Utilisateur :"),
                    default=service.service.user
                ).ask()
                if user:
                    service.service.user = user

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_GROUP):
                group = questionary.text(
                    cli_translations.get_text("Groupe :"),
                    default=service.service.group
                ).ask()
                if group:
                    service.service.group = group

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_WORKING_DIR):
                working_dir = self.get_working_directory()
                if working_dir:
                    service.service.working_directory = working_dir

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_SERVICE_TYPE):
                service_type = self.get_service_type()
                if service_type:
                    service.service.type = service_type

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_START_COMMAND):
                exec_start = questionary.text(
                    cli_translations.get_text("Commande de démarrage :"),
                    default=service.service.exec_start
                ).ask()
                if exec_start:
                    service.service.exec_start = exec_start

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_STOP_COMMAND):
                exec_stop = questionary.text(
                    cli_translations.get_text("Commande d'arrêt :"),
                    default=service.service.exec_stop
                ).ask()
                if exec_stop:
                    service.service.exec_stop = exec_stop

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_RESTART_POLICY):
                restart_choices = [
                    "no",
                    "always",
                    "on-success",
                    "on-failure",
                    "on-abnormal",
                    "on-abort",
                    "on-watchdog"
                ]
                restart = questionary.select(
                    cli_translations.get_text("Politique de redémarrage :"),
                    choices=restart_choices,
                    default=service.service.restart
                ).ask()
                if restart:
                    service.service.restart = restart

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_RESTART_DELAY):
                restart_sec = questionary.text(
                    cli_translations.get_text("Délai de redémarrage (en secondes) :"),
                    default=str(service.service.restart_sec)
                ).ask()
                if restart_sec and restart_sec.isdigit():
                    service.service.restart_sec = int(restart_sec)

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_MAX_RESTARTS):
                max_restarts = questionary.text(
                    cli_translations.get_text("Nombre maximum de redémarrages :"),
                    default=str(service.unit.start_limit_burst)
                ).ask()
                if max_restarts and max_restarts.isdigit():
                    service.unit.start_limit_burst = int(max_restarts)

    def get_start_delay(self) -> Optional[str]:
        """
        Get the start delay for the service.
        Handles input validation and default value.

        Returns:
            Optional[str]: Start delay or None if cancelled
        """
        start_delay = questionary.text(
            cli_translations.get_text(TranslationKeys.START_DELAY),
            validate=lambda text: text.isdigit() or text == "",
            default="0"
        ).ask()

        if start_delay.isdigit():
            return start_delay
        else:
            print(cli_translations.get_text("Entrée invalide pour le délai de démarrage."))
            return None

    def get_max_restarts(self) -> Optional[str]:
        """
        Get the maximum number of restarts for the service.
        Handles input validation and default value.

        Returns:
            Optional[str]: Maximum restarts or None if cancelled
        """
        print("\n" + cli_translations.get_text(TranslationKeys.RESTART_LIMITS_TITLE))
        max_restarts = questionary.text(
            cli_translations.get_text(TranslationKeys.RESTART_LIMITS_MAX_RESTARTS) + " " +
            cli_translations.get_text(TranslationKeys.RESTART_LIMITS_DEFAULT).format(default="3"),
            validate=lambda text: text.isdigit() or text == "",
            default="3"
        ).ask()

        if max_restarts.isdigit():
            return max_restarts
        else:
            print(cli_translations.get_text(TranslationKeys.INVALID_INPUT_FOR_MAX_RESTARTS))
            return None

    def edit_install_section(self, service: ServiceModel):
        """
        Edit the Install section of a service configuration.
        Provides interface to modify wanted by, required by, and also fields.

        Args:
            service (ServiceModel): The service model to edit
        """
        while True:
            choices = [
                cli_translations.get_text(TranslationKeys.EDIT_WANTED_BY),
                cli_translations.get_text(TranslationKeys.EDIT_REQUIRED_BY),
                cli_translations.get_text(TranslationKeys.EDIT_ALSO),
                cli_translations.get_text(TranslationKeys.BACK),
                cli_translations.get_text(TranslationKeys.QUIT)
            ]

            choice = questionary.select(
                cli_translations.get_text(TranslationKeys.WHAT_DO_YOU_WANT_TO_MODIFY),
                choices=choices
            ).ask()

            if choice == cli_translations.get_text(TranslationKeys.QUIT):
                if questionary.confirm(cli_translations.get_text(TranslationKeys.CONFIRM_QUIT)).ask():
                    sys.exit(cli_translations.get_text(TranslationKeys.GOODBYE))
                continue
            elif choice == cli_translations.get_text(TranslationKeys.BACK):
                return

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_WANTED_BY):
                wanted_by = questionary.text(
                    cli_translations.get_text(TranslationKeys.EDIT_WANTED_BY_PROMPT),
                    default=service.install.wanted_by
                ).ask()
                if wanted_by:
                    service.install.wanted_by = wanted_by

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_REQUIRED_BY):
                required_by = questionary.text(
                    cli_translations.get_text(TranslationKeys.EDIT_REQUIRED_BY_PROMPT),
                    default=service.install.required_by
                ).ask()
                if required_by:
                    service.install.required_by = required_by

            elif choice == cli_translations.get_text(TranslationKeys.EDIT_ALSO):
                also = questionary.text(
                    cli_translations.get_text(TranslationKeys.EDIT_ALSO_PROMPT),
                    default=service.install.also
                ).ask()
                if also:
                    service.install.also = also
