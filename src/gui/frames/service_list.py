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

class ServiceListFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        # Initialisation du contrôleur GUI
        self.controller = GUIController()
        
        # Variables d'état
        self.services: List[ServiceModel] = []
        self.selected_service: Optional[ServiceModel] = None
        self.selected_frame = None  # Pour stocker la référence au frame sélectionné
        self.normal_color = ("gray75", "gray15")  # Couleur normale
        self.selected_color = ("gray85", "gray35")  # Couleur de surbrillance
        
        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Création de la liste des services
        self.create_services_list()
        
        # Création des boutons de contrôle
        self.create_control_buttons()
        
        # Chargement initial des services
        self.refresh_services()

    def create_control_buttons(self):
        """Crée les boutons de contrôle"""
        button_frame = ctk.CTkFrame(
            self,
        )
        button_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        
        # Configuration de la grille du button_frame
        button_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        button_frame.grid_rowconfigure(0, weight=1)
        
        # Boutons de contrôle
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
        """Crée la liste des services"""
        # Frame principal avec défilement
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
        )
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # En-tête
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
        """Actualise la liste des services"""
        # Sauvegarder le service sélectionné
        selected_service_name = self.selected_service.name if self.selected_service else None
        
        # Réinitialiser la sélection
        self.selected_frame = None
        
        # Récupération des services
        self.services = self.controller.get_services()
        
        # Suppression des widgets existants (sauf l'en-tête)
        for widget in self.scrollable_frame.winfo_children():
            if widget.grid_info()["row"] != 0:
                widget.destroy()
        
        # Ajout des services
        for i, service in enumerate(self.services):
            # Frame pour le service
            service_frame = ctk.CTkFrame(
                self.scrollable_frame,
            )
            service_frame.grid(row=i+1, column=0, sticky="ew", pady=1)  
            service_frame.grid_columnconfigure(1, weight=1)
            
            # Nom
            name_label = ctk.CTkLabel(
                service_frame,
                text=service.name,
                width=200,
                anchor="w"
            )
            name_label.grid(row=0, column=0, padx=5, pady=2)
            
            # Description
            desc_label = ctk.CTkLabel(
                service_frame,
                text=service.unit.description or _("No description"),
                width=300,
                anchor="w"
            )
            desc_label.grid(row=0, column=1, padx=5, pady=2)
            
            # Statut avec couleur
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
            
            # Rendre la ligne cliquable
            for widget in [service_frame, name_label, desc_label, status_label]:
                widget.bind("<Button-1>", lambda e, s=service, f=service_frame: self.select_service(s, f))
                widget.bind("<Enter>", lambda e, f=service_frame: self.on_service_hover(f, True))
                widget.bind("<Leave>", lambda e, f=service_frame: self.on_service_hover(f, False))
            
            # Si c'était le service sélectionné, le resélectionner
            if selected_service_name and service.name == selected_service_name:
                self.select_service(service, service_frame)

    def create_service_frame(self, service: ServiceModel, row: int) -> ctk.CTkFrame:
        """Crée un frame pour un service"""
        frame = ctk.CTkFrame(self.scrollable_frame)
        frame.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
        frame.grid_columnconfigure(1, weight=1)

        return frame

    def on_service_hover(self, frame: ctk.CTkFrame, enter: bool):
        """Gère le survol d'un service"""
        # Ne pas changer la couleur si le frame est sélectionné
        if frame != self.selected_frame:
            frame.configure(fg_color=("gray85", "gray25") if enter else self.normal_color)

    def select_service(self, service: ServiceModel, frame: ctk.CTkFrame):
        """Sélectionne un service et met à jour l'interface"""
        # Réinitialiser la couleur du frame précédemment sélectionné
        if self.selected_frame and self.selected_frame.winfo_exists():
            try:
                self.selected_frame.configure(fg_color=self.normal_color)
            except:
                pass  # Ignore les erreurs si le widget n'existe plus

        # Mettre à jour la sélection
        self.selected_service = service
        self.selected_frame = frame
        
        # Mettre en surbrillance le nouveau frame sélectionné
        try:
            frame.configure(fg_color=self.selected_color)
        except:
            pass  # Ignore les erreurs si le widget n'existe plus
        
        # Mettre à jour l'état des boutons
        self.update_buttons_state()

    def update_buttons_state(self):
        """Met à jour l'état des boutons en fonction de la sélection"""
        for button in [self.start_button, self.stop_button, self.restart_button,
                      self.edit_button, self.logs_button, self.delete_button]:
            button.configure(state="normal")

    def start_service(self):
        """Démarre le service sélectionné"""
        if not self.selected_service:
            return
            
        service_name = self.selected_service.name
        
        # Vérifier si le service n'est pas déjà actif
        result = subprocess.run(['systemctl', 'is-active', '--quiet', service_name])
        if result.returncode == 0:
            print(f"⚠️  Le service {service_name} est déjà actif")
            return
            
        print(f"🚀 Démarrage du service {service_name}...")
        
        # Démarrer le service
        result = subprocess.run(['systemctl', 'start', service_name], capture_output=True)
        if result.returncode == 0:
            print(f"✅ Service {service_name} démarré avec succès")
            
            # Afficher le statut après le démarrage
            print("\n📊 Statut actuel du service :")
            status_result = subprocess.run(['systemctl', 'status', service_name], capture_output=True, text=True)
            print(status_result.stdout)
            
            # Afficher les logs de démarrage
            print("\n📜 Logs de démarrage :")
            log_result = subprocess.run(['journalctl', '-u', service_name, '-n', '20', '--no-pager'], 
                                     capture_output=True, text=True)
            print(log_result.stdout)
        else:
            print(f"❌ Erreur lors du démarrage du service {service_name}: {result.stderr.decode()}")
        
        # Rafraîchir la liste des services
        self.refresh_services()

    def stop_service(self):
        """Arrête le service sélectionné"""
        if not self.selected_service:
            return
            
        service_name = self.selected_service.name
        
        # Vérifier si le service est actif
        result = subprocess.run(['systemctl', 'is-active', '--quiet', service_name])
        if result.returncode != 0:
            print(f"⚠️  Le service {service_name} n'est pas actif")
            return
            
        print(f"📥 Arrêt du service {service_name}...")
        
        # Arrêter le service
        result = subprocess.run(['systemctl', 'stop', service_name], capture_output=True)
        if result.returncode == 0:
            print(f"✅ Service {service_name} arrêté avec succès")
            
            # Afficher le statut après l'arrêt
            print("\n📊 Statut actuel du service :")
            status_result = subprocess.run(['systemctl', 'status', service_name], 
                                        capture_output=True, text=True)
            print(status_result.stdout)
        else:
            print(f"❌ Erreur lors de l'arrêt du service {service_name}: {result.stderr.decode()}")
            
            # Afficher les logs en cas d'erreur
            print("\n📜 Derniers logs du service :")
            log_result = subprocess.run(['journalctl', '-u', service_name, '-n', '20', '--no-pager'], 
                                     capture_output=True, text=True)
            print(log_result.stdout)
        
        # Rafraîchir la liste des services
        self.refresh_services()

    def restart_service(self):
        """Redémarre le service sélectionné"""
        if not self.selected_service:
            return
            
        service_name = self.selected_service.name
        print(f"🔄 Redémarrage du service {service_name}...")
        
        # Redémarrer le service
        result = subprocess.run(['systemctl', 'restart', service_name], capture_output=True)
        if result.returncode == 0:
            print(f"✅ Service {service_name} redémarré avec succès")
            
            # Afficher le statut après le redémarrage
            print("\n📊 Statut actuel du service :")
            status_result = subprocess.run(['systemctl', 'status', service_name], 
                                        capture_output=True, text=True)
            print(status_result.stdout)
            
            # Afficher les logs de démarrage
            print("\n📜 Logs de redémarrage :")
            log_result = subprocess.run(['journalctl', '-u', service_name, '-n', '20', '--no-pager'], 
                                     capture_output=True, text=True)
            print(log_result.stdout)
        else:
            print(f"❌ Erreur lors du redémarrage du service {service_name}: {result.stderr.decode()}")
            
            # Afficher plus de logs en cas d'erreur
            print("\n📜 Logs d'erreur détaillés :")
            error_log_result = subprocess.run(['journalctl', '-u', service_name, '-n', '50', '--no-pager'], 
                                           capture_output=True, text=True)
            print(error_log_result.stdout)
            
            # Vérifier l'état du service
            print("\n🔍 État détaillé du service :")
            detailed_status = subprocess.run(['systemctl', 'status', service_name, '--no-pager'], 
                                          capture_output=True, text=True)
            print(detailed_status.stdout)
        
        # Rafraîchir la liste des services
        self.refresh_services()

    def edit_service(self):
        """Ouvre la boîte de dialogue d'édition du service"""
        if not self.selected_service:
            return
            
        service_name = self.selected_service.name
        config_path = os.path.join(self.controller.services_dir, f"{service_name}.json")
        
        # Charger les données JSON
        with open(config_path, 'r') as f:
            data = json.load(f)
        # Ajouter le nom du service aux données
        data['name'] = service_name
        
        service = ServiceModel.load_from_json(config_path)
        
        # Créer une fenêtre de dialogue personnalisée
        dialog = customtkinter.CTkToplevel(self.master.master)
        dialog.title(f"Édition du service {service_name}")
        dialog.geometry("800x600")
        
        # Créer un notebook pour les différentes sections
        notebook = ttk.Notebook(dialog)
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Section Unit
        unit_frame = customtkinter.CTkFrame(notebook)
        notebook.add(unit_frame, text=_("Unit"))
        
        # Description
        customtkinter.CTkLabel(unit_frame, text=_("Description :")).pack(pady=5)
        description_entry = customtkinter.CTkEntry(unit_frame, width=400)
        description_entry.insert(0, service.unit.description)
        description_entry.pack(pady=5)
        
        # Limites de redémarrage
        customtkinter.CTkLabel(unit_frame, text=_("Nombre de redémarrages autorisés :")).pack(pady=5)
        burst_entry = customtkinter.CTkEntry(unit_frame)
        burst_entry.insert(0, str(service.unit.start_limit_burst))
        burst_entry.pack(pady=5)
        
        customtkinter.CTkLabel(unit_frame, text=_("Intervalle (secondes) :")).pack(pady=5)
        interval_entry = customtkinter.CTkEntry(unit_frame)
        interval_entry.insert(0, str(service.unit.start_limit_interval))
        interval_entry.pack(pady=5)
        
        # Section Service
        service_frame = customtkinter.CTkFrame(notebook)
        notebook.add(service_frame, text=_("Service"))
        
        # Utilisateur
        customtkinter.CTkLabel(service_frame, text=_("Utilisateur :")).pack(pady=5)
        user_entry = customtkinter.CTkEntry(service_frame)
        user_entry.insert(0, service.service.user)
        user_entry.pack(pady=5)
        
        # Dossier de travail
        customtkinter.CTkLabel(service_frame, text=_("Dossier de travail :")).pack(pady=5)
        working_dir_entry = customtkinter.CTkEntry(service_frame, width=400)
        working_dir_entry.insert(0, service.service.working_directory)
        working_dir_entry.pack(pady=5)
        
        # Commande d'exécution
        customtkinter.CTkLabel(service_frame, text=_("Commande d'exécution :")).pack(pady=5)
        exec_entry = customtkinter.CTkEntry(service_frame, width=400)
        exec_entry.insert(0, service.service.exec_start)
        exec_entry.pack(pady=5)
        
        # Politique de redémarrage
        customtkinter.CTkLabel(service_frame, text=_("Politique de redémarrage :")).pack(pady=5)
        restart_var = customtkinter.StringVar(value=service.service.restart)
        restart_options = {
            "no": _("Pas de redémarrage automatique"),
            "always": _("Redémarre toujours"),
            "on-failure": _("Redémarre sur erreur"),
            "on-abnormal": _("Redémarre sur erreur ou signal")
        }
        for value, text in restart_options.items():
            customtkinter.CTkRadioButton(
                service_frame, 
                text=text,
                variable=restart_var,
                value=value
            ).pack(pady=2)
        
        # Délai de redémarrage
        customtkinter.CTkLabel(service_frame, text=_("Délai de redémarrage (secondes) :")).pack(pady=5)
        restart_sec_entry = customtkinter.CTkEntry(service_frame)
        restart_sec_entry.insert(0, str(service.service.restart_sec))
        restart_sec_entry.pack(pady=5)
        
        # Section Install
        install_frame = customtkinter.CTkFrame(notebook)
        notebook.add(install_frame, text=_("Install"))
        
        # WantedBy
        customtkinter.CTkLabel(install_frame, text=_("Démarrer avec :")).pack(pady=5)
        wanted_by_var = customtkinter.StringVar(value=service.install.wanted_by[0] if service.install.wanted_by else "")
        targets = {
            "multi-user.target": _("Démarrage normal"),
            "graphical.target": _("Interface graphique"),
            "network-online.target": _("Après le réseau")
        }
        for value, text in targets.items():
            customtkinter.CTkRadioButton(
                install_frame,
                text=text,
                variable=wanted_by_var,
                value=value
            ).pack(pady=2)
        
        # Fonction de sauvegarde
        def save_changes():
            try:
                # Mettre à jour le modèle
                service.unit.description = description_entry.get()
                service.unit.start_limit_burst = int(burst_entry.get())
                service.unit.start_limit_interval = int(interval_entry.get())
                
                service.service.user = user_entry.get()
                service.service.working_directory = working_dir_entry.get()
                service.service.exec_start = exec_entry.get()
                service.service.restart = restart_var.get()
                service.service.restart_sec = int(restart_sec_entry.get())
                
                service.install.wanted_by = [wanted_by_var.get()]
                
                # 1. Arrêter le service
                print(f"📥 Arrêt du service {service.name}...")
                subprocess.run(['systemctl', 'stop', service.name], check=True)
                
                # 2. Sauvegarder les fichiers
                service_path = f"/etc/systemd/system/{service.name}.service"
                with open(service_path, 'w') as f:
                    f.write(service.to_systemd_file())
                    
                json_path = os.path.join(self.controller.services_dir, f"{service.name}.json")
                service.save_to_json(json_path)
                
                # 3. Recharger et redémarrer
                subprocess.run(['systemctl', 'daemon-reload'], check=True)
                subprocess.run(['systemctl', 'restart', service.name], check=True)
                
                print(f"✅ Service {service.name} mis à jour et redémarré")
                dialog.destroy()
                self.refresh_services()
                
            except Exception as e:
                print(f"❌ Erreur lors de la sauvegarde : {e}")
                messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")
        
        # Boutons de contrôle
        button_frame = customtkinter.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        customtkinter.CTkButton(
            button_frame,
            text=_("Sauvegarder"),
            command=save_changes
        ).pack(side="left", padx=5)
        
        customtkinter.CTkButton(
            button_frame,
            text=_("Annuler"),
            command=dialog.destroy
        ).pack(side="right", padx=5)

    def show_logs(self):
        """Ouvre la boîte de dialogue des logs"""
        if self.selected_service:
            from src.gui.dialogs.logs_dialog import LogsDialog
            LogsDialog(self.master.master, self.selected_service.name)

    def delete_service(self):
        """Supprime le service sélectionné"""
        if not self.selected_service:
            return
            
        service_name = self.selected_service.name
        
        # 1. Arrêter le service
        print(f"📥 Arrêt du service {service_name}...")
        subprocess.run(['systemctl', 'stop', service_name], capture_output=True)
        
        # 2. Désactiver le service
        print(f"🔌 Désactivation du service {service_name}...")
        subprocess.run(['systemctl', 'disable', service_name], capture_output=True)
        
        # 3. Supprimer le fichier service
        service_path = f"/etc/systemd/system/{service_name}.service"
        if os.path.exists(service_path):
            os.remove(service_path)
            print(f"🗑️  Fichier service supprimé : {service_path}")
        
        # 4. Supprimer le fichier JSON
        json_path = os.path.join(self.controller.services_dir, f"{service_name}.json")
        if os.path.exists(json_path):
            os.remove(json_path)
            print(f"🗑️  Configuration supprimée : {json_path}")
        
        # 5. Recharger systemd
        subprocess.run(['systemctl', 'daemon-reload'], capture_output=True)
        print(f"✅ Service {service_name} complètement supprimé")
        
        # 6. Rafraîchir la liste des services
        self.refresh_services()

    def update_translations(self):
        """Met à jour les traductions des textes de l'interface"""
        # Met à jour les boutons de contrôle
        self.start_button.configure(text=_("Start"))
        self.stop_button.configure(text=_("Stop"))
        self.restart_button.configure(text=_("Restart"))
        self.edit_button.configure(text=_("Edit"))
        self.logs_button.configure(text=_("Logs"))
        self.delete_button.configure(text=_("Delete"))
        
        # Met à jour les en-têtes
        for widget in self.header_frame.winfo_children():
            if isinstance(widget, ctk.CTkLabel):
                if widget.cget("text") == "Nom":
                    widget.configure(text=_("Name"))
                elif widget.cget("text") == "Description":
                    widget.configure(text=_("Description"))
                elif widget.cget("text") == "Statut":
                    widget.configure(text=_("Status"))
        
        # Met à jour les statuts des services
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        current_text = child.cget("text")
                        if current_text in ["actif", "active", "inactif", "inactive", "échec", "failed", "inconnu", "unknown"]:
                            child.configure(text=_(current_text))
                        elif current_text == "Pas de description":
                            child.configure(text=_("No description"))
        
        # Force le rafraîchissement de la liste
        self.refresh_services()
