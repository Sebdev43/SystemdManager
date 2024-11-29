import customtkinter as ctk
from typing import Optional, List, Callable
from src.models.service_model import ServiceModel
from src.gui.gui_controller import GUIController
import subprocess
import os
import json
from src.i18n.translations import i18n, _
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from src.gui.utils.service_validator import ServiceValidator

class ServiceListFrame(ctk.CTkFrame):
    """
    Frame class for displaying and managing systemd services.
    
    This class provides a list view of all systemd services with capabilities
    for starting, stopping, editing, and monitoring services.
    
    Attributes:
        controller (GUIController): Controller for GUI operations
        selected_service (Optional[ServiceModel]): Currently selected service
        services (List[ServiceModel]): List of all available services
    """
    def __init__(self, master):
        super().__init__(master)

        self.controller = GUIController()

        self.validator = ServiceValidator()

        self.services: List[ServiceModel] = []
        self.selected_service: Optional[ServiceModel] = None
        self.selected_frame = None 
        self.normal_color = ("gray75", "gray15")  
        self.selected_color = ("gray85", "gray35") 

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_services_list()

        self.create_control_buttons()

        self.refresh_services()

    def create_control_buttons(self):

        button_frame = ctk.CTkFrame(
            self,
        )
        button_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))

        button_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        button_frame.grid_rowconfigure(0, weight=1)

        self.start_button = ctk.CTkButton(
            button_frame,
            text=_("Démarrer"),
            command=self.start_service,
            state="disabled",
            height=40,
            width=120
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.stop_button = ctk.CTkButton(
            button_frame,
            text=_("Arrêter"),
            command=self.stop_service,
            state="disabled",
            height=40,
            width=120
        )
        self.stop_button.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.restart_button = ctk.CTkButton(
            button_frame,
            text=_("Redémarrer"),
            command=self.restart_service,
            state="disabled",
            height=40,
            width=120
        )
        self.restart_button.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        self.edit_button = ctk.CTkButton(
            button_frame,
            text=_("Éditer"),
            command=self.edit_service,
            state="disabled",
            height=40,
            width=120
        )
        self.edit_button.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        
        self.logs_button = ctk.CTkButton(
            button_frame,
            text=_("Logs"),
            command=self.show_logs,
            state="disabled",
            height=40,
            width=120
        )
        self.logs_button.grid(row=0, column=4, padx=5, pady=5, sticky="nsew")
        
        self.delete_button = ctk.CTkButton(
            button_frame,
            text=_("Supprimer"),
            command=self.delete_service,
            fg_color="red",
            hover_color="#AA0000",
            state="disabled",
            height=40,
            width=120
        )
        self.delete_button.grid(row=0, column=5, padx=5, pady=5, sticky="nsew")

    def create_services_list(self):

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
        )
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.header_frame = ctk.CTkFrame(
            self.scrollable_frame,
        )
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        headers = [
            (_("Nom"), 200),
            (_("Description"), 300),
            (_("Statut"), 100)
        ]
        
        for col, (text, width) in enumerate(headers):
            label = ctk.CTkLabel(
                self.header_frame,
                text=text,
                font=ctk.CTkFont(weight="bold"),
                width=width
            )
            label.grid(row=0, column=col, padx=5, pady=5)

    def refresh_services(self):


        selected_service_name = self.selected_service.name if self.selected_service else None

        self.selected_frame = None

        self.services = self.controller.get_services()

        for widget in self.scrollable_frame.winfo_children():
            if widget.grid_info()["row"] != 0:
                widget.destroy()

        for i, service in enumerate(self.services):

            service_frame = ctk.CTkFrame(
                self.scrollable_frame,
            )
            service_frame.grid(row=i+1, column=0, sticky="ew", pady=1)  
            service_frame.grid_columnconfigure(1, weight=1)

            name_label = ctk.CTkLabel(
                service_frame,
                text=service.name,
                width=200,
                anchor="w"
            )
            name_label.grid(row=0, column=0, padx=5, pady=2)

            desc_label = ctk.CTkLabel(
                service_frame,
                text=service.unit.description or _("No description"),
                width=300,
                anchor="w"
            )
            desc_label.grid(row=0, column=1, padx=5, pady=2)

            status = service.status.get("active", _("unknown"))
            status_colors = {
                "active": "green",
                "inactive": "gray",
                "failed": "red",
                "unknown": "orange"
            }
            
            status_label = ctk.CTkLabel(
                service_frame,
                text=status,
                text_color=status_colors.get(status, "white"),
                width=100
            )
            status_label.grid(row=0, column=2, padx=5, pady=2)

            for widget in [service_frame, name_label, desc_label, status_label]:
                widget.bind("<Button-1>", lambda e, s=service, f=service_frame: self.select_service(s, f))
                widget.bind("<Enter>", lambda e, f=service_frame: self.on_service_hover(f, True))
                widget.bind("<Leave>", lambda e, f=service_frame: self.on_service_hover(f, False))

            if selected_service_name and service.name == selected_service_name:
                self.select_service(service, service_frame)

    def create_service_frame(self, service: ServiceModel, row: int) -> ctk.CTkFrame:

        frame = ctk.CTkFrame(self.scrollable_frame)
        frame.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
        frame.grid_columnconfigure(1, weight=1)

        return frame

    def on_service_hover(self, frame: ctk.CTkFrame, enter: bool):

        if frame != self.selected_frame:
            frame.configure(fg_color=("gray85", "gray25") if enter else self.normal_color)

    def select_service(self, service: ServiceModel, frame: ctk.CTkFrame):


        if self.selected_frame and self.selected_frame.winfo_exists():
            try:
                self.selected_frame.configure(fg_color=self.normal_color)
            except:
                pass  

        self.selected_service = service
        self.selected_frame = frame

        try:
            frame.configure(fg_color=self.selected_color)
        except:
            pass  
 
        self.update_buttons_state()

    def update_buttons_state(self):

        for button in [self.start_button, self.stop_button, self.restart_button,
                      self.edit_button, self.logs_button, self.delete_button]:
            button.configure(state="normal")

    def start_service(self):

        if not self.selected_service:
            return
            
        service_name = self.selected_service.name

        result = subprocess.run(['systemctl', 'is-active', '--quiet', service_name])
        if result.returncode == 0:
            print(f"⚠️  Le service {service_name} est déjà actif")
            return
            
        print(f"🚀 Démarrage du service {service_name}...")

        result = subprocess.run(['systemctl', 'start', service_name], capture_output=True)
        if result.returncode == 0:
            print(f"✅ Service {service_name} démarré avec succès")

            print("\n📊 Statut actuel du service :")
            status_result = subprocess.run(['systemctl', 'status', service_name], capture_output=True, text=True)
            print(status_result.stdout)

            print("\n📜 Logs de démarrage :")
            log_result = subprocess.run(['journalctl', '-u', service_name, '-n', '20', '--no-pager'], 
                                     capture_output=True, text=True)
            print(log_result.stdout)
        else:
            print(f"❌ Erreur lors du démarrage du service {service_name}: {result.stderr.decode()}")

        self.refresh_services()

    def stop_service(self):
        if not self.selected_service:
            return
            
        service_name = self.selected_service.name

        result = subprocess.run(['systemctl', 'is-active', '--quiet', service_name])
        if result.returncode != 0:
            print(f"⚠️  Le service {service_name} n'est pas actif")
            return
            
        print(f"📥 Arrêt du service {service_name}...")

        result = subprocess.run(['systemctl', 'stop', service_name], capture_output=True)
        if result.returncode == 0:
            print(f"✅ Service {service_name} arrêté avec succès")

            print("\n📊 Statut actuel du service :")
            status_result = subprocess.run(['systemctl', 'status', service_name], 
                                        capture_output=True, text=True)
            print(status_result.stdout)
        else:
            print(f"❌ Erreur lors de l'arrêt du service {service_name}: {result.stderr.decode()}")

            print("\n📜 Derniers logs du service :")
            log_result = subprocess.run(['journalctl', '-u', service_name, '-n', '20', '--no-pager'], 
                                     capture_output=True, text=True)
            print(log_result.stdout)

        self.refresh_services()

    def restart_service(self):

        if not self.selected_service:
            return
            
        service_name = self.selected_service.name
        print(f"🔄 Redémarrage du service {service_name}...")

        result = subprocess.run(['systemctl', 'restart', service_name], capture_output=True)
        if result.returncode == 0:
            print(f"✅ Service {service_name} redémarré avec succès")

            print("\n📊 Statut actuel du service :")
            status_result = subprocess.run(['systemctl', 'status', service_name], 
                                        capture_output=True, text=True)
            print(status_result.stdout)

            print("\n📜 Logs de redémarrage :")
            log_result = subprocess.run(['journalctl', '-u', service_name, '-n', '20', '--no-pager'], 
                                     capture_output=True, text=True)
            print(log_result.stdout)
        else:
            print(f"❌ Erreur lors du redémarrage du service {service_name}: {result.stderr.decode()}")

            print("\n📜 Logs d'erreur détaillés :")
            error_log_result = subprocess.run(['journalctl', '-u', service_name, '-n', '50', '--no-pager'], 
                                           capture_output=True, text=True)
            print(error_log_result.stdout)

            print("\n🔍 État détaillé du service :")
            detailed_status = subprocess.run(['systemctl', 'status', service_name, '--no-pager'], 
                                          capture_output=True, text=True)
            print(detailed_status.stdout)

        self.refresh_services()

    def edit_service(self):

        if not self.selected_service:
            return
            
        service_name = self.selected_service.name
        
        try:

            service = self.controller.load_service(service_name)
            if not service:
                self.show_error(_("Impossible de charger le service"))
                return

            from src.gui.dialogs.edit_service_dialog import EditServiceDialog
            dialog = EditServiceDialog(self, service)

            self.wait_window(dialog)

            if dialog.result:

                if self.controller.save_service(dialog.result):
                    self.show_success(_("Service modifié avec succès"))
                    self.refresh_services()
                else:
                    self.show_error(_("Erreur lors de la modification du service"))
            
        except Exception as e:
            self.show_error(str(e))

    def show_error(self, message):

        messagebox.showerror(_("Erreur"), message)
        
    def show_success(self, message):

        messagebox.showinfo(_("Succès"), message)

    def show_logs(self):

        if self.selected_service:
            from src.gui.dialogs.logs_dialog import LogsDialog
            LogsDialog(self.master.master, self.selected_service.name)

    def delete_service(self):

        if not self.selected_service:
            return

        if messagebox.askyesno(
            _("Delete service?"),
            _("Are you sure you want to delete the service '%s'?\n\n%s") % 
            (self.selected_service.name, _("This action cannot be undone."))
        ):
            try:

                self.controller.delete_service(self.selected_service.name)
                self.show_success(_("Service deleted successfully"))

                self.refresh_services()
                
            except Exception as e:
                self.show_error(f"{_('Error deleting service')}: {str(e)}")

    def refresh(self):

        self.refresh_services()

    def update_translations(self):


        self.start_button.configure(text=_("Start"))
        self.stop_button.configure(text=_("Stop"))
        self.restart_button.configure(text=_("Restart"))
        self.edit_button.configure(text=_("Edit"))
        self.logs_button.configure(text=_("Logs"))
        self.delete_button.configure(text=_("Delete"))

        for widget in self.header_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                if widget.cget("text") == "Nom":
                    widget.configure(text=_("Name"))
                elif widget.cget("text") == "Description":
                    widget.configure(text=_("Description"))
                elif widget.cget("text") == "Statut":
                    widget.configure(text=_("Status"))

        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        current_text = child.cget("text")
                        if current_text in ["actif", "active", "inactif", "inactive", "échec", "failed", "inconnu", "unknown"]:
                            child.configure(text=_(current_text))
                        elif current_text == "Pas de description":
                            child.configure(text=_("No description"))

        self.refresh_services()

    def refresh_service_status(self, service_name: str):

        try:

            status, errors = self.validator.analyze_service_status(service_name)

            if service_name in self.service_frames:
                frame = self.service_frames[service_name]
                frame.update_status(status)

                if errors:
                    frame.show_error_indicator()
                    frame.set_error_tooltip("\n".join(errors))
                else:
                    frame.hide_error_indicator()
                    
        except Exception as e:
            print(f"Erreur lors du rafraîchissement du statut de {service_name}: {str(e)}")

    def start_service(self):

        if not self.selected_service:
            return
            
        try:
            self.controller.start_service(self.selected_service.name)
            self.show_success(_("Service started successfully"))
            self.refresh_service_status(self.selected_service.name)
        except Exception as e:
            self.show_error(f"{_('Error starting service')}: {str(e)}")

    def stop_service(self):

        if not self.selected_service:
            return
            
        try:
            self.controller.stop_service(self.selected_service.name)
            self.show_success(_("Service stopped successfully"))
            self.refresh_service_status(self.selected_service.name)
        except Exception as e:
            self.show_error(f"{_('Error stopping service')}: {str(e)}")

    def restart_service(self):

        if not self.selected_service:
            return
            
        try:
            self.controller.restart_service(self.selected_service.name)
            self.show_success(_("Service restarted successfully"))
            self.refresh_service_status(self.selected_service.name)
        except Exception as e:
            self.show_error(f"{_('Error restarting service')}: {str(e)}")
