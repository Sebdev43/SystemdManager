import customtkinter as ctk

class ConfirmDialog(ctk.CTkToplevel):
    """
    Dialog class for displaying confirmation prompts.
    
    This class creates a modal dialog window that prompts the user for confirmation
    of an action, providing confirm and cancel options.
    
    Attributes:
        result (bool): The result of the dialog (True if confirmed, False if cancelled)
    """
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)
        
        self.result = False

        self.title(title)
        self.geometry("400x200")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        message_label = ctk.CTkLabel(
            self,
            text=message,
            wraplength=350
        )
        message_label.grid(row=0, column=0, padx=20, pady=(20, 0))

        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=self.cancel
        ).grid(row=0, column=0, padx=10, pady=10)

        ctk.CTkButton(
            button_frame,
            text="Confirmer",
            command=self.confirm,
            fg_color="red",
            hover_color="#AA0000"
        ).grid(row=0, column=1, padx=10, pady=10)

        self.transient(parent)
        self.grab_set()
    
    def confirm(self):
        self.result = True
        self.destroy()
    
    def cancel(self):
        self.result = False
        self.destroy()
