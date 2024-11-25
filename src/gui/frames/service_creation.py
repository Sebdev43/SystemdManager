import customtkinter as ctk
from src.models.service_model import ServiceModel
from typing import List
import os
import subprocess

class ServiceCreationFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.app = self.winfo_toplevel()
        
        # Configuration de la grille principale pour utiliser tout l'espace
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Créer un conteneur scrollable qui prend tout l'espace
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Configuration de la grille du frame scrollable pour une meilleure répartition
        self.scrollable_frame.grid_columnconfigure(1, weight=3)  # Colonne des champs plus large
        self.scrollable_frame.grid_columnconfigure(0, weight=1)  # Colonne des labels plus étroite
        
        # Configuration du défilement
        canvas = self.scrollable_frame._parent_canvas
        def _configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.bind("<Configure>", _configure_scroll)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
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
        self.create_section_label("Informations de base", row)
        row += 1

        # Nom du service
        ctk.CTkLabel(self.scrollable_frame, text="Nom du service *").grid(row=row, column=0, **padding, sticky="w")
        name_entry = ctk.CTkEntry(self.scrollable_frame, textvariable=self.service_name_var, width=300)
        name_entry.grid(row=row, column=1, **padding, sticky="ew")
        ctk.CTkLabel(self.scrollable_frame, 
            text="Le nom du service sans l'extension .service\nExemple: mon-app", 
            text_color="gray70",
            font=("", 10)
        ).grid(row=row+1, column=1, **padding, sticky="w")
        row += 2

        # Description
        ctk.CTkLabel(self.scrollable_frame, text="Description").grid(row=row, column=0, **padding, sticky="w")
        ctk.CTkEntry(self.scrollable_frame, textvariable=self.description_var, width=300).grid(row=row, column=1, **padding, sticky="ew")
        ctk.CTkLabel(self.scrollable_frame, 
            text="Description courte du service\nExemple: Service de monitoring système", 
            text_color="gray70",
            font=("", 10)
        ).grid(row=row+1, column=1, **padding, sticky="w")
        row += 2

        # Type de service
        ctk.CTkLabel(self.scrollable_frame, text="Type de service").grid(row=row, column=0, **padding, sticky="w")
        type_menu = ctk.CTkOptionMenu(
            self.scrollable_frame,
            values=["simple", "forking", "oneshot", "notify"],
            variable=self.type_var,
            width=300
        )
        type_menu.grid(row=row, column=1, **padding, sticky="ew")
        
        type_descriptions = {
            "simple": "Process principal reste au premier plan",
            "forking": "Process se détache en arrière-plan",
            "oneshot": "S'exécute une fois et s'arrête",
            "notify": "Comme simple, mais avec notifications"
        }
        ctk.CTkLabel(self.scrollable_frame, 
            text="Types de service disponibles :\n" + "\n".join([f"• {k}: {v}" for k, v in type_descriptions.items()]),
            text_color="gray70",
            font=("", 10)
        ).grid(row=row+1, column=1, **padding, sticky="w")
        row += 2

        # Section Configuration d'exécution
        self.create_section_label("Configuration d'exécution", row)
        row += 1

        # Utilisateur
        ctk.CTkLabel(self.scrollable_frame, text="Utilisateur").grid(row=row, column=0, **padding, sticky="w")
        users = self.get_system_users()
        user_menu = ctk.CTkOptionMenu(
            self.scrollable_frame,
            values=users,
            variable=self.user_var,
            width=300
        )
        user_menu.grid(row=row, column=1, **padding, sticky="ew")
        ctk.CTkLabel(self.scrollable_frame, 
            text="Utilisateur qui exécute le service\nUtilisateur actuel par défaut, root pour les services système", 
            text_color="gray70",
            font=("", 10)
        ).grid(row=row+1, column=1, **padding, sticky="w")
        row += 2

        # Dossier de travail
        ctk.CTkLabel(self.scrollable_frame, text="Dossier de travail").grid(row=row, column=0, **padding, sticky="w")
        dir_frame = ctk.CTkFrame(self.scrollable_frame)
        dir_frame.grid(row=row, column=1, **padding, sticky="ew")
        dir_frame.grid_columnconfigure(0, weight=1)

        working_dir_entry = ctk.CTkEntry(dir_frame, textvariable=self.working_dir_var)
        working_dir_entry.grid(row=0, column=0, padx=(0,5), sticky="ew")
        working_dir_entry.bind('<FocusOut>', self.validate_working_directory)

        ctk.CTkButton(dir_frame, text="📂", width=50, command=self.browse_directory).grid(row=0, column=1)
        ctk.CTkLabel(self.scrollable_frame, 
            text="Dossier où le service s'exécute\nChemin absolu requis. Exemple: /home/user/app", 
            text_color="gray70",
            font=("", 10)
        ).grid(row=row+1, column=1, **padding, sticky="w")
        row += 2

        # Commande d'exécution
        ctk.CTkLabel(self.scrollable_frame, text="Commande *").grid(row=row, column=0, **padding, sticky="w")
        exec_frame = ctk.CTkFrame(self.scrollable_frame)
        exec_frame.grid(row=row, column=1, **padding, sticky="ew")
        exec_frame.grid_columnconfigure(0, weight=1)

        # Frame pour la commande
        self.command_frame = ctk.CTkFrame(exec_frame)
        self.command_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.command_frame.grid_columnconfigure(1, weight=1)

        # Méthode de saisie de la commande (manuel ou navigation)
        ctk.CTkRadioButton(
            self.command_frame,
            text="Manuel",
            variable=self.command_method_var,
            value="manual",
            command=self.update_command_frame
        ).grid(row=0, column=0, padx=5)
        
        ctk.CTkRadioButton(
            self.command_frame,
            text="Navigation",
            variable=self.command_method_var,
            value="browse",
            command=self.update_command_frame
        ).grid(row=0, column=1, padx=5)

        # Frame pour la saisie manuelle
        self.manual_frame = ctk.CTkFrame(self.command_frame, fg_color="transparent")
        self.manual_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.manual_frame.grid_columnconfigure(0, weight=1)
        
        self.manual_entry = ctk.CTkEntry(
            self.manual_frame,
            textvariable=self.exec_start_var,
            placeholder_text="Commande complète (ex: /usr/bin/python3 script.py)"
        )
        self.manual_entry.grid(row=0, column=0, sticky="ew", padx=5)
        self.manual_entry.bind('<FocusOut>', self.validate_manual_command)

        # Frame pour la navigation
        self.browse_frame = ctk.CTkFrame(self.command_frame, fg_color="transparent")
        self.browse_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.browse_frame.grid_columnconfigure(1, weight=1)
        
        # Liste des exécutables trouvés
        self.executable_menu = ctk.CTkOptionMenu(
            self.browse_frame,
            variable=self.executables_var,
            values=["Sélectionnez d'abord un dossier de travail"],
            command=self.on_executable_selected,
            width=200
        )
        self.executable_menu.grid(row=0, column=0, sticky="ew", padx=5)
        
        # Bouton rafraîchir
        ctk.CTkButton(
            self.browse_frame,
            text="🔄",
            width=30,
            command=self.refresh_executables
        ).grid(row=0, column=1, padx=5)
        
        # Arguments
        ctk.CTkLabel(self.browse_frame, text="Arguments:").grid(row=1, column=0, padx=5, pady=(5,0))
        self.args_entry = ctk.CTkEntry(
            self.browse_frame,
            textvariable=self.args_var,
            placeholder_text="Arguments optionnels"
        )
        self.args_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))
        self.args_entry.bind('<KeyRelease>', lambda e: self.update_command())

        # Option screen (commune aux deux modes)
        screen_frame = ctk.CTkFrame(self.command_frame, fg_color="transparent")
        screen_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        self.screen_check = ctk.CTkCheckBox(
            screen_frame,
            text="Utiliser screen",
            variable=self.use_screen_var,
            command=self.update_command
        )
        self.screen_check.grid(row=0, column=0, padx=5)
        
        # Vérifier si screen est installé
        if not self.check_screen_installed():
            self.screen_check.configure(state="disabled")
            warning_label = ctk.CTkLabel(
                screen_frame,
                text="⚠️ screen n'est pas installé",
                text_color="orange"
            )
            warning_label.grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(self.scrollable_frame, 
            text="Commande à exécuter\nExemple: /usr/bin/python3 /home/user/app/main.py", 
            text_color="gray70",
            font=("", 10)
        ).grid(row=row+1, column=1, **padding, sticky="w")
        row += 2

        # Section Options avancées
        self.create_section_label("Options avancées", row)
        row += 1

        # Politique de redémarrage
        ctk.CTkLabel(self.scrollable_frame, text="Redémarrage").grid(row=row, column=0, **padding, sticky="w")
        restart_menu = ctk.CTkOptionMenu(
            self.scrollable_frame,
            values=["no", "always", "on-failure", "on-abnormal", "on-abort"],
            variable=self.restart_var,
            width=300
        )
        restart_menu.grid(row=row, column=1, **padding, sticky="ew")
        
        restart_descriptions = {
            "no": "Pas de redémarrage automatique",
            "always": "Redémarre après un arrêt normal ou une erreur",
            "on-failure": "Redémarre uniquement en cas d'erreur",
            "on-abnormal": "Redémarre sur erreur ou signal",
            "on-abort": "Redémarre si le process est abandonné"
        }
        ctk.CTkLabel(self.scrollable_frame, 
            text="Politiques de redémarrage :\n" + "\n".join([f"• {k}: {v}" for k, v in restart_descriptions.items()]),
            text_color="gray70",
            font=("", 10)
        ).grid(row=row+1, column=1, **padding, sticky="w")
        row += 2

        # Délai de redémarrage
        ctk.CTkLabel(self.scrollable_frame, text="Délai de redémarrage (sec)").grid(row=row, column=0, **padding, sticky="w")
        ctk.CTkEntry(self.scrollable_frame, textvariable=self.restart_sec_var, width=300).grid(row=row, column=1, **padding, sticky="ew")
        ctk.CTkLabel(self.scrollable_frame, 
            text="Temps d'attente en secondes avant de redémarrer\n0 = redémarrage immédiat", 
            text_color="gray70",
            font=("", 10)
        ).grid(row=row+1, column=1, **padding, sticky="w")
        row += 2

        # Délai de démarrage après le boot
        ctk.CTkLabel(self.scrollable_frame, text="Délai de démarrage après le boot (sec)").grid(row=row, column=0, **padding, sticky="w")
        ctk.CTkEntry(self.scrollable_frame, textvariable=self.start_delay_var, width=300).grid(row=row, column=1, **padding, sticky="ew")
        ctk.CTkLabel(self.scrollable_frame, 
            text="Temps d'attente en secondes avant de démarrer après le boot\n0 = démarrage immédiat", 
            text_color="gray70",
            font=("", 10)
        ).grid(row=row+1, column=1, **padding, sticky="w")
        row += 2

        # Nombre maximum de redémarrages
        ctk.CTkLabel(self.scrollable_frame, text="Nombre maximum de redémarrages").grid(row=row, column=0, **padding, sticky="w")
        ctk.CTkEntry(self.scrollable_frame, textvariable=self.max_restarts_var, width=300).grid(row=row, column=1, **padding, sticky="ew")
        ctk.CTkLabel(self.scrollable_frame, 
            text="Nombre maximum de redémarrages autorisés en 5 minutes\nDéfaut: 3", 
            text_color="gray70",
            font=("", 10)
        ).grid(row=row+1, column=1, **padding, sticky="w")
        row += 2

        # Option de démarrage après sauvegarde
        ctk.CTkCheckBox(
            self.scrollable_frame,
            text="Lancer le service après la sauvegarde",
            variable=self.start_after_save_var
        ).grid(row=row, column=0, columnspan=2, **padding, sticky="w")
        row += 1

        # Initialiser l'affichage de la commande
        self.update_command_frame()
    
    def create_section_label(self, text, row):
        """Crée un label de section"""
        label = ctk.CTkLabel(self.scrollable_frame, text=text, font=("", 16, "bold"))
        label.grid(row=row, column=0, columnspan=2, padx=10, pady=(20,5), sticky="w")
    
    def create_buttons(self):
        """Crée les boutons de contrôle"""
        buttons_frame = ctk.CTkFrame(self.scrollable_frame)
        buttons_frame.grid(row=99, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        buttons_frame.grid_columnconfigure((0, 1), weight=1)
        
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=self.cancel_creation,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "gray90")
        )
        cancel_btn.grid(row=0, column=0, padx=10, sticky="ew")
        
        create_btn = ctk.CTkButton(
            buttons_frame,
            text="Créer le service",
            command=self.create_service
        )
        create_btn.grid(row=0, column=1, padx=10, sticky="ew")

    def cancel_creation(self):
        """Annule la création et réinitialise le formulaire"""
        self.reset_form()
        # Retour à la page des services
        self.app.switch_tab("services")
        
    def create_service(self):
        """Crée le service avec les données du formulaire"""
        # Validation des données
        valid, error_message = self.validate_form()
        if not valid:
            self.show_error(error_message)
            return
        
        # Récupération de la configuration du service
        service = self.get_service_config()
        
        try:
            # Sauvegarde du service via le contrôleur
            if not self.app.gui_controller.save_service(service):
                raise Exception("Échec de la sauvegarde du service")
            
            # Démarrage du service si demandé
            start_success = False
            if self.start_after_save_var.get():
                start_success = self.app.gui_controller.start_service(service.name)
            
            # Vérifier le statut du service
            status = self.app.gui_controller.get_service_status(service.name)
            
            # Préparer le message selon le statut
            if self.start_after_save_var.get():
                if start_success and status["active"] == "active":
                    message = "Service créé et démarré avec succès !"
                else:
                    raise Exception("Le service a été créé mais n'a pas pu être démarré correctement")
            else:
                if status["load"] == "loaded":
                    message = "Service créé avec succès !"
                else:
                    raise Exception("Le service a été créé mais n'a pas été chargé correctement")
            
            self.show_success(message)
            self.reset_form()
            
            # Retour à la page des services et rafraîchissement
            self.app.switch_tab("services")
            self.app.refresh_current_tab()
            
        except Exception as e:
            self.show_error(f"Erreur lors de la création du service : {str(e)}")
    
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
                self.after(100, lambda: self.show_error("Le dossier spécifié n'existe pas."))
                return False
                
            # Vérifie si c'est un dossier
            if not os.path.isdir(working_dir):
                self.working_dir_var.set("")
                self.after(100, lambda: self.show_error("Le chemin spécifié n'est pas un dossier."))
                return False
                
            # Vérifie les permissions
            if not os.access(working_dir, os.R_OK):
                self.working_dir_var.set("")
                self.after(100, lambda: self.show_error("Vous n'avez pas les permissions pour accéder à ce dossier."))
                return False
                
            # Met à jour le champ avec le chemin absolu
            self.working_dir_var.set(working_dir)
            return True
            
        except Exception as e:
            self.working_dir_var.set("")
            self.after(100, lambda: self.show_error(f"Erreur lors de la validation du dossier : {str(e)}"))
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
            dialog.title("Sélection du dossier de travail")
            dialog.geometry("700x500")
            dialog.grid_columnconfigure(0, weight=1)
            dialog.grid_rowconfigure(1, weight=1)
            
            # Frame pour le chemin et les options
            top_frame = ctk.CTkFrame(dialog)
            top_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
            top_frame.grid_columnconfigure(1, weight=1)
            
            # Label pour afficher le chemin actuel
            path_label = ctk.CTkLabel(top_frame, text="Dossier actuel :")
            path_label.grid(row=0, column=0, padx=5, pady=5)
            
            # Entry pour le chemin avec possibilité de saisie manuelle
            path_entry = ctk.CTkEntry(top_frame)
            path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            path_entry.insert(0, current_path)
            
            # Bouton pour valider la saisie manuelle
            ctk.CTkButton(
                top_frame,
                text="Aller",
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
                        text="⚠️ Accès refusé à ce dossier",
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
                    self.show_error("Le dossier spécifié n'existe pas")
                    return
                if not os.path.isdir(path):
                    self.show_error("Le chemin spécifié n'est pas un dossier")
                    return
                if not os.access(path, os.R_OK):
                    self.show_error("Vous n'avez pas les permissions pour accéder à ce dossier")
                    return
                
                navigate_to(path)
            
            # Boutons de contrôle en bas
            button_frame = ctk.CTkFrame(dialog)
            button_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
            button_frame.grid_columnconfigure((0, 1), weight=1)
            
            ctk.CTkButton(
                button_frame,
                text="Annuler",
                command=dialog.destroy,
                fg_color="transparent",
                border_width=2,
                text_color=("gray10", "gray90")
            ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            ctk.CTkButton(
                button_frame,
                text="Sélectionner",
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
            self.show_error(f"Erreur lors de la navigation : {str(e)}")

    def show_error(self, message):
        """Affiche un message d'erreur"""
        try:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Erreur")
            dialog.geometry("400x150")
            
            ctk.CTkLabel(
                dialog,
                text="⚠️ " + message,
                wraplength=350
            ).pack(padx=20, pady=20)
            
            ctk.CTkButton(
                dialog,
                text="OK",
                command=dialog.destroy
            ).pack(pady=10)
            
            # Centre la fenêtre
            dialog.transient(self)
            
            # Attendre que la fenêtre soit créée
            self.after(100, lambda: self._show_error_grab(dialog))
            
        except Exception:
            # Fallback en cas d'erreur avec la fenêtre modale
            print(f"⚠️ Erreur : {message}")
    
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
            print(f"⚠️  Erreur lors de la lecture des utilisateurs: {e}")
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
            self.show_error("Commande invalide")
            return False
            
        executable = parts[0]
        
        # Vérifie si c'est un chemin absolu
        if not os.path.isabs(executable):
            self.show_error("L'exécutable doit être un chemin absolu")
            return False
            
        # Vérifie si le fichier existe
        if not os.path.isfile(executable):
            self.show_error("L'exécutable spécifié n'existe pas")
            return False
            
        # Vérifie si le fichier est exécutable
        if not os.access(executable, os.X_OK) and not executable.endswith(('.sh', '.py', '.bash', '.js')):
            self.show_error("Le fichier n'est pas exécutable")
            return False
            
        # Vérifie si l'exécutable est dans le dossier de travail
        working_dir = self.working_dir_var.get()
        if working_dir and not executable.startswith(working_dir):
            self.show_error("L'exécutable doit être dans le dossier de travail")
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
            self.show_error(f"Erreur lors de la lecture du dossier : {str(e)}")
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
            return False, "Le nom du service est obligatoire"
        
        if not self.exec_start_var.get().strip():
            return False, "La commande d'exécution est obligatoire"
        
        try:
            restart_sec = int(self.restart_sec_var.get())
            if restart_sec < 0:
                return False, "Le délai de redémarrage doit être positif"
        except ValueError:
            return False, "Le délai de redémarrage doit être un nombre entier"
        
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
        messagebox.showinfo("Succès", message)
