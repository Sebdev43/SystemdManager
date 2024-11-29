import customtkinter as ctk
from typing import Optional
from src.models.service_model import ServiceModel
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import re

class ServiceDialog(ctk.CTkToplevel):
    """
    Base dialog class for service-related operations.
    
    This class serves as a base for service creation and editing dialogs,
    providing common functionality and UI elements.
    
    Attributes:
        result (ServiceModel): The resulting service configuration after dialog completion
        service (ServiceModel): The service being operated on
    """
    def __init__(self, parent, service: Optional[ServiceModel] = None):
        super().__init__(parent)

        self.title("Nouveau Service" if not service else "Modifier Service")
        self.geometry("800x800")

        self.update_idletasks()
        width = 800
        height = 800
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.service = service or ServiceModel("")
        self.result = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_form()
        self.create_buttons()

        self.transient(parent)
        self.grab_set()
    
    def create_form(self):

        form_frame = ctk.CTkScrollableFrame(self)
        form_frame.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="nsew")

        unit_label = ctk.CTkLabel(form_frame, text="[Unit]", font=("Arial", 16, "bold"))
        unit_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        ctk.CTkLabel(form_frame, text="Description :").grid(row=1, column=0, sticky="w")
        description_entry = ctk.CTkEntry(form_frame, width=300)
        description_entry.grid(row=1, column=1, pady=5, sticky="w")
        description_entry.insert(0, self.service.unit.description or "")

        ctk.CTkLabel(form_frame, text="Documentation :").grid(row=2, column=0, sticky="w")
        documentation_entry = ctk.CTkEntry(form_frame, width=300)
        documentation_entry.grid(row=2, column=1, pady=5, sticky="w")
        documentation_entry.insert(0, self.service.unit.documentation or "")

        service_label = ctk.CTkLabel(form_frame, text="[Service]", font=("Arial", 16, "bold"))
        service_label.grid(row=3, column=0, columnspan=2, pady=(20, 10), sticky="w")

        ctk.CTkLabel(form_frame, text="Type :").grid(row=4, column=0, sticky="w")
        type_combobox = ctk.CTkComboBox(form_frame, values=["simple", "forking", "oneshot", "notify"])
        type_combobox.grid(row=4, column=1, pady=5, sticky="w")
        type_combobox.set(self.service.service.type or "simple")

        ctk.CTkLabel(form_frame, text="Utilisateur :").grid(row=5, column=0, sticky="w")
        user_entry = ctk.CTkEntry(form_frame, width=300)
        user_entry.grid(row=5, column=1, pady=5, sticky="w")
        user_entry.insert(0, self.service.service.user or "")

        ctk.CTkLabel(form_frame, text="Groupe :").grid(row=6, column=0, sticky="w")
        group_entry = ctk.CTkEntry(form_frame, width=300)
        group_entry.grid(row=6, column=1, pady=5, sticky="w")
        group_entry.insert(0, self.service.service.group or "")

        ctk.CTkLabel(form_frame, text="Dossier de travail :").grid(row=7, column=0, sticky="w")
        working_dir_frame = ctk.CTkFrame(form_frame)
        working_dir_frame.grid(row=7, column=1, pady=5, sticky="w")
        working_dir_entry = ctk.CTkEntry(working_dir_frame, width=250)
        working_dir_entry.pack(side="left", padx=(0, 5))
        working_dir_entry.insert(0, self.service.service.working_directory or "")
        browse_button = ctk.CTkButton(working_dir_frame, text="...", width=40, command=lambda: self.browse_directory(working_dir_entry))
        browse_button.pack(side="left")

        ctk.CTkLabel(form_frame, text="ExecStart :").grid(row=8, column=0, sticky="w")
        execstart_entry = ctk.CTkEntry(form_frame, width=300)
        execstart_entry.grid(row=8, column=1, pady=5, sticky="w")
        execstart_entry.insert(0, self.service.service.exec_start or "")

        ctk.CTkLabel(form_frame, text="ExecStop :").grid(row=9, column=0, sticky="w")
        execstop_entry = ctk.CTkEntry(form_frame, width=300)
        execstop_entry.grid(row=9, column=1, pady=5, sticky="w")
        execstop_entry.insert(0, self.service.service.exec_stop or "")

        ctk.CTkLabel(form_frame, text="Restart :").grid(row=10, column=0, sticky="w")
        restart_combobox = ctk.CTkComboBox(form_frame, values=["no", "on-success", "on-failure", "on-abnormal", "on-abort", "always"])
        restart_combobox.grid(row=10, column=1, pady=5, sticky="w")
        restart_combobox.set(self.service.service.restart or "no")

        ctk.CTkLabel(form_frame, text="Délai de redémarrage (s) :").grid(row=11, column=0, sticky="w")
        restart_sec_entry = ctk.CTkEntry(form_frame, width=100)
        restart_sec_entry.grid(row=11, column=1, pady=5, sticky="w")
        restart_sec_entry.insert(0, str(self.service.service.restart_sec or 0))

        resources_label = ctk.CTkLabel(form_frame, text="Limites de ressources", font=("Arial", 14, "bold"))
        resources_label.grid(row=12, column=0, columnspan=2, pady=(20, 10), sticky="w")

        ctk.CTkLabel(form_frame, text="Limite mémoire :").grid(row=13, column=0, sticky="w")
        memory_frame = ctk.CTkFrame(form_frame)
        memory_frame.grid(row=13, column=1, pady=5, sticky="w")
        memory_entry = ctk.CTkEntry(memory_frame, width=200)
        memory_entry.pack(side="left", padx=(0, 5))
        memory_entry.insert(0, self.service.service.memory_limit or "")
        memory_unit = ctk.CTkComboBox(memory_frame, values=["M", "G"], width=80)
        memory_unit.pack(side="left")
        memory_unit.set("M")

        ctk.CTkLabel(form_frame, text="Quota CPU (%) :").grid(row=14, column=0, sticky="w")
        cpu_entry = ctk.CTkEntry(form_frame, width=100)
        cpu_entry.grid(row=14, column=1, pady=5, sticky="w")
        cpu_entry.insert(0, str(self.service.service.cpu_quota or 100))

        install_label = ctk.CTkLabel(form_frame, text="[Install]", font=("Arial", 16, "bold"))
        install_label.grid(row=15, column=0, columnspan=2, pady=(20, 10), sticky="w")

        ctk.CTkLabel(form_frame, text="WantedBy :").grid(row=16, column=0, sticky="w")
        wantedby_entry = ctk.CTkEntry(form_frame, width=300)
        wantedby_entry.grid(row=16, column=1, pady=5, sticky="w")
        wantedby_entry.insert(0, self.service.install.wanted_by or "multi-user.target")

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

        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=self.cancel
        ).grid(row=0, column=0, padx=10, pady=10)

        ctk.CTkButton(
            button_frame,
            text="Enregistrer",
            command=self.save
        ).grid(row=0, column=1, padx=10, pady=10)
    
    def save(self):

        if not self.validate_fields():
            return

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

        self.result = False
        self.destroy()

    def browse_directory(self, entry_widget):

        directory = filedialog.askdirectory(
            title="Sélectionner le dossier de travail",
            initialdir=entry_widget.get() or "/"
        )
        if directory:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, directory)

    def validate_fields(self) -> bool:

        try:
            errors = []
            warnings = []

            name = getattr(self.service, 'name', None)
            if name and not re.match(r'^[a-zA-Z][a-zA-Z0-9-_]*$', name):
                errors.append("Le nom du service doit commencer par une lettre et ne contenir que des lettres, chiffres, tirets et underscores")

            description = self.description_entry.get().strip()
            if len(description) > 256:
                errors.append("La description est trop longue (maximum 256 caractères)")

            try:
                restart_sec = int(self.restart_sec_entry.get() or 0)
                if restart_sec < 0:
                    errors.append("Le délai de redémarrage doit être positif")
                elif restart_sec > 300:
                    warnings.append("Un délai de redémarrage supérieur à 5 minutes pourrait être problématique")
            except ValueError:
                errors.append("Le délai de redémarrage doit être un nombre entier")

            try:
                cpu_quota = int(self.cpu_entry.get() or 100)
                if not 0 <= cpu_quota <= 100:
                    errors.append("Le quota CPU doit être entre 0 et 100")
                elif cpu_quota < 10:
                    warnings.append("Un quota CPU très bas pourrait affecter les performances du service")
            except ValueError:
                errors.append("Le quota CPU doit être un nombre entier")

            memory_value = self.memory_entry.get().strip()
            if memory_value:
                try:
                    memory = int(memory_value)
                    unit = self.memory_unit.get()
                    if memory <= 0:
                        errors.append("La limite de mémoire doit être positive")
                    elif unit == 'G' and memory > 32:
                        warnings.append("Une limite de mémoire très élevée pourrait affecter le système")
                except ValueError:
                    errors.append("La limite de mémoire doit être un nombre entier")

            working_dir = self.working_dir_entry.get().strip()
            if working_dir:
                if not os.path.isabs(working_dir):
                    errors.append("Le dossier de travail doit être un chemin absolu")
                elif not os.path.isdir(working_dir):
                    errors.append("Le dossier de travail spécifié n'existe pas")
                elif not os.access(working_dir, os.R_OK | os.X_OK):
                    warnings.append("Le dossier de travail pourrait ne pas être accessible")

            exec_start = self.execstart_entry.get().strip()
            if not exec_start:
                errors.append("La commande ExecStart est requise")
            else:
                cmd_parts = exec_start.split()
                if cmd_parts:
                    executable = cmd_parts[0]
                    if not os.path.isabs(executable):
                        errors.append("La commande ExecStart doit utiliser un chemin absolu")
                    elif os.path.exists(executable):
                        if not os.path.isfile(executable):
                            errors.append(f"'{executable}' n'est pas un fichier")
                        elif not os.access(executable, os.X_OK):
                            if not executable.endswith(('.sh', '.py', '.bash', '.js')):
                                warnings.append(f"'{executable}' n'a pas les permissions d'exécution")

            if errors:
                error_message = "Erreurs de validation :\n• " + "\n• ".join(errors)
                if warnings:
                    error_message += "\n\nAvertissements :\n• " + "\n• ".join(warnings)
                messagebox.showerror("Erreur de validation", error_message)
                return False

            if warnings:
                warning_message = "Avertissements :\n• " + "\n• ".join(warnings)
                result = messagebox.askokcancel("Avertissements", warning_message + "\n\nVoulez-vous continuer ?")
                return result

            return True

        except Exception as e:
            messagebox.showerror("Erreur de validation", f"Une erreur inattendue s'est produite : {str(e)}")
            return False
