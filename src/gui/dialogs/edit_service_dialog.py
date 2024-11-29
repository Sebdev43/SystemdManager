import customtkinter as ctk
from typing import Optional
from src.models.service_model import ServiceModel
import subprocess
from src.i18n.translations import _
import os
import tkinter.messagebox as messagebox

class EditServiceDialog(ctk.CTkToplevel):
    """
    Dialog class for editing systemd service configurations.
    
    This class provides a form interface for modifying existing systemd service
    configurations, including service metadata, execution parameters, and restart policies.
    
    Attributes:
        result (Optional[ServiceModel]): The modified service configuration if saved
        service (ServiceModel): The original service being edited
    """
    def __init__(self, parent, service: ServiceModel):
        super().__init__(parent)
        
        self.service = service
        self.result = None

        self.title(_("Edit service") + f" {service.name}")
        self.geometry("800x600")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.help_text_style = {
            "text_color": "gray60",
            "font": ("", 10),
            "justify": "left",
            "anchor": "w"
        }

        self.padding = {"padx": 10, "pady": (2, 5)}
        self.help_padding = {"padx": (25, 10), "pady": (0, 10)}

        self.create_tabs()

        self.create_control_buttons()

        self.transient(parent)
        self.grab_set()

        self.update_translations()
    
    def create_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

        unit_tab = self.tabview.add("Unit")
        unit_tab.grid_columnconfigure(1, weight=1)

        self.description_label = ctk.CTkLabel(unit_tab, text=_("Description:"))
        self.description_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.description_entry = ctk.CTkEntry(unit_tab, width=400)
        self.description_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.description_entry.insert(0, self.service.unit.description or "")
        self.description_help = ctk.CTkLabel(
            unit_tab,
            text=_("Short description of the service\nExample: System monitoring service"),
            **self.help_text_style
        )
        self.description_help.grid(row=1, column=1, **self.help_padding, sticky="w")

        restart_limits_frame = ctk.CTkFrame(unit_tab)
        restart_limits_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        restart_limits_frame.grid_columnconfigure(1, weight=1)
        
        self.restart_limits_label = ctk.CTkLabel(restart_limits_frame, text=_("Restart limits"))
        self.restart_limits_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.burst_label = ctk.CTkLabel(restart_limits_frame, text=_("Maximum number:"))
        self.burst_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.start_limit_burst_entry = ctk.CTkEntry(restart_limits_frame, width=100)
        self.start_limit_burst_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.start_limit_burst_entry.insert(0, str(self.service.unit.start_limit_burst or 5))
        self.burst_help = ctk.CTkLabel(
            restart_limits_frame,
            text=_("Maximum number of restarts allowed in the interval\nDefault: 5"),
            **self.help_text_style
        )
        self.burst_help.grid(row=2, column=1, **self.help_padding, sticky="w")

        self.interval_label = ctk.CTkLabel(restart_limits_frame, text=_("Interval (s):"))
        self.interval_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")
        self.start_limit_interval_entry = ctk.CTkEntry(restart_limits_frame, width=100)
        self.start_limit_interval_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")
        self.start_limit_interval_entry.insert(0, str(self.service.unit.start_limit_interval or 10))
        self.interval_help = ctk.CTkLabel(
            restart_limits_frame,
            text=_("Time interval in seconds for restart limit\nDefault: 10"),
            **self.help_text_style
        )
        self.interval_help.grid(row=4, column=1, **self.help_padding, sticky="w")

        service_tab = self.tabview.add("Service")
        service_tab.grid_columnconfigure(1, weight=1)

        self.type_label = ctk.CTkLabel(service_tab, text=_("Type:"))
        self.type_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.type_option = ctk.CTkOptionMenu(
            service_tab,
            values=["simple", "forking", "oneshot", "notify"],
            width=200
        )
        self.type_option.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.type_option.set(self.service.service.type or "simple")
        
        type_descriptions = {
            "simple": _("Main process stays in foreground"),
            "forking": _("Process detaches to background"),
            "oneshot": _("Runs once and stops"),
            "notify": _("Like simple, but with notifications")
        }
        self.type_help = ctk.CTkLabel(
            service_tab,
            text=_("Available service types:\n") + "\n".join([f"• {k}: {v}" for k, v in type_descriptions.items()]),
            **self.help_text_style
        )
        self.type_help.grid(row=1, column=1, **self.help_padding, sticky="w")

        self.user_label = ctk.CTkLabel(service_tab, text=_("User:"))
        self.user_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.user_entry = ctk.CTkEntry(service_tab, width=200)
        self.user_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.user_entry.insert(0, self.service.service.user or "")
        self.user_help = ctk.CTkLabel(
            service_tab,
            text=_("User who runs the service\nCurrent user by default, root for system services"),
            **self.help_text_style
        )
        self.user_help.grid(row=3, column=1, **self.help_padding, sticky="w")

        self.working_dir_label = ctk.CTkLabel(service_tab, text=_("Working directory:"))
        self.working_dir_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.working_dir_entry = ctk.CTkEntry(service_tab, width=400)
        self.working_dir_entry.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        self.working_dir_entry.insert(0, self.service.service.working_directory or "")
        self.working_dir_help = ctk.CTkLabel(
            service_tab,
            text=_("Directory where the service runs\nAbsolute path required. Example: /home/user/app"),
            **self.help_text_style
        )
        self.working_dir_help.grid(row=5, column=1, **self.help_padding, sticky="w")

        self.command_label = ctk.CTkLabel(service_tab, text=_("Command:"))
        self.command_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.exec_entry = ctk.CTkEntry(service_tab, width=400)
        self.exec_entry.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        self.exec_entry.insert(0, self.service.service.exec_start or "")
        self.command_help = ctk.CTkLabel(
            service_tab,
            text=_("Command to execute\nExample: /usr/bin/python3 script.py"),
            **self.help_text_style
        )
        self.command_help.grid(row=7, column=1, **self.help_padding, sticky="w")

        restart_frame = ctk.CTkFrame(service_tab)
        restart_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        restart_frame.grid_columnconfigure(1, weight=1)
        
        self.restart_label = ctk.CTkLabel(restart_frame, text=_("Restart:"))
        self.restart_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.restart_option = ctk.CTkOptionMenu(
            restart_frame,
            values=["no", "always", "on-failure", "on-abnormal"],
            width=200
        )
        self.restart_option.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.restart_option.set(self.service.service.restart or "no")
        
        restart_descriptions = {
            "no": _("No automatic restart"),
            "always": _("Restarts after normal stop or error"),
            "on-failure": _("Restarts only on error"),
            "on-abnormal": _("Restarts on error or signal")
        }
        self.restart_help = ctk.CTkLabel(
            restart_frame,
            text=_("Restart policies:\n") + "\n".join([f"• {k}: {v}" for k, v in restart_descriptions.items()]),
            **self.help_text_style
        )
        self.restart_help.grid(row=1, column=1, **self.help_padding, sticky="w")

        self.restart_sec_label = ctk.CTkLabel(restart_frame, text=_("Delay (s):"))
        self.restart_sec_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.restart_sec_entry = ctk.CTkEntry(restart_frame, width=100)
        self.restart_sec_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.restart_sec_entry.insert(0, str(self.service.service.restart_sec or 1))
        self.restart_sec_help = ctk.CTkLabel(
            restart_frame,
            text=_("Time in seconds to wait before restart\nDefault: 1"),
            **self.help_text_style
        )
        self.restart_sec_help.grid(row=3, column=1, **self.help_padding, sticky="w")
    
    def create_control_buttons(self):
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.cancel_button = ctk.CTkButton(
            button_frame,
            text=_("Cancel"),
            command=self.cancel
        )
        self.cancel_button.grid(row=0, column=0, padx=10, pady=10)

        self.save_button = ctk.CTkButton(
            button_frame,
            text=_("Save"),
            command=self.save
        )
        self.save_button.grid(row=0, column=1, padx=10, pady=10)
    
    def update_translations(self):
        try:

            self.title(_("Edit service") + f" {self.service.name}")

            self.description_label.configure(text=_("Description:"))
            self.description_help.configure(
                text=_("Short description of the service\nExample: System monitoring service")
            )

            self.restart_limits_label.configure(text=_("Restart limits"))
            self.burst_label.configure(text=_("Maximum number:"))
            self.burst_help.configure(
                text=_("Maximum number of restarts allowed in the interval\nDefault: 5")
            )
            self.interval_label.configure(text=_("Interval (s):"))
            self.interval_help.configure(
                text=_("Time interval in seconds for restart limit\nDefault: 10")
            )

            self.type_label.configure(text=_("Type:"))
            type_descriptions = {
                "simple": _("Main process stays in foreground"),
                "forking": _("Process detaches to background"),
                "oneshot": _("Runs once and stops"),
                "notify": _("Like simple, but with notifications")
            }
            self.type_help.configure(
                text=_("Available service types:\n") + "\n".join([f"• {k}: {v}" for k, v in type_descriptions.items()])
            )

            self.user_label.configure(text=_("User:"))
            self.user_help.configure(
                text=_("User who runs the service\nCurrent user by default, root for system services")
            )

            self.working_dir_label.configure(text=_("Working directory:"))
            self.working_dir_help.configure(
                text=_("Directory where the service runs\nAbsolute path required. Example: /home/user/app")
            )

            self.command_label.configure(text=_("Command:"))
            self.command_help.configure(
                text=_("Command to execute\nExample: /usr/bin/python3 script.py")
            )

            self.restart_label.configure(text=_("Restart:"))
            restart_descriptions = {
                "no": _("No automatic restart"),
                "always": _("Restarts after normal stop or error"),
                "on-failure": _("Restarts only on error"),
                "on-abnormal": _("Restarts on error or signal")
            }
            self.restart_help.configure(
                text=_("Restart policies:\n") + "\n".join([f"• {k}: {v}" for k, v in restart_descriptions.items()])
            )

            self.restart_sec_label.configure(text=_("Delay (s):"))
            self.restart_sec_help.configure(
                text=_("Time in seconds to wait before restart\nDefault: 1")
            )

            self.cancel_button.configure(text=_("Cancel"))
            self.save_button.configure(text=_("Save"))
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour des traductions : {str(e)}")
    
    def set_language(self, language):
        self.update_translations()
    
    def validate_fields(self) -> bool:
        try:
            errors = []
            warnings = []

            description = self.description_entry.get().strip()
            if len(description) > 256:
                errors.append(_("Description is too long (maximum 256 characters)"))

            try:
                burst = int(self.start_limit_burst_entry.get() or 5)
                if burst < 0:
                    errors.append(_("Number cannot be negative"))
                elif burst == 0:
                    warnings.append(_("A value of 0 will disable all restarts"))
                elif burst > 100:
                    warnings.append(_("High number could indicate a problem"))
            except ValueError:
                errors.append(_("Must be an integer"))

            try:
                interval = int(self.start_limit_interval_entry.get() or 10)
                if interval < 0:
                    errors.append(_("Interval cannot be negative"))
                elif interval > 300:
                    warnings.append(_("Interval > 5 min could be problematic"))
            except ValueError:
                errors.append(_("Must be an integer"))

            service_type = self.type_option.get()
            valid_types = ["simple", "forking", "oneshot", "notify"]
            if service_type not in valid_types:
                errors.append(_("Invalid service type"))

            user = self.user_entry.get().strip()
            if not user:
                errors.append(_("User is required"))
            else:
                try:
                    import pwd
                    pwd.getpwnam(user)
                except KeyError:
                    errors.append(_("User '%s' does not exist") % user)

            working_dir = self.working_dir_entry.get().strip()
            if working_dir:
                if not os.path.isabs(working_dir):
                    errors.append(_("Must be an absolute path"))
                elif not os.path.exists(working_dir):
                    errors.append(_("Directory does not exist"))
                elif not os.path.isdir(working_dir):
                    errors.append(_("Not a directory"))
                else:
                    if not os.access(working_dir, os.R_OK | os.X_OK):
                        warnings.append(_("Insufficient permissions"))

            exec_start = self.exec_entry.get().strip()
            if not exec_start:
                errors.append(_("Command is required"))
            else:
                if len(exec_start) > 1024:
                    errors.append(_("Command is too long"))
                cmd_parts = exec_start.split()
                if cmd_parts:
                    executable = cmd_parts[0]
                    if not os.path.isabs(executable):
                        errors.append(_("Must be an absolute path"))
                    if not os.path.exists(executable):
                        errors.append(_("Executable does not exist"))
                    elif not os.path.isfile(executable):
                        errors.append(_("Not a file"))
                    elif not os.access(executable, os.X_OK):
                        warnings.append(_("Insufficient permissions"))

            try:
                restart_sec = int(self.restart_sec_entry.get() or 1)
                if restart_sec < 0:
                    errors.append(_("Delay cannot be negative"))
                elif restart_sec > 300:
                    warnings.append(_("Delay > 5 min could be problematic"))
            except ValueError:
                errors.append(_("Must be an integer"))

            if errors:
                error_message = _("Validation errors:\n") + "\n".join(errors)
                if warnings:
                    error_message += "\n\n" + _("Warnings:\n") + "\n".join(warnings)
                messagebox.showerror(_("Validation error"), error_message)
                return False

            if warnings:
                warning_message = _("Warnings:\n") + "\n".join(warnings)
                result = messagebox.askokcancel(_("Warnings"), warning_message + "\n\n" + _("Do you want to continue?"))
                return result

            return True

        except Exception as e:
            messagebox.showerror(_("Validation error"), _("An unexpected error occurred: ") + str(e))
            return False
    
    def save(self):
        if self.validate_fields():
            try:

                self.service.unit.description = self.description_entry.get()

                try:
                    self.service.unit.start_limit_burst = int(self.start_limit_burst_entry.get() or 5)
                    self.service.unit.start_limit_interval = int(self.start_limit_interval_entry.get() or 10)
                except ValueError:
                    pass

                self.service.service.type = self.type_option.get()
                self.service.service.user = self.user_entry.get()
                self.service.service.working_directory = self.working_dir_entry.get()
                self.service.service.exec_start = self.exec_entry.get()
                self.service.service.restart = self.restart_option.get()
                
                try:
                    self.service.service.restart_sec = int(self.restart_sec_entry.get() or 1)
                except ValueError:
                    self.service.service.restart_sec = 1
                
                self.result = self.service
                self.destroy()
                
            except Exception as e:
                import tkinter.messagebox as messagebox
                messagebox.showerror(_("Error"), _("Error saving changes: ") + str(e))
    
    def cancel(self):
        self.result = None
        self.destroy()
