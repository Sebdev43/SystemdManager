# Changelog

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