# SystemD Manager - Guide d'Installation

[English version below](#english-version)

## 🇫🇷 Version Française

### Installation

1. Téléchargez `systemd-manager-linux.tar` depuis la [page des releases](https://github.com/Sebdev43/SystemdManager/releases)
2. Extrayez l'archive :

```bash
tar xf systemd-manager-linux.tar
cd systemd-manager
```

3. Exécutez le script d'installation :

```bash
sudo ./install.sh
```

L'exécutable sera installé dans `/usr/local/bin/systemd-manager`

### Vérification de l'installation

Pour vérifier que l'installation est réussie :

```bash
systemd-manager --version
sudo systemd-manager
```

### Structure des fichiers

- Exécutable : `/usr/local/bin/systemd-manager`
- Fichiers de configuration : `~/.config/systemd-manager/`
- Services systemd : `/etc/systemd/system/`
- Logs : accessibles via `journalctl`

### Désinstallation

Pour désinstaller SystemD Manager :

```bash
sudo rm /usr/local/bin/systemd-manager
```

### Résolution des problèmes

#### Erreur de permission

Si vous rencontrez une erreur de permission :

```bash
sudo chmod +x /usr/local/bin/systemd-manager
```

#### Erreur "Command not found"

Vérifiez que `/usr/local/bin` est dans votre PATH :

```bash
echo $PATH
```

### Mise à jour

1. Désinstallez la version actuelle
2. Téléchargez et installez la nouvelle version en suivant les étapes d'installation ci-dessus

### Support

En cas de problème :

- Ouvrez une issue sur GitHub
- Consultez la documentation complète
- Vérifiez les logs dans `journalctl`

---

## 🇬🇧 English Version

### Installation

1. Download `systemd-manager-linux.tar` from the [releases page](https://github.com/Sebdev43/SystemdManager/releases)
2. Extract the archive:

```bash
tar xf systemd-manager-linux.tar
cd systemd-manager
```

3. Run the installation script:

```bash
sudo ./install.sh
```

The executable will be installed in `/usr/local/bin/systemd-manager`

### Verifying the Installation

To verify the installation:

```bash
systemd-manager --version
sudo systemd-manager
```

### File Structure

- Executable: `/usr/local/bin/systemd-manager`
- Configuration files: `~/.config/systemd-manager/`
- Systemd services: `/etc/systemd/system/`
- Logs: accessible via `journalctl`

### Uninstallation

To uninstall SystemD Manager:

```bash
sudo rm /usr/local/bin/systemd-manager
```

### Troubleshooting

#### Permission Error

If you encounter a permission error:

```bash
sudo chmod +x /usr/local/bin/systemd-manager
```

#### "Command not found" Error

Check that `/usr/local/bin` is in your PATH:

```bash
echo $PATH
```

### Updating

1. Uninstall the current version
2. Download and install the new version following the installation steps above

### Support

If you encounter any issues:

- Open an issue on GitHub
- Check the complete documentation
- Check the logs in `journalctl`
