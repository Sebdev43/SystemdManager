# SystemdManager

Un gestionnaire graphique et en ligne de commande pour les services systemd sous Linux.

## 🚀 Fonctionnalités

- Interface graphique intuitive (GUI)
- Interface en ligne de commande (CLI)
- Création et gestion de services systemd
- Support du lancement dans screen
- Gestion des délais de démarrage
- Choix de l'utilisateur d'exécution

## 📋 Prérequis

- Linux (testé sur Ubuntu)
- Python 3.10 ou supérieur
- Droits sudo pour la gestion des services

## 💻 Installation

### Option 1 : Via les releases

1. Téléchargez la dernière version depuis [Releases](https://github.com/votre-username/systemd-manager/releases)
2. Rendez le fichier exécutable :
```bash
chmod +x systemd-manager
```
3. Exécutez le programme :
```bash
sudo ./systemd-manager
```

### Option 2 : Depuis les sources

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/systemd-manager.git
cd systemd-manager

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
sudo python src/main.py
```

## 🛠️ Utilisation

1. **Mode GUI** :
   - Lancez l'application
   - Utilisez l'interface graphique pour gérer vos services

2. **Mode CLI** :
   - Utilisez les commandes en ligne pour une gestion rapide
   - Parfait pour les scripts et l'automatisation

## 🤝 Contribution

Les contributions sont les bienvenues ! Voici comment participer :

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add: Amazing Feature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence Apache 2.0 - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🔒 Sécurité

- L'application nécessite des droits sudo pour gérer les services
- Vérifiez toujours les scripts avant de les exécuter
- Utilisez des chemins absolus pour plus de sécurité

## 📞 Support

- Ouvrez une issue pour les bugs
- Utilisez les discussions pour les questions
- Consultez le wiki pour la documentation détaillée