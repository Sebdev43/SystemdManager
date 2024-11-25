import customtkinter as ctk
from typing import Optional, List, Callable
from src.models.service_model import ServiceModel
from src.gui.gui_controller import GUIController
import subprocess
import os

class ServiceListFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Initialisation du contrôleur GUI
        self.controller = GUIController()
        
        # Variables d'état
        self.services: List[ServiceModel] = []
        self.selected_service: Optional[ServiceModel] = None
        
        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Création de la barre de titre principale avec le filtre
        self.create_main_header()
        
        # Création des boutons de contrôle
        self.create_control_buttons()
        
        # Création de la liste des services
        self.create_services_list()
        
        # Chargement initial des services
        self.refresh_services()
    
    def create_main_header(self):
        """Crée la barre de titre principale avec le filtre"""
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header_frame.grid_columnconfigure(9, weight=1)  # Ajusté pour le bouton de suppression
        
        # Barre de recherche
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_services())
        search_entry = ctk.CTkEntry(
            header_frame,
            placeholder_text="Rechercher un service...",
            textvariable=self.search_var,
            width=200
        )
        search_entry.grid(row=0, column=0, padx=5)
        
        # Filtre de statut
        self.status_var = ctk.StringVar(value="Tous")
        status_filter = ctk.CTkOptionMenu(
            header_frame,
            values=["Tous", "Actif", "Inactif", "Échec"],
            variable=self.status_var,
            command=lambda _: self.filter_services(),
            width=120
        )
        status_filter.grid(row=0, column=1, padx=5)
    
    def create_control_buttons(self):
        """Crée les boutons de contrôle"""
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 0))
        
        # Boutons de contrôle
        self.start_button = ctk.CTkButton(
            button_frame,
            text="Démarrer",
            command=self.start_service,
            state="disabled"
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Arrêter",
            command=self.stop_service,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.restart_button = ctk.CTkButton(
            button_frame,
            text="Redémarrer",
            command=self.restart_service,
            state="disabled"
        )
        self.restart_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.edit_button = ctk.CTkButton(
            button_frame,
            text="Éditer",
            command=self.edit_service,
            state="disabled"
        )
        self.edit_button.grid(row=0, column=3, padx=5, pady=5)
        
        self.logs_button = ctk.CTkButton(
            button_frame,
            text="Logs",
            command=self.show_logs,
            state="disabled"
        )
        self.logs_button.grid(row=0, column=4, padx=5, pady=5)
        
        self.delete_button = ctk.CTkButton(
            button_frame,
            text="Supprimer",
            command=self.delete_service,
            fg_color="red",
            hover_color="#AA0000",
            state="disabled"
        )
        self.delete_button.grid(row=0, column=5, padx=5, pady=5)
    
    def create_services_list(self):
        """Crée la liste des services"""
        # Frame principal avec défilement
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # En-tête
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        headers = [
            ("Nom", 200),
            ("Description", 300),
            ("Statut", 100),
            ("Démarrage auto", 100)
        ]
        
        for col, (text, width) in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame,
                text=text,
                font=ctk.CTkFont(weight="bold"),
                width=width
            )
            label.grid(row=0, column=col, padx=5)
        
        # Liste des services
        self.services_frame = ctk.CTkFrame(main_frame)
        self.services_frame.grid(row=2, column=0, sticky="nsew")
        self.services_frame.grid_columnconfigure(1, weight=1)
    
    def refresh_services(self):
        """Actualise la liste des services"""
        # Récupération des services
        self.services = self.controller.get_services()
        
        # Effacement de la liste actuelle
        for widget in self.services_frame.winfo_children():
            widget.destroy()
        
        # Ajout des services
        for i, service in enumerate(self.services):
            # Frame pour le service
            service_frame = ctk.CTkFrame(self.services_frame)
            service_frame.grid(row=i, column=0, sticky="ew", pady=2)
            service_frame.grid_columnconfigure(1, weight=1)
            
            # Nom
            name_label = ctk.CTkLabel(
                service_frame,
                text=service.name,
                width=200,
                anchor="w"
            )
            name_label.grid(row=0, column=0, padx=5)
            
            # Description
            desc_label = ctk.CTkLabel(
                service_frame,
                text=service.unit.description or "Pas de description",
                width=300,
                anchor="w"
            )
            desc_label.grid(row=0, column=1, padx=5)
            
            # Statut avec couleur
            status = service.status.get("active", "unknown")
            status_colors = {
                "active": "green",
                "inactive": "gray",
                "failed": "red",
                "unknown": "orange"
            }
            status_frame = ctk.CTkFrame(service_frame, width=100)
            status_frame.grid(row=0, column=2, padx=5)
            status_frame.grid_propagate(False)
            
            status_label = ctk.CTkLabel(
                status_frame,
                text=status,
                text_color=status_colors.get(status, "white")
            )
            status_label.place(relx=0.5, rely=0.5, anchor="center")
            
            # Démarrage automatique
            auto_start = "Oui" if service.install.wanted_by else "Non"
            auto_label = ctk.CTkLabel(
                service_frame,
                text=auto_start,
                width=100
            )
            auto_label.grid(row=0, column=3, padx=5)
            
            # Rendre la ligne cliquable
            for widget in [service_frame, name_label, desc_label, status_frame, auto_label]:
                widget.bind("<Button-1>", lambda e, s=service: self.select_service(s))
                widget.bind("<Enter>", lambda e, f=service_frame: self.on_service_hover(f, True))
                widget.bind("<Leave>", lambda e, f=service_frame: self.on_service_hover(f, False))
    
    def on_service_hover(self, frame: ctk.CTkFrame, enter: bool):
        """Gère le survol d'un service"""
        frame.configure(fg_color=("gray85", "gray25") if enter else ("gray75", "gray15"))
    
    def select_service(self, service: ServiceModel):
        """Sélectionne un service"""
        self.selected_service = service
        
        # Mise à jour des boutons
        for button in [self.start_button, self.stop_button, self.restart_button,
                      self.edit_button, self.logs_button, self.delete_button]:
            button.configure(state="normal")
        
        # Mise à jour visuelle de la sélection
        for widget in self.services_frame.winfo_children():
            widget.configure(fg_color=("gray75", "gray15"))
        
        # Trouver et mettre en surbrillance le service sélectionné
        for widget in self.services_frame.winfo_children():
            if widget.winfo_children()[0].cget("text") == service.name:
                widget.configure(fg_color=("gray85", "gray35"))
                break
    
    def filter_services(self):
        """Filtre les services selon la recherche et le statut"""
        search_text = self.search_var.get().lower()
        status_filter = self.status_var.get()
        
        for widget in self.services_frame.winfo_children():
            service_name = widget.winfo_children()[0].cget("text").lower()
            service = next((s for s in self.services if s.name == service_name), None)
            
            if not service:
                continue
            
            status = service.status.get("active", "unknown")
            show_by_status = (
                status_filter == "Tous" or
                (status_filter == "Actif" and status == "active") or
                (status_filter == "Inactif" and status == "inactive") or
                (status_filter == "Échec" and status == "failed")
            )
            
            show_by_search = search_text in service_name.lower()
            
            if show_by_status and show_by_search:
                widget.grid()
            else:
                widget.grid_remove()
    
    def start_service(self):
        """Démarre le service sélectionné"""
        if self.selected_service:
            if self.controller.start_service(self.selected_service.name):
                self.master.master.notification_manager.show_notification(
                    self.master.master,
                    f"Service {self.selected_service.name} démarré avec succès",
                    "success"
                )
                self.refresh_services()
            else:
                self.master.master.notification_manager.show_notification(
                    self.master.master,
                    f"Erreur lors du démarrage du service {self.selected_service.name}",
                    "error"
                )
    
    def stop_service(self):
        """Arrête le service sélectionné"""
        if self.selected_service:
            if self.controller.stop_service(self.selected_service.name):
                self.master.master.notification_manager.show_notification(
                    self.master.master,
                    f"Service {self.selected_service.name} arrêté avec succès",
                    "success"
                )
                self.refresh_services()
            else:
                self.master.master.notification_manager.show_notification(
                    self.master.master,
                    f"Erreur lors de l'arrêt du service {self.selected_service.name}",
                    "error"
                )
    
    def restart_service(self):
        """Redémarre le service sélectionné"""
        if self.selected_service:
            if self.controller.restart_service(self.selected_service.name):
                self.master.master.notification_manager.show_notification(
                    self.master.master,
                    f"Service {self.selected_service.name} redémarré avec succès",
                    "success"
                )
                self.refresh_services()
            else:
                self.master.master.notification_manager.show_notification(
                    self.master.master,
                    f"Erreur lors du redémarrage du service {self.selected_service.name}",
                    "error"
                )
    
    def edit_service(self):
        """Ouvre la boîte de dialogue d'édition du service"""
        if self.selected_service:
            from src.gui.dialogs.edit_service_dialog import EditServiceDialog
            dialog = EditServiceDialog(self.master.master, self.selected_service)
            self.wait_window(dialog)
            if dialog.result:
                # Sauvegarder les modifications
                json_path = os.path.join(self.controller.services_dir, f"{dialog.result.name}.json")
                dialog.result.save_to_json(json_path)
                
                # Mettre à jour le service dans systemd
                service_path = f"/etc/systemd/system/{dialog.result.name}.service"
                try:
                    with open(service_path, 'w') as f:
                        f.write(dialog.result.to_systemd_file())
                    
                    # Recharger systemd
                    subprocess.run(["systemctl", "daemon-reload"], check=True)
                    
                    self.master.master.notification_manager.show_notification(
                        self.master.master,
                        f"Service {dialog.result.name} mis à jour avec succès",
                        "success"
                    )
                    self.refresh_services()
                except Exception as e:
                    self.master.master.notification_manager.show_notification(
                        self.master.master,
                        f"Erreur lors de la mise à jour du service : {str(e)}",
                        "error"
                    )
    
    def show_logs(self):
        """Ouvre la boîte de dialogue des logs"""
        if self.selected_service:
            from src.gui.dialogs.logs_dialog import LogsDialog
            LogsDialog(self.master.master, self.selected_service.name)

    def delete_service(self):
        """Supprime le service sélectionné"""
        if self.selected_service:
            from src.gui.dialogs.confirm_dialog import ConfirmDialog
            
            dialog = ConfirmDialog(
                self.master.master,
                "Confirmer la suppression",
                f"Êtes-vous sûr de vouloir supprimer le service {self.selected_service.name} ?\n"
                "Cette action est irréversible."
            )
            self.wait_window(dialog)
            
            if dialog.result:
                try:
                    # Arrêter le service s'il est en cours d'exécution
                    subprocess.run(["systemctl", "stop", self.selected_service.name], check=True)
                    
                    # Désactiver le service
                    subprocess.run(["systemctl", "disable", self.selected_service.name], check=True)
                    
                    # Supprimer le fichier de service
                    service_path = f"/etc/systemd/system/{self.selected_service.name}.service"
                    if os.path.exists(service_path):
                        os.remove(service_path)
                    
                    # Supprimer le fichier de configuration JSON
                    json_path = os.path.join(self.controller.services_dir, f"{self.selected_service.name}.json")
                    if os.path.exists(json_path):
                        os.remove(json_path)
                    
                    # Recharger systemd
                    subprocess.run(["systemctl", "daemon-reload"], check=True)
                    
                    self.master.master.notification_manager.show_notification(
                        self.master.master,
                        f"Service {self.selected_service.name} supprimé avec succès",
                        "success"
                    )
                    
                    # Rafraîchir la liste des services
                    self.refresh_services()
                except Exception as e:
                    self.master.master.notification_manager.show_notification(
                        self.master.master,
                        f"Erreur lors de la suppression du service : {str(e)}",
                        "error"
                    )
