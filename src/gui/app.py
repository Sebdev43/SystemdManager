import customtkinter as ctk
from src.gui.frames.service_list import ServiceListFrame
from src.gui.frames.service_creation import ServiceCreationFrame
from src.cli.cli_controller import CLIController
from src.gui.gui_controller import GUIController
from src.gui.utils.notification import NotificationManager
from src.i18n.translations import i18n, _

class SystemdManagerApp(ctk.CTk):
    """
    Main application class for the SystemD Manager GUI.
    
    This class handles the main window setup, theme management,
    and navigation between different views of the application.
    
    Attributes:
        notification_manager (NotificationManager): Handles application notifications
        gui_controller (GUIController): Controls GUI-related operations
        cli_controller (CLIController): Controls CLI-related operations
        current_frame: Currently displayed frame
        nav_buttons (list): Navigation buttons in the sidebar
    """

    def __init__(self):
        super().__init__()

        self.notification_manager = NotificationManager()

        self.gui_controller = GUIController()
        self.cli_controller = CLIController()

        self.title("SystemD Manager")
        self.geometry("1200x800")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        if not self.cli_controller.check_sudo():
            self.cli_controller.request_sudo("Ce programme nécessite les droits sudo pour gérer les services systemd.")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_view()
    
    def create_sidebar(self):

        sidebar = ctk.CTkFrame(
            self,
            width=200,
            corner_radius=0,
        )
        sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        sidebar.grid_rowconfigure(4, weight=1)

        logo_label = ctk.CTkLabel(
            sidebar,
            text="SystemD\nManager",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.nav_buttons = []
        
        creation_btn = ctk.CTkButton(
            sidebar,
            text="➕ Nouveau Service",
            command=self.show_service_creation_dialog
        )
        creation_btn.grid(row=1, column=0, padx=20, pady=10)
        self.nav_buttons.append(creation_btn)

        spacer = ctk.CTkFrame(sidebar, fg_color="transparent", height=50)
        spacer.grid(row=4, column=0, sticky="ew")
        
        refresh_btn = ctk.CTkButton(
            sidebar,
            text="🔄 Actualiser",
            command=self.refresh_current_tab
        )
        refresh_btn.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
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
        self.theme_switch.select()  

        dev_label = ctk.CTkLabel(
            sidebar,
            text="Developed by sevdev43",
            font=ctk.CTkFont(size=12, slant="italic"), 
            text_color=("gray50", "gray70") 
        )
        dev_label.grid(row=8, column=0, padx=20, pady=(5, 10))
    
    def create_main_view(self):

        self.main_container = ctk.CTkFrame(
            self,
        )
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(
            self.main_container,
        )
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)  
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        title_frame = ctk.CTkFrame(
            self.main_frame,
        )
        title_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        title_frame.grid_columnconfigure(0, weight=1)  

        self.title_label = ctk.CTkLabel(
            title_frame,
            text=_("Services systemd"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.lang_button = ctk.CTkButton(
            title_frame,
            text="FR/EN",
            width=60,
            height=30,
            command=self.change_language
        )
        self.lang_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        self.views_frame = ctk.CTkFrame(
            self.main_frame,
        )
        self.views_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.views_frame.grid_columnconfigure(0, weight=1)
        self.views_frame.grid_rowconfigure(0, weight=1)
        
        self.services_frame = ServiceListFrame(self.views_frame)
        self.creation_frame = ServiceCreationFrame(self.views_frame)
    
        self.current_frame = self.services_frame
        self.services_frame.grid(row=0, column=0, sticky="nsew")
    
    def switch_tab(self, tab_name: str):

        titles = {
            "services": _("Services systemd"),
            "creation": _("Creation of a new service")
        }
        self.title_label.configure(text=titles.get(tab_name, ""))

        for frame in [self.services_frame, self.creation_frame]:
            frame.grid_remove()
        
        if tab_name == "services":
            self.services_frame.grid(row=0, column=0, sticky="nsew")
            self.current_frame = self.services_frame
            self.services_frame.update_translations() 
        elif tab_name == "creation":
            self.creation_frame.grid(row=0, column=0, sticky="nsew")
            self.current_frame = self.creation_frame
            self.creation_frame.update_translations() 
        

        for btn in self.nav_buttons:
            btn.configure(fg_color=("gray75", "gray25"))

        button_index = list(["services", "creation"]).index(tab_name)
        self.nav_buttons[button_index].configure(fg_color=("gray85", "gray35"))
    
    def refresh_current_tab(self):

        if hasattr(self.current_frame, "refresh"):
            self.current_frame.refresh()
    
    def toggle_theme(self):

        current_mode = ctk.get_appearance_mode()
 
        new_mode = "light" if current_mode == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)

        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkSwitch):
                        child.configure(text="Mode sombre" if new_mode == "dark" else "Mode clair")
                        if new_mode == "dark":
                            child.select()
                        else:
                            child.deselect()

    def change_language(self):

        try:

            current_locale = i18n.current_locale
            new_locale = "en" if current_locale == "fr" else "fr"
            i18n.set_locale(new_locale)

            self.update_translations()

            for widget in self.winfo_children():
                if isinstance(widget, ctk.CTkToplevel):
                    if hasattr(widget, 'creation_frame'):
                        widget.creation_frame.update_translations()
                    widget.title(_("Création d'un nouveau service"))
            
        except Exception as e:
            print(f"Erreur lors du changement de langue : {str(e)}")
    
    def update_translations(self):

        self.title_label.configure(text=_("Services systemd"))
        self.nav_buttons[0].configure(text=_("➕ New Service"))
        
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkFrame): 
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkButton) and child not in self.nav_buttons:
                        if "🔄" in child.cget("text"):
                            child.configure(text=_("🔄 Refresh"))
                    elif isinstance(child, ctk.CTkLabel):
                        if "🎨" in child.cget("text"):
                            child.configure(text=_("🎨 Theme"))
                    elif isinstance(child, ctk.CTkSwitch):
                        child.configure(text=_("Dark mode"))

        if hasattr(self, 'services_frame'):
            self.services_frame.update_translations()
        if hasattr(self, 'creation_frame'):
            self.creation_frame.update_translations()
    
    def show_service_creation_dialog(self):

        dialog = ctk.CTkToplevel(self)
        dialog.title(_("Creation of a new service"))
        dialog.geometry("800x600")
        dialog.resizable(True, True)
        dialog.transient(self)
        dialog.gui_controller = self.gui_controller
        
        creation_frame = ServiceCreationFrame(dialog)
        creation_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        dialog.creation_frame = creation_frame
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.update()
        dialog.deiconify()
        dialog.focus_force()
        dialog.after(100, lambda: self._finalize_dialog(dialog))
        
    def _finalize_dialog(self, dialog):

        try:
            dialog.grab_set()
            dialog.wait_window()
        except Exception as e:
            print(f"Erreur lors de la finalisation du dialogue : {str(e)}")
