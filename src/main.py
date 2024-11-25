#!/usr/bin/env python3

import sys
import signal
import questionary
from src.cli.cli_controller import CLIController
from src.utils.banner import print_banner
from src.gui.app import SystemdManagerApp

def signal_handler(sig, frame):
    """Gestionnaire global pour Ctrl+C"""
    print("\n\n👋 Au revoir !")
    sys.exit(0)

# Installation du gestionnaire de signal AVANT toute autre configuration
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Configuration de questionary pour le Ctrl+C
questionary.prompts.confirm.KEYBOARD_INTERRUPT_MSG = None
questionary.prompts.select.KEYBOARD_INTERRUPT_MSG = None
questionary.prompts.text.KEYBOARD_INTERRUPT_MSG = None

# Désactivation du message "Cancelled by user"
questionary.prompts.confirm.DEFAULT_KBI_MESSAGE = None
questionary.prompts.select.DEFAULT_KBI_MESSAGE = None
questionary.prompts.text.DEFAULT_KBI_MESSAGE = None

def main():
    """Point d'entrée principal"""
    print_banner()  # Affiche la bannière au démarrage
    
    # Choix de l'interface
    interface = questionary.select(
        "Choisissez votre interface :",
        choices=[
            "🖥️  Interface graphique (GUI)",
            "💻 Interface en ligne de commande (CLI)",
            "❌ Quitter"
        ]
    ).ask()
    
    if interface == "❌ Quitter":
        print("\n👋 Au revoir !")
        sys.exit(0)
    elif interface == "🖥️  Interface graphique (GUI)":
        app = SystemdManagerApp()
        app.mainloop()
    else:
        # Interface CLI
        cli = CLIController()
        if not cli.check_sudo():
            cli.request_sudo("Ce programme nécessite les droits sudo pour gérer les services systemd.")
        cli.main_menu()

if __name__ == "__main__":
    main()