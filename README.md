# SystemD Manager

[![Build Status](https://github.com/Sebdev43/SystemdManager/actions/workflows/release.yml/badge.svg)](https://github.com/Sebdev43/SystemdManager/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

[English version below](#english-version)

## 🇫🇷 Version Française

Un gestionnaire graphique et en ligne de commande pour les services systemd sous Linux.

### 🎯 Objectif

SystemD Manager simplifie la gestion des services systemd en proposant une interface graphique intuitive et une interface en ligne de commande puissante. Il permet aux administrateurs système et aux développeurs de créer, gérer et surveiller facilement leurs services systemd sans avoir à mémoriser les commandes complexes.

### ✨ Fonctionnalités Principales

- **Double Interface**
  - Interface graphique (GUI) intuitive
  - Interface en ligne de commande (CLI) pour l'automatisation
  
- **Gestion Complète des Services**
  - Création guidée de services
  - Démarrage/Arrêt/Redémarrage
  - Édition des configurations
  - Surveillance des statuts
  - Visualisation des logs en temps réel

- **Fonctionnalités Avancées**
  - Support de GNU Screen
  - Configuration des redémarrages automatiques
  - Gestion des délais de démarrage
  - Validation des configurations
  - Support multilingue (FR/EN)

### 📋 Prérequis

- Linux (testé sur Ubuntu/Debian)
- Python 3.10 ou supérieur
- Droits sudo pour la gestion des services
- Systemd

### 💻 Installation

1. **Via le package binaire**
   - Téléchargez `systemd-manager-linux.tar` depuis la [page des releases](https://github.com/Sebdev43/SystemdManager/releases)
   - Suivez les instructions dans [RELEASE.md](RELEASE.md)

2. **Depuis les sources (pour le développement)**

```bash
git clone https://github.com/Sebdev43/SystemdManager.git
cd SystemdManager
python3 -m pip install -r requirements.txt
```

### 🚀 Utilisation

1. **Lancer l'application**

```bash
sudo python3 src/main.py
```

2. **Choisir l'interface**
   - GUI : Interface graphique intuitive
   - CLI : Interface en ligne de commande

3. **Créer un service**
   - Suivre l'assistant de création
   - Configurer les paramètres du service
   - Installer et démarrer le service

### 🔧 Configuration

- Les configurations sont stockées dans `~/.config/systemd-manager/`
- Les services sont créés dans `/etc/systemd/system/`
- Les logs sont disponibles via `journalctl`

### 🤝 Contribution

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour plus de détails.

### 📝 Licence

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Environnements testés

- Ubuntu 22.04 LTS (Python 3.10, 3.11)
- Ubuntu 20.04 LTS (Python 3.10, 3.11)

---

## 🇬🇧 English Version

A graphical and command-line manager for systemd services on Linux.

### 🎯 Purpose

SystemD Manager simplifies systemd service management by providing both an intuitive graphical interface and a powerful command-line interface. It allows system administrators and developers to easily create, manage, and monitor their systemd services without having to remember complex commands.

### ✨ Key Features

- **Dual Interface**
  - Intuitive graphical interface (GUI)
  - Command-line interface (CLI) for automation
  
- **Complete Service Management**
  - Guided service creation
  - Start/Stop/Restart
  - Configuration editing
  - Status monitoring
  - Real-time log viewing

- **Advanced Features**
  - GNU Screen support
  - Automatic restart configuration
  - Start delay management
  - Configuration validation
  - Multilingual support (EN/FR)

### 📋 Prerequisites

- Linux (tested on Ubuntu/Debian)
- Python 3.10 or higher
- Sudo rights for service management
- Systemd

### 💻 Installation

1. **Via binary package**
   - Download `systemd-manager-linux.tar` from the [releases page](https://github.com/Sebdev43/SystemdManager/releases)
   - Follow instructions in [RELEASE.md](RELEASE.md)

2. **From source (for development)**

```bash
git clone https://github.com/Sebdev43/SystemdManager.git
cd SystemdManager
python3 -m pip install -r requirements.txt
```

### 🚀 Usage

1. **Launch the application**

```bash
sudo python3 src/main.py
```

2. **Choose interface**
   - GUI: Intuitive graphical interface
   - CLI: Command-line interface

3. **Create a service**
   - Follow the creation wizard
   - Configure service parameters
   - Install and start the service

### 🔧 Configuration

- Configurations are stored in `~/.config/systemd-manager/`
- Services are created in `/etc/systemd/system/`
- Logs are available via `journalctl`

### 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

### 📝 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Environnements testés

- Ubuntu 22.04 LTS (Python 3.10, 3.11)
- Ubuntu 20.04 LTS (Python 3.10, 3.11)
