# 🚀 Guide de Déploiement - GuardAI

Ce guide explique comment déployer GuardAI en production.

## 📋 Prérequis

- Serveur Linux (Ubuntu 20.04+ recommandé)
- Python 3.8+
- PostgreSQL 12+ (recommandé pour la production)
- Nginx
- Supervisor (pour gérer les processus)
- Nom de domaine (optionnel)

## 🔧 Configuration du Serveur

### 1. Installer les Dépendances Système

```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx supervisor postgresql postgresql-contrib
```

### 2. Créer un Utilisateur Dédié

```bash
sudo adduser guardai
sudo usermod -aG sudo guardai
su - guardai
```

### 3. Cloner le Projet

```bash
cd /home/guardai
git clone https://github.com/votre-username/GuardAI.git
cd GuardAI
```

### 4. Configurer l'Environnement Virtuel

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

## 🗄️ Configuration de PostgreSQL

### 1. Créer la Base de Données

```bash
sudo -u postgres psql

CREATE DATABASE guardai_db;
CREATE USER guardai_user WITH PASSWORD 'votre_mot_de_passe_securise';
ALTER ROLE guardai_user SET client_encoding TO 'utf8';
ALTER ROLE guardai_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE guardai_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE guardai_db TO guardai_user;
\q
```

### 2. Mettre à Jour settings.py

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'guardai_db',
        'USER': 'guardai_user',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🔐 Configuration de Production

### 1. Créer .env de Production

```bash
nano /home/guardai/GuardAI/.env
```

```env
# Django Configuration
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com

# Database
DB_PASSWORD=votre_mot_de_passe_securise

# Groq AI Configuration
GROQ_API_KEY=votre-cle-api-groq

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 2. Générer une Clé Secrète

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 3. Appliquer les Migrations

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Créer un Superutilisateur (Optionnel)

```bash
python manage.py createsuperuser
```

## 🌐 Configuration Nginx

### Créer /etc/nginx/sites-available/guardai

```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/guardai/GuardAI;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/guardai/GuardAI/guardai.sock;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_redirect off;
    }
}
```

### Activer le Site

```bash
sudo ln -s /etc/nginx/sites-available/guardai /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 🔄 Configuration Supervisor

### Créer /etc/supervisor/conf.d/guardai.conf

```ini
[program:guardai]
command=/home/guardai/GuardAI/venv/bin/gunicorn --workers 3 --bind unix:/home/guardai/GuardAI/guardai.sock guardai.wsgi:application
directory=/home/guardai/GuardAI
user=guardai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/guardai/GuardAI/logs/gunicorn.log
```

### Démarrer Supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start guardai
```

### Commandes Supervisor Utiles

```bash
# Vérifier le statut
sudo supervisorctl status guardai

# Redémarrer
sudo supervisorctl restart guardai

# Arrêter
sudo supervisorctl stop guardai

# Voir les logs
sudo supervisorctl tail -f guardai
```

## 🔒 SSL avec Let's Encrypt

### Installation de Certbot

```bash
sudo apt install certbot python3-certbot-nginx
```

### Obtenir un Certificat SSL

```bash
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com
```

### Renouvellement Automatique

```bash
# Tester le renouvellement
sudo certbot renew --dry-run

# Le renouvellement automatique est configuré via cron
```

## 📊 Monitoring

### Vérifier les Logs

```bash
# Logs Django
tail -f /home/guardai/GuardAI/logs/guardai.log

# Logs d'erreurs
tail -f /home/guardai/GuardAI/logs/errors.log

# Logs Gunicorn
tail -f /home/guardai/GuardAI/logs/gunicorn.log

# Logs Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Configuration de Logrotate

Créer `/etc/logrotate.d/guardai` :

```
/home/guardai/GuardAI/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 guardai guardai
    sharedscripts
    postrotate
        supervisorctl restart guardai > /dev/null
    endscript
}
```

## 🔄 Mise à Jour

### Procédure de Mise à Jour

```bash
cd /home/guardai/GuardAI

# 1. Sauvegarder la base de données
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

# 2. Récupérer les dernières modifications
git pull origin main

# 3. Activer l'environnement virtuel
source venv/bin/activate

# 4. Installer les nouvelles dépendances
pip install -r requirements.txt

# 5. Appliquer les migrations
python manage.py migrate

# 6. Collecter les fichiers statiques
python manage.py collectstatic --noinput

# 7. Redémarrer l'application
sudo supervisorctl restart guardai
```

## 🔐 Sécurité en Production

### 1. Firewall (UFW)

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2Ban

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Permissions des Fichiers

```bash
# Définir les permissions correctes
chmod 600 /home/guardai/GuardAI/.env
chmod 755 /home/guardai/GuardAI
chmod -R 755 /home/guardai/GuardAI/static
```

### 4. Sauvegardes Automatiques

Créer un script de sauvegarde `/home/guardai/backup.sh` :

```bash
#!/bin/bash
BACKUP_DIR="/home/guardai/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Créer le répertoire de sauvegarde
mkdir -p $BACKUP_DIR

# Sauvegarder la base de données
cd /home/guardai/GuardAI
source venv/bin/activate
python manage.py dumpdata > $BACKUP_DIR/db_backup_$DATE.json

# Compresser
gzip $BACKUP_DIR/db_backup_$DATE.json

# Supprimer les sauvegardes de plus de 30 jours
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

Ajouter au crontab :

```bash
crontab -e

# Sauvegarde quotidienne à 2h du matin
0 2 * * * /home/guardai/backup.sh
```

## 📈 Optimisation des Performances

### 1. Configuration Gunicorn

Ajuster le nombre de workers dans `/etc/supervisor/conf.d/guardai.conf` :

```ini
# Formule : (2 x nombre_de_cores) + 1
command=/home/guardai/GuardAI/venv/bin/gunicorn --workers 5 --bind unix:/home/guardai/GuardAI/guardai.sock guardai.wsgi:application
```

### 2. Cache Django

Dans `settings.py` :

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. Compression Nginx

Ajouter dans la configuration Nginx :

```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
```

## 🐛 Dépannage

### Problème : Gunicorn ne démarre pas

```bash
# Vérifier les logs
sudo supervisorctl tail -f guardai stderr

# Tester manuellement
cd /home/guardai/GuardAI
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 guardai.wsgi:application
```

### Problème : Erreur 502 Bad Gateway

```bash
# Vérifier que Gunicorn tourne
sudo supervisorctl status guardai

# Vérifier les permissions du socket
ls -l /home/guardai/GuardAI/guardai.sock

# Redémarrer Nginx
sudo systemctl restart nginx
```

### Problème : Fichiers statiques non chargés

```bash
# Re-collecter les fichiers statiques
python manage.py collectstatic --noinput

# Vérifier les permissions
chmod -R 755 /home/guardai/GuardAI/static
```

## ✅ Checklist de Déploiement

- [ ] Serveur configuré avec Python 3.8+
- [ ] PostgreSQL installé et configuré
- [ ] Variables d'environnement définies dans .env
- [ ] SECRET_KEY généré et sécurisé
- [ ] DEBUG=False en production
- [ ] ALLOWED_HOSTS configuré
- [ ] Migrations appliquées
- [ ] Fichiers statiques collectés
- [ ] Nginx configuré et testé
- [ ] Supervisor configuré et démarré
- [ ] SSL activé avec Let's Encrypt
- [ ] Firewall configuré (UFW)
- [ ] Fail2Ban installé
- [ ] Sauvegardes automatiques configurées
- [ ] Logs configurés et rotatifs
- [ ] Tests de charge effectués
- [ ] Monitoring en place
- [ ] Documentation mise à jour

## 📞 Support Post-Déploiement

En cas de problème :

1. Consultez les logs : `/home/guardai/GuardAI/logs/`
2. Vérifiez le statut des services : `sudo supervisorctl status`
3. Testez la connectivité : `curl http://localhost:8000`
4. Contactez le support : support@guardai.com

---

**Déploiement Réussi !** 🎉

**Prochaines étapes** :
- Configurer le monitoring (Sentry, New Relic)
- Mettre en place des alertes
- Optimiser les performances
- Planifier les mises à jour régulières