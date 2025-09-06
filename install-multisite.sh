#!/bin/bash

# =============================================================================
# 🚀 INSTALLATION ABETOILE LOCATION - SERVEUR MULTI-SITES
# =============================================================================
# Domaine: abetoile-location.fr
# Port Backend: 8001
# Compatible: Ubuntu 25.04+ (sans python3-distutils)
# Type: Serveur multi-sites (pas d'interférence avec autres sites)
# =============================================================================

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration spécifique
DOMAIN="abetoile-location.fr"
APP_DIR="/var/www/abetoile-location"
BACKEND_PORT="8001"
DB_NAME="abetoile_location_prod"
SERVICE_NAME="abetoile-location-backend"

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
# VÉRIFICATIONS PRÉLIMINAIRES
# =============================================================================
log_info "🔍 Vérifications serveur multi-sites..."

check_root

UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "unknown")
UBUNTU_CODENAME=$(lsb_release -cs 2>/dev/null || echo "unknown")

log_info "Serveur: Ubuntu $UBUNTU_VERSION ($UBUNTU_CODENAME)"
log_info "Configuration: Multi-sites, port $BACKEND_PORT"

# Vérifier si le port 8001 est libre
if netstat -tuln 2>/dev/null | grep -q ":$BACKEND_PORT "; then
    log_warning "Port $BACKEND_PORT déjà utilisé, vérification..."
    netstat -tuln | grep ":$BACKEND_PORT "
fi

log_success "Vérifications OK pour serveur multi-sites"

# =============================================================================
# MISE À JOUR SYSTÈME
# =============================================================================
log_info "📦 Mise à jour système..."

export DEBIAN_FRONTEND=noninteractive
apt update -y
apt upgrade -y
apt install -y curl wget git nano htop unzip software-properties-common \
    apt-transport-https ca-certificates gnupg lsb-release build-essential

log_success "Système mis à jour"

# =============================================================================
# PYTHON - UBUNTU 25.04+ COMPATIBLE
# =============================================================================
log_info "🐍 Installation Python pour Ubuntu 25.04+..."

# Packages Python disponibles sur Ubuntu récent (sans distutils)
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    python3-full

# python3-distutils n'existe plus sur Ubuntu 25.04+
# Installer setuptools qui le remplace
python3 -m pip install --break-system-packages setuptools distutils-extra

PYTHON_VERSION=$(python3 --version 2>&1)
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

log_success "$PYTHON_VERSION installé (compatible Ubuntu 25.04+)"

# Vérifier version compatible FastAPI
if [[ "$PYTHON_MAJOR" -ge "3" ]] && [[ "$PYTHON_MINOR" -ge "8" ]]; then
    log_success "Version Python compatible: $PYTHON_MAJOR.$PYTHON_MINOR"
else
    log_error "Python 3.8+ requis, trouvé: $PYTHON_MAJOR.$PYTHON_MINOR"
    exit 1
fi

# Mettre à jour pip
python3 -m pip install --break-system-packages --upgrade pip

log_success "Python configuré pour Ubuntu récent"

# =============================================================================
# NODE.JS ET YARN
# =============================================================================
log_info "📦 Installation Node.js et Yarn..."

# Nettoyer installations précédentes
rm -f /etc/apt/sources.list.d/nodesource.list 2>/dev/null || true
rm -f /etc/apt/sources.list.d/yarn.list 2>/dev/null || true

# Node.js 18.x LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Yarn avec keyring moderne
curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor -o /usr/share/keyrings/yarn.gpg
echo "deb [signed-by=/usr/share/keyrings/yarn.gpg] https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list
apt update -y
apt install -y yarn

NODE_VERSION=$(node --version 2>/dev/null)
YARN_VERSION=$(yarn --version 2>/dev/null)

log_success "Node.js $NODE_VERSION et Yarn $YARN_VERSION installés"

# =============================================================================
# MONGODB - COMPATIBLE UBUNTU RÉCENT
# =============================================================================
log_info "🗄️ Installation MongoDB..."

# Nettoyer installations précédentes
systemctl stop mongod 2>/dev/null || true
rm -f /etc/apt/sources.list.d/mongodb-org-*.list 2>/dev/null || true
rm -f /usr/share/keyrings/mongodb-server-*.gpg 2>/dev/null || true

# MongoDB avec keyring moderne
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg

# Pour Ubuntu 25.04, utiliser le repo jammy (le plus récent supporté)
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" > /etc/apt/sources.list.d/mongodb-org-7.0.list

apt update -y
apt install -y mongodb-org

# Configuration MongoDB
systemctl start mongod
systemctl enable mongod

sleep 5

if systemctl is-active --quiet mongod; then
    log_success "MongoDB installé et actif"
else
    log_error "Problème MongoDB"
    systemctl status mongod --no-pager
    exit 1
fi

# =============================================================================
# NGINX - CONFIGURATION MULTI-SITES
# =============================================================================
log_info "🌐 Installation Nginx (configuration multi-sites)..."

apt install -y nginx

# NE PAS toucher au site par défaut sur serveur multi-sites
# Créer seulement le site spécifique

systemctl start nginx
systemctl enable nginx

if systemctl is-active --quiet nginx; then
    NGINX_VERSION=$(nginx -v 2>&1 | cut -d' ' -f3)
    log_success "Nginx $NGINX_VERSION prêt pour multi-sites"
else
    log_error "Problème Nginx"
    exit 1
fi

# =============================================================================
# FIREWALL - CONFIGURATION SERVEUR MULTI-SITES
# =============================================================================
log_info "🔥 Configuration firewall multi-sites..."

# Configuration UFW pour serveur multi-sites
# Ne pas réinitialiser complètement sur un serveur existant
if ! ufw status | grep -q "Status: active"; then
    log_info "Activation UFW (première fois)"
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
fi

# Ajouter seulement le port spécifique pour ce site
ufw allow $BACKEND_PORT/tcp comment "Abetoile Location Backend"
ufw --force enable

log_success "Firewall configuré pour serveur multi-sites"

# =============================================================================
# CRÉATION STRUCTURE APPLICATION
# =============================================================================
log_info "📁 Création structure Abetoile Location..."

# Créer l'utilisateur www-data s'il n'existe pas
if ! id "www-data" &>/dev/null; then
    useradd -r -s /bin/false www-data
fi

# Structure de répertoires spécifique
mkdir -p $APP_DIR/backend
mkdir -p $APP_DIR/frontend
mkdir -p /var/log/abetoile-location
mkdir -p /var/backups/abetoile-location

# Permissions
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data /var/log/abetoile-location
chmod -R 755 $APP_DIR

log_success "Structure application créée"

# =============================================================================
# CONFIGURATION MONGODB SÉCURISÉE
# =============================================================================
log_info "🗄️ Configuration MongoDB pour Abetoile Location..."

sleep 5

# Créer utilisateur base de données spécifique
mongosh --eval "
use $DB_NAME;
try {
  db.createUser({
    user: 'abetoile_user',
    pwd: 'Ab3t0il3L0c4t10n2024!',
    roles: [
      { role: 'readWrite', db: '$DB_NAME' }
    ]
  });
  print('✅ Utilisateur BD créé: abetoile_user');
} catch (e) {
  if (e.code === 11000) {
    print('ℹ️ Utilisateur BD existe déjà');
  } else {
    print('❌ Erreur BD: ' + e);
  }
}
" --quiet

# Configuration MongoDB sécurisée (ne pas écraser sur serveur multi-sites)
if [ ! -f /etc/mongod.conf.backup ]; then
    cp /etc/mongod.conf /etc/mongod.conf.backup
    
    # Configuration MongoDB optimisée
    cat > /etc/mongod.conf << 'EOF'
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log
  logRotate: rename

net:
  port: 27017
  bindIp: 127.0.0.1

processManagement:
  timeZoneInfo: /usr/share/zoneinfo

security:
  authorization: enabled
EOF

    systemctl restart mongod
    sleep 5
fi

if systemctl is-active --quiet mongod; then
    log_success "MongoDB configuré avec authentification"
else
    log_error "Problème configuration MongoDB"
    exit 1
fi

# =============================================================================
# CONFIGURATION APPLICATION
# =============================================================================
log_info "⚙️ Configuration Abetoile Location..."

# Générer clé secrète unique
SECRET_KEY=$(openssl rand -hex 32)

# Configuration Backend
cat > $APP_DIR/backend/.env << EOF
MONGO_URL="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/$DB_NAME"
DB_NAME="$DB_NAME"
CORS_ORIGINS="https://$DOMAIN,https://www.$DOMAIN,http://localhost:3000"
SECRET_KEY="$SECRET_KEY"
EMERGENT_LLM_KEY=sk-emergent-c68C3249e6154EcE22
EOF

# Configuration Frontend
cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF

# Service systemd spécifique
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Abetoile Location Backend (Port $BACKEND_PORT)
After=network.target mongod.service
Requires=mongod.service
StartLimitBurst=5
StartLimitIntervalSec=10

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR/backend
Environment=PATH=$APP_DIR/backend/venv/bin
Environment=PYTHONPATH=$APP_DIR/backend
ExecStart=$APP_DIR/backend/venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port $BACKEND_PORT --workers 1
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=abetoile-backend

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$APP_DIR /var/log/abetoile-location

[Install]
WantedBy=multi-user.target
EOF

# Permissions sécurisées
chmod 600 $APP_DIR/backend/.env
chmod 600 $APP_DIR/frontend/.env
chown www-data:www-data $APP_DIR/backend/.env
chown www-data:www-data $APP_DIR/frontend/.env

log_success "Configuration application terminée"

# =============================================================================
# NGINX - SITE SPÉCIFIQUE MULTI-SITES
# =============================================================================
log_info "🌐 Configuration Nginx site spécifique..."

# Configuration Nginx pour serveur multi-sites
cat > /etc/nginx/sites-available/abetoile-location << EOF
# Abetoile Location - Site spécifique sur serveur multi-sites
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Logs dédiés pour ce site
    access_log /var/log/nginx/abetoile-location.access.log combined;
    error_log /var/log/nginx/abetoile-location.error.log warn;

    # Redirection HTTPS (activer après SSL)
    # return 301 https://\$server_name\$request_uri;

    # Frontend React
    root $APP_DIR/frontend/build;
    index index.html index.htm;

    # Headers de sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Routes React SPA
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # API Backend sur port $BACKEND_PORT (local seulement)
    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
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
        
        # Pas de cache API
        expires off;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # Fichiers statiques optimisés
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Sécurité - Bloquer fichiers sensibles
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    location ~ ^/(\.env|package\.json|yarn\.lock|node_modules)$ {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Gestion erreurs
    error_page 404 /index.html;
    error_page 500 502 503 504 /index.html;
}
EOF

# Activer SEULEMENT ce site (ne pas toucher aux autres)
ln -sf /etc/nginx/sites-available/abetoile-location /etc/nginx/sites-enabled/abetoile-location

# Tester configuration
if nginx -t; then
    systemctl reload nginx
    log_success "Site Nginx configuré (serveur multi-sites)"
else
    log_error "Erreur configuration Nginx"
    nginx -t
    exit 1
fi

# =============================================================================
# SSL/CERTBOT
# =============================================================================
log_info "🔒 Installation Certbot..."

apt install -y certbot python3-certbot-nginx

log_success "Certbot installé"

# =============================================================================
# SCRIPTS DE GESTION SPÉCIFIQUES
# =============================================================================
log_info "🔧 Scripts de gestion..."

# Script redémarrage
cat > /usr/local/bin/abetoile-location-restart << 'SCRIPT'
#!/bin/bash
echo "🔄 Redémarrage Abetoile Location..."
systemctl restart abetoile-location-backend
systemctl reload nginx
echo "📊 Statut:"
echo "  Backend: $(systemctl is-active abetoile-location-backend)"
echo "  Nginx: $(systemctl is-active nginx)"
echo "✅ Redémarrage terminé"
SCRIPT

# Script logs
cat > /usr/local/bin/abetoile-location-logs << 'SCRIPT'
#!/bin/bash
echo "📋 Logs Abetoile Location"
echo "========================"
echo "1) Backend FastAPI"
echo "2) Nginx Access"
echo "3) Nginx Errors"
echo "4) MongoDB"
read -p "Choix (1-4): " choice
case $choice in
    1) journalctl -u abetoile-location-backend -f ;;
    2) tail -f /var/log/nginx/abetoile-location.access.log ;;
    3) tail -f /var/log/nginx/abetoile-location.error.log ;;
    4) tail -f /var/log/mongodb/mongod.log ;;
    *) echo "Choix invalide" ;;
esac
SCRIPT

# Script sauvegarde
cat > /usr/local/bin/abetoile-location-backup << 'SCRIPT'
#!/bin/bash
BACKUP_DIR="/var/backups/abetoile-location"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

echo "💾 Sauvegarde Abetoile Location [$DATE]"

# Base de données
mongodump --uri="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/abetoile_location_prod" --out "$BACKUP_DIR/mongo-$DATE" --quiet
echo "✅ Base sauvegardée"

# Code source
tar -czf "$BACKUP_DIR/code-$DATE.tar.gz" /var/www/abetoile-location --exclude="*/node_modules" --exclude="*/venv" 2>/dev/null
echo "✅ Code sauvegardé"

# Nettoyage (7 jours)
find "$BACKUP_DIR" -name "mongo-*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
find "$BACKUP_DIR" -name "code-*.tar.gz" -mtime +7 -delete 2>/dev/null || true

echo "📁 Sauvegardes: $(ls -1 $BACKUP_DIR | wc -l) fichiers"
SCRIPT

chmod +x /usr/local/bin/abetoile-location-restart
chmod +x /usr/local/bin/abetoile-location-logs
chmod +x /usr/local/bin/abetoile-location-backup

log_success "Scripts de gestion créés"

# =============================================================================
# FINALISATION
# =============================================================================
log_info "🔧 Finalisation..."

# Recharger systemd
systemctl daemon-reload

# Créer logs
mkdir -p /var/log/abetoile-location
touch /var/log/abetoile-location/app.log
chown -R www-data:www-data /var/log/abetoile-location

# =============================================================================
# RAPPORT FINAL
# =============================================================================
clear
echo -e "${GREEN}"
echo "================================================================================"
echo "🎉 INSTALLATION TERMINÉE - SERVEUR MULTI-SITES"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}🖥️ CONFIGURATION SERVEUR:${NC}"
echo "   • Type: Serveur multi-sites"
echo "   • OS: Ubuntu $UBUNTU_VERSION ($UBUNTU_CODENAME)"
echo "   • Python: $PYTHON_VERSION (Ubuntu 25.04+ compatible)"
echo "   • Node.js: $NODE_VERSION"
echo "   • Yarn: $YARN_VERSION"
echo ""

echo -e "${BLUE}🌐 SITE ABETOILE LOCATION:${NC}"
echo "   • Domaine: $DOMAIN"
echo "   • Port Backend: $BACKEND_PORT (local)"
echo "   • Base de données: $DB_NAME"
echo "   • Répertoire: $APP_DIR"
echo "   • Service: $SERVICE_NAME"
echo ""

echo -e "${BLUE}📊 STATUT SERVICES:${NC}"
echo "   • MongoDB: $(systemctl is-active mongod)"
echo "   • Nginx: $(systemctl is-active nginx)"
echo "   • UFW: $(systemctl is-active ufw)"
echo ""

echo -e "${YELLOW}📋 PROCHAINES ÉTAPES:${NC}"
echo ""
echo -e "${RED}1. DÉPLOYER LE CODE:${NC}"
echo "   curl -sSL https://raw.githubusercontent.com/redademechety-ux/abetoile-location/main/deploy.sh | sudo bash"
echo ""
echo -e "${RED}2. CONFIGURER SSL:${NC}"
echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""

echo -e "${BLUE}🔧 COMMANDES GESTION:${NC}"
echo "   • abetoile-location-restart (redémarrage)"
echo "   • abetoile-location-logs (voir logs)"  
echo "   • abetoile-location-backup (sauvegarde)"
echo ""

echo -e "${GREEN}✅ INSTALLATION RÉUSSIE POUR SERVEUR MULTI-SITES!${NC}"
echo -e "${BLUE}🔗 Futur accès: https://$DOMAIN${NC}"
echo ""

log_success "Prêt pour le déploiement du code!"