# Guide de Contribution

[English version below](#contributing-guide)

## 🇫🇷 Version Française

### 🚀 Comment contribuer

1. **Créez une Issue**
   - Décrivez le bug ou la fonctionnalité
   - Attendez la validation d'un mainteneur
   - Référencez l'issue dans votre PR

2. **Fork & Pull Request**
   - Forkez le dépôt
   - Créez une branche : `feature/nom-feature` ou `fix/nom-fix`
   - Faites vos modifications
   - Soumettez une PR

### 💻 Standards de Code

- **Style**
  - Utilisez Black pour le formatage
  - Suivez les règles Flake8
  - Validation MyPy pour le typage

- **Conventions de nommage**
  - camelCase pour méthodes/variables
  - PascalCase pour les classes
  - snake_case pour les modules

- **Documentation**
  - Docstrings en anglais
  - Commentaires bilingues (FR/EN)
  - README et docs bilingues

### ✅ Tests

```bash
# Installation des dépendances de développement
pip install -r requirements.txt

# Lancement des tests
pytest tests/

# Vérification du style
black src/
flake8 src/
mypy src/
```

### 🏗️ Environnement de développement

**Prérequis**
- Python 3.10+
- Droits sudo pour les tests
- Systemd

**Dépendances principales**
- PyQt6
- CustomTkinter
- Questionary
- Python-i18n

### 🔍 Revue de Code

- Tests automatiques réussis
- Au moins 1 review approuvée
- Style et typage validés
- Documentation à jour

### 🔒 Sécurité

- Validez toujours les entrées utilisateur
- Utilisez les chemins absolus
- Vérifiez les permissions
- Signalez les vulnérabilités en privé

---

## 🇬🇧 Contributing Guide

### 🚀 How to Contribute

1. **Create an Issue**
   - Describe the bug or feature
   - Wait for maintainer approval
   - Reference issue in your PR

2. **Fork & Pull Request**
   - Fork the repository
   - Create branch: `feature/feature-name` or `fix/fix-name`
   - Make your changes
   - Submit a PR

### 💻 Code Standards

- **Style**
  - Use Black for formatting
  - Follow Flake8 rules
  - MyPy validation for typing

- **Naming Conventions**
  - camelCase for methods/variables
  - PascalCase for classes
  - snake_case for modules

- **Documentation**
  - English docstrings
  - Bilingual comments (FR/EN)
  - Bilingual README and docs

### ✅ Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Check style
black src/
flake8 src/
mypy src/
```

### 🏗️ Development Environment

**Prerequisites**
- Python 3.10+
- Sudo rights for testing
- Systemd

**Main Dependencies**
- PyQt6
- CustomTkinter
- Questionary
- Python-i18n

### 🔍 Code Review

- Passing automated tests
- At least 1 approved review
- Style and typing validated
- Updated documentation

### 🔒 Security

- Always validate user input
- Use absolute paths
- Check permissions
- Report vulnerabilities privately 