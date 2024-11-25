import customtkinter as ctk
import subprocess
from datetime import datetime, timedelta
import threading

class LogsDialog(ctk.CTkToplevel):
    def __init__(self, parent, service_name: str):
        super().__init__(parent)
        
        self.service_name = service_name
        self.stop_update = False
        
        # Configuration de la fenêtre
        self.title(f"Logs - {service_name}")
        self.geometry("1000x600")
        
        # Configuration de la grille
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Création des widgets
        self.create_toolbar()
        self.create_log_view()
        
        # Rendre la fenêtre modale
        self.transient(parent)
        self.grab_set()
        
        # Charger les logs initiaux
        self.update_logs()
        
        # Démarrer la mise à jour automatique
        self.update_thread = threading.Thread(target=self.auto_update_logs)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Gestionnaire de fermeture
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_toolbar(self):
        """Crée la barre d'outils"""
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="ew")
        toolbar.grid_columnconfigure(4, weight=1)
        
        # Période
        ctk.CTkLabel(toolbar, text="Période :").grid(row=0, column=0, padx=5)
        self.period_var = ctk.StringVar(value="1h")
        period_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["30m", "1h", "3h", "6h", "12h", "24h", "7d"],
            variable=self.period_var,
            command=self.update_logs,
            width=100
        )
        period_menu.grid(row=0, column=1, padx=5)
        
        # Nombre de lignes
        ctk.CTkLabel(toolbar, text="Lignes :").grid(row=0, column=2, padx=5)
        self.lines_var = ctk.StringVar(value="100")
        lines_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["50", "100", "200", "500", "1000"],
            variable=self.lines_var,
            command=self.update_logs,
            width=100
        )
        lines_menu.grid(row=0, column=3, padx=5)
        
        # Mise à jour automatique
        self.auto_update_var = ctk.BooleanVar(value=True)
        auto_update = ctk.CTkSwitch(
            toolbar,
            text="Mise à jour automatique",
            variable=self.auto_update_var,
            onvalue=True,
            offvalue=False
        )
        auto_update.grid(row=0, column=4, padx=20)
        
        # Bouton de rafraîchissement
        refresh_button = ctk.CTkButton(
            toolbar,
            text="🔄 Actualiser",
            command=self.update_logs,
            width=100
        )
        refresh_button.grid(row=0, column=5, padx=5)
        
        # Bouton de fermeture
        close_button = ctk.CTkButton(
            toolbar,
            text="Fermer",
            command=self.on_close,
            width=100
        )
        close_button.grid(row=0, column=6, padx=5)
    
    def create_log_view(self):
        """Crée la vue des logs"""
        # Frame scrollable pour les logs
        self.log_frame = ctk.CTkScrollableFrame(self)
        self.log_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        # Zone de texte pour les logs
        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            wrap="none",
            font=("Courier", 12)
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
    
    def update_logs(self, *args):
        """Met à jour les logs"""
        # Convertir la période en secondes
        period = self.period_var.get()
        unit = period[-1]
        value = int(period[:-1])
        
        if unit == "m":
            seconds = value * 60
        elif unit == "h":
            seconds = value * 3600
        elif unit == "d":
            seconds = value * 86400
        
        # Construire la commande journalctl
        since = (datetime.now() - timedelta(seconds=seconds)).strftime("%Y-%m-%d %H:%M:%S")
        lines = self.lines_var.get()
        
        try:
            # Exécuter la commande
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
            
            # Effacer le contenu actuel
            self.log_text.delete("1.0", "end")
            
            # Insérer les nouveaux logs
            if result.stdout:
                self.log_text.insert("1.0", result.stdout)
            else:
                self.log_text.insert("1.0", "Aucun log disponible pour cette période")
            
            # Défiler jusqu'en bas
            self.log_text.see("end")
            
        except subprocess.CalledProcessError as e:
            self.log_text.delete("1.0", "end")
            self.log_text.insert("1.0", f"Erreur lors de la récupération des logs : {str(e)}")
    
    def auto_update_logs(self):
        """Met à jour automatiquement les logs"""
        while not self.stop_update:
            if self.auto_update_var.get():
                self.update_logs()
            threading.Event().wait(5)  # Attendre 5 secondes
    
    def on_close(self):
        """Gestionnaire de fermeture"""
        self.stop_update = True
        self.destroy()
