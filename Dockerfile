FROM debian:bullseye-slim

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libglib2.0-dev \
    libfreetype6-dev \
    libpng-dev \
    libfontconfig1 \
    libx11-dev \
    libxext-dev \
    libxrender-dev \
    zlib1g-dev \
    patchelf \
    git \
    libxcb1 \
    libxcb-render0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-sync1 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libgl1-mesa-glx \
    libegl1-mesa \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    python3-tk \
    tk-dev \
    libffi-dev \
    libncurses5-dev \
    libtinfo5 \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Configuration de l'environnement Python
ENV PYTHONPATH=/app
WORKDIR /app

# Copier les dépendances Python (versions de l'hôte)
COPY requirements.txt requirements.txt

# Installation des dépendances Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Vérification des modules critiques
RUN python3 -c "import customtkinter, PyQt6, questionary, prompt_toolkit"

# Nettoyer les warnings liés à fontconfig
RUN rm -f /etc/fonts/conf.d/05-reset-dirs-sample.conf

# Copier les fichiers sources
COPY . .

# Construction avec PyInstaller
RUN pyinstaller --clean \
    --onefile \
    --name=systemd-manager \
    --add-data=src/i18n/locale:i18n/locale \
    --hidden-import=pkg_resources.py2_warn \
    --hidden-import=jaraco.text \
    --hidden-import=setuptools \
    --hidden-import=PyQt6.QtCore \
    --hidden-import=PyQt6.QtGui \
    --hidden-import=PyQt6.QtWidgets \
    --hidden-import=customtkinter \
    --hidden-import=questionary \
    --hidden-import=prompt_toolkit \
    --hidden-import=tkinter \
    --noconsole \
    --windowed \
    src/main.py

# Vérification des bibliothèques dynamiques manquantes
RUN ldd /app/dist/systemd-manager | grep "not found" || echo "Toutes les bibliothèques nécessaires sont présentes"

# Copie de l'exécutable dans /output pour extraction
RUN mkdir -p /output && cp /app/dist/systemd-manager /output/

# Nettoyage pour réduire la taille de l'image
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Point d'entrée
ENTRYPOINT ["/output/systemd-manager"]
