#!/bin/bash

# Nom de l'image Docker
IMAGE_NAME="systemd-manager"

# Répertoire local pour l'exécutable
LOCAL_DIST_DIR="./dist"
EXECUTABLE_NAME="systemd-manager"

# Fonction pour afficher des messages
log() {
    echo -e "\e[1;34m$1\e[0m"
}

# Étape 1 : Supprimer l'ancienne version
log "🔍 Suppression de l'ancienne version..."
if [ -d "$LOCAL_DIST_DIR" ]; then
    rm -rf "$LOCAL_DIST_DIR"
    log "✅ Répertoire '$LOCAL_DIST_DIR' supprimé."
fi

# Recréer le répertoire dist
mkdir -p "$LOCAL_DIST_DIR"

# Étape 2 : Construire l'image Docker
log "🔨 Construction de l'image Docker..."
docker build -t "$IMAGE_NAME" .

if [ $? -ne 0 ]; then
    log "❌ Échec de la construction de l'image Docker."
    exit 1
fi

log "✅ Image Docker construite avec succès."

# Étape 3 : Créer un conteneur temporaire
log "🚀 Création d'un conteneur temporaire..."
container_id=$(docker create "$IMAGE_NAME")

if [ -z "$container_id" ]; then
    log "❌ Échec de la création du conteneur."
    exit 1
fi

log "✅ Conteneur temporaire créé : $container_id"

# Étape 4 : Copier l'exécutable du conteneur vers le local
log "📦 Extraction de l'exécutable généré..."
docker cp "$container_id:/output/$EXECUTABLE_NAME" "$LOCAL_DIST_DIR/$EXECUTABLE_NAME"

if [ $? -ne 0 ]; then
    log "❌ Échec de la copie de l'exécutable."
    docker rm "$container_id"
    exit 1
fi

log "✅ Exécutable extrait avec succès dans '$LOCAL_DIST_DIR'."

# Étape 5 : Supprimer le conteneur temporaire
log "🗑️ Suppression du conteneur temporaire..."
docker rm "$container_id"

if [ $? -eq 0 ]; then
    log "✅ Conteneur temporaire supprimé."
else
    log "⚠️ Impossible de supprimer le conteneur temporaire."
fi

# Étape 6 : Vérification finale
if [ -f "$LOCAL_DIST_DIR/$EXECUTABLE_NAME" ]; then
    log "🎉 Build terminé avec succès. L'exécutable est disponible dans '$LOCAL_DIST_DIR/$EXECUTABLE_NAME'."
else
    log "❌ L'exécutable n'a pas été trouvé. Vérifiez votre Dockerfile ou les journaux."
    exit 1
fi

exit 0
