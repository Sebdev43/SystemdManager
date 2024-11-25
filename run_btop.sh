#!/bin/bash

# Vérifie si btop est installé
if ! command -v btop &> /dev/null; then
    echo "Erreur : btop n'est pas installé. Veuillez l'installer et réessayer."
    exit 1
fi

# Exécute btop
echo "Lancement de btop..."
btop
