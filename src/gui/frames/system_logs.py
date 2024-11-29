import customtkinter as ctk
import subprocess
from datetime import datetime, timedelta
import threading
import queue

class SystemLogsFrame(ctk.CTkFrame):
    """
    A frame component for displaying and monitoring system logs in real-time.

    This frame provides a comprehensive interface for viewing system logs with features such as:
    - Real-time log monitoring with auto-scroll capability
    - Log filtering by time period and severity level
    - Search functionality within logs
    - Log following (auto-scroll) option
    - Multi-threaded log updates to maintain UI responsiveness

    Attributes:
        parent: The parent widget containing this frame
        log_queue (Queue): Thread-safe queue for handling log updates
        follow_logs (bool): Flag to control automatic log following
        current_filter (str): Current active log filter
        update_thread (Thread): Background thread for log updates
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.log_queue = queue.Queue()
        self.follow_logs = False
        self.current_filter = None
 
        self.create_toolbar()
        self.create_log_view()

        self.update_thread = None
        self.start_log_updates()
    
    def create_toolbar(self):

        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        toolbar.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(toolbar, text="Période :").grid(row=0, column=0, padx=5)
        self.period_var = ctk.StringVar(value="1h")
        period_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["30m", "1h", "3h", "6h", "12h", "24h", "7j"],
            variable=self.period_var,
            command=self.refresh_logs,
            width=100
        )
        period_menu.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(toolbar, text="Niveau :").grid(row=0, column=2, padx=5)
        self.level_var = ctk.StringVar(value="Tous")
        level_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["Tous", "Info", "Warning", "Error"],
            variable=self.level_var,
            command=self.refresh_logs,
            width=100
        )
        level_menu.grid(row=0, column=3, padx=5)

        self.filter_var = ctk.StringVar()
        self.filter_var.trace_add("write", lambda *args: self.apply_filter())
        filter_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Filtrer par service...",
            textvariable=self.filter_var,
            width=200
        )
        filter_entry.grid(row=0, column=4, padx=5, sticky="ew")

        self.follow_var = ctk.BooleanVar(value=False)
        follow_switch = ctk.CTkSwitch(
            toolbar,
            text="Suivre",
            variable=self.follow_var,
            command=self.toggle_follow
        )
        follow_switch.grid(row=0, column=5, padx=5)

        refresh_button = ctk.CTkButton(
            toolbar,
            text="🔄 Actualiser",
            command=self.refresh_logs
        )
        refresh_button.grid(row=0, column=6, padx=5)

        export_button = ctk.CTkButton(
            toolbar,
            text="📥 Exporter",
            command=self.export_logs
        )
        export_button.grid(row=0, column=7, padx=5)
    
    def create_log_view(self):

        self.log_frame = ctk.CTkTextbox(self)
        self.log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.log_frame.tag_config("error", foreground="red")
        self.log_frame.tag_config("warning", foreground="orange")
        self.log_frame.tag_config("info", foreground="white")
        self.log_frame.tag_config("timestamp", foreground="gray")
        self.log_frame.tag_config("service", foreground="cyan")
    
    def start_log_updates(self):

        if self.update_thread is None or not self.update_thread.is_alive():
            self.update_thread = threading.Thread(target=self.update_logs, daemon=True)
            self.update_thread.start()
    
    def update_logs(self):

        while True:
            if self.follow_var.get():
                try:

                    cmd = ["journalctl", "-f", "-n", "0", "--no-pager"]

                    level = self.level_var.get()
                    if level != "Tous":
                        cmd.extend(["-p", level.lower()])

                    service_filter = self.filter_var.get()
                    if service_filter:
                        cmd.extend(["-u", f"*{service_filter}*"])

                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                    for line in process.stdout:
                        if not self.follow_var.get():
                            process.terminate()
                            break
                        
                        self.log_queue.put(line)

                        self.after(100, self.process_log_queue)
                
                except Exception as e:
                    print(f"Erreur lors de la mise à jour des logs : {e}")
                    break
    
    def process_log_queue(self):

        while not self.log_queue.empty():
            line = self.log_queue.get()
            self.add_log_line(line)
    
    def add_log_line(self, line: str):

        try:

            parts = line.split(" ", 3)
            timestamp = parts[0]
            service = parts[2]
            message = parts[3] if len(parts) > 3 else ""

            level = "info"
            if "error" in message.lower():
                level = "error"
            elif "warning" in message.lower():
                level = "warning"

            self.log_frame.insert("end", f"{timestamp} ", "timestamp")
            self.log_frame.insert("end", f"{service} ", "service")
            self.log_frame.insert("end", f"{message}\n", level)

            if self.follow_var.get():
                self.log_frame.see("end")
        
        except Exception:

            self.log_frame.insert("end", f"{line}\n", "info")
    
    def refresh_logs(self, *args):

        self.log_frame.delete("1.0", "end")
        
        try:

            cmd = ["journalctl", "--no-pager"]

            period = self.period_var.get()
            if period.endswith("m"):
                minutes = int(period[:-1])
                cmd.extend(["--since", f"{minutes} minutes ago"])
            elif period.endswith("h"):
                hours = int(period[:-1])
                cmd.extend(["--since", f"{hours} hours ago"])
            elif period.endswith("j"):
                days = int(period[:-1])
                cmd.extend(["--since", f"{days} days ago"])

            level = self.level_var.get()
            if level != "Tous":
                cmd.extend(["-p", level.lower()])

            service_filter = self.filter_var.get()
            if service_filter:
                cmd.extend(["-u", f"*{service_filter}*"])

            result = subprocess.run(cmd, capture_output=True, text=True)

            for line in result.stdout.splitlines():
                self.add_log_line(line)
        
        except Exception as e:
            self.log_frame.insert("end", f"Erreur lors de la récupération des logs : {e}\n", "error")
    
    def apply_filter(self, *args):

        self.refresh_logs()
    
    def toggle_follow(self):

        if self.follow_var.get():
            self.start_log_updates()
        else:
            self.refresh_logs()
    
    def export_logs(self):

        try:

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"systemd_logs_{timestamp}.txt"
            
            with open(filename, "w") as f:
                f.write(self.log_frame.get("1.0", "end"))

            print(f"Logs exportés dans {filename}")
        
        except Exception as e:
            print(f"Erreur lors de l'export des logs : {e}")
