import customtkinter as ctk
import subprocess
from datetime import datetime, timedelta
import threading
import queue

class SystemLogsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Variables
        self.log_queue = queue.Queue()
        self.follow_logs = False
        self.current_filter = None
        
        # Création des widgets
        self.create_toolbar()
        self.create_log_view()
        
        # Démarrage du thread de mise à jour
        self.update_thread = None
        self.start_log_updates()
    
    def create_toolbar(self):
        """Crée la barre d'outils"""
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        toolbar.grid_columnconfigure(4, weight=1)
        
        # Période
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
        
        # Niveau de log
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
        
        # Filtre de service
        self.filter_var = ctk.StringVar()
        self.filter_var.trace_add("write", lambda *args: self.apply_filter())
        filter_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Filtrer par service...",
            textvariable=self.filter_var,
            width=200
        )
        filter_entry.grid(row=0, column=4, padx=5, sticky="ew")
        
        # Bouton de suivi
        self.follow_var = ctk.BooleanVar(value=False)
        follow_switch = ctk.CTkSwitch(
            toolbar,
            text="Suivre",
            variable=self.follow_var,
            command=self.toggle_follow
        )
        follow_switch.grid(row=0, column=5, padx=5)
        
        # Bouton d'actualisation
        refresh_button = ctk.CTkButton(
            toolbar,
            text="🔄 Actualiser",
            command=self.refresh_logs
        )
        refresh_button.grid(row=0, column=6, padx=5)
        
        # Bouton d'export
        export_button = ctk.CTkButton(
            toolbar,
            text="📥 Exporter",
            command=self.export_logs
        )
        export_button.grid(row=0, column=7, padx=5)
    
    def create_log_view(self):
        """Crée la vue des logs"""
        # Frame avec défilement
        self.log_frame = ctk.CTkTextbox(self)
        self.log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configuration des tags pour la coloration
        self.log_frame.tag_config("error", foreground="red")
        self.log_frame.tag_config("warning", foreground="orange")
        self.log_frame.tag_config("info", foreground="white")
        self.log_frame.tag_config("timestamp", foreground="gray")
        self.log_frame.tag_config("service", foreground="cyan")
    
    def start_log_updates(self):
        """Démarre le thread de mise à jour des logs"""
        if self.update_thread is None or not self.update_thread.is_alive():
            self.update_thread = threading.Thread(target=self.update_logs, daemon=True)
            self.update_thread.start()
    
    def update_logs(self):
        """Met à jour les logs en continu"""
        while True:
            if self.follow_var.get():
                try:
                    # Construire la commande journalctl
                    cmd = ["journalctl", "-f", "-n", "0", "--no-pager"]
                    
                    # Ajouter le filtre de niveau
                    level = self.level_var.get()
                    if level != "Tous":
                        cmd.extend(["-p", level.lower()])
                    
                    # Ajouter le filtre de service
                    service_filter = self.filter_var.get()
                    if service_filter:
                        cmd.extend(["-u", f"*{service_filter}*"])
                    
                    # Exécuter la commande
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Lire les logs en continu
                    for line in process.stdout:
                        if not self.follow_var.get():
                            process.terminate()
                            break
                        
                        self.log_queue.put(line)
                        
                        # Mettre à jour l'interface
                        self.after(100, self.process_log_queue)
                
                except Exception as e:
                    print(f"Erreur lors de la mise à jour des logs : {e}")
                    break
    
    def process_log_queue(self):
        """Traite la file d'attente des logs"""
        while not self.log_queue.empty():
            line = self.log_queue.get()
            self.add_log_line(line)
    
    def add_log_line(self, line: str):
        """Ajoute une ligne de log avec la coloration appropriée"""
        # Analyser la ligne
        try:
            # Format typique : "timestamp hostname service[pid]: message"
            parts = line.split(" ", 3)
            timestamp = parts[0]
            service = parts[2]
            message = parts[3] if len(parts) > 3 else ""
            
            # Déterminer le niveau
            level = "info"
            if "error" in message.lower():
                level = "error"
            elif "warning" in message.lower():
                level = "warning"
            
            # Insérer la ligne avec les tags appropriés
            self.log_frame.insert("end", f"{timestamp} ", "timestamp")
            self.log_frame.insert("end", f"{service} ", "service")
            self.log_frame.insert("end", f"{message}\n", level)
            
            # Défiler si nécessaire
            if self.follow_var.get():
                self.log_frame.see("end")
        
        except Exception:
            # En cas d'erreur de parsing, ajouter la ligne brute
            self.log_frame.insert("end", f"{line}\n", "info")
    
    def refresh_logs(self, *args):
        """Actualise les logs"""
        # Effacer les logs actuels
        self.log_frame.delete("1.0", "end")
        
        try:
            # Construire la commande journalctl
            cmd = ["journalctl", "--no-pager"]
            
            # Ajouter la période
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
            
            # Ajouter le filtre de niveau
            level = self.level_var.get()
            if level != "Tous":
                cmd.extend(["-p", level.lower()])
            
            # Ajouter le filtre de service
            service_filter = self.filter_var.get()
            if service_filter:
                cmd.extend(["-u", f"*{service_filter}*"])
            
            # Exécuter la commande
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Ajouter les logs
            for line in result.stdout.splitlines():
                self.add_log_line(line)
        
        except Exception as e:
            self.log_frame.insert("end", f"Erreur lors de la récupération des logs : {e}\n", "error")
    
    def apply_filter(self, *args):
        """Applique le filtre de service"""
        self.refresh_logs()
    
    def toggle_follow(self):
        """Active/désactive le suivi des logs"""
        if self.follow_var.get():
            self.start_log_updates()
        else:
            self.refresh_logs()
    
    def export_logs(self):
        """Exporte les logs dans un fichier"""
        try:
            # Créer le nom du fichier
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"systemd_logs_{timestamp}.txt"
            
            # Sauvegarder les logs
            with open(filename, "w") as f:
                f.write(self.log_frame.get("1.0", "end"))
            
            # Afficher une notification
            print(f"Logs exportés dans {filename}")
        
        except Exception as e:
            print(f"Erreur lors de l'export des logs : {e}")
