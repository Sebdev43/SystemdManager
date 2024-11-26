import customtkinter as ctk
from src.gui.frames.service_list import ServiceListFrame
from src.gui.frames.service_creation import ServiceCreationFrame
from src.cli.cli_controller import CLIController
from src.gui.gui_controller import GUIController
from src.gui.utils.notification import NotificationManager
from src.i18n.translations import i18n, _

class SystemdManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialisation du gestionnaire de notifications
        self.notification_manager = NotificationManager()
        
        # Initialisation des contrôleurs
        self.gui_controller = GUIController()
        self.cli_controller = CLIController()
        
        # Configuration de la fenêtre
        self.title("SystemD Manager")
        self.geometry("1200x800")
        
        # Configuration du thème
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Vérification des droits sudo
        if not self.cli_controller.check_sudo():
            self.cli_controller.request_sudo("Ce programme nécessite les droits sudo pour gérer les services systemd.")
        
        # Configuration de la grille
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Création des composants
        self.create_sidebar()
        self.create_main_view()
    
    def create_sidebar(self):
        """Crée la barre latérale"""
        sidebar = ctk.CTkFrame(
            self,
            width=200,
            corner_radius=0,
        )
        sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        sidebar.grid_rowconfigure(4, weight=1)
        
        # Logo et titre
        logo_label = ctk.CTkLabel(
            sidebar,
            text="SystemD\nManager",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Navigation
        self.nav_buttons = []
        
        services_btn = ctk.CTkButton(
            sidebar,
            text="📋 Services",
            command=lambda: self.switch_tab("services")
        )
        services_btn.grid(row=1, column=0, padx=20, pady=10)
        self.nav_buttons.append(services_btn)
        
        creation_btn = ctk.CTkButton(
            sidebar,
            text="➕ Nouveau Service",
            command=lambda: self.switch_tab("creation")
        )
        creation_btn.grid(row=2, column=0, padx=20, pady=10)
        self.nav_buttons.append(creation_btn)
        
        # Déplacer le bouton Actualiser en bas
        spacer = ctk.CTkFrame(sidebar, fg_color="transparent", height=50)
        spacer.grid(row=4, column=0, sticky="ew")
        
        refresh_btn = ctk.CTkButton(
            sidebar,
            text="🔄 Actualiser",
            command=self.refresh_current_tab
        )
        refresh_btn.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        # Thème
        theme_label = ctk.CTkLabel(sidebar, text="🎨 Thème")
        theme_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        
        self.theme_switch = ctk.CTkSwitch(
            sidebar,
            text="Mode sombre",
            command=self.gui_controller.toggle_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.grid(row=7, column=0, padx=20, pady=(0, 10))
        self.theme_switch.select()  # Mode sombre par défaut
        
        # Développeur
        dev_label = ctk.CTkLabel(
            sidebar,
            text="Developed by sevdev43",
            font=ctk.CTkFont(size=12, slant="italic"),  # Police italique et plus petite
            text_color=("gray50", "gray70")  # Couleur grise pour un effet discret
        )
        dev_label.grid(row=8, column=0, padx=20, pady=(5, 10))
    
    def create_main_view(self):
        """Crée la vue principale"""
        # Frame principal qui contient les différentes vues
        self.main_container = ctk.CTkFrame(
            self,
        )
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # Frame principal
        self.main_frame = ctk.CTkFrame(
            self.main_container,
        )
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)  
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Titre dynamique dans son propre frame
        title_frame = ctk.CTkFrame(
            self.main_frame,
        )
        title_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        title_frame.grid_columnconfigure(0, weight=1)  # Colonne du titre prend l'espace
        
        # Titre à gauche
        self.title_label = ctk.CTkLabel(
            title_frame,
            text=_("Services systemd"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Bouton de traduction à droite
        self.lang_button = ctk.CTkButton(
            title_frame,
            text="FR/EN",
            width=60,
            height=30,
            command=self.toggle_language
        )
        self.lang_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        # Frame pour les vues (services et création)
        self.views_frame = ctk.CTkFrame(
            self.main_frame,
        )
        self.views_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.views_frame.grid_columnconfigure(0, weight=1)
        self.views_frame.grid_rowconfigure(0, weight=1)
        
        # Création des vues
        self.services_frame = ServiceListFrame(self.views_frame)
        self.creation_frame = ServiceCreationFrame(self.views_frame)
        
        # Afficher la vue des services par défaut
        self.current_frame = self.services_frame
        self.services_frame.grid(row=0, column=0, sticky="nsew")
    
    def switch_tab(self, tab_name: str):
        """Change l'onglet actif"""
        # Mise à jour du titre
        titles = {
            "services": _("Services systemd"),
            "creation": _("Creation of a new service")
        }
        self.title_label.configure(text=titles.get(tab_name, ""))
        
        # Cacher tous les frames
        for frame in [self.services_frame, self.creation_frame]:
            frame.grid_remove()
        
        # Afficher le frame sélectionné
        if tab_name == "services":
            self.services_frame.grid(row=0, column=0, sticky="nsew")
            self.current_frame = self.services_frame
            self.services_frame.update_translations()  # Met à jour les traductions
        elif tab_name == "creation":
            self.creation_frame.grid(row=0, column=0, sticky="nsew")
            self.current_frame = self.creation_frame
            self.creation_frame.update_translations()  # Met à jour les traductions
        
        # Mettre à jour l'apparence des boutons
        for btn in self.nav_buttons:
            btn.configure(fg_color=("gray75", "gray25"))
        
        # Mettre en surbrillance le bouton actif
        button_index = list(["services", "creation"]).index(tab_name)
        self.nav_buttons[button_index].configure(fg_color=("gray85", "gray35"))
    
    def refresh_current_tab(self):
        """Actualise l'onglet actif"""
        if hasattr(self.current_frame, "refresh"):
            self.current_frame.refresh()
    
    def toggle_theme(self):
        """Change le thème de l'application"""
        # Récupérer l'état actuel du switch
        current_mode = ctk.get_appearance_mode()
        
        # Basculer entre les modes
        new_mode = "light" if current_mode == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        
        # Mettre à jour le texte du switch
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):  # Le sidebar
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkSwitch):
                        child.configure(text="Mode sombre" if new_mode == "dark" else "Mode clair")
                        if new_mode == "dark":
                            child.select()
                        else:
                            child.deselect()

    def toggle_language(self):
        """Change la langue de l'application"""
        # Change la langue
        current_locale = i18n.current_locale
        new_locale = "en" if current_locale == "fr" else "fr"
        i18n.set_locale(new_locale)
        
        # Met à jour le texte du bouton
        self.lang_button.configure(text=f"{new_locale.upper()}")
        
        # Met à jour les textes de la barre latérale
        self.update_translations()
        
        # Rafraîchit l'interface
        self.refresh_current_tab()
    
    def update_translations(self):
        """Met à jour toutes les traductions de l'interface"""
        # Mise à jour du titre
        self.title_label.configure(text=_("Services systemd"))
        
        # Mise à jour des boutons de la barre latérale
        self.nav_buttons[0].configure(text=_("📋 Services"))
        self.nav_buttons[1].configure(text=_("➕ New Service"))
        
        # Mise à jour des autres éléments de la barre latérale
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):  # Le sidebar
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkButton) and child not in self.nav_buttons:
                        if "🔄" in child.cget("text"):
                            child.configure(text=_("🔄 Refresh"))
                    elif isinstance(child, ctk.CTkLabel):
                        if "🎨" in child.cget("text"):
                            child.configure(text=_("🎨 Theme"))
                    elif isinstance(child, ctk.CTkSwitch):
                        child.configure(text=_("Dark mode"))
        
        # Mise à jour des frames
        if hasattr(self, 'services_frame'):
            self.services_frame.update_translations()
        if hasattr(self, 'creation_frame'):
            self.creation_frame.update_translations()
