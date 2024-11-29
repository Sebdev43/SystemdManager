import customtkinter as ctk
import time
import threading
from typing import Optional
from gettext import gettext as _

class NotificationManager:
    """
    Manager class for handling application notifications.
    
    This class manages the display and lifecycle of notifications in the application,
    including creation, display duration, and cleanup of notification windows.
    
    Attributes:
        _notifications (list): List of active notifications
        _lock (threading.Lock): Thread lock for synchronizing notification operations
    """
    def __init__(self):
        self._notifications = []
        self._lock = threading.Lock()
    
    def show_notification(self, parent: ctk.CTk, message: str, type: str = "info", duration: int = 3000):


        thread = threading.Thread(
            target=self._create_notification,
            args=(parent, message, type, duration)
        )
        thread.daemon = True
        thread.start()
    
    def _create_notification(self, parent, message, type, duration):

        try:

            colors = {
                "info": ("#3498db", "#2980b9"), 
                "success": ("#2ecc71", "#27ae60"), 
                "error": ("#e74c3c", "#c0392b") 
            }
            bg_color, hover_color = colors.get(type, colors["info"])

            parent.after(0, lambda: self._show_notification_widget(
                parent, message, bg_color, hover_color, duration
            ))
            
        except Exception as e:
            print(_("Error creating notification: ") + str(e))
    
    def _show_notification_widget(self, parent, message, bg_color, hover_color, duration):

        try:
            print(_("Creating notification widget..."))

            root = parent.winfo_toplevel()

            notification = ctk.CTkFrame(
                root,
                fg_color=bg_color,
                corner_radius=10
            )

            label = ctk.CTkLabel(
                notification,
                text=message,
                text_color="white",
                font=ctk.CTkFont(size=12)
            )
            label.pack(padx=20, pady=10)

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

            notification.update_idletasks()
            width = label.winfo_reqwidth() + 40 
            height = label.winfo_reqheight() + 20

            root.update_idletasks()
            window_width = root.winfo_width()
            window_height = root.winfo_height()
            
            with self._lock:
                self._notifications.append(notification)

                total_height = sum(n.winfo_reqheight() + 10 for n in self._notifications[:-1])
                y = window_height - 60 - total_height - height 

                x = window_width - width - 20 
                notification.place(x=x, y=y)
                notification.lift()

            if duration > 0:
                root.after(duration, lambda: self._close_notification(notification))
            
            print(_("Notification created and positioned"))
            
        except Exception as e:
            print(_("Error displaying notification: ") + str(e))
            import traceback
            print(traceback.format_exc())
    
    def _close_notification(self, notification: ctk.CTkFrame) -> None:

        try:
            if notification.winfo_exists():
                notification.destroy()
            if notification in self._notifications:
                self._notifications.remove(notification)
                self._update_positions()
        except Exception:

            if notification in self._notifications:
                self._notifications.remove(notification)
    
    def _update_positions(self) -> None:

        with self._lock:
            if not self._notifications: 
                return

            root = self._notifications[0].winfo_toplevel()
            window_width = root.winfo_width()
            window_height = root.winfo_height()

            x = window_width - 20
            y = window_height - 60

            for notification in reversed(self._notifications):
                try:
                    if notification.winfo_exists():

                        new_x = x - notification.winfo_reqwidth()
                        notification.place(x=new_x, y=y)
                        y -= notification.winfo_reqheight() + 10
                except Exception:

                    if notification in self._notifications:
                        self._notifications.remove(notification)
