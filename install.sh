#!/bin/bash

# =============================================================================
# 🚀 SCRIPT D'INSTALLATION AUTOMATIQUE - Abetoile Location Management
# =============================================================================
# Domaine: abetoile-location.fr / www.abetoile-location.fr
# Port Backend: 8001
# Version: SANS PPA DEADSNAKES (Compatible Ubuntu récent)
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

# Détecter la version Ubuntu
UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "unknown")
UBUNTU_CODENAME=$(lsb_release -cs 2>/dev/null || echo "unknown")

log_info "Système détecté: Ubuntu $UBUNTU_VERSION ($UBUNTU_CODENAME)"

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
apt install -y curl wget git nano htop unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release build-essential

log_success "Système mis à jour"

# =============================================================================
# ÉTAPE 3: INSTALLATION PYTHON (MÉTHODE DIRECTE - SANS PPA)
# =============================================================================
log_info "🐍 Installation de Python (méthode directe)..."

# JAMAIS utiliser le PPA deadsnakes - Installation directe depuis les repos Ubuntu
log_info "Installation de Python depuis les repositories officiels Ubuntu..."

# Installer Python disponible dans la distribution
apt install -y python3 python3-pip python3-venv python3-dev python3-distutils

# Détecter la version Python installée
PYTHON_VERSION=$(python3 --version 2>&1)
PYTHON_CMD="python3"

log_success "$PYTHON_VERSION installé avec succès (méthode officielle)"

# Vérifier que Python 3.8+ est disponible (minimum pour FastAPI)
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [[ "$PYTHON_MAJOR" -ge "3" ]] && [[ "$PYTHON_MINOR" -ge "8" ]]; then
    log_success "Version Python compatible: $PYTHON_MAJOR.$PYTHON_MINOR"
else
    log_error "Python 3.8+ requis, trouvé: $PYTHON_MAJOR.$PYTHON_MINOR"
    exit 1
fi

# Créer les liens symboliques
ln -sf /usr/bin/python3 /usr/bin/python

# S'assurer que pip est installé et à jour
python3 -m pip install --upgrade pip

log_success "Python configuré avec pip mis à jour"

# =============================================================================
# ÉTAPE 4: INSTALLATION NODE.JS ET YARN (MÉTHODE MISE À JOUR)
# =============================================================================
log_info "📦 Installation de Node.js et Yarn..."

# Node.js 18.x LTS - Méthode officielle
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Yarn - Méthode GPG moderne
curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor | tee /usr/share/keyrings/yarn.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/yarn.gpg] https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
apt update -y
apt install -y yarn

# Vérifier les installations
NODE_VERSION=$(node --version 2>/dev/null || echo "N/A")
YARN_VERSION=$(yarn --version 2>/dev/null || echo "N/A")

log_success "Node.js $NODE_VERSION et Yarn $YARN_VERSION installés"

# =============================================================================
# ÉTAPE 5: INSTALLATION MONGODB (MÉTHODE ROBUSTE)
# =============================================================================
log_info "🗄️ Installation de MongoDB..."

# Nettoyer d'éventuelles installations précédentes
rm -f /usr/share/keyrings/mongodb-server-*.gpg 2>/dev/null || true
rm -f /etc/apt/sources.list.d/mongodb-org-*.list 2>/dev/null || true

# Méthode GPG moderne pour MongoDB
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg

# Utiliser le repo Ubuntu approprié selon la version
case "$UBUNTU_CODENAME" in
    "noble"|"plucky"|"oracular")
        # Ubuntu 24.04+ utilise le repo jammy (le plus récent supporté)
        MONGO_REPO="ubuntu jammy/mongodb-org/7.0"
        log_info "Ubuntu récent détecté, utilisation du repo MongoDB jammy"
        ;;
    "jammy")
        MONGO_REPO="ubuntu jammy/mongodb-org/7.0"
        ;;
    "focal")
        MONGO_REPO="ubuntu focal/mongodb-org/7.0"
        ;;
    *)
        # Fallback vers jammy pour toutes les versions récentes
        MONGO_REPO="ubuntu jammy/mongodb-org/7.0"
        log_warning "Version Ubuntu non reconnue, utilisation du repo jammy"
        ;;
esac

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/$MONGO_REPO multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Installation MongoDB
apt update -y
apt install -y mongodb-org

# Configuration et démarrage
systemctl start mongod
systemctl enable mongod

# Attendre que MongoDB soit prêt
log_info "Attente du démarrage de MongoDB..."
sleep 10

# Vérifier que MongoDB fonctionne
if systemctl is-active --quiet mongod; then
    MONGO_VERSION=$(mongod --version 2>/dev/null | grep "db version" | head -1 || echo "MongoDB 7.0")
    log_success "MongoDB installé et fonctionnel: $MONGO_VERSION"
else
    log_error "Problème avec MongoDB"
    systemctl status mongod --no-pager
    exit 1
fi

# =============================================================================
# ÉTAPE 6: INSTALLATION NGINX
# =============================================================================
log_info "🌐 Installation de Nginx..."

apt install -y nginx
systemctl start nginx
systemctl enable nginx

if systemctl is-active --quiet nginx; then
    NGINX_VERSION=$(nginx -v 2>&1 | cut -d' ' -f3 || echo "nginx")
    log_success "Nginx installé: $NGINX_VERSION"
else
    log_error "Problème avec Nginx"
    exit 1
fi

# =============================================================================
# ÉTAPE 7: CONFIGURATION DU FIREWALL
# =============================================================================
log_info "🔥 Configuration du firewall..."

apt install -y ufw

# Configuration UFW sécurisée
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Autoriser les services nécessaires
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow $BACKEND_PORT/tcp

# Activer UFW
ufw --force enable

log_success "Firewall configuré et actif"

# =============================================================================
# ÉTAPE 8: CRÉATION DES RÉPERTOIRES ET UTILISATEURS
# =============================================================================
log_info "📁 Création des répertoires et utilisateur..."

# Créer l'utilisateur www-data s'il n'existe pas
if ! id "www-data" &>/dev/null; then
    useradd -r -s /bin/false www-data
fi

# Créer la structure de répertoires
mkdir -p $APP_DIR/backend
mkdir -p $APP_DIR/frontend
mkdir -p /var/log/abetoile-location
mkdir -p /var/backups/abetoile-location

# Permissions appropriées
chown -R www-data:www-data $APP_DIR
chown -R www-data:www-data /var/log/abetoile-location
chmod -R 755 $APP_DIR

log_success "Répertoires créés avec les bonnes permissions"

# =============================================================================
# ÉTAPE 9: CONFIGURATION MONGODB SÉCURISÉE
# =============================================================================
log_info "🗄️ Configuration sécurisée de MongoDB..."

# Attendre que MongoDB soit complètement opérationnel
sleep 5

# Créer l'utilisateur de base de données
log_info "Création de l'utilisateur de base de données..."

# Commande MongoDB pour créer l'utilisateur
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
  print('Utilisateur créé avec succès');
} catch (e) {
  if (e.code === 11000) {
    print('Utilisateur existe déjà');
  } else {
    print('Erreur: ' + e);
  }
}
" --quiet

# Configuration sécurisée MongoDB avec authentification
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

operationProfiling:
  slowOpThresholdMs: 100
EOF

# Redémarrer MongoDB avec la nouvelle configuration
systemctl restart mongod
sleep 5

if systemctl is-active --quiet mongod; then
    log_success "MongoDB configuré avec authentification"
else
    log_error "Problème avec la configuration MongoDB"
    systemctl status mongod --no-pager
    exit 1
fi

# =============================================================================
# ÉTAPE 10: CRÉATION DES FICHIERS DE CONFIGURATION
# =============================================================================
log_info "⚙️ Création des fichiers de configuration..."

# Générer une clé secrète forte
SECRET_KEY=$(openssl rand -hex 32)

# Configuration Backend (.env)
cat > $APP_DIR/backend/.env << EOF
MONGO_URL="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/$DB_NAME"
DB_NAME="$DB_NAME"
CORS_ORIGINS="https://$DOMAIN,https://www.$DOMAIN,http://localhost:3000"
SECRET_KEY="$SECRET_KEY"
EMERGENT_LLM_KEY=sk-emergent-c68C3249e6154EcE22
EOF

# Configuration Frontend (.env)
cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF

# Service systemd pour le backend
cat > /etc/systemd/system/abetoile-location-backend.service << EOF
[Unit]
Description=Abetoile Location Backend FastAPI Application
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
ExecStart=$APP_DIR/backend/venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port $BACKEND_PORT --workers 1
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

# Protéger les fichiers de configuration
chmod 600 $APP_DIR/backend/.env
chmod 600 $APP_DIR/frontend/.env
chown www-data:www-data $APP_DIR/backend/.env
chown www-data:www-data $APP_DIR/frontend/.env

log_success "Fichiers de configuration créés et sécurisés"

# =============================================================================
# ÉTAPE 11: CONFIGURATION NGINX MULTI-SITES
# =============================================================================
log_info "🌐 Configuration Nginx multi-sites..."

# Configuration Nginx optimisée pour Abetoile Location
cat > /etc/nginx/sites-available/abetoile-location << EOF
# Abetoile Location - Configuration Nginx
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirection HTTPS (activer après configuration SSL)
    # return 301 https://\$server_name\$request_uri;

    # Répertoire racine du frontend React
    root $APP_DIR/frontend/build;
    index index.html index.htm;

    # Logs dédiés
    access_log /var/log/nginx/abetoile-location.access.log combined;
    error_log /var/log/nginx/abetoile-location.error.log warn;

    # Sécurité - Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-Robots-Tag "noindex, nofollow" always;

    # Gestion des routes React SPA
    location / {
        try_files \$uri \$uri/ /index.html;
        
        # Cache pour les fichiers HTML
        location ~* \.html$ {
            expires 1h;
            add_header Cache-Control "public, must-revalidate";
        }
    }

    # Proxy pour l'API backend
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
        proxy_send_timeout 300s;
        
        # Pas de cache pour l'API
        expires off;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # Optimisation des fichiers statiques
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
        
        # Compression gzip
        gzip on;
        gzip_vary on;
        gzip_types text/css application/javascript image/svg+xml;
    }

    # Bloquer l'accès aux fichiers sensibles
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

    # Page d'erreur personnalisée
    error_page 404 /index.html;
    error_page 500 502 503 504 /index.html;
}
EOF

# Désactiver le site par défaut de Nginx
rm -f /etc/nginx/sites-enabled/default

# Activer le site Abetoile Location
ln -sf /etc/nginx/sites-available/abetoile-location /etc/nginx/sites-enabled/

# Tester la configuration Nginx
if nginx -t; then
    log_success "Configuration Nginx valide"
    systemctl reload nginx
    log_success "Nginx rechargé avec la nouvelle configuration"
else
    log_error "Erreur dans la configuration Nginx"
    exit 1
fi

# =============================================================================
# ÉTAPE 12: INSTALLATION SSL/CERTBOT
# =============================================================================
log_info "🔒 Installation de Certbot pour SSL..."

# Installer Certbot et le plugin Nginx
apt install -y certbot python3-certbot-nginx

log_success "Certbot installé"
log_warning "⚠️  Pour configurer SSL après installation complète:"
log_warning "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"

# =============================================================================
# ÉTAPE 13: SCRIPTS DE MAINTENANCE
# =============================================================================
log_info "🔧 Création des scripts de maintenance..."

# Script de redémarrage
cat > /usr/local/bin/abetoile-location-restart << 'EOF'
#!/bin/bash
echo "🔄 Redémarrage des services Abetoile Location..."

# Arrêter les services
systemctl stop abetoile-location-backend 2>/dev/null || true

# Redémarrer dans l'ordre
systemctl restart mongod
sleep 3
systemctl start abetoile-location-backend
sleep 2
systemctl reload nginx

# Vérifier les statuts
echo "📊 Statut des services:"
echo "   MongoDB: $(systemctl is-active mongod)"
echo "   Backend: $(systemctl is-active abetoile-location-backend)"
echo "   Nginx: $(systemctl is-active nginx)"

if systemctl is-active --quiet abetoile-location-backend; then
    echo "✅ Redémarrage réussi!"
else
    echo "❌ Problème avec le backend, vérifiez les logs:"
    echo "   journalctl -u abetoile-location-backend --lines=10"
fi
EOF

# Script de sauvegarde
cat > /usr/local/bin/abetoile-location-backup << EOF
#!/bin/bash
BACKUP_DIR="/var/backups/abetoile-location"
DATE=\$(date +%Y%m%d_%H%M%S)

echo "💾 Sauvegarde Abetoile Location [\$DATE]..."

# Créer le répertoire de sauvegarde
mkdir -p "\$BACKUP_DIR"

# Sauvegarde MongoDB
echo "📦 Sauvegarde de la base de données..."
if mongodump --uri="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/$DB_NAME" --out "\$BACKUP_DIR/mongo-\$DATE" --quiet; then
    echo "✅ Base de données sauvegardée"
else
    echo "❌ Erreur sauvegarde base de données"
fi

# Sauvegarde du code
echo "📁 Sauvegarde du code source..."
if tar -czf "\$BACKUP_DIR/code-\$DATE.tar.gz" "$APP_DIR" --exclude="*/node_modules" --exclude="*/venv" 2>/dev/null; then
    echo "✅ Code source sauvegardé"
else
    echo "❌ Erreur sauvegarde code"
fi

# Sauvegarde configuration Nginx
cp /etc/nginx/sites-available/abetoile-location "\$BACKUP_DIR/nginx-\$DATE.conf" 2>/dev/null || true

# Nettoyage automatique (garder 7 jours)
find "\$BACKUP_DIR" -name "mongo-*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
find "\$BACKUP_DIR" -name "code-*.tar.gz" -mtime +7 -delete 2>/dev/null || true
find "\$BACKUP_DIR" -name "nginx-*.conf" -mtime +7 -delete 2>/dev/null || true

echo "📋 Contenu des sauvegardes:"
ls -lah "\$BACKUP_DIR" | tail -10
echo "✅ Sauvegarde terminée: \$BACKUP_DIR"
EOF

# Script de logs
cat > /usr/local/bin/abetoile-location-logs << 'EOF'
#!/bin/bash
echo "📋 Logs Abetoile Location"
echo "========================="
echo ""
echo "🔍 Choisissez les logs à afficher:"
echo "1) Backend (FastAPI)"
echo "2) Nginx (accès)"
echo "3) Nginx (erreurs)"
echo "4) MongoDB"
echo "5) Système (UFW)"
echo ""
read -p "Votre choix (1-5): " choice

case $choice in
    1) echo "🐍 Logs Backend FastAPI:"; journalctl -u abetoile-location-backend -f ;;
    2) echo "🌐 Logs Nginx (accès):"; tail -f /var/log/nginx/abetoile-location.access.log ;;
    3) echo "🌐 Logs Nginx (erreurs):"; tail -f /var/log/nginx/abetoile-location.error.log ;;
    4) echo "🗄️ Logs MongoDB:"; tail -f /var/log/mongodb/mongod.log ;;
    5) echo "🔥 Logs UFW:"; tail -f /var/log/ufw.log ;;
    *) echo "❌ Choix invalide" ;;
esac
EOF

# Rendre tous les scripts exécutables
chmod +x /usr/local/bin/abetoile-location-restart
chmod +x /usr/local/bin/abetoile-location-backup  
chmod +x /usr/local/bin/abetoile-location-logs

log_success "Scripts de maintenance créés"

# =============================================================================
# ÉTAPE 14: TÂCHES CRON AUTOMATIQUES
# =============================================================================
log_info "⏰ Configuration des tâches automatiques..."

# Sauvegarde quotidienne à 2h du matin
cat > /etc/cron.d/abetoile-location-backup << 'EOF'
# Sauvegarde quotidienne Abetoile Location
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
0 2 * * * root /usr/local/bin/abetoile-location-backup >> /var/log/abetoile-location/backup.log 2>&1
EOF

# Nettoyage des logs hebdomadaire
cat > /etc/cron.d/abetoile-location-cleanup << 'EOF'
# Nettoyage hebdomadaire des logs
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
0 3 * * 0 root find /var/log/abetoile-location -name "*.log" -size +100M -delete 2>/dev/null || true
EOF

log_success "Tâches automatiques configurées"

# =============================================================================
# ÉTAPE 15: FINALISATION ET VÉRIFICATIONS
# =============================================================================
log_info "🔧 Finalisation de l'installation..."

# Recharger la configuration systemd
systemctl daemon-reload

# Créer les fichiers de logs
mkdir -p /var/log/abetoile-location
touch /var/log/abetoile-location/app.log
touch /var/log/abetoile-location/backup.log
touch /var/log/abetoile-location/access.log

# Permissions finales
chown -R www-data:www-data /var/log/abetoile-location
chmod -R 644 /var/log/abetoile-location/*.log
chmod 755 /var/log/abetoile-location

# Vérifications finales des services
log_info "🔍 Vérifications finales..."

# Test de connectivité MongoDB
if mongosh --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; then
    log_success "MongoDB répond correctement"
else
    log_warning "MongoDB pourrait avoir des problèmes"
fi

# Test Nginx
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200\|404"; then
    log_success "Nginx répond correctement"
else
    log_warning "Nginx pourrait avoir des problèmes"
fi

# =============================================================================
# RAPPORT FINAL
# =============================================================================
clear
echo -e "${GREEN}"
echo "================================================================================"
echo "🎉 INSTALLATION TERMINÉE - ABETOILE LOCATION MANAGEMENT"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}📋 CONFIGURATION SYSTÈME:${NC}"
echo "   • OS: Ubuntu $UBUNTU_VERSION ($UBUNTU_CODENAME)"
echo "   • Python: $PYTHON_VERSION"
echo "   • Node.js: $NODE_VERSION"
echo "   • Yarn: $YARN_VERSION" 
echo "   • MongoDB: Actif avec authentification"
echo "   • Nginx: $NGINX_VERSION"
echo ""

echo -e "${BLUE}🌐 CONFIGURATION APPLICATION:${NC}"
echo "   • Domaine: $DOMAIN / www.$DOMAIN"
echo "   • Backend: Port $BACKEND_PORT"
echo "   • Base de données: $DB_NAME"
echo "   • Répertoire: $APP_DIR"
echo "   • Logs: /var/log/abetoile-location/"
echo ""

echo -e "${BLUE}📊 STATUT DES SERVICES:${NC}"
echo "   • MongoDB: $(systemctl is-active mongod)"
echo "   • Nginx: $(systemctl is-active nginx)"
echo "   • UFW (Firewall): $(systemctl is-active ufw)"
echo ""

echo -e "${YELLOW}⚠️  PROCHAINES ÉTAPES OBLIGATOIRES:${NC}"
echo ""
echo -e "${RED}1. DÉPLOYER LE CODE SOURCE:${NC}"
echo "   curl -sSL https://raw.githubusercontent.com/redademechety-ux/abetoile-location/main/deploy.sh | sudo bash"
echo ""
echo -e "${RED}2. CONFIGURER SSL (après déploiement):${NC}"
echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""

echo -e "${BLUE}🔧 COMMANDES DE GESTION:${NC}"
echo "   • Redémarrer: abetoile-location-restart"
echo "   • Sauvegarder: abetoile-location-backup"
echo "   • Voir les logs: abetoile-location-logs"
echo "   • Statut backend: systemctl status abetoile-location-backend"
echo ""

echo -e "${GREEN}✅ INSTALLATION DE BASE RÉUSSIE!${NC}"
echo -e "${YELLOW}🔗 Accès futur: https://$DOMAIN${NC}"
echo ""

# Résumé des ports utilisés
echo -e "${BLUE}🔌 PORTS CONFIGURÉS:${NC}"
echo "   • 80 (HTTP) → Ouvert"
echo "   • 443 (HTTPS) → Ouvert" 
echo "   • $BACKEND_PORT (Backend) → Ouvert"
echo "   • 22 (SSH) → Ouvert"
echo "   • 27017 (MongoDB) → Local seulement"
echo ""

log_success "Installation terminée avec succès!"