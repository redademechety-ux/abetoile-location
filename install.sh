#!/bin/bash

# =============================================================================
# 🚀 SCRIPT D'INSTALLATION AUTOMATIQUE - Abetoile Location Management
# =============================================================================
# Domaine: abetoile-location.fr / www.abetoile-location.fr
# Port Backend: 8001
# Serveur: Multi-sites
# =============================================================================

set -e  # Arrêt en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="abetoile-location.fr"
APP_DIR="/var/www/abetoile-location"
BACKEND_PORT="8001"
DB_NAME="abetoile_location_prod"

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Ce script doit être exécuté en tant que root (sudo)"
        exit 1
    fi
}

# =============================================================================
# ÉTAPE 1: VÉRIFICATIONS PRÉLIMINAIRES
# =============================================================================
log_info "🔍 Vérifications préliminaires..."

check_root

# Vérifier la distribution
if ! command -v apt &> /dev/null; then
    log_error "Ce script est conçu pour Ubuntu/Debian uniquement"
    exit 1
fi

log_success "Système compatible détecté"

# =============================================================================
# ÉTAPE 2: MISE À JOUR DU SYSTÈME
# =============================================================================
log_info "📦 Mise à jour du système..."

export DEBIAN_FRONTEND=noninteractive
apt update -y
apt upgrade -y
apt install -y curl wget git nano htop unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

log_success "Système mis à jour"

# =============================================================================
# ÉTAPE 3: INSTALLATION PYTHON 3.11
# =============================================================================
log_info "🐍 Installation de Python 3.11..."

add-apt-repository ppa:deadsnakes/ppa -y
apt update -y
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip python3.11-distutils

# Créer les liens symboliques
ln -sf /usr/bin/python3.11 /usr/bin/python3
ln -sf /usr/bin/python3.11 /usr/bin/python

log_success "Python 3.11 installé"

# =============================================================================
# ÉTAPE 4: INSTALLATION NODE.JS ET YARN
# =============================================================================
log_info "📦 Installation de Node.js et Yarn..."

# Node.js 18.x LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Yarn
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
apt update -y
apt install -y yarn

log_success "Node.js $(node --version) et Yarn $(yarn --version) installés"

# =============================================================================
# ÉTAPE 5: INSTALLATION MONGODB
# =============================================================================
log_info "🗄️ Installation de MongoDB..."

# Clé GPG MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add -

# Repository MongoDB
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Installation
apt update -y
apt install -y mongodb-org

# Configuration et démarrage
systemctl start mongod
systemctl enable mongod

log_success "MongoDB installé et démarré"

# =============================================================================
# ÉTAPE 6: INSTALLATION NGINX
# =============================================================================
log_info "🌐 Installation de Nginx..."

apt install -y nginx
systemctl start nginx
systemctl enable nginx

log_success "Nginx installé et démarré"

# =============================================================================
# ÉTAPE 7: CONFIGURATION DU FIREWALL
# =============================================================================
log_info "🔥 Configuration du firewall..."

apt install -y ufw
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow $BACKEND_PORT
ufw --force enable

log_success "Firewall configuré"

# =============================================================================
# ÉTAPE 8: CRÉATION DE L'UTILISATEUR ET RÉPERTOIRES
# =============================================================================
log_info "📁 Création des répertoires et utilisateur..."

# Créer l'utilisateur www-data s'il n'existe pas
if ! id "www-data" &>/dev/null; then
    useradd -r -s /bin/false www-data
fi

# Créer les répertoires
mkdir -p $APP_DIR
mkdir -p /var/log/abetoile-location
mkdir -p /var/backups/abetoile-location

# Permissions
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data /var/log/abetoile-location

log_success "Répertoires créés"

# =============================================================================
# ÉTAPE 9: TÉLÉCHARGEMENT DU CODE SOURCE
# =============================================================================
log_info "📥 Téléchargement du code source..."

cd $APP_DIR

# Si vous avez un repository GitHub, décommentez cette ligne:
# git clone https://github.com/VOTRE-USERNAME/abetoile-location.git .

# Sinon, créer la structure de base
mkdir -p backend frontend

log_success "Structure de base créée"

# =============================================================================
# ÉTAPE 10: CONFIGURATION MONGODB
# =============================================================================
log_info "🗄️ Configuration de MongoDB..."

# Créer l'utilisateur MongoDB
mongosh --eval "
use $DB_NAME;
db.createUser({
  user: 'abetoile_user',
  pwd: 'Ab3t0il3L0c4t10n2024!',
  roles: [
    { role: 'readWrite', db: '$DB_NAME' }
  ]
});
"

# Configuration sécurisée MongoDB
cat > /etc/mongod.conf << 'EOF'
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

net:
  port: 27017
  bindIp: 127.0.0.1

processManagement:
  timeZoneInfo: /usr/share/zoneinfo

security:
  authorization: enabled
EOF

systemctl restart mongod

log_success "MongoDB configuré avec authentification"

# =============================================================================
# ÉTAPE 11: CRÉATION DES FICHIERS DE CONFIGURATION
# =============================================================================
log_info "⚙️ Création des fichiers de configuration..."

# Backend .env
cat > $APP_DIR/backend/.env << EOF
MONGO_URL="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/$DB_NAME"
DB_NAME="$DB_NAME"
CORS_ORIGINS="https://$DOMAIN,https://www.$DOMAIN,http://localhost:3000"
SECRET_KEY="$(openssl rand -hex 32)"
EMERGENT_LLM_KEY=sk-emergent-c68C3249e6154EcE22
EOF

# Frontend .env
cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF

# Service systemd pour le backend
cat > /etc/systemd/system/abetoile-location-backend.service << EOF
[Unit]
Description=Abetoile Location Backend
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR/backend
Environment=PATH=$APP_DIR/backend/venv/bin
ExecStart=$APP_DIR/backend/venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port $BACKEND_PORT
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

log_success "Fichiers de configuration créés"

# =============================================================================
# ÉTAPE 12: CONFIGURATION NGINX MULTI-SITES
# =============================================================================
log_info "🌐 Configuration Nginx multi-sites..."

# Configuration pour abetoile-location.fr
cat > /etc/nginx/sites-available/abetoile-location << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirection HTTPS (décommentez après l'installation SSL)
    # return 301 https://\$server_name\$request_uri;

    # Root du frontend React
    root $APP_DIR/frontend/build;
    index index.html;

    # Logs spécifiques
    access_log /var/log/nginx/abetoile-location.access.log;
    error_log /var/log/nginx/abetoile-location.error.log;

    # Gestion des routes React (SPA)
    location / {
        try_files \$uri \$uri/ /index.html;
        
        # Headers de sécurité
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    }

    # Proxy pour l'API backend sur port $BACKEND_PORT
    location /api/ {
        proxy_pass http://localhost:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Optimisation des fichiers statiques
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, no-transform";
        access_log off;
    }

    # Fichiers sensibles
    location ~ /\. {
        deny all;
    }

    location ~ ^/(\.env|package\.json|yarn\.lock)$ {
        deny all;
    }
}
EOF

# Activer le site
ln -sf /etc/nginx/sites-available/abetoile-location /etc/nginx/sites-enabled/

# Tester la configuration
nginx -t

# Recharger Nginx
systemctl reload nginx

log_success "Configuration Nginx multi-sites terminée"

# =============================================================================
# ÉTAPE 13: INSTALLATION SSL (CERTBOT)
# =============================================================================
log_info "🔒 Installation de Certbot pour SSL..."

apt install -y certbot python3-certbot-nginx

log_success "Certbot installé"
log_warning "⚠️  N'oubliez pas d'exécuter après l'installation:"
log_warning "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"

# =============================================================================
# ÉTAPE 14: SCRIPTS DE MAINTENANCE
# =============================================================================
log_info "🔧 Création des scripts de maintenance..."

# Script de redémarrage
cat > /usr/local/bin/abetoile-location-restart << 'EOF'
#!/bin/bash
echo "🔄 Redémarrage Abetoile Location..."
systemctl restart abetoile-location-backend
systemctl reload nginx
systemctl status abetoile-location-backend
echo "✅ Redémarrage terminé!"
EOF

# Script de déploiement
cat > /usr/local/bin/abetoile-location-deploy << EOF
#!/bin/bash
set -e

APP_DIR="$APP_DIR"
BACKUP_DIR="/var/backups/abetoile-location"

echo "🚀 Déploiement Abetoile Location..."

# Backup de la base de données
echo "💾 Sauvegarde de la base de données..."
mongodump --uri="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/$DB_NAME" --out "\$BACKUP_DIR/mongo-\$(date +%Y%m%d_%H%M%S)"

# Backup du code
echo "📁 Sauvegarde du code..."
tar -czf "\$BACKUP_DIR/code-\$(date +%Y%m%d_%H%M%S).tar.gz" "\$APP_DIR"

# Mise à jour du code (si repository Git)
cd "\$APP_DIR"
if [ -d ".git" ]; then
    echo "📥 Mise à jour depuis Git..."
    git pull origin main
fi

# Backend
echo "🐍 Mise à jour Backend..."
cd "\$APP_DIR/backend"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install -r requirements.txt
    systemctl restart abetoile-location-backend
fi

# Frontend
echo "⚛️  Mise à jour Frontend..."
cd "\$APP_DIR/frontend"
if [ -f "package.json" ]; then
    yarn install
    yarn build
    systemctl reload nginx
fi

echo "✅ Déploiement terminé!"
systemctl status abetoile-location-backend
EOF

# Script de sauvegarde
cat > /usr/local/bin/abetoile-location-backup << EOF
#!/bin/bash
BACKUP_DIR="/var/backups/abetoile-location"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p "\$BACKUP_DIR"

echo "💾 Sauvegarde Abetoile Location [\$DATE]..."

# Sauvegarde MongoDB
mongodump --uri="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/$DB_NAME" --out "\$BACKUP_DIR/mongo-\$DATE"

# Sauvegarde code
tar -czf "\$BACKUP_DIR/code-\$DATE.tar.gz" "$APP_DIR"

# Sauvegarde configuration Nginx
cp /etc/nginx/sites-available/abetoile-location "\$BACKUP_DIR/nginx-\$DATE.conf"

# Nettoyage des anciennes sauvegardes (garder 7 jours)
find "\$BACKUP_DIR" -name "mongo-*" -mtime +7 -exec rm -rf {} \;
find "\$BACKUP_DIR" -name "code-*.tar.gz" -mtime +7 -delete

echo "✅ Sauvegarde terminée: \$BACKUP_DIR"
ls -lah "\$BACKUP_DIR"
EOF

# Rendre les scripts exécutables
chmod +x /usr/local/bin/abetoile-location-restart
chmod +x /usr/local/bin/abetoile-location-deploy
chmod +x /usr/local/bin/abetoile-location-backup

log_success "Scripts de maintenance créés"

# =============================================================================
# ÉTAPE 15: CONFIGURATION DES TÂCHES CRON
# =============================================================================
log_info "⏰ Configuration des tâches automatiques..."

# Sauvegarde quotidienne à 2h du matin
cat > /etc/cron.d/abetoile-location-backup << 'EOF'
0 2 * * * root /usr/local/bin/abetoile-location-backup >> /var/log/abetoile-location/backup.log 2>&1
EOF

log_success "Tâches cron configurées"

# =============================================================================
# ÉTAPE 16: FINALISATION
# =============================================================================
log_info "🔧 Finalisation de l'installation..."

# Recharger systemd
systemctl daemon-reload

# Créer les répertoires de logs
mkdir -p /var/log/abetoile-location
touch /var/log/abetoile-location/app.log
touch /var/log/abetoile-location/backup.log

# Permissions finales
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data /var/log/abetoile-location
chmod -R 755 $APP_DIR
chmod -R 644 $APP_DIR/backend/.env
chmod -R 644 $APP_DIR/frontend/.env

# =============================================================================
# RÉSUMÉ ET INSTRUCTIONS FINALES
# =============================================================================
clear
echo -e "${GREEN}"
echo "================================================================================"
echo "🎉 INSTALLATION TERMINÉE - ABETOILE LOCATION MANAGEMENT"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}📋 RÉSUMÉ DE L'INSTALLATION:${NC}"
echo "   • Domaine: $DOMAIN / www.$DOMAIN"
echo "   • Backend: Port $BACKEND_PORT"
echo "   • Base de données: $DB_NAME"
echo "   • Répertoire: $APP_DIR"
echo ""

echo -e "${YELLOW}⚠️  ÉTAPES MANUELLES RESTANTES:${NC}"
echo ""
echo -e "${RED}1. COPIER LE CODE SOURCE:${NC}"
echo "   cd $APP_DIR"
echo "   # Copiez vos fichiers backend et frontend ici"
echo ""

echo -e "${RED}2. INSTALLER LES DÉPENDANCES BACKEND:${NC}"
echo "   cd $APP_DIR/backend"
echo "   python3.11 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/"
echo "   pip install -r requirements.txt"
echo ""

echo -e "${RED}3. INSTALLER LES DÉPENDANCES FRONTEND:${NC}"
echo "   cd $APP_DIR/frontend"
echo "   yarn install"
echo "   yarn build"
echo ""

echo -e "${RED}4. DÉMARRER LES SERVICES:${NC}"
echo "   systemctl enable abetoile-location-backend"
echo "   systemctl start abetoile-location-backend"
echo "   systemctl reload nginx"
echo ""

echo -e "${RED}5. CONFIGURER SSL:${NC}"
echo "   certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""

echo -e "${BLUE}🔧 COMMANDES UTILES:${NC}"
echo "   • Redémarrer: abetoile-location-restart"
echo "   • Déployer: abetoile-location-deploy"
echo "   • Sauvegarder: abetoile-location-backup"
echo "   • Logs backend: journalctl -u abetoile-location-backend -f"
echo "   • Logs nginx: tail -f /var/log/nginx/abetoile-location.error.log"
echo ""

echo -e "${GREEN}✅ Installation de base terminée avec succès!${NC}"
echo -e "${YELLOW}🔗 Une fois le code copié: https://$DOMAIN${NC}"
echo ""