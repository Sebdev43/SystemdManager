# SystemD Manager

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

[English version below](#english-version)

## 🇫🇷 Version Française

Un gestionnaire graphique et en ligne de commande pour les services systemd sous Linux.

### 🎯 Objectif

SystemD Manager simplifie la gestion des services systemd en proposant une interface graphique intuitive et une interface en ligne de commande puissante. Il permet aux administrateurs système et aux développeurs de créer, gérer et surveiller facilement leurs services systemd sans avoir à mémoriser les commandes complexes.

### ✨ Fonctionnalités Principales

- **Trois façons de piloter**
  - Interface graphique (GUI) intuitive
  - Assistant interactif dans le terminal
  - **CLI non interactive** `systemd-manager <commande>` : création et pilotage en une commande, `--dry-run` sans privilèges, sortie `--json` et codes de retour stables, pour les scripts, la supervision et les agents (voir [Mode non interactif](#mode-non-interactif-commandes))
  
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

⚠️ **Note importante**: Cette application a été développée sous Ubuntu 24.04. Des incompatibilités de dépendances peuvent survenir sur d'autres versions ou distributions Linux.

### 💻 Installation

1. **Via le package binaire**
   - Téléchargez `systemd-manager-linux.tar` depuis la [page des releases](https://github.com/Sebdev43/SystemdManager/releases)
   - Extrayez l'archive : `tar -xf systemd-manager-linux.tar`
   - Installez : `cd systemd-manager && sudo ./install.sh`

2. **Depuis les sources (pour le développement)**

```bash
git clone https://github.com/Sebdev43/SystemdManager.git
cd SystemdManager
python3 -m pip install -e ".[dev]"   # ou : uv sync
```

### 🚀 Utilisation

L'outil a deux modes en ligne de commande : l'assistant interactif (sans argument) et des commandes non interactives (avec arguments), pour les scripts, la supervision et les agents.

#### Mode interactif (menu)

```bash
sudo python3 src/main.py
```

1. **Choisir l'interface**
   - GUI : Interface graphique intuitive
   - CLI : Assistant interactif dans le terminal

2. **Créer un service**
   - Suivre l'assistant de création
   - Configurer les paramètres du service
   - Installer et démarrer le service

#### Mode non interactif (commandes)

Toute commande passée en argument court-circuite la bannière et le menu (`systemd-manager` une fois installé, sinon `python3 src/main.py`).

```bash
# Voir l'unité sans rien installer (ni root, ni appel à systemctl)
systemd-manager create --name proxima --exec /home/seb43/proxima-node/bin/proxima \
  --workdir /home/seb43/proxima-node --user seb43 \
  --restart always --restart-sec 10 --after network-online.target --dry-run

# Installer et activer (écrit dans /etc/systemd/system : --yes et root obligatoires)
sudo systemd-manager create ... --yes

sudo systemd-manager start|stop|restart|enable|disable proxima
systemd-manager status proxima --json     # un seul objet JSON sur stdout
systemd-manager list --json               # {"services": [...]}
systemd-manager show proxima              # unité générée depuis la config JSON
sudo systemd-manager remove proxima --yes
```

| Option de `create` | Rôle |
|---|---|
| `--name`, `--exec`, `--user` | obligatoires ; `--exec` est un chemin absolu |
| `--workdir`, `--description` | répertoire de travail absolu ; description (par défaut : le nom) |
| `--restart no\|always\|on-failure`, `--restart-sec N` | politique et délai de redémarrage (défauts : `no`, `0`) |
| `--after UNIT` (répétable), `--wanted-by CIBLE` | ordre de démarrage ; cible d'installation (défaut : `multi-user.target`) |
| `--env CLE=VALEUR` (répétable), `--screen` | variables d'environnement ; lancement dans une session GNU Screen |
| `--dry-run`, `--yes` | afficher l'unité sans rien faire ; confirmer l'écriture |

- `--after network-online.target` ajoute aussi `Wants=network-online.target`, sans quoi la cible n'est pas activée.
- `--dry-run` valide la syntaxe (chemins absolus, nom, valeurs) mais pas l'existence de l'exécutable ni de l'utilisateur sur la machine courante : l'unité peut être préparée pour un autre hôte.
- Sans `--yes`, `create` (hors `--dry-run`) et `remove` refusent de s'exécuter au lieu de poser une question. `create` refuse d'écraser une unité existante ; `remove` ne supprime que les services créés par l'outil. `create` installe et active le service sans le démarrer.
- Testé de bout en bout contre un vrai systemd 255 (Ubuntu 24.04) : création, démarrage, relance automatique après `kill -9`, arrêt, `enable`/`disable`, mode GNU Screen, redémarrage de la machine (le service repart au boot), suppression, et chaque code de retour.
- Sortie : stdout ne contient que les données (unité, statut, liste) ; messages et erreurs vont sur stderr. Avec `--json`, une erreur produit `{"error": {"code", "kind", "message"}}`.
- La config JSON est rangée dans `~/.config/systemd-manager/services` ; sous `sudo`, c'est le répertoire de l'utilisateur appelant (`SUDO_USER`), pour que `list` et `status` sans `sudo` voient les services créés avec `sudo`.
- `%` est refusé dans les options autres que `--exec`. Dans `--exec`, il est transmis tel quel comme spécificateur systemd (écrire `%%` pour un `%` littéral).

| Code de retour | Signification |
|---|---|
| 0 | succès |
| 1 | erreur d'usage (argument ou configuration invalide, `--yes` manquant, unité déjà existante) |
| 2 | service introuvable |
| 3 | échec d'une opération systemd |
| 4 | privilèges insuffisants (root requis) |

### 🔧 Configuration

- Les configurations sont stockées dans `~/.config/systemd-manager/`
- Les services sont créés dans `/etc/systemd/system/`
- Les logs sont disponibles via `journalctl`

### 🤝 Contribution

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour plus de détails.

### 📝 Licence

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Environnements testés

- Ubuntu 24.04 LTS (Python 3.10, 3.11) - Environnement de développement principal
- Ubuntu 22.04 LTS (Python 3.10, 3.11)
- Ubuntu 20.04 LTS (Python 3.10, 3.11)

---

## 🇬🇧 English Version

A graphical and command-line manager for systemd services on Linux.

### 🎯 Purpose

SystemD Manager simplifies systemd service management by providing both an intuitive graphical interface and a powerful command-line interface. It allows system administrators and developers to easily create, manage, and monitor their systemd services without having to remember complex commands.

### ✨ Key Features

- **Three ways to drive it**
  - Intuitive graphical interface (GUI)
  - Interactive terminal wizard
  - **Non-interactive CLI** `systemd-manager <command>`: create and control a service in one command, privilege-free `--dry-run`, `--json` output and stable exit codes, for scripts, monitoring and agents (see [Non-interactive mode](#non-interactive-mode-commands))
  
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

⚠️ **Important note**: This application was developed on Ubuntu 24.04. Dependency incompatibilities may occur on other Linux versions or distributions.

### 💻 Installation

1. **Via binary package**
   - Download `systemd-manager-linux.tar` from the [releases page](https://github.com/Sebdev43/SystemdManager/releases)
   - Extract the archive: `tar -xf systemd-manager-linux.tar`
   - Install: `cd systemd-manager && sudo ./install.sh`

2. **From source (for development)**

```bash
git clone https://github.com/Sebdev43/SystemdManager.git
cd SystemdManager
python3 -m pip install -e ".[dev]"   # or: uv sync
```

### 🚀 Usage

The tool has two command-line modes: the interactive wizard (no arguments) and non-interactive commands (with arguments) for scripts, monitoring and agents.

#### Interactive mode (menu)

```bash
sudo python3 src/main.py
```

1. **Choose interface**
   - GUI: Intuitive graphical interface
   - CLI: Interactive terminal wizard

2. **Create a service**
   - Follow the creation wizard
   - Configure service parameters
   - Install and start the service

#### Non-interactive mode (commands)

Any command given as an argument skips the banner and the menu (`systemd-manager` once installed, otherwise `python3 src/main.py`).

```bash
# Print the unit without installing anything (no root, no systemctl call)
systemd-manager create --name proxima --exec /home/seb43/proxima-node/bin/proxima \
  --workdir /home/seb43/proxima-node --user seb43 \
  --restart always --restart-sec 10 --after network-online.target --dry-run

# Install and enable (writes to /etc/systemd/system: --yes and root required)
sudo systemd-manager create ... --yes

sudo systemd-manager start|stop|restart|enable|disable proxima
systemd-manager status proxima --json     # a single JSON object on stdout
systemd-manager list --json               # {"services": [...]}
systemd-manager show proxima              # unit generated from the JSON config
sudo systemd-manager remove proxima --yes
```

| `create` option | Purpose |
|---|---|
| `--name`, `--exec`, `--user` | required; `--exec` is an absolute path |
| `--workdir`, `--description` | absolute working directory; description (defaults to the name) |
| `--restart no\|always\|on-failure`, `--restart-sec N` | restart policy and delay (defaults: `no`, `0`) |
| `--after UNIT` (repeatable), `--wanted-by TARGET` | start ordering; install target (default: `multi-user.target`) |
| `--env KEY=VALUE` (repeatable), `--screen` | environment variables; run inside a GNU Screen session |
| `--dry-run`, `--yes` | print the unit and do nothing; confirm the write |

- `--after network-online.target` also adds `Wants=network-online.target`, without which the target is not activated.
- `--dry-run` checks syntax (absolute paths, name, values) but not whether the executable or user exist on the current machine, so a unit can be prepared for another host.
- Without `--yes`, `create` (outside `--dry-run`) and `remove` refuse to run instead of prompting. `create` refuses to overwrite an existing unit; `remove` only deletes services created by the tool. `create` installs and enables the service without starting it.
- Tested end to end against a real systemd 255 (Ubuntu 24.04): create, start, automatic restart after `kill -9`, stop, `enable`/`disable`, GNU Screen mode, machine reboot (the service comes back at boot), removal, and every exit code.
- Output: stdout carries only data (unit, status, list); messages and errors go to stderr. With `--json`, an error yields `{"error": {"code", "kind", "message"}}`.
- The JSON config is stored in `~/.config/systemd-manager/services`; under `sudo` it is the invoking user's directory (`SUDO_USER`), so `list` and `status` without `sudo` see services created with `sudo`.
- `%` is rejected in options other than `--exec`. In `--exec` it is passed verbatim as a systemd specifier (write `%%` for a literal `%`).

| Exit code | Meaning |
|---|---|
| 0 | success |
| 1 | usage error (invalid argument or configuration, missing `--yes`, unit already exists) |
| 2 | service not found |
| 3 | systemd operation failed |
| 4 | insufficient privileges (root required) |

### 🔧 Configuration

- Configurations are stored in `~/.config/systemd-manager/`
- Services are created in `/etc/systemd/system/`
- Logs are available via `journalctl`

### 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

### 📝 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Tested Environments

- Ubuntu 24.04 LTS (Python 3.10, 3.11) - Main development environment
- Ubuntu 22.04 LTS (Python 3.10, 3.11)
- Ubuntu 20.04 LTS (Python 3.10, 3.11)
