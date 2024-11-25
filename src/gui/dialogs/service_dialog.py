import customtkinter as ctk
from typing import Optional
from src.models.service_model import ServiceModel
import tkinter as tk
from tkinter import messagebox, filedialog
import os

class ServiceDialog(ctk.CTkToplevel):
    def __init__(self, parent, service: Optional[ServiceModel] = None):
        super().__init__(parent)
        
        # Configuration de la fenêtre
        self.title("Nouveau Service" if not service else "Modifier Service")
        self.geometry("800x800")
        
        # Centrer la fenêtre
        self.update_idletasks()
        width = 800
        height = 800
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Variables
        self.service = service or ServiceModel("")
        self.result = False
        
        # Configuration de la grille principale
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Création des widgets
        self.create_form()
        self.create_buttons()
        
        # Rendre la fenêtre modale
        self.transient(parent)
        self.grab_set()
    
    def create_form(self):
        """Crée le formulaire"""
        # Frame pour les champs
        form_frame = ctk.CTkScrollableFrame(self)
        form_frame.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="nsew")
        
        # Section [Unit]
        unit_label = ctk.CTkLabel(form_frame, text="[Unit]", font=("Arial", 16, "bold"))
        unit_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        # Description
        ctk.CTkLabel(form_frame, text="Description :").grid(row=1, column=0, sticky="w")
        description_entry = ctk.CTkEntry(form_frame, width=300)
        description_entry.grid(row=1, column=1, pady=5, sticky="w")
        description_entry.insert(0, self.service.unit.description or "")
        
        # Documentation
        ctk.CTkLabel(form_frame, text="Documentation :").grid(row=2, column=0, sticky="w")
        documentation_entry = ctk.CTkEntry(form_frame, width=300)
        documentation_entry.grid(row=2, column=1, pady=5, sticky="w")
        documentation_entry.insert(0, self.service.unit.documentation or "")
        
        # Section [Service]
        service_label = ctk.CTkLabel(form_frame, text="[Service]", font=("Arial", 16, "bold"))
        service_label.grid(row=3, column=0, columnspan=2, pady=(20, 10), sticky="w")
        
        # Type
        ctk.CTkLabel(form_frame, text="Type :").grid(row=4, column=0, sticky="w")
        type_combobox = ctk.CTkComboBox(form_frame, values=["simple", "forking", "oneshot", "notify"])
        type_combobox.grid(row=4, column=1, pady=5, sticky="w")
        type_combobox.set(self.service.service.type or "simple")

        # Utilisateur et Groupe
        ctk.CTkLabel(form_frame, text="Utilisateur :").grid(row=5, column=0, sticky="w")
        user_entry = ctk.CTkEntry(form_frame, width=300)
        user_entry.grid(row=5, column=1, pady=5, sticky="w")
        user_entry.insert(0, self.service.service.user or "")

        ctk.CTkLabel(form_frame, text="Groupe :").grid(row=6, column=0, sticky="w")
        group_entry = ctk.CTkEntry(form_frame, width=300)
        group_entry.grid(row=6, column=1, pady=5, sticky="w")
        group_entry.insert(0, self.service.service.group or "")

        # Dossier de travail
        ctk.CTkLabel(form_frame, text="Dossier de travail :").grid(row=7, column=0, sticky="w")
        working_dir_frame = ctk.CTkFrame(form_frame)
        working_dir_frame.grid(row=7, column=1, pady=5, sticky="w")
        working_dir_entry = ctk.CTkEntry(working_dir_frame, width=250)
        working_dir_entry.pack(side="left", padx=(0, 5))
        working_dir_entry.insert(0, self.service.service.working_directory or "")
        browse_button = ctk.CTkButton(working_dir_frame, text="...", width=40, command=lambda: self.browse_directory(working_dir_entry))
        browse_button.pack(side="left")
        
        # ExecStart
        ctk.CTkLabel(form_frame, text="ExecStart :").grid(row=8, column=0, sticky="w")
        execstart_entry = ctk.CTkEntry(form_frame, width=300)
        execstart_entry.grid(row=8, column=1, pady=5, sticky="w")
        execstart_entry.insert(0, self.service.service.exec_start or "")
        
        # ExecStop
        ctk.CTkLabel(form_frame, text="ExecStop :").grid(row=9, column=0, sticky="w")
        execstop_entry = ctk.CTkEntry(form_frame, width=300)
        execstop_entry.grid(row=9, column=1, pady=5, sticky="w")
        execstop_entry.insert(0, self.service.service.exec_stop or "")
        
        # Restart
        ctk.CTkLabel(form_frame, text="Restart :").grid(row=10, column=0, sticky="w")
        restart_combobox = ctk.CTkComboBox(form_frame, values=["no", "on-success", "on-failure", "on-abnormal", "on-abort", "always"])
        restart_combobox.grid(row=10, column=1, pady=5, sticky="w")
        restart_combobox.set(self.service.service.restart or "no")

        # Délai de redémarrage
        ctk.CTkLabel(form_frame, text="Délai de redémarrage (s) :").grid(row=11, column=0, sticky="w")
        restart_sec_entry = ctk.CTkEntry(form_frame, width=100)
        restart_sec_entry.grid(row=11, column=1, pady=5, sticky="w")
        restart_sec_entry.insert(0, str(self.service.service.restart_sec or 0))

        # Limites de ressources
        resources_label = ctk.CTkLabel(form_frame, text="Limites de ressources", font=("Arial", 14, "bold"))
        resources_label.grid(row=12, column=0, columnspan=2, pady=(20, 10), sticky="w")

        # Mémoire
        ctk.CTkLabel(form_frame, text="Limite mémoire :").grid(row=13, column=0, sticky="w")
        memory_frame = ctk.CTkFrame(form_frame)
        memory_frame.grid(row=13, column=1, pady=5, sticky="w")
        memory_entry = ctk.CTkEntry(memory_frame, width=200)
        memory_entry.pack(side="left", padx=(0, 5))
        memory_entry.insert(0, self.service.service.memory_limit or "")
        memory_unit = ctk.CTkComboBox(memory_frame, values=["M", "G"], width=80)
        memory_unit.pack(side="left")
        memory_unit.set("M")

        # CPU
        ctk.CTkLabel(form_frame, text="Quota CPU (%) :").grid(row=14, column=0, sticky="w")
        cpu_entry = ctk.CTkEntry(form_frame, width=100)
        cpu_entry.grid(row=14, column=1, pady=5, sticky="w")
        cpu_entry.insert(0, str(self.service.service.cpu_quota or 100))

        # Section [Install]
        install_label = ctk.CTkLabel(form_frame, text="[Install]", font=("Arial", 16, "bold"))
        install_label.grid(row=15, column=0, columnspan=2, pady=(20, 10), sticky="w")
        
        # WantedBy
        ctk.CTkLabel(form_frame, text="WantedBy :").grid(row=16, column=0, sticky="w")
        wantedby_entry = ctk.CTkEntry(form_frame, width=300)
        wantedby_entry.grid(row=16, column=1, pady=5, sticky="w")
        wantedby_entry.insert(0, self.service.install.wanted_by or "multi-user.target")
        
        # Enregistrement des entrées
        self.description_entry = description_entry
        self.documentation_entry = documentation_entry
        self.type_combobox = type_combobox
        self.user_entry = user_entry
        self.group_entry = group_entry
        self.working_dir_entry = working_dir_entry
        self.execstart_entry = execstart_entry
        self.execstop_entry = execstop_entry
        self.restart_combobox = restart_combobox
        self.restart_sec_entry = restart_sec_entry
        self.memory_entry = memory_entry
        self.memory_unit = memory_unit
        self.cpu_entry = cpu_entry
        self.wantedby_entry = wantedby_entry
    
    def create_buttons(self):
        """Crée les boutons de validation/annulation"""
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Bouton Annuler
        ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=self.cancel
        ).grid(row=0, column=0, padx=10, pady=10)
        
        # Bouton Enregistrer
        ctk.CTkButton(
            button_frame,
            text="Enregistrer",
            command=self.save
        ).grid(row=0, column=1, padx=10, pady=10)
    
    def save(self):
        """Enregistre le service"""
        if not self.validate_fields():
            return
        
        # Mise à jour du modèle
        self.service.unit.description = self.description_entry.get()
        self.service.unit.documentation = self.documentation_entry.get()
        self.service.service.type = self.type_combobox.get()
        self.service.service.user = self.user_entry.get()
        self.service.service.group = self.group_entry.get()
        self.service.service.working_directory = self.working_dir_entry.get()
        self.service.service.exec_start = self.execstart_entry.get()
        self.service.service.exec_stop = self.execstop_entry.get()
        self.service.service.restart = self.restart_combobox.get()
        self.service.service.restart_sec = int(self.restart_sec_entry.get() or 0)
        self.service.service.memory_limit = self.memory_entry.get() + self.memory_unit.get()
        self.service.service.cpu_quota = int(self.cpu_entry.get() or 100)
        self.service.install.wanted_by = self.wantedby_entry.get()
        
        self.result = self.service
        self.destroy()
    
    def cancel(self):
        """Annule la création/modification"""
        self.result = False
        self.destroy()

    def browse_directory(self, entry_widget):
        """Ouvre un dialogue pour sélectionner un dossier"""
        directory = filedialog.askdirectory(
            title="Sélectionner le dossier de travail",
            initialdir=entry_widget.get() or "/"
        )
        if directory:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, directory)

    def validate_fields(self):
        """Valide les champs du formulaire"""
        try:
            # Validation du délai de redémarrage
            restart_sec = int(self.restart_sec_entry.get() or 0)
            if restart_sec < 0:
                raise ValueError("Le délai de redémarrage doit être positif")

            # Validation du quota CPU
            cpu_quota = int(self.cpu_entry.get() or 100)
            if not 0 <= cpu_quota <= 100:
                raise ValueError("Le quota CPU doit être entre 0 et 100")

            # Validation du dossier de travail
            working_dir = self.working_dir_entry.get()
            if working_dir and not os.path.isdir(working_dir):
                raise ValueError("Le dossier de travail spécifié n'existe pas")

            # Validation de la commande ExecStart
            if not self.execstart_entry.get().strip():
                raise ValueError("La commande ExecStart est requise")

            return True

        except ValueError as e:
            messagebox.showerror("Erreur de validation", str(e))
            return False
