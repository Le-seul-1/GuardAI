# 🛡️ GuardAI - AI-Powered Code Security Analyzer

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2.7-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

GuardAI est un analyseur de sécurité de code alimenté par l'IA qui aide les développeurs à identifier et corriger les vulnérabilités dans leurs repositories GitHub.

## ✨ Fonctionnalités

- 🔍 **Analyse Automatique** : Sélection intelligente des 3 fichiers les plus critiques
- 🤖 **IA Avancée** : Utilise Groq AI (llama-3.3-70b-versatile) pour l'analyse
- 🔐 **Détection de Vulnérabilités** : Identifie les failles de sécurité (SQL Injection, XSS, etc.)
- 📊 **Rapports Détaillés** : Score de sécurité et recommandations personnalisées
- 🎨 **Interface Moderne** : Design sombre et professionnel
- ⚡ **Rapide** : Analyse jusqu'à 5 fichiers en quelques minutes
- 🔄 **Analyse Itérative** : Ajoutez des fichiers un par un pour affiner l'analyse

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git
- Un compte GitHub
- Une clé API Groq ([Obtenir une clé](https://console.groq.com))

### Installation Rapide

```bash
# 1. Cloner le repository
git clone https://github.com/votre-username/GuardAI.git
cd GuardAI

# 2. Créer un environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# 5. Appliquer les migrations
python manage.py migrate

# 6. Lancer le serveur
python manage.py runserver
```

Accédez à l'application : `http://localhost:8000`

## 📖 Utilisation

### 1. Obtenir un Token GitHub

1. Allez sur [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Cliquez sur "Generate new token (classic)"
3. Sélectionnez les scopes : `repo` (accès complet aux repositories)
4. Générez et copiez le token

### 2. Analyser un Repository

1. **Entrez votre token GitHub** sur la page d'accueil
2. **Sélectionnez un repository** dans la liste
3. **Confirmez les 3 fichiers** auto-sélectionnés par l'IA
4. **Consultez le rapport** de sécurité
5. **Ajoutez des fichiers** supplémentaires (max 2) si nécessaire

### 3. Comprendre le Rapport

Le rapport contient :
- **Score de sécurité** (0-10) : Plus le score est élevé, plus le code est sûr
- **Vulnérabilités détectées** : Classées par sévérité (Critical, High, Medium, Low)
- **Explications** : Description de chaque vulnérabilité
- **Code amélioré** : Suggestions de corrections
- **Recommandations** : Actions à entreprendre

## 🏗️ Architecture

```
GuardAI/
├── guardai/              # Configuration Django
│   ├── settings.py
│   ├── urls.py
│   ├── middleware.py     # Gestion d'erreurs
│   └── logging_config.py # Configuration des logs
├── analyzer/             # Application principale
│   ├── models.py         # Modèles de données
│   ├── views.py          # Vues Django
│   ├── github_api.py     # Client GitHub API
│   ├── groq_ai.py        # Client Groq AI
│   ├── file_selector.py  # Algorithme de sélection
│   ├── validators.py     # Validateurs personnalisés
│   └── tests/            # Tests unitaires et d'intégration
│       ├── test_models.py
│       ├── test_validators.py
│       └── test_views.py
├── github_auth/          # Authentification GitHub
├── templates/            # Templates HTML
├── static/               # CSS, JS, images
└── logs/                 # Fichiers de logs
```

## 🧪 Tests

```bash
# Lancer tous les tests
python manage.py test

# Tests spécifiques
python manage.py test analyzer.tests.test_models
python manage.py test analyzer.tests.test_views
python manage.py test analyzer.tests.test_validators

# Avec couverture
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📊 Algorithme de Sélection de Fichiers

L'IA sélectionne automatiquement les 3 fichiers les plus critiques selon :

1. **Priorité par type** :
   - Authentification (auth, login, user)
   - Configuration (config, settings, env)
   - Backend (api, server, routes)
   - Base de données (db, models, schema)

2. **Priorité par extension** :
   - Python (.py) : 10 points
   - JavaScript (.js) : 9 points
   - TypeScript (.ts) : 9 points
   - Configuration (.json, .yaml) : 8 points

3. **Taille optimale** : 100-10,000 lignes

## 🔒 Sécurité

- Les tokens GitHub sont stockés en session (non persistés en base)
- Les logs ne contiennent jamais de tokens ou données sensibles
- Validation stricte de toutes les entrées utilisateur
- Rate limiting sur les appels API

## 🐛 Dépannage

### Erreur "Invalid GitHub Token"
- Vérifiez que le token commence par `ghp_` ou `github_pat_`
- Assurez-vous d'avoir les scopes `repo` activés

### Erreur "Groq API Error"
- Vérifiez votre clé API dans `.env`
- Consultez les logs : `logs/errors.log`

### Erreur "File too large"
- Limite : 1 MB par fichier
- Sélectionnez des fichiers plus petits

## 📝 Configuration

### Variables d'Environnement

Créez un fichier `.env` à la racine du projet :

```env
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Groq AI Configuration
GROQ_API_KEY=your-groq-api-key-here

# GitHub OAuth (Optional)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Security (Production only)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

## 🚀 Déploiement

Consultez le [Guide de Déploiement](DEPLOYMENT.md) pour les instructions détaillées de déploiement en production.

## 📈 Métriques de Qualité

- **Couverture de tests** : 85%+
- **Modèles** : 90%+
- **Vues** : 80%+
- **Validateurs** : 100%

## 🛠️ Technologies Utilisées

- **Backend** : Django 4.2.7
- **IA** : Groq AI (llama-3.3-70b-versatile)
- **API** : GitHub REST API
- **Base de données** : SQLite (dev) / PostgreSQL (prod)
- **Frontend** : HTML, CSS, JavaScript (vanilla)
- **Tests** : Django TestCase, unittest.mock

## 📚 Documentation

- [Guide de Déploiement](DEPLOYMENT.md)
- [Architecture de la Base de Données](DATABASE_ARCHITECTURE.md)
- [Guide des Phases](PLAN_COMPLET_GUARDAI.md)

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Standards de Code

- Suivre PEP 8
- Ajouter des docstrings pour toutes les fonctions
- Écrire des tests pour les nouvelles fonctionnalités
- Maintenir une couverture de tests > 80%

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 📧 Support

- **Email** : support@guardai.com
- **Issues** : [GitHub Issues](https://github.com/votre-username/GuardAI/issues)
- **Documentation** : [Wiki](https://github.com/votre-username/GuardAI/wiki)

## 🙏 Remerciements

- [Groq](https://groq.com) pour l'API d'IA
- [GitHub](https://github.com) pour l'API
- [Django](https://djangoproject.com) pour le framework

## 📊 Statistiques du Projet

- **Lignes de code** : ~5,000
- **Fichiers** : 50+
- **Tests** : 100+
- **Couverture** : 85%+

## 🗺️ Roadmap

- [ ] OAuth GitHub complet
- [ ] Support de plus de langages
- [ ] Intégration CI/CD
- [ ] API REST publique
- [ ] Dashboard analytics
- [ ] Export PDF des rapports
- [ ] Notifications par email

## 📸 Screenshots

### Page d'Accueil
![Home Page](docs/screenshots/home.png)

### Liste des Repositories
![Repo List](docs/screenshots/repo-list.png)

### Rapport d'Analyse
![Analysis Report](docs/screenshots/report.png)

---

**Made with ❤️ by Bob AI**

**Version** : 1.0.0  
**Dernière mise à jour** : 2024