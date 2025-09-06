#!/bin/bash

# =============================================================================
# 🚀 INSTALLATION CORRIGÉE - ABETOILE LOCATION (UBUNTU 25.04+ COMPATIBLE)
# =============================================================================
# Domaine: abetoile-location.fr
# Port Backend: 8001
# Compatible: Ubuntu 25.04+ (environnement Python externalement géré)
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
# PYTHON - MÉTHODE COMPATIBLE ENVIRONNEMENT EXTERNE UBUNTU 25.04+
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

# Test de création d'environnement virtuel
log_info "Test création environnement virtuel..."
TEMP_VENV="/tmp/test-venv-$$"
if python3 -m venv $TEMP_VENV; then
    rm -rf $TEMP_VENV
    log_success "Environnement virtuel Python fonctionnel"
else
    log_error "Problème avec la création d'environnement virtuel"
    exit 1
fi

# =============================================================================
# NODE.JS ET YARN (MÉTHODE ROBUSTE MULTI-SYSTÈME)
# =============================================================================
log_info "📦 Installation Node.js et Yarn..."

# Fonction pour nettoyer les installations Node.js précédentes
cleanup_nodejs() {
    log_info "Nettoyage des installations Node.js précédentes..."
    apt remove -y nodejs npm node yarn 2>/dev/null || true
    apt purge -y nodejs npm node yarn 2>/dev/null || true
    apt autoremove -y 2>/dev/null || true
    
    # Nettoyer les repositories et clés
    rm -f /etc/apt/sources.list.d/nodesource.list* 2>/dev/null || true
    rm -f /etc/apt/sources.list.d/yarn.list* 2>/dev/null || true
    rm -f /etc/apt/keyrings/nodesource.gpg* 2>/dev/null || true
    rm -f /usr/share/keyrings/yarn.gpg* 2>/dev/null || true
    
    apt update 2>/dev/null || true
    log_success "Nettoyage Node.js terminé"
}

# Installer Node.js avec méthodes multiples
install_nodejs() {
    if ! command -v node &> /dev/null; then
        cleanup_nodejs
        
        log_info "Tentative 1: Installation via NodeSource..."
        
        # Créer le répertoire pour les clés GPG
        mkdir -p /etc/apt/keyrings
        
        # Téléchargement et installation de la clé GPG NodeSource
        if curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg; then
            # Détecter la distribution Ubuntu pour compatibilité
            DISTRO_CODENAME="jammy"  # Utiliser jammy par défaut pour Ubuntu 25.04+
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                case $VERSION_CODENAME in
                    "focal"|"jammy"|"noble") 
                        DISTRO_CODENAME=$VERSION_CODENAME
                        ;;
                    *)
                        log_warning "Version Ubuntu $VERSION_CODENAME non supportée, utilisation de jammy"
                        DISTRO_CODENAME="jammy"
                        ;;
                esac
            fi
            
            NODE_MAJOR=18
            echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x $DISTRO_CODENAME main" > /etc/apt/sources.list.d/nodesource.list
            
            if apt update && apt install -y nodejs; then
                if node --version && npm --version; then
                    log_success "Node.js $(node --version) et npm $(npm --version) installés via NodeSource"
                    return 0
                fi
            fi
        fi
        
        log_warning "Méthode NodeSource échouée, tentative avec snap..."
        
        # Méthode 2: Snap (fallback)
        if ! command -v snap &> /dev/null; then
            apt install -y snapd
            systemctl enable snapd
            systemctl start snapd
            sleep 10
        fi
        
        if snap install node --classic; then
            # Créer des liens symboliques
            ln -sf /snap/bin/node /usr/local/bin/node
            ln -sf /snap/bin/npm /usr/local/bin/npm
            
            if node --version && npm --version; then
                log_success "Node.js $(node --version) installé via Snap"
                return 0
            fi
        fi
        
        log_error "Impossible d'installer Node.js"
        exit 1
    else
        log_success "Node.js déjà installé: $(node --version)"
    fi
}

# Installer Yarn
install_yarn() {
    if ! command -v yarn &> /dev/null; then
        log_info "Installation de Yarn..."
        
        # Méthode 1: Via npm (recommandée)
        if npm install -g yarn; then
            if yarn --version; then
                log_success "Yarn $(yarn --version) installé via npm"
                return 0
            fi
        fi
        
        log_warning "Yarn non installé, npm sera utilisé à la place"
    else
        log_success "Yarn déjà installé: $(yarn --version)"
    fi
}

install_nodejs
install_yarn

# =============================================================================
# MONGODB (MÉTHODE COMPATIBLE UBUNTU 25.04+)
# =============================================================================
log_info "🗄️ Installation MongoDB..."

# Nettoyer installations précédentes
systemctl stop mongod 2>/dev/null || true
apt remove -y mongodb-org* 2>/dev/null || true
rm -f /etc/apt/sources.list.d/mongodb-org-*.list 2>/dev/null || true
rm -f /usr/share/keyrings/mongodb-server-*.gpg 2>/dev/null || true

# MongoDB 7.0 avec keyring moderne
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg

# Utiliser repo jammy pour Ubuntu 25.04+ (compatibilité)
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
# CONFIGURATION APPLICATION (PRÊT POUR DÉPLOIEMENT)
# =============================================================================
log_info "⚙️ Configuration application (prêt pour déploiement du code)..."

# Clé secrète
SECRET_KEY=$(openssl rand -hex 32)

log_info "Structure prête pour le déploiement du code source"
log_warning "L'environnement virtuel Python sera créé lors du déploiement du code"

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

# Service systemd (sera activé après déploiement du code)
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

log_info "Service systemd créé (sera activé après déploiement du code)"

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
echo "🎉 INSTALLATION RÉUSSIE - UBUNTU 25.04+ COMPATIBLE (ENVIRONNEMENT EXTERNE)"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}✅ SYSTÈME:${NC}"
echo "   • Ubuntu: $UBUNTU_VERSION ($UBUNTU_CODENAME)"
echo "   • Python: $PYTHON_VERSION_FULL (avec venv)"
NODE_VERSION=$(node --version 2>/dev/null || echo "ERROR")
YARN_VERSION=$(yarn --version 2>/dev/null || echo "npm sera utilisé")
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
echo -e "${YELLOW}   OU copier manuellement le code dans $APP_DIR avec:${NC}"
echo "   • Répertoire frontend/ avec package.json"
echo "   • Répertoire backend/ avec requirements.txt"
echo "   • Puis installer les dépendances Python:"
echo "     cd $APP_DIR/backend && sudo -u www-data venv/bin/pip install -r requirements.txt"
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
echo -e "${YELLOW}⚠️  Environnement Python externe géré détecté et configuré${NC}"