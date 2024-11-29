"""
SystemdManager - A graphical and command-line interface for managing systemd services.

This module serves as the main entry point for the SystemdManager application.
It provides both a GUI and CLI interface for managing systemd services, allowing users
to create, edit, start, stop, and monitor services through an intuitive interface.

The application handles Ctrl+C gracefully and requires sudo privileges for certain
operations involving systemd service management.

Features:
    - Dual interface (GUI/CLI) for maximum flexibility
    - Real-time service monitoring
    - Service creation and management
    - System logs viewing
    - Internationalization support
"""

import sys
import signal
import questionary
from src.cli.cli_controller import CLIController
from src.utils.banner import print_banner
from src.gui.app import SystemdManagerApp
from src.i18n.translations import i18n

def signal_handler(sig, frame):

    print("\n\n" + i18n.get_text("Au revoir ! 👋"))
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

questionary.prompts.confirm.KEYBOARD_INTERRUPT_MSG = None
questionary.prompts.select.KEYBOARD_INTERRUPT_MSG = None
questionary.prompts.text.KEYBOARD_INTERRUPT_MSG = None

questionary.prompts.confirm.DEFAULT_KBI_MESSAGE = None
questionary.prompts.select.DEFAULT_KBI_MESSAGE = None
questionary.prompts.text.DEFAULT_KBI_MESSAGE = None

def main():

    print_banner()  

    interface = questionary.select(
        i18n.get_text("Choisissez votre interface :"),
        choices=[
            i18n.get_text("🖥️  Interface graphique (GUI)"),
            i18n.get_text("💻 Interface en ligne de commande (CLI)"),
            i18n.get_text("❌ Quitter")
        ]
    ).ask()
    
    if interface == i18n.get_text("❌ Quitter"):
        print("\n" + i18n.get_text("Au revoir ! 👋"))
        sys.exit(0)
    elif interface == i18n.get_text("🖥️  Interface graphique (GUI)"):
        app = SystemdManagerApp()
        app.mainloop()
    else:

        cli = CLIController()
        if not cli.check_sudo():
            cli.request_sudo(i18n.get_text("⚠️  Droits administrateur requis pour"))
        cli.main_menu()

if __name__ == "__main__":
    main()