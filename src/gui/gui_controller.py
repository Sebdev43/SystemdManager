import os
import json
import subprocess
from typing import List, Optional
from src.models.service_model import ServiceModel
import customtkinter

class GUIController:
    """
    Controller class for managing GUI operations and service interactions.
    
    This class handles all GUI-related operations including service management,
    theme switching, and file system operations for service configurations.
    
    Attributes:
        services_dir (str): Directory path for storing service configurations
        current_theme (str): Current application theme ('dark' or 'light')
    """
    
    def __init__(self):

        self.services_dir = os.path.expanduser("~/.config/systemd-manager/services")
        self.setup_directories()
        self.current_theme = "dark"
        
    def setup_directories(self):

        if not os.path.exists(self.services_dir):
            os.makedirs(self.services_dir)

    def get_services(self) -> List[ServiceModel]:

        services = []
        
        try:
            
            for filename in os.listdir(self.services_dir):
                if filename.endswith('.json'):
                    service_path = os.path.join(self.services_dir, filename)
                    try:
                       
                        with open(service_path, 'r') as f:
                            service_data = json.load(f)

                        service_name = os.path.splitext(filename)[0]
                        service = ServiceModel(service_name)

                        if isinstance(service_data, dict):

                            if 'Unit' in service_data:
                                service.unit.__dict__.update(service_data['Unit'])
                            if 'Service' in service_data:
                                service.service.__dict__.update(service_data['Service'])
                            if 'Install' in service_data:
                                service.install.__dict__.update(service_data['Install'])

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

        try:

            result = subprocess.run(
                ["systemctl", "status", f"{service_name}.service"],
                capture_output=True,
                text=True
            )

            if "Stopped" in result.stdout or "inactive" in result.stdout:
                active_state = "inactive"
            elif "Active: active" in result.stdout:
                active_state = "active"
            elif "Active: failed" in result.stdout:
                active_state = "failed"
            else:
                active_state = "unknown"

            props_result = subprocess.run(
                ["systemctl", "show", f"{service_name}.service", "--property=SubState,LoadState"],
                capture_output=True,
                text=True,
                check=True
            )
            
            status = {}
            for line in props_result.stdout.splitlines():
                if '=' in line:
                    key, value = line.split('=', 1)
                    status[key.lower()] = value
            
            return {
                "active": active_state,
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

        try:
            subprocess.run(
                ["systemctl", "start", f"{service_name}.service"],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def stop_service(self, service_name: str) -> bool:

        try:
            subprocess.run(
                ["systemctl", "stop", f"{service_name}.service"],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def restart_service(self, service_name: str) -> bool:

        try:
            subprocess.run(
                ["systemctl", "restart", f"{service_name}.service"],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def check_sudo(self) -> bool:

        return subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True
        ).returncode == 0

    def save_service(self, service: ServiceModel) -> bool:

        try:

            service_path = os.path.join(self.services_dir, f"{service.name}.json")

            service_data = {
                'Unit': service.unit.__dict__,
                'Service': service.service.__dict__,
                'Install': service.install.__dict__
            }

            with open(service_path, 'w') as f:
                json.dump(service_data, f, indent=4)

            systemd_path = f"/etc/systemd/system/{service.name}.service"
            systemd_content = []

            systemd_content.append("[Unit]")
            if service.unit.description:
                systemd_content.append(f"Description={service.unit.description}")
            if hasattr(service.unit, 'start_limit_burst') and service.unit.start_limit_burst:
                systemd_content.append(f"StartLimitBurst={service.unit.start_limit_burst}")

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
            if service.service.remain_after_exit:
                systemd_content.append("RemainAfterExit=yes")

            systemd_content.append("\n[Install]")
            if service.install.wanted_by:
                systemd_content.append(f"WantedBy={','.join(service.install.wanted_by)}")

            with open("/tmp/service.tmp", 'w') as f:
                f.write("\n".join(systemd_content))
            
            subprocess.run(["sudo", "mv", "/tmp/service.tmp", systemd_path], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du service : {e}")
            return False

    def load_service(self, service_name: str) -> Optional[ServiceModel]:

        try:

            service_path = os.path.join(self.services_dir, f"{service_name}.json")

            if not os.path.exists(service_path):
                print(f"Le fichier de service {service_path} n'existe pas")
                return None

            with open(service_path, 'r') as f:
                service_data = json.load(f)

            service = ServiceModel(service_name)

            if isinstance(service_data, dict):

                if 'Unit' in service_data:
                    service.unit.__dict__.update(service_data['Unit'])
                if 'Service' in service_data:
                    service.service.__dict__.update(service_data['Service'])
                if 'Install' in service_data:
                    service.install.__dict__.update(service_data['Install'])

            status = self.get_service_status(service_name)
            service.status = status
            
            return service
            
        except Exception as e:
            print(f"Erreur lors du chargement du service {service_name}: {e}")
            return None

    def call_refresh_if_exists(self, widget):

        try:

            if not hasattr(widget, 'winfo_exists') or not widget.winfo_exists():
                return False

            if not hasattr(widget, 'refresh'):
                return False

            if not callable(widget.refresh):
                return False

            widget.refresh()
            return True
            
        except Exception as e:
            print(f"Erreur lors du refresh du widget : {e}")
            return False

    def toggle_theme(self):

        if self.current_theme == "dark":
            customtkinter.set_appearance_mode("light")
            self.current_theme = "light"
        else:
            customtkinter.set_appearance_mode("dark")
            self.current_theme = "dark"
        return self.current_theme

    def delete_service(self, service_name: str):
        """
        Delete a systemd service.
        
        This method will:
        1. Stop the service
        2. Disable the service
        3. Remove the service file
        4. Remove the service configuration
        
        Args:
            service_name (str): Name of the service to delete
            
        Raises:
            Exception: If any step of the deletion process fails
        """
        try:

            subprocess.run(['systemctl', 'stop', service_name], check=True)
            

            subprocess.run(['systemctl', 'disable', service_name], check=True)
            

            service_path = f"/etc/systemd/system/{service_name}.service"
            if os.path.exists(service_path):
                os.remove(service_path)
            

            json_path = os.path.join(self.services_dir, f"{service_name}.json")
            if os.path.exists(json_path):
                os.remove(json_path)
                

            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to delete service: {str(e)}")
        except OSError as e:
            raise Exception(f"Failed to remove service files: {str(e)}")
