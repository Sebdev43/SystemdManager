import customtkinter as ctk
import subprocess
from datetime import datetime, timedelta
import threading
from src.i18n.translations import i18n, _

class LogsDialog(ctk.CTkToplevel):
    """
    Dialog class for displaying and monitoring service logs.
    
    This class provides a real-time view of systemd service logs with features
    for filtering, auto-updating, and time-based log retrieval.
    
    Attributes:
        service_name (str): Name of the service to monitor
        stop_update (bool): Flag to control automatic log updates
        update_thread (threading.Thread): Thread for automatic log updates
    """
    def __init__(self, parent, service_name: str):
        super().__init__(parent)
        
        self.service_name = service_name
        self.stop_update = False

        self.title(_("Logs") + f" - {service_name}")
        self.geometry("1200x800")
        self.minsize(800, 600) 

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_toolbar()
        self.create_log_view()

        self.center_window(parent)

        self.transient(parent)
        self.grab_set()

        self.update_logs()

        self.update_thread = threading.Thread(target=self.auto_update_logs)
        self.update_thread.daemon = True
        self.update_thread.start()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def center_window(self, parent):
        self.update_idletasks()

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.geometry(f"+{x}+{y}")
    
    def create_toolbar(self):
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="ew")

        left_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w")
        
        middle_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        middle_frame.grid(row=0, column=1, padx=20, sticky="w")
        
        right_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="e")
        
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(left_frame, text=_("Period") + " :").grid(row=0, column=0, padx=(0, 5))
        self.period_var = ctk.StringVar(value="1h")
        period_menu = ctk.CTkOptionMenu(
            left_frame,
            values=["30m", "1h", "3h", "6h", "12h", "24h", "7d"],
            variable=self.period_var,
            command=self.update_logs,
            width=80
        )
        period_menu.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(middle_frame, text=_("Lines") + " :").grid(row=0, column=0, padx=(0, 5))
        self.lines_var = ctk.StringVar(value="100")
        lines_menu = ctk.CTkOptionMenu(
            middle_frame,
            values=["50", "100", "200", "500", "1000"],
            variable=self.lines_var,
            command=self.update_logs,
            width=80
        )
        lines_menu.grid(row=0, column=1, padx=5)

        self.auto_update_var = ctk.BooleanVar(value=True)
        auto_update = ctk.CTkSwitch(
            middle_frame,
            text=_("Auto-update"),
            variable=self.auto_update_var,
            onvalue=True,
            offvalue=False
        )
        auto_update.grid(row=0, column=2, padx=20)

        refresh_button = ctk.CTkButton(
            right_frame,
            text=_("Refresh"),
            command=self.update_logs,
            width=100
        )
        refresh_button.grid(row=0, column=0, padx=5)
        
        close_button = ctk.CTkButton(
            right_frame,
            text=_("Close"),
            command=self.on_close,
            width=100
        )
        close_button.grid(row=0, column=1, padx=5)
    
    def create_log_view(self):

        log_container = ctk.CTkFrame(self)
        log_container.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        log_container.grid_columnconfigure(0, weight=1)
        log_container.grid_rowconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(
            log_container,
            wrap="none",
            font=("Courier", 12),
            height=600 
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
    
    def update_logs(self, *args):

        period = self.period_var.get()
        unit = period[-1]
        value = int(period[:-1])
        
        if unit == "m":
            seconds = value * 60
        elif unit == "h":
            seconds = value * 3600
        elif unit == "d":
            seconds = value * 86400

        since = (datetime.now() - timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")
        lines = self.lines_var.get()
        
        try:

            result = subprocess.run(
                [
                    "journalctl",
                    "-u", f"{self.service_name}",
                    "--since", since,
                    "-n", lines,
                    "--no-pager",
                    "--output=short-precise"
                ],
                capture_output=True,
                text=True
            )

            self.log_text.delete("1.0", "end")

            if result.stdout:
                self.log_text.insert("1.0", result.stdout)
            else:
                self.log_text.insert("1.0", _("No logs available for this period"))

            self.log_text.see("end")
            
        except subprocess.CalledProcessError as e:
            self.log_text.delete("1.0", "end")
            self.log_text.insert("1.0", _("Error retrieving logs: ") + str(e))
    
    def auto_update_logs(self):
        while not self.stop_update:
            if self.auto_update_var.get():
                self.update_logs()
            threading.Event().wait(5)
    
    def on_close(self):
        self.stop_update = True
        self.destroy()
