#!/bin/bash

# Fonction pour afficher des messages
log() {
    echo -e "\e[1;34m$1\e[0m"
}

# Nom du package et des répertoires
PACKAGE_NAME="systemd-manager-linux.tar"
TEMP_DIR="systemd-manager"
EXECUTABLE_NAME="systemd-manager"
DIST_DIR="./dist"

# Vérifier si l'exécutable existe dans le répertoire dist
if [ ! -f "$DIST_DIR/$EXECUTABLE_NAME" ]; then
    log "❌ Erreur: L'exécutable '$EXECUTABLE_NAME' n'a pas été trouvé dans le répertoire $DIST_DIR"
    exit 1
fi

# Supprimer l'ancien package et le répertoire temporaire s'ils existent
log "🧹 Nettoyage des fichiers existants..."
rm -f "$PACKAGE_NAME"
rm -rf "$TEMP_DIR"

# Créer la structure de répertoires
log "📁 Création de la structure de répertoires..."
mkdir -p "$TEMP_DIR"

# Copier l'exécutable depuis le dossier dist
log "📦 Copie de l'exécutable depuis $DIST_DIR..."
cp "$DIST_DIR/$EXECUTABLE_NAME" "$TEMP_DIR/"
chmod +x "$TEMP_DIR/$EXECUTABLE_NAME"

# Créer le script d'installation
log "📝 Création du script d'installation..."
cat > "$TEMP_DIR/install.sh" << 'EOF'
#!/bin/bash

# Vérification des droits sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Ce script doit être exécuté avec les droits sudo"
    exit 1
fi

# Copie de l'exécutable
cp systemd-manager /usr/local/bin/
chmod +x /usr/local/bin/systemd-manager

echo "Installation terminée !"
echo "Vous pouvez maintenant lancer systemd-manager depuis n'importe quel terminal"
EOF

# Rendre le script d'installation exécutable
chmod +x "$TEMP_DIR/install.sh"

# Créer l'archive tar
log "📦 Création de l'archive..."
tar -cf "$PACKAGE_NAME" "$TEMP_DIR"

# Nettoyage
log "🧹 Nettoyage..."
rm -rf "$TEMP_DIR"

# Vérification finale
if [ -f "$PACKAGE_NAME" ]; then
    log "✅ Package créé avec succès: $PACKAGE_NAME"
    log "📋 Structure du package:"
    tar -tvf "$PACKAGE_NAME"
else
    log "❌ Erreur lors de la création du package"
    exit 1
fi

exit 0 