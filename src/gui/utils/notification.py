import customtkinter as ctk
import time
import threading
from typing import Optional

class NotificationManager:
    def __init__(self):
        self._notifications = []
        self._lock = threading.Lock()
    
    def show_notification(self, parent: ctk.CTk, message: str, type: str = "info", duration: int = 3000):
        """Affiche une notification de manière non bloquante"""
        # Créer et afficher la notification dans un thread séparé
        thread = threading.Thread(
            target=self._create_notification,
            args=(parent, message, type, duration)
        )
        thread.daemon = True
        thread.start()
    
    def _create_notification(self, parent, message, type, duration):
        """Crée et affiche une notification"""
        try:
            # Couleurs selon le type
            colors = {
                "info": ("#3498db", "#2980b9"),    # Bleu
                "success": ("#2ecc71", "#27ae60"),  # Vert
                "error": ("#e74c3c", "#c0392b")     # Rouge
            }
            bg_color, hover_color = colors.get(type, colors["info"])
            
            # Utiliser after pour créer la notification dans le thread principal
            parent.after(0, lambda: self._show_notification_widget(
                parent, message, bg_color, hover_color, duration
            ))
            
        except Exception as e:
            print(f"Erreur lors de la création de la notification: {e}")
    
    def _show_notification_widget(self, parent, message, bg_color, hover_color, duration):
        """Crée et affiche le widget de notification dans le thread principal"""
        try:
            print("Création du widget de notification...")
            # Trouver la fenêtre principale (root)
            root = parent.winfo_toplevel()
            
            # Créer le widget de notification
            notification = ctk.CTkFrame(
                root,
                fg_color=bg_color,
                corner_radius=10
            )
            
            # Label avec le message
            label = ctk.CTkLabel(
                notification,
                text=message,
                text_color="white",
                font=ctk.CTkFont(size=12)
            )
            label.pack(padx=20, pady=10)
            
            # Bouton de fermeture
            close_button = ctk.CTkButton(
                notification,
                text="✕",
                width=20,
                height=20,
                fg_color="transparent",
                hover_color=hover_color,
                command=lambda: self._close_notification(notification)
            )
            close_button.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)
            
            # Calculer la taille de la notification
            notification.update_idletasks()
            width = label.winfo_reqwidth() + 40  # Ajouter du padding
            height = label.winfo_reqheight() + 20
            
            # Obtenir les dimensions de la fenêtre principale
            root.update_idletasks()
            window_width = root.winfo_width()
            window_height = root.winfo_height()
            
            with self._lock:
                self._notifications.append(notification)
                # Calculer la position y en fonction des notifications existantes
                total_height = sum(n.winfo_reqheight() + 10 for n in self._notifications[:-1])
                y = window_height - 60 - total_height - height  # 60px du bas
                
                # Positionner la notification
                x = window_width - width - 20  # 20px de la droite
                notification.place(x=x, y=y)
                notification.lift()
            
            # Planifier la fermeture automatique
            if duration > 0:
                root.after(duration, lambda: self._close_notification(notification))
            
            print("Notification créée et positionnée")
            
        except Exception as e:
            print(f"Erreur lors de l'affichage de la notification: {e}")
            import traceback
            print(traceback.format_exc())
    
    def _close_notification(self, notification: ctk.CTkFrame) -> None:
        """Ferme une notification"""
        try:
            if notification.winfo_exists():
                notification.destroy()
            if notification in self._notifications:
                self._notifications.remove(notification)
                self._update_positions()
        except Exception:
            # Si la notification n'existe plus, on la retire simplement de la liste
            if notification in self._notifications:
                self._notifications.remove(notification)
    
    def _update_positions(self) -> None:
        """Met à jour la position des notifications"""
        with self._lock:
            if not self._notifications:  # Si la liste est vide, on sort
                return
                
            # Obtenir les dimensions de la fenêtre principale
            root = self._notifications[0].winfo_toplevel()
            window_width = root.winfo_width()
            window_height = root.winfo_height()
            
            # Position initiale (coin inférieur droit de la fenêtre)
            x = window_width - 20
            y = window_height - 60
            
            # Mettre à jour la position de chaque notification
            for notification in reversed(self._notifications):
                try:
                    if notification.winfo_exists():
                        # Calculer la nouvelle position
                        new_x = x - notification.winfo_reqwidth()
                        notification.place(x=new_x, y=y)
                        y -= notification.winfo_reqheight() + 10
                except Exception:
                    # Si la notification n'existe plus, on la retire de la liste
                    if notification in self._notifications:
                        self._notifications.remove(notification)
