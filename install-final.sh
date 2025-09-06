#!/bin/bash

# =============================================================================
# 🚀 INSTALLATION FINALE - ABETOILE LOCATION (UBUNTU 25.04 COMPATIBLE)
# =============================================================================
# Domaine: abetoile-location.fr
# Port Backend: 8001
# Compatible: Ubuntu 25.04+ (méthode moderne sans distutils)
# Type: Serveur multi-sites
# =============================================================================

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
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
# VÉRIFICATIONS
# =============================================================================
log_info "🔍 Vérifications Ubuntu 25.04..."

check_root

UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "unknown")
UBUNTU_CODENAME=$(lsb_release -cs 2>/dev/null || echo "unknown")

log_info "Système: Ubuntu $UBUNTU_VERSION ($UBUNTU_CODENAME)"

# =============================================================================
# NETTOYAGE PRÉLIMINAIRE
# =============================================================================
log_info "🧹 Nettoyage des résidus..."

# Supprimer PPA deadsnakes résiduel
rm -f /etc/apt/sources.list.d/deadsnakes*.list 2>/dev/null || true
add-apt-repository --remove ppa:deadsnakes/ppa -y 2>/dev/null || true

# Nettoyer APT
apt-get clean
rm -rf /var/lib/apt/lists/* 2>/dev/null || true

log_success "Nettoyage terminé"

# =============================================================================
# MISE À JOUR SYSTÈME
# =============================================================================
log_info "📦 Mise à jour système..."

export DEBIAN_FRONTEND=noninteractive
apt update -y
apt upgrade -y

# Packages de base Ubuntu 25.04
apt install -y \
    curl \
    wget \
    git \
    nano \
    htop \
    unzip \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

log_success "Système mis à jour"

# =============================================================================
# PYTHON - MÉTHODE MODERNE UBUNTU 25.04 (ENVIRONNEMENT EXTERNE GÉRÉ)
# =============================================================================
log_info "🐍 Installation Python (compatible environnement externe Ubuntu 25.04+)..."

# Détecter la version Python spécifique pour les packages venv
PYTHON_VERSION_FULL=$(python3 --version 2>&1)
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)" 2>/dev/null)
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)" 2>/dev/null)

log_info "Version Python détectée: $PYTHON_VERSION"

# Installation des packages Python de base
apt install -y python3 python3-pip python3-dev

# Installation des packages venv spécifiques à la version Ubuntu 25.04+
log_info "Installation des packages venv pour Python $PYTHON_VERSION..."
case $PYTHON_VERSION in
    "3.13")
        log_info "Installation des packages Python 3.13..."
        apt install -y python3.13-venv python3.13-dev
        ;;
    "3.12")
        log_info "Installation des packages Python 3.12..."
        apt install -y python3.12-venv python3.12-dev
        ;;
    "3.11")
        log_info "Installation des packages Python 3.11..."
        apt install -y python3.11-venv python3.11-dev
        ;;
    "3.10")
        log_info "Installation des packages Python 3.10..."
        apt install -y python3.10-venv python3.10-dev
        ;;
    *)
        log_info "Installation des packages Python génériques..."
        apt install -y python3-venv
        ;;
esac

# Vérifier que python3-venv fonctionne (contournement environnement externe)
if ! python3 -m venv --help >/dev/null 2>&1; then
    log_warning "python3-venv ne fonctionne pas, installation forcée de tous les packages venv..."
    apt install -y python3-venv python3.13-venv python3.12-venv python3.11-venv python3.10-venv 2>/dev/null || true
fi

log_success "$PYTHON_VERSION_FULL installé avec support venv"

# Vérifier version compatible
if [[ "$PYTHON_MAJOR" -ge "3" ]] && [[ "$PYTHON_MINOR" -ge "8" ]]; then
    log_success "Version Python compatible: $PYTHON_MAJOR.$PYTHON_MINOR"
else
    log_error "Python 3.8+ requis, trouvé: $PYTHON_MAJOR.$PYTHON_MINOR"
    exit 1
fi

# ⚠️ NE PAS mettre à jour pip au niveau système (environnement externe géré)
log_info "Environnement Python configuré (environnement externe géré détecté)"
log_info "Les dépendances Python seront installées dans un environnement virtuel"

# =============================================================================
# NODE.JS ET YARN
# =============================================================================
log_info "📦 Installation Node.js et Yarn..."

# Nettoyer anciennes installations
apt remove -y nodejs npm yarn 2>/dev/null || true
rm -f /etc/apt/sources.list.d/nodesource.list 2>/dev/null || true
rm -f /etc/apt/sources.list.d/yarn.list 2>/dev/null || true
rm -f /usr/share/keyrings/yarn.gpg 2>/dev/null || true

# Node.js 18.x LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Yarn avec keyring moderne
curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor -o /usr/share/keyrings/yarn.gpg
echo "deb [signed-by=/usr/share/keyrings/yarn.gpg] https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list
apt update -y
apt install -y yarn

# Vérifications
NODE_VERSION=$(node --version 2>/dev/null || echo "ERROR")
YARN_VERSION=$(yarn --version 2>/dev/null || echo "ERROR")

if [[ "$NODE_VERSION" == "ERROR" ]] || [[ "$YARN_VERSION" == "ERROR" ]]; then
    log_error "Erreur installation Node.js/Yarn"
    exit 1
fi

log_success "Node.js $NODE_VERSION et Yarn $YARN_VERSION installés"

# =============================================================================
# MONGODB
# =============================================================================
log_info "🗄️ Installation MongoDB..."

# Nettoyer installations précédentes
systemctl stop mongod 2>/dev/null || true
apt remove -y mongodb-org* 2>/dev/null || true
rm -f /etc/apt/sources.list.d/mongodb-org-*.list 2>/dev/null || true
rm -f /usr/share/keyrings/mongodb-server-*.gpg 2>/dev/null || true

# MongoDB 7.0 avec keyring moderne
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg

# Utiliser repo jammy pour Ubuntu 25.04
echo "deb [signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" > /etc/apt/sources.list.d/mongodb-org-7.0.list

apt update -y
apt install -y mongodb-org

# Démarrer MongoDB
systemctl start mongod
systemctl enable mongod

# Attendre et vérifier
sleep 10

if systemctl is-active --quiet mongod; then
    log_success "MongoDB installé et actif"
else
    log_error "Problème MongoDB"
    systemctl status mongod --no-pager
    exit 1
fi

# =============================================================================
# NGINX
# =============================================================================
log_info "🌐 Installation Nginx..."

apt install -y nginx
systemctl start nginx
systemctl enable nginx

if systemctl is-active --quiet nginx; then
    NGINX_VERSION=$(nginx -v 2>&1 | cut -d' ' -f3)
    log_success "Nginx $NGINX_VERSION installé"
else
    log_error "Problème Nginx"
    exit 1
fi

# =============================================================================
# FIREWALL (MULTI-SITES)
# =============================================================================
log_info "🔥 Configuration firewall..."

apt install -y ufw

# Configuration non-destructive pour serveur multi-sites
if ! ufw status | grep -q "Status: active"; then
    log_info "Première activation UFW"
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable
else
    log_info "UFW déjà actif, ajout des règles"
fi

# Ajouter port spécifique
ufw allow $BACKEND_PORT/tcp comment "Abetoile Location Backend"

log_success "Firewall configuré"

# =============================================================================
# STRUCTURE APPLICATION
# =============================================================================
log_info "📁 Création structure application..."

# Utilisateur www-data
if ! id "www-data" &>/dev/null; then
    useradd -r -s /bin/false www-data
fi

# Répertoires
mkdir -p $APP_DIR/backend
mkdir -p $APP_DIR/frontend
mkdir -p /var/log/abetoile-location
mkdir -p /var/backups/abetoile-location

# Permissions
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data /var/log/abetoile-location
chmod -R 755 $APP_DIR

log_success "Structure créée"

# =============================================================================
# CONFIGURATION MONGODB
# =============================================================================
log_info "🗄️ Configuration MongoDB..."

sleep 5

# Créer utilisateur base de données
mongosh --eval "
use $DB_NAME;
try {
  db.createUser({
    user: 'abetoile_user',
    pwd: 'Ab3t0il3L0c4t10n2024!',
    roles: [{ role: 'readWrite', db: '$DB_NAME' }]
  });
  print('✅ Utilisateur BD créé');
} catch (e) {
  if (e.code === 11000) {
    print('ℹ️ Utilisateur existe déjà');
  } else {
    print('❌ Erreur: ' + e);
  }
}
" --quiet

log_success "Base de données configurée"

# =============================================================================
# CONFIGURATION APPLICATION
# =============================================================================
log_info "⚙️ Configuration application..."

# Clé secrète
SECRET_KEY=$(openssl rand -hex 32)

# Backend .env
cat > $APP_DIR/backend/.env << EOF
MONGO_URL="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/$DB_NAME"
DB_NAME="$DB_NAME"
CORS_ORIGINS="https://$DOMAIN,https://www.$DOMAIN,http://localhost:3000"
SECRET_KEY="$SECRET_KEY"
EMERGENT_LLM_KEY=sk-emergent-c68C3249e6154EcE22
EOF

# Frontend .env
cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF

# Service systemd
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
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
ExecStart=$APP_DIR/backend/venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port $BACKEND_PORT
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Permissions
chmod 600 $APP_DIR/backend/.env
chmod 600 $APP_DIR/frontend/.env
chown www-data:www-data $APP_DIR/backend/.env
chown www-data:www-data $APP_DIR/frontend/.env

log_success "Configuration terminée"

# =============================================================================
# NGINX SITE
# =============================================================================
log_info "🌐 Configuration site Nginx..."

cat > /etc/nginx/sites-available/abetoile-location << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name abetoile-location.fr www.abetoile-location.fr;
    
    access_log /var/log/nginx/abetoile-location.access.log;
    error_log /var/log/nginx/abetoile-location.error.log;
    
    root /var/www/abetoile-location/frontend/build;
    index index.html;
    
    # Headers sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Routes React
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Fichiers statiques
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Sécurité
    location ~ /\. {
        deny all;
    }
}
EOF

# Activer site
ln -sf /etc/nginx/sites-available/abetoile-location /etc/nginx/sites-enabled/

# Test et reload
if nginx -t; then
    systemctl reload nginx
    log_success "Site Nginx configuré"
else
    log_error "Erreur configuration Nginx"
    exit 1
fi

# =============================================================================
# SSL/CERTBOT
# =============================================================================
log_info "🔒 Installation Certbot..."

apt install -y certbot python3-certbot-nginx

log_success "Certbot installé"

# =============================================================================
# SCRIPTS UTILITAIRES
# =============================================================================
log_info "🔧 Création scripts utilitaires..."

# Script restart
cat > /usr/local/bin/abetoile-restart << 'EOF'
#!/bin/bash
echo "🔄 Redémarrage Abetoile Location..."
systemctl restart abetoile-location-backend
systemctl reload nginx
echo "✅ Status: Backend=$(systemctl is-active abetoile-location-backend) Nginx=$(systemctl is-active nginx)"
EOF

# Script logs
cat > /usr/local/bin/abetoile-logs << 'EOF'
#!/bin/bash
echo "📋 Logs Abetoile Location"
echo "1) Backend  2) Nginx Access  3) Nginx Errors"
read -p "Choix: " c
case $c in
  1) journalctl -u abetoile-location-backend -f ;;
  2) tail -f /var/log/nginx/abetoile-location.access.log ;;
  3) tail -f /var/log/nginx/abetoile-location.error.log ;;
esac
EOF

chmod +x /usr/local/bin/abetoile-restart
chmod +x /usr/local/bin/abetoile-logs

log_success "Scripts créés"

# =============================================================================
# FINALISATION
# =============================================================================
systemctl daemon-reload

touch /var/log/abetoile-location/app.log
chown www-data:www-data /var/log/abetoile-location/app.log

# =============================================================================
# RAPPORT FINAL
# =============================================================================
clear
echo -e "${GREEN}"
echo "================================================================================"
echo "🎉 INSTALLATION RÉUSSIE - UBUNTU 25.04 COMPATIBLE"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}✅ SYSTÈME:${NC}"
echo "   • Ubuntu: $UBUNTU_VERSION ($UBUNTU_CODENAME)"
echo "   • Python: $PYTHON_VERSION"
echo "   • Node.js: $NODE_VERSION"
echo "   • Yarn: $YARN_VERSION"
echo ""

echo -e "${BLUE}🌐 APPLICATION:${NC}"
echo "   • Domaine: $DOMAIN"
echo "   • Port Backend: $BACKEND_PORT (local)"
echo "   • Service: $SERVICE_NAME"
echo "   • Base: $DB_NAME"
echo ""

echo -e "${BLUE}📊 SERVICES:${NC}"
echo "   • MongoDB: $(systemctl is-active mongod)"
echo "   • Nginx: $(systemctl is-active nginx)"
echo "   • UFW: $(systemctl is-active ufw)"
echo ""

echo -e "${YELLOW}📋 PROCHAINES ÉTAPES:${NC}"
echo ""
echo -e "${RED}1. DÉPLOYER LE CODE:${NC}"
echo "   curl -sSL https://raw.githubusercontent.com/redademechety-ux/abetoile-location/main/deploy.sh | sudo bash"
echo ""
echo -e "${RED}2. SSL:${NC}"
echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""

echo -e "${BLUE}🛠️ COMMANDES:${NC}"
echo "   • abetoile-restart"
echo "   • abetoile-logs"
echo ""

echo -e "${GREEN}✅ INSTALLATION TERMINÉE AVEC SUCCÈS!${NC}"
echo -e "${BLUE}🔗 Accès futur: https://$DOMAIN${NC}"