import customtkinter as ctk
from src.models.service_model import ServiceModel
from typing import List
import os
import subprocess
from src.i18n.translations import _
from src.gui.utils.service_validator import ServiceValidator

class ServiceCreationFrame(ctk.CTkFrame):
    """
    A customized frame for creating and configuring systemd services through a graphical interface.

    This frame provides a user-friendly interface for creating systemd service units with various
    configuration options. It includes form fields for essential service properties such as name,
    description, type, user, and other systemd-specific configurations.

    Attributes:
        parent: The parent widget that contains this frame
        app: Reference to the top-level application window
        gui_controller: Controller managing GUI interactions
        validator: ServiceValidator instance for input validation
        help_text_style (dict): Style configuration for help text labels
        padding (dict): Standard padding configuration for widgets
        help_padding (dict): Padding configuration for help text
        service_name_var (StringVar): Variable for service name input
        description_var (StringVar): Variable for service description
        type_var (StringVar): Variable for service type selection
        user_var (StringVar): Variable for service user configuration
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.app = self.winfo_toplevel()
        self.gui_controller = self.app.gui_controller

        self.validator = ServiceValidator()

        self.help_text_style = {
            "text_color": "gray60",
            "font": ("", 10),
            "justify": "left",
            "anchor": "w"
        }

        self.padding = {"padx": 10, "pady": (2, 5)}
        self.help_padding = {"padx": (25, 10), "pady": (0, 10)}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
            fg_color="transparent"
        )
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=3)

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
        self.start_delay_var = ctk.StringVar(value="0")
        self.max_restarts_var = ctk.StringVar(value="3")
        self.start_after_save_var = ctk.BooleanVar(value=True)

        self.create_form()
        self.create_buttons()

        self._bind_mousewheel(self.scrollable_frame)

        self.update_translations()
    
    def create_form(self):

        padding = {"padx": 10, "pady": 5}
        row = 0

        self.create_section_label(_("Basic Information"), row)
        row += 1

        base_info_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent",
        )
        base_info_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        base_info_frame.grid_columnconfigure(1, weight=1)

        name_frame = ctk.CTkFrame(base_info_frame, fg_color="transparent")
        name_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        name_frame.grid_columnconfigure(1, weight=1)
        
        self.name_label = ctk.CTkLabel(name_frame, text=_("Service Name *"))
        self.name_label.grid(row=0, column=0, padx=5, sticky="w")
        name_entry = ctk.CTkEntry(name_frame, textvariable=self.service_name_var)
        name_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.name_help = ctk.CTkLabel(
            name_frame,
            text=_("Le nom du service (sans .service)"),
            **self.help_text_style
        )
        self.name_help.grid(row=1, column=0, columnspan=2, **self.help_padding)
        row += 2

        ctk.CTkLabel(base_info_frame, text=_("Description")).grid(row=row, column=0, **self.padding, sticky="w")
        ctk.CTkEntry(base_info_frame, textvariable=self.description_var).grid(row=row, column=1, **self.padding, sticky="ew")
        ctk.CTkLabel(
            base_info_frame,
            text=_("Short description of the service\nExample: System monitoring service"),
            text_color="gray60",
            font=("", 10)
        ).grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

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

        self.create_section_label(_("Execution Configuration"), row)
        row += 1

        exec_config_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent",
        )
        exec_config_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        exec_config_frame.grid_columnconfigure(1, weight=1)

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

        self.command_frame = ctk.CTkFrame(
            exec_config_frame,
            fg_color="transparent" 
        )
        self.command_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        self.command_frame.grid_columnconfigure(1, weight=1)

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

        self.manual_frame = ctk.CTkFrame(
            self.command_frame,
            fg_color="transparent"
        )
        self.manual_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.manual_frame.grid_columnconfigure(1, weight=1)
        
        self.command_label = ctk.CTkLabel(self.manual_frame, text=_("Command *"))
        self.command_label.grid(row=0, column=0, padx=5, sticky="w")
        self.manual_entry = ctk.CTkEntry(
            self.manual_frame,
            textvariable=self.exec_start_var,
            placeholder_text=_("Full command (e.g.: /usr/bin/python3 script.py)")
        )
        self.manual_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.manual_entry.bind('<FocusOut>', self.validate_manual_command)

        self.command_help = ctk.CTkLabel(
            self.manual_frame,
            text=_("Command to execute\nExample: /usr/bin/python3 script.py"),
            text_color="gray60",
            font=("", 10)
        )
        self.command_help.grid(row=1, column=1, padx=5, sticky="w")

        self.browse_frame = ctk.CTkFrame(
            self.command_frame,
            fg_color="transparent"
        )
        self.browse_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.browse_frame.grid_columnconfigure(1, weight=1)
        
        self.executable_label = ctk.CTkLabel(self.browse_frame, text=_("Executable *"))
        self.executable_label.grid(row=0, column=0, padx=5, sticky="w")
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
        
        self.args_entry = ctk.CTkEntry(
            self.browse_frame,
            textvariable=self.args_var,
            placeholder_text=_("Optional arguments")
        )
        self.args_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=(5,0))
        self.args_entry.bind('<KeyRelease>', lambda e: self.update_command())

        self.args_help = ctk.CTkLabel(
            self.browse_frame,
            text=_("Example: --config config.ini"),
            text_color="gray60",
            font=("", 10)
        )
        self.args_help.grid(row=2, column=1, padx=5, sticky="w", pady=(0, 5))

        screen_frame = ctk.CTkFrame(
            self.command_frame,
            fg_color="transparent"
        )
        screen_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5)
        screen_frame.grid_columnconfigure(0, weight=1)
        
        self.screen_check = ctk.CTkCheckBox(
            screen_frame,
            text=_("Use screen to run the service in a virtual terminal"),
            variable=self.use_screen_var,
            command=self.update_command
        )
        self.screen_check.grid(row=0, column=0, padx=5, pady=(5, 10), sticky="w")

        spacer = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent", height=20)
        spacer.grid(row=row-1, column=0, columnspan=2, sticky="ew", pady=(10, 10))

        self.create_section_label(_("Advanced Options"), row)
        row += 1

        advanced_frame = ctk.CTkFrame(
            self.scrollable_frame,
            fg_color="transparent"
        )
        advanced_frame.grid(row=row, column=0, columnspan=2, sticky="nsew", padx=10, pady=(15, 5))
        advanced_frame.grid_columnconfigure(1, weight=1)
        advanced_frame.grid_rowconfigure(99, weight=1)  

        self.restart_label = ctk.CTkLabel(advanced_frame, text=_("Restart"))
        self.restart_label.grid(row=row, column=0, **self.padding, sticky="w")
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
        self.restart_help = ctk.CTkLabel(
            advanced_frame,
            text=_("Restart policies:\n") + "\n".join([f"• {k}: {v}" for k, v in restart_descriptions.items()]),
            text_color="gray60",
            font=("", 10)
        )
        self.restart_help.grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        self.restart_sec_label = ctk.CTkLabel(advanced_frame, text=_("Restart Delay (sec)"))
        self.restart_sec_label.grid(row=row, column=0, **self.padding, sticky="w")
        ctk.CTkEntry(advanced_frame, textvariable=self.restart_sec_var, width=300).grid(row=row, column=1, **self.padding, sticky="ew")
        self.restart_sec_help = ctk.CTkLabel(advanced_frame, 
            text=_("Wait time in seconds before restarting\n0 = immediate restart"), 
            text_color="gray60",
            font=("", 10)
        )
        self.restart_sec_help.grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        self.start_delay_label = ctk.CTkLabel(advanced_frame, text=_("Start Delay after boot (sec)"))
        self.start_delay_label.grid(row=row, column=0, **self.padding, sticky="w")
        ctk.CTkEntry(advanced_frame, textvariable=self.start_delay_var, width=300).grid(row=row, column=1, **self.padding, sticky="ew")
        self.start_delay_help = ctk.CTkLabel(advanced_frame, 
            text=_("Wait time in seconds before starting after boot\n0 = immediate start"), 
            text_color="gray60",
            font=("", 10)
        )
        self.start_delay_help.grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        self.max_restarts_label = ctk.CTkLabel(advanced_frame, text=_("Maximum number of restarts"))
        self.max_restarts_label.grid(row=row, column=0, **self.padding, sticky="w")
        ctk.CTkEntry(advanced_frame, textvariable=self.max_restarts_var, width=300).grid(row=row, column=1, **self.padding, sticky="ew")
        self.max_restarts_help = ctk.CTkLabel(advanced_frame, 
            text=_("Maximum number of restarts allowed in 5 minutes\nDefault: 3"), 
            text_color="gray60",
            font=("", 10)
        )
        self.max_restarts_help.grid(row=row+1, column=1, **self.help_padding, sticky="w")
        row += 2

        self.start_after_save_label = ctk.CTkCheckBox(
            advanced_frame,
            text=_("Start service after saving"),
            variable=self.start_after_save_var
        )
        self.start_after_save_label.grid(row=row, column=0, columnspan=2, **self.padding, sticky="w")
        row += 1

        self.update_command_frame()
    
    def create_section_label(self, text, row):

        section_frame = ctk.CTkFrame(
            self.scrollable_frame,
        )
        section_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        self.section_label = ctk.CTkLabel(
            section_frame,
            text=text,
            font=("", 16, "bold")
        )
        self.section_label.grid(row=0, column=0, padx=10, pady=5)
    
    def create_buttons(self):

        button_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        button_frame.grid(row=1000, column=0, columnspan=2, sticky="ew", padx=10, pady=20)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.cancel_button = ctk.CTkButton(
            button_frame,
            text=_("Annuler"), 
            command=self.cancel_creation
        )
        self.cancel_button.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.create_button = ctk.CTkButton(
            button_frame,
            text=_("Créer"),  
            command=self.create_service
        )
        self.create_button.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    def cancel_creation(self):
        self.reset_form()

        self.winfo_toplevel().destroy()

    def create_service(self):
        try:
            config = self.get_service_config()

            validation_result = self.validator.validate_service_config(config)
            
            if not validation_result.is_valid:
                error_message = "\n".join(validation_result.errors)
                if validation_result.warnings:
                    error_message += "\n\nAvertissements:\n" + "\n".join(validation_result.warnings)
                self.show_error(error_message)
                return

            if validation_result.warnings:
                warning_message = _("Avertissements:\n") + "\n".join(validation_result.warnings)
            service = ServiceModel(config['name'])
            service.unit.description = config['description']
            service.service.type = config['type']
            service.service.user = config['user']
            service.service.working_directory = config['working_directory']
            service.service.exec_start = config['command']
            service.service.restart = config['restart']
            try:
                restart_sec = int(config['restart_sec']) if config['restart_sec'] else 0
                service.service.restart_sec = restart_sec
            except (ValueError, TypeError):
                service.service.restart_sec = 0
                
            try:
                start_limit_burst = int(config['max_restarts']) if config['max_restarts'] else 3
                service.unit.start_limit_burst = start_limit_burst
            except (ValueError, TypeError):
                service.unit.start_limit_burst = 3
                
            service.unit.start_limit_interval = 300  

            if service.install.wanted_by is None:
                service.install.wanted_by = ['multi-user.target']

            success = self.gui_controller.save_service(service)
            
            if not success:
                self.show_error(_("Erreur lors de la sauvegarde du service"))
                return

            if self.start_after_save_var.get():
                try:
                    subprocess.run(['systemctl', 'start', f"{service.name}.service"], check=True)
                except subprocess.CalledProcessError as e:
                    self.show_error(_("Erreur lors du démarrage du service : ") + str(e))
                    return

            success_message = _("Service créé avec succès")
            if self.start_after_save_var.get():
                success_message += _(" et démarré")
            self.show_success(success_message)

            self.winfo_toplevel().destroy()
            
        except Exception as e:
            self.show_error(str(e))
    
    def reset_form(self):

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

        working_dir = self.working_dir_var.get().strip()

        if not working_dir:
            return

        working_dir = os.path.expanduser(working_dir)
        working_dir = os.path.expandvars(working_dir)
        working_dir = os.path.abspath(working_dir)
        
        try:

            if not os.path.exists(working_dir):
                self.working_dir_var.set("")
                self.after(100, lambda: self.show_error(_("Le dossier spécifié n'existe pas.")))
                return False

            if not os.path.isdir(working_dir):
                self.working_dir_var.set("")
                self.after(100, lambda: self.show_error(_("Le chemin spécifié n'est pas un dossier.")))
                return False

            if not os.access(working_dir, os.R_OK):
                self.working_dir_var.set("")
                self.after(100, lambda: self.show_error(_("Vous n'avez pas les permissions pour accéder à ce dossier.")))
                return False

            self.working_dir_var.set(working_dir)
            return True
            
        except Exception as e:
            self.working_dir_var.set("")
            self.after(100, lambda: self.show_error(_("Erreur lors de la validation du dossier : ") + str(e)))
            return False

    def browse_directory(self):

        selected_user = self.user_var.get()
        if selected_user == "root":
            current_path = "/"
        else:

            try:
                with open('/etc/passwd', 'r') as f:
                    for line in f:
                        user_info = line.strip().split(':')
                        if user_info[0] == selected_user:
                            current_path = user_info[5]  
                            break
                    else:
                        current_path = os.path.expanduser('~')
            except Exception:
                current_path = os.path.expanduser('~')
        
        try:

            dialog = ctk.CTkToplevel(self)
            dialog.title(_("Select Working Directory"))
            dialog.geometry("700x500")
            dialog.grid_columnconfigure(0, weight=1)
            dialog.grid_rowconfigure(1, weight=1)

            top_frame = ctk.CTkFrame(dialog)
            top_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
            top_frame.grid_columnconfigure(1, weight=1)

            path_label = ctk.CTkLabel(top_frame, text=_("Current Directory:"))
            path_label.grid(row=0, column=0, padx=5, pady=5)

            path_entry = ctk.CTkEntry(top_frame)
            path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            path_entry.insert(0, current_path)

            ctk.CTkButton(
                top_frame,
                text=_("Go"),
                width=60,
                command=lambda: validate_manual_entry()
            ).grid(row=0, column=2, padx=5, pady=5)

            scrollable_frame = ctk.CTkScrollableFrame(dialog)
            scrollable_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
            
            def update_directory_list(path):

                for widget in scrollable_frame.winfo_children():
                    widget.destroy()
                
                try:

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

                    items = []
                    for item in sorted(os.listdir(path)):
                        if item.startswith('.'):
                            continue
                        full_path = os.path.join(path, item)
                        if os.path.isdir(full_path):
                            items.append((item, full_path))

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

                path_entry.delete(0, 'end')
                path_entry.insert(0, path)
            
            def navigate_to(path):
                nonlocal current_path
                current_path = path
                update_directory_list(path)
            
            def validate_manual_entry():
                path = path_entry.get().strip()

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

            update_directory_list(current_path)

            path_entry.bind('<Return>', lambda e: validate_manual_entry())

            dialog.transient(self)
            dialog.grab_set()
            dialog.focus_set()

            self.wait_window(dialog)
            
        except Exception as e:
            self.show_error(_("Erreur lors de la navigation : ") + str(e))

    def show_error(self, message):

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

            dialog.transient(self)

            self.after(100, lambda: self._show_error_grab(dialog))
            
        except Exception:

            print(_("⚠️ Erreur : ") + message)
    
    def _show_error_grab(self, dialog):

        try:
            if dialog.winfo_exists():
                dialog.grab_set()
                dialog.focus_set()
        except Exception:
            pass

    def get_system_users(self) -> List[str]:

        try:

            current_user = os.getenv('SUDO_USER', os.getenv('USER', 'root'))

            users = ["root", current_user]

            return sorted(set(users))
            
        except Exception as e:
            print(_("⚠️  Erreur lors de la lecture des utilisateurs: ") + str(e))
            return ["root"]  
    
    def update_command_frame(self):
 
        if self.command_method_var.get() == "manual":
            self.manual_frame.grid()
            self.browse_frame.grid_remove()
        else:
            self.manual_frame.grid_remove()
            self.browse_frame.grid()
            self.refresh_executables()

    def validate_manual_command(self, event=None):

        cmd = self.exec_start_var.get().strip()
        if not cmd:
            return

        parts = cmd.split()
        if not parts:
            self.show_error(_("Commande invalide"))
            return False
            
        executable = parts[0]

        if not os.path.isabs(executable):
            self.show_error(_("L'exécutable doit être un chemin absolu"))
            return False

        if not os.path.isfile(executable):
            self.show_error(_("L'exécutable spécifié n'existe pas"))
            return False

        if not os.access(executable, os.X_OK) and not executable.endswith(('.sh', '.py', '.bash', '.js')):
            self.show_error(_("Le fichier n'est pas exécutable"))
            return False

        working_dir = self.working_dir_var.get()
        if working_dir and not executable.startswith(working_dir):
            self.show_error(_("L'exécutable doit être dans le dossier de travail"))
            return False
            
        return True

    def on_executable_selected(self, value):

        if value not in ["Sélectionnez d'abord un dossier de travail", "Aucun exécutable trouvé", "Erreur de lecture"]:
            working_dir = self.working_dir_var.get()
            self.executable_var.set(os.path.join(working_dir, value))
            self.update_command()

    def refresh_executables(self):

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

                first_executable = executables[0]
                self.executable_menu.set(first_executable)
                self.on_executable_selected(first_executable) 
            else:
                self.executable_menu.configure(values=["Aucun exécutable trouvé"])
                
        except Exception as e:
            self.show_error(_("Erreur lors de la lecture du dossier : ") + str(e))
            self.executable_menu.configure(values=["Erreur de lecture"])

    def update_command(self):

        if self.command_method_var.get() == "browse":
            executable = self.executable_var.get()
            if executable and executable not in ["Sélectionnez d'abord un dossier de travail", "Aucun exécutable trouvé", "Erreur de lecture"]:

                base_cmd = executable

                if self.args_var.get().strip():
                    base_cmd += f" {self.args_var.get().strip()}"

                final_cmd = base_cmd

                if self.use_screen_var.get():
                    service_name = self.service_name_var.get() or "service"
                    screen_name = f"service_{service_name}"
                    final_cmd = f"/usr/bin/screen -dmS {screen_name} {base_cmd}"

                self.after(10, lambda: self.exec_start_var.set(final_cmd))

                self.after(20, self.command_frame.update_idletasks)
                
    def check_screen_installed(self):

        try:
            result = subprocess.run(['which', 'screen'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception:
            return False
    
    def validate_form(self):

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

        config = {
            'name': self.service_name_var.get().strip(),
            'description': self.description_var.get().strip(),
            'type': self.type_var.get(),
            'user': self.user_var.get(),
            'working_directory': self.working_dir_var.get().strip(),
            'command': self.exec_start_var.get().strip(),
            'restart': self.restart_var.get(),
            'restart_sec': self.restart_sec_var.get(),
            'max_restarts': self.max_restarts_var.get()
        }
        return config

    def show_success(self, message):

        import tkinter.messagebox as messagebox
        messagebox.showinfo(_("Succès"), message)

    def _bind_mousewheel(self, widget):

        widget.bind("<Button-4>", self._on_mousewheel_up, add="+")
        widget.bind("<Button-5>", self._on_mousewheel_down, add="+")
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")

        for child in widget.winfo_children():
            self._bind_mousewheel(child)
    
    def _on_mousewheel(self, event):

        if event.delta:
            self.scrollable_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
        
    def _on_mousewheel_up(self, event):

        self.scrollable_frame._parent_canvas.yview_scroll(-1, "units")
        return "break"
        
    def _on_mousewheel_down(self, event):

        self.scrollable_frame._parent_canvas.yview_scroll(1, "units")
        return "break"
    
    def update_translations(self):

        try:

            self.create_button.configure(text=_("Create"))
            self.cancel_button.configure(text=_("Cancel"))

            if hasattr(self, 'name_label'):
                self.name_label.configure(text=_("Nom du service") + " *")
                self.name_help.configure(text=_("Le nom du service (sans .service)"))
            
            if hasattr(self, 'description_label'):
                self.description_label.configure(text=_("Description"))
                self.description_help.configure(text=_("Une brève description du service"))
            
            if hasattr(self, 'type_label'):
                self.type_label.configure(text=_("Type de service") + " *")
                self.type_help.configure(text=_("Le type détermine le comportement du service"))
            
            if hasattr(self, 'user_label'):
                self.user_label.configure(text=_("Utilisateur") + " *")
                self.user_help.configure(text=_("L'utilisateur qui exécutera le service"))
            
            if hasattr(self, 'working_directory_label'):
                self.working_directory_label.configure(text=_("Répertoire de travail") + " *")
                self.working_directory_help.configure(text=_("Le répertoire de travail du service"))
            
            if hasattr(self, 'command_label'):
                self.command_label.configure(text=_("Commande") + " *")
                self.command_help.configure(text=_("La commande à exécuter"))
            
            if hasattr(self, 'restart_label'):
                self.restart_label.configure(text=_("Redémarrage automatique"))
                self.restart_help.configure(text=_("Redémarre automatiquement en cas d'échec"))
            
            if hasattr(self, 'restart_sec_label'):
                self.restart_sec_label.configure(text=_("Délai avant redémarrage (secondes)"))
                self.restart_sec_help.configure(text=_("Temps d'attente avant redémarrage"))
            
            if hasattr(self, 'max_restarts_label'):
                self.max_restarts_label.configure(text=_("Nombre maximum de redémarrages"))
                self.max_restarts_help.configure(text=_("Nombre maximum de tentatives de redémarrage"))
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour des traductions : {str(e)}")

    def set_language(self, language):
        self.update_translations()
