import customtkinter as ctk
from src.models.service_model import ServiceModel
from typing import List
import os
import subprocess
from src.i18n.translations import _

class ServiceCreationFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)  # Utiliser la couleur de fond par défaut
        self.parent = parent
        self.app = self.winfo_toplevel()
        
        # Style des textes d'aide
        self.help_text_style = {
            "text_color": "gray60",  # Plus lisible en mode clair
            "font": ("", 10),
            "justify": "left",
            "anchor": "w"
        }
        
        # Padding standard
        self.padding = {"padx": 10, "pady": (2, 5)}
        self.help_padding = {"padx": (25, 10), "pady": (0, 10)}
        
        # Configuration de la grille principale
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Créer un conteneur scrollable qui prend tout l'espace
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=0
        )
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Ajuster la marge de la scrollbar
        scrollbar = self.scrollable_frame._scrollbar
        scrollbar.grid(padx=(5, 0))
        
        # Configuration du défilement avec la molette
        canvas = self.scrollable_frame._parent_canvas
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Bind les événements de la molette de souris
        self.scrollable_frame.bind_all("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind_all("<Button-4>", self._on_mousewheel)
        self.scrollable_frame.bind_all("<Button-5>", self._on_mousewheel)

        # Configuration du frame interne
        self.scrollable_frame._scrollbar.grid_configure(padx=(5, 0))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=3)
        
        # Variables
        self.service_name_var = ctk.StringVar()
        self.description_var = ctk.StringVar()
        self.type_var = ctk.StringVar(value="simple")
        self.user_var = ctk.StringVar(value=os.getenv('SUDO_USER', os.getenv('USER', 'root')))
        self.working_dir_var = ctk.StringVar()
        self.exec_start_var = ctk.StringVar()
        self.restart_var = ctk.StringVar(value="no")
        self.restart_sec_var = ctk.StringVar(value="0")
        self.command_method_var = ctk.StringVar(value="manual")
        self.executable_var = ctk.StringVar()
        self.args_var = ctk.StringVar()
        self.use_screen_var = ctk.BooleanVar(value=False)
        self.executables_var = ctk.StringVar()
        # Nouvelles variables
        self.start_delay_var = ctk.StringVar(value="0")
        self.max_restarts_var = ctk.StringVar(value="3")
        self.start_after_save_var = ctk.BooleanVar(value=True)
        
        # Création des widgets
        self.create_form()
        self.create_buttons()
    
    def create_form(self):
        """Crée le formulaire de création de service"""
        padding = {"padx": 10, "pady": 5}
        row = 0

        # Section Informations de base
        self.create_section_label(_("Basic Information"), row)
        row += 1

        # Frame pour les informations de base
        base_info_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent",
        )
        base_info_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        base_info_frame.grid_columnconfigure(1, weight=1)

        # Nom du service
        name_frame = ctk.CTkFrame(base_info_frame, fg_color="transparent")
        name_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        name_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(name_frame, text=_("Service Name *")).grid(row=0, column=0, padx=5, sticky="w")
        name_entry = ctk.CTkEntry(name_frame, textvariable=self.service_name_var)
        name_entry.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkLabel(name_frame, 
            text=_("Service name without .service extension\nExample: my-app"), 
            text_color="gray60",
            font=("", 10)
        ).grid(row=1, column=1, padx=5, sticky="w")
        row += 2

        # Description
        ctk.CTkLabel(base_info_frame, text=_("Description")).grid(row=row, column=0, **self.padding, sticky="w")
        ctk.CTkEntry(base_info_frame, textvariable=self.description_var).grid(row=row, column=1, **self.padding, sticky="ew")
        ctk.CTkLabel(
            base_info_frame,
            text=_("Short description of the service\nExample: System monitoring service"),
            text_color="gray60",
            font=("", 10)
        ).grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        # Type de service
        ctk.CTkLabel(base_info_frame, text=_("Service Type")).grid(row=row, column=0, **self.padding, sticky="w")
        type_menu = ctk.CTkOptionMenu(
            base_info_frame,
            values=["simple", "forking", "oneshot", "notify"],
            variable=self.type_var
        )
        type_menu.grid(row=row, column=1, **self.padding, sticky="ew")
        
        type_descriptions = {
            "simple": _("Main process stays in foreground"),
            "forking": _("Process detaches to background"),
            "oneshot": _("Runs once and stops"),
            "notify": _("Like simple, but with notifications")
        }
        ctk.CTkLabel(
            base_info_frame,
            text=_("Available service types:\n") + "\n".join([f"• {k}: {v}" for k, v in type_descriptions.items()]),
            text_color="gray60",
            font=("", 10)
        ).grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        # Section Configuration d'exécution
        self.create_section_label(_("Execution Configuration"), row)
        row += 1

        # Frame pour la configuration d'exécution
        exec_config_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent",
        )
        exec_config_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        exec_config_frame.grid_columnconfigure(1, weight=1)

        # Utilisateur
        ctk.CTkLabel(exec_config_frame, text=_("User")).grid(row=row, column=0, **self.padding, sticky="w")
        users = self.get_system_users()
        user_menu = ctk.CTkOptionMenu(
            exec_config_frame,
            values=users,
            variable=self.user_var
        )
        user_menu.grid(row=row, column=1, **self.padding, sticky="ew")
        ctk.CTkLabel(exec_config_frame, 
            text=_("User who runs the service\nCurrent user by default, root for system services"), 
            text_color="gray60",
            font=("", 10)
        ).grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        # Dossier de travail
        dir_frame = ctk.CTkFrame(exec_config_frame, fg_color="transparent")
        dir_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        dir_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(dir_frame, text=_("Working Directory")).grid(row=0, column=0, padx=5, sticky="w")
        working_dir_entry = ctk.CTkEntry(dir_frame, textvariable=self.working_dir_var)
        working_dir_entry.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkButton(dir_frame, text="📂", width=50, command=self.browse_directory).grid(row=0, column=2, padx=5)
        ctk.CTkLabel(exec_config_frame, 
            text=_("Directory where the service runs\nAbsolute path required. Example: /home/user/app"), 
            text_color="gray60",
            font=("", 10)
        ).grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        # Commande d'exécution
        self.command_frame = ctk.CTkFrame(
            exec_config_frame,
        )
        self.command_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        self.command_frame.grid_columnconfigure(1, weight=1)

        # Conteneur horizontal pour les radio buttons
        radio_frame = ctk.CTkFrame(self.command_frame, fg_color="transparent")
        radio_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=5)
        
        ctk.CTkRadioButton(
            radio_frame,
            text=_("Manual Input"),
            variable=self.command_method_var,
            value="manual",
            command=self.update_command_frame
        ).grid(row=0, column=0, padx=(0, 10))
        
        ctk.CTkRadioButton(
            radio_frame,
            text=_("Select Executable"),
            variable=self.command_method_var,
            value="browse",
            command=self.update_command_frame
        ).grid(row=0, column=1)

        # Frame pour la saisie manuelle
        self.manual_frame = ctk.CTkFrame(
            self.command_frame,
        )
        self.manual_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.manual_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.manual_frame, text=_("Command *")).grid(row=0, column=0, padx=5, sticky="w")
        self.manual_entry = ctk.CTkEntry(
            self.manual_frame,
            textvariable=self.exec_start_var,
            placeholder_text=_("Full command (e.g.: /usr/bin/python3 script.py)")
        )
        self.manual_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.manual_entry.bind('<FocusOut>', self.validate_manual_command)

        # Frame pour la navigation
        self.browse_frame = ctk.CTkFrame(
            self.command_frame,
        )
        self.browse_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.browse_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.browse_frame, text=_("Executable *")).grid(row=0, column=0, padx=5, sticky="w")
        executable_container = ctk.CTkFrame(self.browse_frame, fg_color="transparent")
        executable_container.grid(row=0, column=1, sticky="ew", padx=5)
        executable_container.grid_columnconfigure(0, weight=1)
        
        self.executable_menu = ctk.CTkOptionMenu(
            executable_container,
            variable=self.executables_var,
            values=[_("Select working directory first")],
            command=self.on_executable_selected
        )
        self.executable_menu.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        ctk.CTkButton(
            executable_container,
            text="🔄",
            width=30,
            command=self.refresh_executables
        ).grid(row=0, column=1)
        
        ctk.CTkLabel(self.browse_frame, text=_("Arguments")).grid(row=1, column=0, padx=5, pady=(5,0), sticky="w")
        self.args_entry = ctk.CTkEntry(
            self.browse_frame,
            textvariable=self.args_var,
            placeholder_text=_("Optional arguments")
        )
        self.args_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))
        self.args_entry.bind('<KeyRelease>', lambda e: self.update_command())

        # Frame pour l'option screen (commun aux deux modes)
        screen_frame = ctk.CTkFrame(
            self.command_frame,
        )
        screen_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.screen_check = ctk.CTkCheckBox(
            screen_frame,
            text=_("Use screen"),
            variable=self.use_screen_var,
            command=self.update_command
        )
        self.screen_check.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        
        ctk.CTkLabel(exec_config_frame, 
            text=_("Command to execute\nExample: /usr/bin/python3 /home/user/app/main.py"), 
            text_color="gray60",
            font=("", 10)
        ).grid(row=row+2, column=1, **self.help_padding, sticky="w")
        row += 3

        # Section Options avancées
        self.create_section_label(_("Advanced Options"), row)
        row += 1

        # Frame pour les options avancées
        advanced_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent",
        )
        advanced_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        advanced_frame.grid_columnconfigure(1, weight=1)

        # Politique de redémarrage
        ctk.CTkLabel(advanced_frame, text=_("Restart")).grid(row=row, column=0, **self.padding, sticky="w")
        restart_menu = ctk.CTkOptionMenu(
            advanced_frame,
            values=["no", "always", "on-failure", "on-abnormal", "on-abort"],
            variable=self.restart_var,
            width=300
        )
        restart_menu.grid(row=row, column=1, **self.padding, sticky="ew")
        
        restart_descriptions = {
            "no": _("No automatic restart"),
            "always": _("Restarts after normal stop or error"),
            "on-failure": _("Restarts only on error"),
            "on-abnormal": _("Restarts on error or signal"),
            "on-abort": _("Restarts if process is aborted")
        }
        ctk.CTkLabel(
            advanced_frame,
            text=_("Restart policies:\n") + "\n".join([f"• {k}: {v}" for k, v in restart_descriptions.items()]),
            text_color="gray60",
            font=("", 10)
        ).grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        # Délai de redémarrage
        ctk.CTkLabel(advanced_frame, text=_("Restart Delay (sec)")).grid(row=row, column=0, **self.padding, sticky="w")
        ctk.CTkEntry(advanced_frame, textvariable=self.restart_sec_var, width=300).grid(row=row, column=1, **self.padding, sticky="ew")
        ctk.CTkLabel(advanced_frame, 
            text=_("Wait time in seconds before restarting\n0 = immediate restart"), 
            text_color="gray60",
            font=("", 10)
        ).grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        # Délai de démarrage après le boot
        ctk.CTkLabel(advanced_frame, text=_("Start Delay after boot (sec)")).grid(row=row, column=0, **self.padding, sticky="w")
        ctk.CTkEntry(advanced_frame, textvariable=self.start_delay_var, width=300).grid(row=row, column=1, **self.padding, sticky="ew")
        ctk.CTkLabel(advanced_frame, 
            text=_("Wait time in seconds before starting after boot\n0 = immediate start"), 
            text_color="gray60",
            font=("", 10)
        ).grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        # Nombre maximum de redémarrages
        ctk.CTkLabel(advanced_frame, text=_("Maximum number of restarts")).grid(row=row, column=0, **self.padding, sticky="w")
        ctk.CTkEntry(advanced_frame, textvariable=self.max_restarts_var, width=300).grid(row=row, column=1, **self.padding, sticky="ew")
        ctk.CTkLabel(advanced_frame, 
            text=_("Maximum number of restarts allowed in 5 minutes\nDefault: 3"), 
            text_color="gray60",
            font=("", 10)
        ).grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        # Option de démarrage après sauvegarde
        ctk.CTkCheckBox(
            advanced_frame,
            text=_("Start service after saving"),
            variable=self.start_after_save_var
        ).grid(row=row, column=0, columnspan=2, **self.padding, sticky="w")
        row += 1

        # Initialiser l'affichage de la commande
        self.update_command_frame()
    
    def create_section_label(self, text, row):
        """Crée un label de section avec un style distinctif"""
        section_frame = ctk.CTkFrame(
            self.scrollable_frame,
        )
        section_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        ctk.CTkLabel(
            section_frame,
            text=text,
            font=("", 16, "bold")
        ).grid(row=0, column=0, padx=10, pady=5)
    
    def create_buttons(self):
        """Crée les boutons de contrôle"""
        buttons_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent",
        )
        buttons_frame.grid(row=99, column=0, columnspan=2, sticky="nsew", pady=(20, 0))
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        buttons_frame.grid_rowconfigure(0, weight=1)
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text=_("Cancel"),
            command=self.cancel_creation,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90"),
            height=40,  # Hauteur fixe pour maintenir l'aspect
            width=120   # Largeur minimale
        )
        cancel_btn.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        
        create_btn = ctk.CTkButton(
            buttons_frame,
            text=_("Create Service"),
            command=self.create_service,
            height=40,  # Hauteur fixe pour maintenir l'aspect
            width=120   # Largeur minimale
        )
        create_btn.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

    def cancel_creation(self):
        """Annule la création et réinitialise le formulaire"""
        self.reset_form()
        # Retour à la page des services
        self.app.switch_tab(_("services"))
        
    def create_service(self):
        """Crée le service avec les données du formulaire"""
        # Validation des données
        valid, error_message = self.validate_form()
        if not valid:
            self.show_error(error_message)
            return
        
        try:
            # Étape 1: Validation du nom du service
            service_name = self.service_name_var.get().strip()
            if not service_name:
                raise ValueError(_("Le nom du service est requis"))
            
            # Création du service
            service = ServiceModel(service_name)
            
            # Étape 2: Description
            service.unit.description = self.description_var.get().strip()
            
            # Étape 3: Type de service
            service.service.type = self.type_var.get()
            
            # Étape 4: Configuration utilisateur
            service.service.user = self.user_var.get()
            
            # Étape 5: Dossier de travail
            working_dir = self.working_dir_var.get().strip()
            if working_dir:
                if not os.path.isabs(working_dir):
                    raise ValueError(_("Le dossier de travail doit être un chemin absolu"))
                if not os.path.exists(working_dir):
                    raise ValueError(_("Le dossier de travail n'existe pas"))
                service.service.working_directory = working_dir
            
            # Étape 6: Commande d'exécution
            exec_command = self.exec_start_var.get().strip()
            if not exec_command:
                raise ValueError(_("La commande d'exécution est requise"))
            service.service.exec_start = exec_command
            
            # Configuration du redémarrage
            service.service.restart = self.restart_var.get()
            service.service.restart_sec = int(self.restart_sec_var.get() or 0)
            
            # Limites de redémarrage
            service.unit.start_limit_burst = int(self.max_restarts_var.get() or 3)
            service.unit.start_limit_interval = 300  # 5 minutes
            
            # Sauvegarde du service
            if not self.app.gui_controller.save_service(service):
                raise Exception(_("Échec de la sauvegarde du service"))
            
            # Démarrage du service si demandé
            start_success = False
            if self.start_after_save_var.get():
                start_success = self.app.gui_controller.start_service(service.name)
            
            # Vérifier le statut du service
            status = self.app.gui_controller.get_service_status(service.name)
            
            # Message de succès
            if self.start_after_save_var.get():
                if start_success and status["active"] == "active":
                    message = _("Service créé et démarré avec succès !")
                else:
                    raise Exception(_("Le service a été créé mais n'a pas pu être démarré correctement"))
            else:
                if status["load"] == "loaded":
                    message = _("Service créé avec succès !")
                else:
                    raise Exception(_("Le service a été créé mais n'a pas été chargé correctement"))
            
            self.show_success(message)
            self.reset_form()
            
            # Retour à la page des services et rafraîchissement
            self.app.switch_tab(_("services"))
            self.app.refresh_current_tab()
            
        except Exception as e:
            self.show_error(_("Erreur lors de la création du service : ") + str(e))
    
    def reset_form(self):
        """Réinitialise tous les champs du formulaire"""
        self.service_name_var.set("")
        self.description_var.set("")
        self.type_var.set("simple")
        self.user_var.set("")
        self.working_dir_var.set("")
        self.exec_start_var.set("")
        self.restart_var.set("no")
        self.restart_sec_var.set("0")
        self.use_screen_var.set(False)
        self.command_method_var.set("manual")
        self.executable_var.set("")
        self.args_var.set("")
        self.start_delay_var.set("0")
        self.max_restarts_var.set("3")
        self.start_after_save_var.set(True)

    def validate_working_directory(self, event=None):
        """Valide le dossier de travail"""
        working_dir = self.working_dir_var.get().strip()
        
        # Si le champ est vide, on ne fait rien
        if not working_dir:
            return
            
        # Expansion du chemin
        working_dir = os.path.expanduser(working_dir)
        working_dir = os.path.expandvars(working_dir)
        working_dir = os.path.abspath(working_dir)
        
        try:
            # Vérifie si le chemin existe
            if not os.path.exists(working_dir):
                self.working_dir_var.set("")
                self.after(100, lambda: self.show_error(_("Le dossier spécifié n'existe pas.")))
                return False
                
            # Vérifie si c'est un dossier
            if not os.path.isdir(working_dir):
                self.working_dir_var.set("")
                self.after(100, lambda: self.show_error(_("Le chemin spécifié n'est pas un dossier.")))
                return False
                
            # Vérifie les permissions
            if not os.access(working_dir, os.R_OK):
                self.working_dir_var.set("")
                self.after(100, lambda: self.show_error(_("Vous n'avez pas les permissions pour accéder à ce dossier.")))
                return False
                
            # Met à jour le champ avec le chemin absolu
            self.working_dir_var.set(working_dir)
            return True
            
        except Exception as e:
            self.working_dir_var.set("")
            self.after(100, lambda: self.show_error(_("Erreur lors de la validation du dossier : ") + str(e)))
            return False

    def browse_directory(self):
        """Assistant de navigation dans les dossiers"""
        # Détermine le point de départ en fonction de l'utilisateur sélectionné
        selected_user = self.user_var.get()
        if selected_user == "root":
            current_path = "/"
        else:
            # Pour un utilisateur normal, utiliser son dossier personnel
            try:
                with open('/etc/passwd', 'r') as f:
                    for line in f:
                        user_info = line.strip().split(':')
                        if user_info[0] == selected_user:
                            current_path = user_info[5]  # Le 6ème champ est le home directory
                            break
                    else:
                        current_path = os.path.expanduser('~')
            except Exception:
                current_path = os.path.expanduser('~')
        
        try:
            # Crée une nouvelle fenêtre pour la navigation
            dialog = ctk.CTkToplevel(self)
            dialog.title(_("Select Working Directory"))
            dialog.geometry("700x500")
            dialog.grid_columnconfigure(0, weight=1)
            dialog.grid_rowconfigure(1, weight=1)
            
            # Frame pour le chemin et les options
            top_frame = ctk.CTkFrame(dialog)
            top_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
            top_frame.grid_columnconfigure(1, weight=1)
            
            # Label pour afficher le chemin actuel
            path_label = ctk.CTkLabel(top_frame, text=_("Current Directory:"))
            path_label.grid(row=0, column=0, padx=5, pady=5)
            
            # Entry pour le chemin avec possibilité de saisie manuelle
            path_entry = ctk.CTkEntry(top_frame)
            path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            path_entry.insert(0, current_path)
            
            # Bouton pour valider la saisie manuelle
            ctk.CTkButton(
                top_frame,
                text=_("Go"),
                width=60,
                command=lambda: validate_manual_entry()
            ).grid(row=0, column=2, padx=5, pady=5)
            
            # Liste des dossiers
            scrollable_frame = ctk.CTkScrollableFrame(dialog)
            scrollable_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
            
            def update_directory_list(path):
                # Nettoie la frame
                for widget in scrollable_frame.winfo_children():
                    widget.destroy()
                
                try:
                    # Ajoute le bouton pour remonter d'un niveau
                    if path != "/":
                        parent_btn = ctk.CTkButton(
                            scrollable_frame,
                            text="📁 ..",
                            anchor="w",
                            command=lambda: navigate_to(os.path.dirname(path)),
                            fg_color="transparent",
                            text_color=("gray10", "gray90"),
                            hover_color=("gray70", "gray30")
                        )
                        parent_btn.pack(fill="x", padx=5, pady=2)
                    
                    # Liste les dossiers (pas les fichiers cachés)
                    items = []
                    for item in sorted(os.listdir(path)):
                        if item.startswith('.'):
                            continue
                        full_path = os.path.join(path, item)
                        if os.path.isdir(full_path):
                            items.append((item, full_path))
                    
                    # Crée les boutons pour chaque dossier
                    for name, full_path in items:
                        btn = ctk.CTkButton(
                            scrollable_frame,
                            text=f"📁 {name}",
                            anchor="w",
                            command=lambda p=full_path: navigate_to(p),
                            fg_color="transparent",
                            text_color=("gray10", "gray90"),
                            hover_color=("gray70", "gray30")
                        )
                        btn.pack(fill="x", padx=5, pady=2)
                
                except PermissionError:
                    error_label = ctk.CTkLabel(
                        scrollable_frame,
                        text=_("⚠️ Accès refusé à ce dossier"),
                        text_color="red"
                    )
                    error_label.pack(pady=10)
                    if path != "/":
                        navigate_to(os.path.dirname(path))
                
                # Met à jour le champ de saisie
                path_entry.delete(0, 'end')
                path_entry.insert(0, path)
            
            def navigate_to(path):
                nonlocal current_path
                current_path = path
                update_directory_list(path)
            
            def validate_manual_entry():
                path = path_entry.get().strip()
                # Expansion du chemin
                path = os.path.expanduser(path)
                path = os.path.expandvars(path)
                path = os.path.abspath(path)
                
                if not os.path.exists(path):
                    self.show_error(_("Le dossier spécifié n'existe pas"))
                    return
                if not os.path.isdir(path):
                    self.show_error(_("Le chemin spécifié n'est pas un dossier"))
                    return
                if not os.access(path, os.R_OK):
                    self.show_error(_("Vous n'avez pas les permissions pour accéder à ce dossier"))
                    return
                
                navigate_to(path)
            
            # Boutons de contrôle en bas
            button_frame = ctk.CTkFrame(dialog)
            button_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
            button_frame.grid_columnconfigure((0, 1), weight=1)
            
            ctk.CTkButton(
                button_frame,
                text=_("Cancel"),
                command=dialog.destroy,
                fg_color="transparent",
                border_width=2,
                text_color=("gray10", "gray90")
            ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            ctk.CTkButton(
                button_frame,
                text=_("Select"),
                command=lambda: select_directory(current_path)
            ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            def select_directory(path):
                self.working_dir_var.set(path)
                if self.validate_working_directory():
                    dialog.destroy()
            
            # Initialise l'affichage
            update_directory_list(current_path)
            
            # Bind la touche Entrée pour la saisie manuelle
            path_entry.bind('<Return>', lambda e: validate_manual_entry())
            
            # Centre la fenêtre
            dialog.transient(self)
            dialog.grab_set()
            dialog.focus_set()
            
            # Attend que la fenêtre soit fermée
            self.wait_window(dialog)
            
        except Exception as e:
            self.show_error(_("Erreur lors de la navigation : ") + str(e))

    def show_error(self, message):
        """Affiche un message d'erreur"""
        try:
            dialog = ctk.CTkToplevel(self)
            dialog.title(_("Erreur"))
            dialog.geometry("400x150")
            
            ctk.CTkLabel(
                dialog,
                text=_("⚠️ ") + message,
                wraplength=350
            ).pack(padx=20, pady=20)
            
            ctk.CTkButton(
                dialog,
                text=_("OK"),
                command=dialog.destroy
            ).pack(pady=10)
            
            # Centre la fenêtre
            dialog.transient(self)
            
            # Attendre que la fenêtre soit créée
            self.after(100, lambda: self._show_error_grab(dialog))
            
        except Exception:
            # Fallback en cas d'erreur avec la fenêtre modale
            print(_("⚠️ Erreur : ") + message)
    
    def _show_error_grab(self, dialog):
        """Helper pour définir le grab après que la fenêtre soit visible"""
        try:
            if dialog.winfo_exists():
                dialog.grab_set()
                dialog.focus_set()
        except Exception:
            pass

    def get_system_users(self) -> List[str]:
        """Récupère la liste des utilisateurs du système"""
        try:
            # Obtenir l'utilisateur courant (celui qui a lancé sudo si applicable)
            current_user = os.getenv('SUDO_USER', os.getenv('USER', 'root'))
            
            # Liste restreinte aux utilisateurs pertinents
            users = ["root", current_user]
            
            # Supprimer les doublons et trier
            return sorted(set(users))
            
        except Exception as e:
            print(_("⚠️  Erreur lors de la lecture des utilisateurs: ") + str(e))
            return ["root"]  # Fallback minimal en cas d'erreur
    
    def update_command_frame(self):
        """Met à jour l'affichage selon le mode de saisie"""
        if self.command_method_var.get() == "manual":
            self.manual_frame.grid()
            self.browse_frame.grid_remove()
        else:
            self.manual_frame.grid_remove()
            self.browse_frame.grid()
            self.refresh_executables()

    def validate_manual_command(self, event=None):
        """Valide la commande saisie manuellement"""
        cmd = self.exec_start_var.get().strip()
        if not cmd:
            return
        
        # Extraire l'exécutable (première partie de la commande)
        parts = cmd.split()
        if not parts:
            self.show_error(_("Commande invalide"))
            return False
            
        executable = parts[0]
        
        # Vérifie si c'est un chemin absolu
        if not os.path.isabs(executable):
            self.show_error(_("L'exécutable doit être un chemin absolu"))
            return False
            
        # Vérifie si le fichier existe
        if not os.path.isfile(executable):
            self.show_error(_("L'exécutable spécifié n'existe pas"))
            return False
            
        # Vérifie si le fichier est exécutable
        if not os.access(executable, os.X_OK) and not executable.endswith(('.sh', '.py', '.bash', '.js')):
            self.show_error(_("Le fichier n'est pas exécutable"))
            return False
            
        # Vérifie si l'exécutable est dans le dossier de travail
        working_dir = self.working_dir_var.get()
        if working_dir and not executable.startswith(working_dir):
            self.show_error(_("L'exécutable doit être dans le dossier de travail"))
            return False
            
        return True

    def on_executable_selected(self, value):
        """Met à jour la commande lorsqu'un exécutable est sélectionné"""
        if value not in ["Sélectionnez d'abord un dossier de travail", "Aucun exécutable trouvé", "Erreur de lecture"]:
            working_dir = self.working_dir_var.get()
            self.executable_var.set(os.path.join(working_dir, value))
            self.update_command()

    def refresh_executables(self):
        """Rafraîchit la liste des exécutables"""
        working_dir = self.working_dir_var.get()
        if not working_dir:
            self.executable_menu.configure(values=["Sélectionnez d'abord un dossier de travail"])
            return
            
        try:
            executables = []
            for item in os.listdir(working_dir):
                full_path = os.path.join(working_dir, item)
                if os.path.isfile(full_path):
                    if os.access(full_path, os.X_OK):
                        executables.append(item)
                    elif item.endswith(('.sh', '.py', '.bash', '.js')):
                        executables.append(item)
                        
            if executables:
                self.executable_menu.configure(values=executables)
                # Définir la valeur dans le menu et appeler le callback
                first_executable = executables[0]
                self.executable_menu.set(first_executable)
                self.on_executable_selected(first_executable)  # Appel explicite du callback
            else:
                self.executable_menu.configure(values=["Aucun exécutable trouvé"])
                
        except Exception as e:
            self.show_error(_("Erreur lors de la lecture du dossier : ") + str(e))
            self.executable_menu.configure(values=["Erreur de lecture"])

    def update_command(self):
        """Met à jour la commande complète"""
        if self.command_method_var.get() == "browse":
            executable = self.executable_var.get()
            if executable and executable not in ["Sélectionnez d'abord un dossier de travail", "Aucun exécutable trouvé", "Erreur de lecture"]:
                cmd = executable
                
                if self.args_var.get().strip():
                    cmd += f" {self.args_var.get().strip()}"
                
                if self.use_screen_var.get():
                    service_name = self.service_name_var.get() or "service"
                    screen_name = f"service_{service_name}"
                    cmd = f"/usr/bin/screen -dmS {screen_name} {cmd}"
                
                self.exec_start_var.set(cmd)

    def check_screen_installed(self):
        """Vérifie si screen est installé"""
        try:
            result = subprocess.run(['which', 'screen'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception:
            return False
    
    def validate_form(self):
        """Valide les données du formulaire"""
        if not self.service_name_var.get().strip():
            return False, _("Le nom du service est obligatoire")
        
        if not self.exec_start_var.get().strip():
            return False, _("La commande d'exécution est obligatoire")
        
        try:
            restart_sec = int(self.restart_sec_var.get())
            if restart_sec < 0:
                return False, _("Le délai de redémarrage doit être positif")
        except ValueError:
            return False, _("Le délai de redémarrage doit être un nombre entier")
        
        return True, None
    
    def get_service_config(self):
        """Récupère la configuration complète du service"""
        service = ServiceModel(self.service_name_var.get())
        
        # Section Unit
        service.unit.description = self.description_var.get()
        if self.restart_var.get() != "no" and self.max_restarts_var.get():
            service.unit.start_limit_burst = int(self.max_restarts_var.get())
        
        # Section Service
        service.service.type = self.type_var.get()
        service.service.user = self.user_var.get()
        service.service.working_directory = self.working_dir_var.get()
        service.service.exec_start = self.exec_start_var.get()
        
        # Configuration du redémarrage
        service.service.restart = self.restart_var.get()
        if service.service.restart != "no":
            if self.restart_sec_var.get():
                service.service.restart_sec = int(self.restart_sec_var.get())
        
        # Délai de démarrage
        if self.start_delay_var.get():
            service.service.start_sec = int(self.start_delay_var.get())
        
        # Si on utilise screen
        if self.use_screen_var.get():
            service.service.type = "forking"
            service.service.remain_after_exit = True
        
        # Section Install
        service.install.wanted_by = ["multi-user.target"]
        
        return service

    def show_success(self, message):
        """Affiche un message de succès"""
        import tkinter.messagebox as messagebox
        messagebox.showinfo(_("Succès"), message)

    def _on_mousewheel(self, event):
        """Gère le défilement avec la molette de souris"""
        canvas = self.scrollable_frame._parent_canvas
        
        # Détermine la direction et la quantité de défilement
        if event.num == 4 or event.delta > 0:  # Défilement vers le haut
            canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  # Défilement vers le bas
            canvas.yview_scroll(1, "units")

    def update_translations(self):
        """Met à jour les traductions des textes de l'interface"""
        # Sauvegarder les valeurs actuelles des variables
        current_values = {
            'service_name': self.service_name_var.get() if hasattr(self, 'service_name_var') else "",
            'description': self.description_var.get() if hasattr(self, 'description_var') else "",
            'type': self.type_var.get() if hasattr(self, 'type_var') else "simple",
            'user': self.user_var.get() if hasattr(self, 'user_var') else "",
            'working_dir': self.working_dir_var.get() if hasattr(self, 'working_dir_var') else "",
            'exec_start': self.exec_start_var.get() if hasattr(self, 'exec_start_var') else "",
            'restart': self.restart_var.get() if hasattr(self, 'restart_var') else "no",
            'restart_sec': self.restart_sec_var.get() if hasattr(self, 'restart_sec_var') else "0",
            'command_method': self.command_method_var.get() if hasattr(self, 'command_method_var') else "manual",
            'executable': self.executable_var.get() if hasattr(self, 'executable_var') else "",
            'args': self.args_var.get() if hasattr(self, 'args_var') else "",
            'use_screen': self.use_screen_var.get() if hasattr(self, 'use_screen_var') else False,
            'start_delay': self.start_delay_var.get() if hasattr(self, 'start_delay_var') else "0",
            'max_restarts': self.max_restarts_var.get() if hasattr(self, 'max_restarts_var') else "3",
            'start_after_save': self.start_after_save_var.get() if hasattr(self, 'start_after_save_var') else True
        }
        
        # Détruire la scrollable frame existante
        if hasattr(self, 'scrollable_frame'):
            self.scrollable_frame.destroy()
        
        # Recréer la scrollable frame avec la même configuration
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=0
        )
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Ajuster la marge de la scrollbar
        scrollbar = self.scrollable_frame._scrollbar
        scrollbar.grid(padx=(5, 0))
        
        # Configuration du défilement avec la molette
        canvas = self.scrollable_frame._parent_canvas
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Bind les événements de la molette de souris
        self.scrollable_frame.bind_all("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind_all("<Button-4>", self._on_mousewheel)
        self.scrollable_frame.bind_all("<Button-5>", self._on_mousewheel)

        # Configuration du frame interne
        self.scrollable_frame._scrollbar.grid_configure(padx=(5, 0))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=3)
        
        # Réinitialiser les variables avec les valeurs sauvegardées
        self.service_name_var = ctk.StringVar(value=current_values['service_name'])
        self.description_var = ctk.StringVar(value=current_values['description'])
        self.type_var = ctk.StringVar(value=current_values['type'])
        self.user_var = ctk.StringVar(value=current_values['user'])
        self.working_dir_var = ctk.StringVar(value=current_values['working_dir'])
        self.exec_start_var = ctk.StringVar(value=current_values['exec_start'])
        self.restart_var = ctk.StringVar(value=current_values['restart'])
        self.restart_sec_var = ctk.StringVar(value=current_values['restart_sec'])
        self.command_method_var = ctk.StringVar(value=current_values['command_method'])
        self.executable_var = ctk.StringVar(value=current_values['executable'])
        self.args_var = ctk.StringVar(value=current_values['args'])
        self.use_screen_var = ctk.BooleanVar(value=current_values['use_screen'])
        self.start_delay_var = ctk.StringVar(value=current_values['start_delay'])
        self.max_restarts_var = ctk.StringVar(value=current_values['max_restarts'])
        self.start_after_save_var = ctk.BooleanVar(value=current_values['start_after_save'])
        
        # Recréer le formulaire avec les nouvelles traductions
        self.create_form()
        self.create_buttons()
        
        # Mettre à jour l'affichage de la commande si nécessaire
        if current_values['command_method'] == 'browse':
            self.update_command_frame()
            if current_values['working_dir']:
                self.refresh_executables()
                if current_values['executable']:
                    self.executable_menu.set(os.path.basename(current_values['executable']))
                    self.on_executable_selected(os.path.basename(current_values['executable']))
