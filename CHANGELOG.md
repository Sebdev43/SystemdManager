# Changelog

## [Non publié / Unreleased]

### Ajouté
- **Mode non interactif** : `systemd-manager create|start|stop|restart|enable|disable|status|list|show|remove` (argparse). `create --dry-run` affiche l'unité sans privilèges ni appel à systemctl ; `--yes` est obligatoire pour écrire dans `/etc/systemd/system` ou supprimer ; `status`/`list --json` produisent un objet JSON unique ; codes de retour stables 0 (succès), 1 (usage), 2 (service introuvable), 3 (échec systemd), 4 (privilèges insuffisants). Sans argument, le menu interactif reste inchangé.
- Le fichier d'unité inclut désormais `Wants=` et `Environment=` quand ils sont renseignés.

### Sécurité
- Une valeur de directive se terminant par `\` est rejetée : elle collerait la directive suivante à la valeur.

### Modifié
- `ServiceValidator` déplacé dans `src/utils/` (partagé, importable sans la GUI) ; option `check_host` pour valider une unité destinée à un autre hôte.
- La GUI n'est plus importée au démarrage du mode commande (utilisable sur un serveur sans affichage).

### Added (EN)
- **Non-interactive mode**: `systemd-manager create|start|stop|restart|enable|disable|status|list|show|remove` (argparse). `create --dry-run` prints the unit with no privileges and no systemctl call; `--yes` is required to write to `/etc/systemd/system` or to remove; `status`/`list --json` emit a single JSON object; stable exit codes 0 (success), 1 (usage), 2 (service not found), 3 (systemd failure), 4 (insufficient privileges). Without arguments the interactive menu is unchanged.
- Unit files now include `Wants=` and `Environment=` when set.

### Security (EN)
- A directive value ending with `\` is rejected: it would splice the next directive into the value.

### Changed (EN)
- `ServiceValidator` moved to `src/utils/` (shared, importable without the GUI); `check_host` option to validate a unit meant for another host.
- The GUI is no longer imported when running a command (usable on a headless server).

## [1.1.0] - 2026-06-20

### Fixed
- **GNU Screen + systemd** : les services lancés dans screen ne restaient jamais actifs — passage de `-dmS` (forking) à `-DmS` (non-forking) avec `Type=simple` et un `ExecStop` adapté.
- **Persistance JSON** : perte de données silencieuse à la création/rechargement via la GUI (incohérence de casse des clés), `KeyError` sur section absente, migration `start_limit` restaurée, garde sur `makedirs`.
- **Génération du fichier `.service`** : la GUI et la CLI produisent désormais des unités identiques (un seul générateur, `RestartSec`/`After`/`StartLimitIntervalSec`).
- **Pipeline de release** : l'archive `systemd-manager-linux.tar` est de nouveau produite par la CI.
- Suppression de méthodes mortes et d'un test obsolète ; correction de bugs latents révélés par ruff.

### Security
- Élimination de l'injection shell : tous les appels `os.system`/`subprocess.getoutput` interpolés remplacés par `subprocess.run([...])` (listes d'arguments, jamais de shell).
- Validation stricte des noms de service chargés (anti path/shell-injection) et rejet des retours à la ligne dans les valeurs de directive systemd (anti directive-injection).
- Mise à jour des dépendances + correction des vulnérabilités Dependabot (suppression de black, `pytest>=9.0.3`, retrait de psutil inutilisé).

### Changed
- **Modernisation de l'outillage** : `setup.py`/`pytest.ini` → `pyproject.toml` (PEP 621) ; black/flake8 → **ruff** ; compatible **uv**.
- Dépendances à jour (PyQt6 6.11, questionary 2.1, typing-extensions 4.15, etc.).

## [1.0.0] - 2024-01-30

### Added
- Interface graphique complète pour la gestion des services
- Support multilingue (FR/EN)
- Interface en ligne de commande
- Création guidée de services
- Surveillance des logs en temps réel

### Changed
- Amélioration des performances
- Interface utilisateur plus intuitive

### Fixed
- Correction des problèmes de permissions
- Meilleure gestion des erreurs 