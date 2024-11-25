import customtkinter as ctk
from typing import Optional
from src.models.service_model import ServiceModel
import subprocess

class EditServiceDialog(ctk.CTkToplevel):
    def __init__(self, parent, service: ServiceModel):
        super().__init__(parent)
        
        self.service = service
        self.result = None
        
        # Configuration de la fenêtre
        self.title(f"Édition du service {service.name}")
        self.geometry("800x600")
        
        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Création des onglets
        self.create_tabs()
        
        # Boutons de contrôle
        self.create_control_buttons()
        
        # Rendre la fenêtre modale
        self.transient(parent)
        self.grab_set()
    
    def create_tabs(self):
        """Crée les onglets pour chaque section"""
        # Conteneur d'onglets
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Onglet Unit
        unit_tab = self.tabview.add("Unit")
        unit_tab.grid_columnconfigure(1, weight=1)
        
        # Description
        ctk.CTkLabel(unit_tab, text="Description :").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.description_entry = ctk.CTkEntry(unit_tab, width=400)
        self.description_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.description_entry.insert(0, self.service.unit.description or "")
        
        # Dépendances
        ctk.CTkLabel(unit_tab, text="Dépendances :").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        dependencies_frame = ctk.CTkFrame(unit_tab)
        dependencies_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # After
        ctk.CTkLabel(dependencies_frame, text="After :").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.after_entry = ctk.CTkEntry(dependencies_frame)
        self.after_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.after_entry.insert(0, " ".join(self.service.unit.after or []))
        
        # Requires
        ctk.CTkLabel(dependencies_frame, text="Requires :").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.requires_entry = ctk.CTkEntry(dependencies_frame)
        self.requires_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.requires_entry.insert(0, " ".join(self.service.unit.requires or []))
        
        # Wants
        ctk.CTkLabel(dependencies_frame, text="Wants :").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.wants_entry = ctk.CTkEntry(dependencies_frame)
        self.wants_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        self.wants_entry.insert(0, " ".join(self.service.unit.wants or []))
        
        # Onglet Service
        service_tab = self.tabview.add("Service")
        service_tab.grid_columnconfigure(1, weight=1)
        
        # Type de service
        ctk.CTkLabel(service_tab, text="Type :").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.type_option = ctk.CTkOptionMenu(
            service_tab,
            values=["simple", "forking", "oneshot", "notify"],
            width=200
        )
        self.type_option.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.type_option.set(self.service.service.type or "simple")
        
        # Utilisateur
        ctk.CTkLabel(service_tab, text="Utilisateur :").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.user_entry = ctk.CTkEntry(service_tab, width=200)
        self.user_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.user_entry.insert(0, self.service.service.user or "")
        
        # Dossier de travail
        ctk.CTkLabel(service_tab, text="Dossier de travail :").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.working_dir_entry = ctk.CTkEntry(service_tab, width=400)
        self.working_dir_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.working_dir_entry.insert(0, self.service.service.working_directory or "")
        
        # Commande d'exécution
        ctk.CTkLabel(service_tab, text="Commande :").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.exec_entry = ctk.CTkEntry(service_tab, width=400)
        self.exec_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        self.exec_entry.insert(0, self.service.service.exec_start or "")
        
        # Configuration du redémarrage
        restart_frame = ctk.CTkFrame(service_tab)
        restart_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        restart_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(restart_frame, text="Redémarrage :").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.restart_option = ctk.CTkOptionMenu(
            restart_frame,
            values=["no", "always", "on-failure", "on-abnormal"],
            width=200
        )
        self.restart_option.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.restart_option.set(self.service.service.restart or "no")
        
        # Délai de redémarrage
        ctk.CTkLabel(restart_frame, text="Délai de redémarrage (s) :").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.restart_sec_entry = ctk.CTkEntry(restart_frame, width=100)
        self.restart_sec_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.restart_sec_entry.insert(0, self.service.service.restart_sec or "1")
        
        # Limites de redémarrage
        ctk.CTkLabel(restart_frame, text="Limite de redémarrages :").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.start_limit_entry = ctk.CTkEntry(restart_frame, width=100)
        self.start_limit_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.start_limit_entry.insert(0, self.service.service.start_limit_burst or "3")
        
        # Onglet Install
        install_tab = self.tabview.add("Install")
        install_tab.grid_columnconfigure(1, weight=1)
        
        # WantedBy
        ctk.CTkLabel(install_tab, text="WantedBy :").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.wanted_by_entry = ctk.CTkEntry(install_tab, width=400)
        self.wanted_by_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.wanted_by_entry.insert(0, " ".join(self.service.install.wanted_by or ["multi-user.target"]))
    
    def create_control_buttons(self):
        """Crée les boutons de contrôle"""
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Bouton Annuler
        ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=self.cancel
        ).grid(row=0, column=0, padx=10, pady=10)
        
        # Bouton Sauvegarder
        ctk.CTkButton(
            button_frame,
            text="Sauvegarder",
            command=self.save
        ).grid(row=0, column=1, padx=10, pady=10)
    
    def save(self):
        """Sauvegarde les modifications"""
        # Section Unit
        self.service.unit.description = self.description_entry.get()
        self.service.unit.after = [x.strip() for x in self.after_entry.get().split() if x.strip()]
        self.service.unit.requires = [x.strip() for x in self.requires_entry.get().split() if x.strip()]
        self.service.unit.wants = [x.strip() for x in self.wants_entry.get().split() if x.strip()]
        
        # Section Service
        self.service.service.type = self.type_option.get()
        self.service.service.user = self.user_entry.get()
        self.service.service.working_directory = self.working_dir_entry.get()
        self.service.service.exec_start = self.exec_entry.get()
        self.service.service.restart = self.restart_option.get()
        self.service.service.restart_sec = self.restart_sec_entry.get()
        
        try:
            limit = int(self.start_limit_entry.get())
            self.service.service.start_limit_burst = limit
            self.service.service.start_limit_interval = 300
        except ValueError:
            pass
        
        # Section Install
        self.service.install.wanted_by = [x.strip() for x in self.wanted_by_entry.get().split() if x.strip()]
        
        self.result = self.service
        self.destroy()
    
    def cancel(self):
        """Annule les modifications"""
        self.result = None
        self.destroy()
