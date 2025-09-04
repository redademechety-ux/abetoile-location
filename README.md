# 🚗 **Abetoile Rental Management System**

Une application complète de gestion de location de véhicules développée avec React, FastAPI, et MongoDB. Système intelligent avec génération PDF automatique et comptabilité française intégrée.

## ✨ **Fonctionnalités**

### 🔐 **Authentification & Sécurité**
- Authentification JWT sécurisée
- Gestion des utilisateurs et permissions
- Protection des routes et données sensibles

### 👥 **Gestion Clients**
- Fiche client complète (entreprise, contact, adresse)
- Gestion TVA personnalisée par client
- Numéros RCS et TVA intracommunautaire
- Upload de documents (permis, pièces d'identité)
- Validation automatique des données

### 🚗 **Gestion Véhicules**
- Catalogue véhicules multi-types (voitures, camionnettes, camions, motos)
- Suivi complet des assurances et contrôles techniques
- Alertes d'expiration automatiques
- Tarification personnalisée
- Gestion de la disponibilité

### 📋 **Commandes & Devis**
- Création de commandes multi-véhicules
- **Locations reconductibles automatiques**
- Périodes flexibles (jours, semaines, mois, années)
- Calculs automatiques HT/TTC
- Workflow complet devis → commande → facture

### 🧾 **Facturation Intelligente**
- **Génération PDF automatique avec IA** (GPT-4o-mini)
- Factures conformes aux standards français
- Gestion des échéances et relances
- Suivi des impayés avec alertes
- Reconduction automatique conditionnelle

### 📊 **Comptabilité Française**
- **Plan Comptable Général (PCG) intégré**
- Écritures comptables automatiques
- Exports multi-formats : CSV, CIEL, SAGE, CEGID
- Vérification d'équilibrage
- Reporting comptable complet

### 🎯 **Dashboard & Reporting**
- Tableau de bord temps réel
- Alertes factures impayées
- Statistiques et KPIs
- Suivi de l'activité

## 🛠️ **Technologies**

### Backend
- **FastAPI** - API moderne et performante
- **MongoDB** - Base de données NoSQL
- **Python 3.11** - Langage principal
- **JWT** - Authentification sécurisée
- **ReportLab** - Génération PDF
- **EmergentAI** - Intelligence artificielle intégrée

### Frontend
- **React 19** - Interface utilisateur moderne
- **React Router** - Navigation SPA
- **Axios** - Client HTTP
- **Tailwind CSS** - Framework CSS utilitaire
- **Shadcn/UI** - Composants UI élégants
- **Lucide React** - Icônes modernes

### Infrastructure
- **Nginx** - Serveur web et proxy
- **Systemd** - Gestion des services
- **UFW** - Firewall
- **Certbot** - Certificats SSL automatiques

## 🚀 **Installation**

### Installation Automatique (Recommandée)

```bash
# Télécharger et exécuter le script d'installation
curl -sSL https://raw.githubusercontent.com/VOTRE-USERNAME/abetoile-rental/main/install.sh | sudo bash

# Déployer le code source
curl -sSL https://raw.githubusercontent.com/VOTRE-USERNAME/abetoile-rental/main/deploy.sh | sudo bash

# Configurer SSL
sudo certbot --nginx -d abetoile-rental.com -d www.abetoile-rental.com
```

### Configuration Manuelle

#### Prérequis
- Ubuntu 20.04+ ou Debian 11+
- 2GB RAM minimum, 4GB recommandé
- Accès root ou sudo

#### Backend
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
yarn install
yarn build
```

## ⚙️ **Configuration**

### Variables d'environnement Backend (.env)
```bash
MONGO_URL="mongodb://abetoile_user:PASSWORD@localhost:27017/abetoile_rental_prod"
DB_NAME="abetoile_rental_prod"
CORS_ORIGINS="https://abetoile-rental.com,https://www.abetoile-rental.com"
SECRET_KEY="votre-clé-secrète-32-caractères"
EMERGENT_LLM_KEY="sk-emergent-c68C3249e6154EcE22"
```

### Variables d'environnement Frontend (.env)
```bash
REACT_APP_BACKEND_URL=https://abetoile-rental.com
```

## 🔧 **Commandes Utiles**

### Gestion des services
```bash
# Redémarrer l'application
abetoile-restart

# Déployer une mise à jour
abetoile-deploy

# Effectuer une sauvegarde
abetoile-backup

# Voir les logs
journalctl -u abetoile-backend -f
tail -f /var/log/nginx/abetoile-rental.error.log
```

### Maintenance MongoDB
```bash
# Sauvegarde manuelle
mongodump --uri="mongodb://abetoile_user:PASSWORD@localhost:27017/abetoile_rental_prod" --out backup/

# Restauration
mongorestore --uri="mongodb://abetoile_user:PASSWORD@localhost:27017/abetoile_rental_prod" backup/abetoile_rental_prod/
```

## 📋 **Structure du Projet**

```
abetoile-rental/
├── backend/
│   ├── server.py              # API FastAPI principale
│   ├── pdf_generator.py       # Génération PDF avec IA
│   ├── accounting.py          # Système comptable français
│   ├── requirements.txt       # Dépendances Python
│   └── .env                   # Configuration backend
├── frontend/
│   ├── src/
│   │   ├── components/        # Composants React
│   │   ├── App.js            # Application principale
│   │   └── App.css           # Styles globaux
│   ├── public/               # Fichiers statiques
│   ├── package.json          # Dépendances Node.js
│   └── .env                  # Configuration frontend
├── install.sh                # Script d'installation automatique
├── deploy.sh                 # Script de déploiement
└── README.md                 # Documentation
```

## 🎯 **Utilisation**

### Premier démarrage
1. Accédez à https://abetoile-rental.com
2. Créez un compte administrateur
3. Configurez les paramètres de l'entreprise
4. Ajoutez vos premiers clients et véhicules
5. Créez votre première commande

### Workflow type
1. **Client** → Créer une fiche client complète
2. **Véhicule** → Ajouter un véhicule avec assurance/contrôle
3. **Commande** → Créer une commande (mono ou multi-véhicules)
4. **Facture** → Génération automatique avec PDF intelligent
5. **Comptabilité** → Écritures automatiques + exports

## 🔒 **Sécurité**

- Authentification JWT avec expiration
- Hashage des mots de passe avec bcrypt
- Validation des données côté serveur
- Protection CORS configurée
- Headers de sécurité HTTP
- Firewall UFW configuré
- SSL/TLS avec renouvellement automatique

## 📊 **Monitoring**

- Logs systemd intégrés
- Monitoring Nginx
- Alertes MongoDB
- Sauvegardes automatiques quotidiennes
- Métriques d'utilisation

## 🆘 **Support & Dépannage**

### Problèmes courants

**Backend ne démarre pas :**
```bash
journalctl -u abetoile-backend -n 50
```

**Erreur MongoDB :**
```bash
systemctl status mongod
tail -f /var/log/mongodb/mongod.log
```

**Problème SSL :**
```bash
certbot certificates
nginx -t
```

### Contacts
- **Documentation** : Ce README
- **Issues** : GitHub Issues
- **Logs** : `/var/log/abetoile-rental/`

## 📄 **Licence**

Ce projet est propriétaire et confidentiel. Tous droits réservés.

## 🎉 **Crédits**

Développé avec ❤️ pour une gestion professionnelle de location de véhicules.

- **Framework IA** : Emergent Platform
- **Design** : Tailwind CSS + Shadcn/UI
- **Architecture** : FastAPI + React + MongoDB

---

**Version** : 1.0.0  
**Dernière mise à jour** : Décembre 2024  
**Domaine** : https://abetoile-rental.com