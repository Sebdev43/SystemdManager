import customtkinter as ctk
from src.i18n.translations import _

class ErrorDetailsDialog(ctk.CTkToplevel):
    """
    Dialog class for displaying detailed error information.
    
    This class creates a modal dialog that shows detailed error information,
    including error messages, stack traces, and additional context when available.
    
    Attributes:
        error_text (str): The detailed error message to display
    """

    def __init__(self, parent, title, errors, warnings=None):
        super().__init__(parent)
        
        self.title(title)
        self.geometry("600x400")

        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkLabel(
            self,
            text=_("Détails des erreurs"),
            font=("", 16, "bold")
        )
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        self.text_widget = ctk.CTkTextbox(
            content_frame,
            wrap="word",
            font=("", 12)
        )
        self.text_widget.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        if errors:
            self.text_widget.insert("end", _("Erreurs :\n"), "heading")
            for error in errors:
                self.text_widget.insert("end", f"• {error}\n")

        if warnings:
            if errors: 
                self.text_widget.insert("end", "\n")
            self.text_widget.insert("end", _("Avertissements :\n"), "heading")
            for warning in warnings:
                self.text_widget.insert("end", f"• {warning}\n")

        self.text_widget.configure(state="disabled")

        close_button = ctk.CTkButton(
            self,
            text=_("Fermer"),
            command=self.destroy
        )
        close_button.grid(row=2, column=0, padx=20, pady=20)

        self.center_window()
    
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
