import customtkinter as ctk
from src.gui.frames.service_list import ServiceListFrame
from src.gui.frames.service_creation import ServiceCreationFrame
from src.cli.cli_controller import CLIController
from src.gui.gui_controller import GUIController
from src.gui.utils.notification import NotificationManager

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
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
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
        """Crée la vue principale avec les onglets"""
        # Frame principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Titre dynamique
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Services systemd",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # Création des frames pour chaque onglet
        self.frames = {}
        
        # Frame liste des services
        self.frames["services"] = ServiceListFrame(self.main_frame)
        
        # Frame création de service
        self.frames["creation"] = ServiceCreationFrame(self.main_frame)
        
        # Afficher l'onglet services par défaut
        self.current_tab = "services"
        self.switch_tab("services")
    
    def switch_tab(self, tab_name: str):
        """Change l'onglet actif"""
        # Mise à jour du titre
        titles = {
            "services": "Services systemd",
            "creation": "Création d'un nouveau service"
        }
        self.title_label.configure(text=titles.get(tab_name, ""))
        
        # Cacher tous les frames
        for frame in self.frames.values():
            frame.grid_remove()
        
        # Afficher le frame sélectionné
        self.frames[tab_name].grid(row=1, column=0, sticky="nsew")
        self.current_tab = tab_name
        
        # Mettre à jour l'apparence des boutons
        for btn in self.nav_buttons:
            btn.configure(fg_color=("gray75", "gray25"))
        
        # Mettre en surbrillance le bouton actif
        button_index = list(self.frames.keys()).index(tab_name)
        self.nav_buttons[button_index].configure(fg_color=("gray85", "gray35"))
    
    def refresh_current_tab(self):
        """Actualise l'onglet actif"""
        if hasattr(self.frames[self.current_tab], "refresh"):
            self.frames[self.current_tab].refresh()
    
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
