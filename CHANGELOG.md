# Changelog

## [1.3.0] - 2026-11-06

### Ajouté
- **Timers systemd** : `create --every 5min` (`OnBootSec=` + `OnUnitActiveSec=`) ou `create --calendar EXPR` (`OnCalendar=` + `Persistent=true`) installent un service `Type=oneshot` et son `.timer`. Seul le timer est activé ; `start`, `restart`, `enable`, `disable` agissent sur lui et `stop` arrête aussi une exécution en cours. `--screen`, `--restart always` et `--wanted-by` sont refusés avec un timer. `--timeout SPAN` limite la durée d'une exécution (1h par défaut), car un oneshot bloqué empêcherait sinon tout nouveau déclenchement. `--dry-run` et `show` affichent les deux fichiers, chacun précédé d'un en-tête.
- `run NOM` exécute le service une fois, tout de suite, sans toucher au timer.
- `status --json` et `list --json` ajoutent un champ `timer` : `null`, ou `unit`, `active_state`, `sub_state`, `unit_file_state`, `next_run`, `next_run_monotonic`, `last_run`.
- `create --adopt` reprend aussi un `.timer` existant quand un timer est demandé, avec copie et restauration en cas d'échec. Un service actif est alors refusé : à arrêter d'abord.

### Modifié
- `remove`, l'interface graphique et le mode interactif suppriment le timer d'un service géré ; un timer écrit à la main reste intact et `remove` le signale.
- Dans l'interface graphique et le mode interactif, démarrer, arrêter et redémarrer un service à timer pilotent son timer.

### Supprimé
- `configure_timer` et ses traductions : code mort, jamais appelé.

### Added (EN)
- **systemd timers**: `create --every 5min` (`OnBootSec=` + `OnUnitActiveSec=`) or `create --calendar EXPR` (`OnCalendar=` + `Persistent=true`) install a `Type=oneshot` service and its `.timer`. Only the timer is enabled; `start`, `restart`, `enable`, `disable` act on it and `stop` also stops a run in progress. `--screen`, `--restart always` and `--wanted-by` are refused with a timer. `--timeout SPAN` limits how long a run may take (1h by default), since a stuck oneshot would otherwise prevent any further firing. `--dry-run` and `show` print both files, each after a header.
- `run NAME` runs the service once, right away, without touching the timer.
- `status --json` and `list --json` add a `timer` field: `null`, or `unit`, `active_state`, `sub_state`, `unit_file_state`, `next_run`, `next_run_monotonic`, `last_run`.
- `create --adopt` also takes over an existing `.timer` when a timer is requested, with a copy and a restore on failure. An active service is then refused: stop it first.

### Changed (EN)
- `remove`, the GUI and the interactive mode delete the timer of a managed service; a hand-written timer stays intact and `remove` says so.
- In the GUI and the interactive mode, starting, stopping and restarting a timer-run service drive its timer.

### Removed (EN)
- `configure_timer` and its translations: dead code, never called.

## [1.2.1] - 2026-11-06

### Corrigé
- **Adoption d'une unité existante** : `create` et `remove` se bloquaient mutuellement sur une unité écrite à la main, absente de la configuration de l'outil. `create --adopt --yes` la reprend : copie conservée en `<nom>.service.adopted-<horodatage>`, anciens liens d'activation retirés, nouvelle unité écrite de façon atomique, sans arrêter ni démarrer le service. Refus pour une unité déjà gérée, masquée, liée par symlink, fournie par un paquet, ou dont le `[Install]` perdrait des activations (`Also=`, `Alias=`, `RequiredBy=`, `DefaultInstance=`, plusieurs `WantedBy=`). En cas d'échec, y compris si systemd refuse de charger la nouvelle unité, l'ancienne est restaurée. L'ancienne configuration n'est pas importée : l'unité est reconstruite à partir des options passées.
- `create` n'écrit plus à travers un lien symbolique cassé dans le répertoire des unités.
- Les messages de `create` et `remove` indiquent `--adopt` pour une unité non gérée.

### Fixed (EN)
- **Adopting an existing unit**: `create` and `remove` deadlocked on a hand-written unit absent from the tool's configuration. `create --adopt --yes` takes it over: a copy is kept as `<name>.service.adopted-<timestamp>`, old enablement symlinks are removed, the new unit is written atomically, and the service is neither stopped nor started. It refuses a unit that is already managed, masked, symlinked, package-provided, or whose `[Install]` would lose activations (`Also=`, `Alias=`, `RequiredBy=`, `DefaultInstance=`, several `WantedBy=`). On failure, including when systemd will not load the new unit, the previous one is restored. The previous configuration is not imported: the unit is rebuilt from the options given.
- `create` no longer writes through a dangling symlink in the unit directory.
- `create` and `remove` messages point to `--adopt` for an unmanaged unit.

## [1.2.0] - 2026-11-02

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