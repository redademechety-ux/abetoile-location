#!/bin/bash

# =============================================================================
# 🚀 SCRIPT DE DÉPLOIEMENT - Abetoile Rental Management
# =============================================================================
# Ce script copie automatiquement le code source et démarre l'application
# =============================================================================

set -e

# Configuration
APP_DIR="/var/www/abetoile-rental"
DOMAIN="abetoile-rental.com"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Vérifier que l'installation de base est faite
if [ ! -d "$APP_DIR" ]; then
    log_error "Le répertoire $APP_DIR n'existe pas. Exécutez d'abord install.sh"
    exit 1
fi

log_info "🚀 Déploiement du code source Abetoile Rental..."

# =============================================================================
# COPIE DU CODE SOURCE
# =============================================================================
log_info "📁 Copie du code source..."

# Créer la structure si elle n'existe pas
mkdir -p $APP_DIR/backend
mkdir -p $APP_DIR/frontend/src
mkdir -p $APP_DIR/frontend/public

# Copier les fichiers depuis /app vers le répertoire de production
if [ -d "/app/backend" ]; then
    log_info "Copie du backend..."
    cp -r /app/backend/* $APP_DIR/backend/
    
    # S'assurer que le .env existe avec la bonne configuration
    cat > $APP_DIR/backend/.env << EOF
MONGO_URL="mongodb://abetoile_user:Ab3t0il3R3nt4l2024!@localhost:27017/abetoile_rental_prod"
DB_NAME="abetoile_rental_prod"
CORS_ORIGINS="https://$DOMAIN,https://www.$DOMAIN,http://localhost:3000"
SECRET_KEY="$(openssl rand -hex 32)"
EMERGENT_LLM_KEY=sk-emergent-c68C3249e6154EcE22
EOF
fi

if [ -d "/app/frontend" ]; then
    log_info "Copie du frontend..."
    cp -r /app/frontend/* $APP_DIR/frontend/
    
    # Configuration frontend
    cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF
fi

log_success "Code source copié"

# =============================================================================
# INSTALLATION DES DÉPENDANCES BACKEND
# =============================================================================
log_info "🐍 Installation des dépendances Python..."

cd $APP_DIR/backend

# Créer l'environnement virtuel
python3.11 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
pip install -r requirements.txt

log_success "Dépendances Python installées"

# =============================================================================
# INSTALLATION DES DÉPENDANCES FRONTEND
# =============================================================================
log_info "⚛️  Installation des dépendances Frontend..."

cd $APP_DIR/frontend

# Installer les dépendances
yarn install

# Builder pour production
yarn build

log_success "Frontend buildé pour production"

# =============================================================================
# CONFIGURATION DES PERMISSIONS
# =============================================================================
log_info "🔒 Configuration des permissions..."

chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod 600 $APP_DIR/backend/.env
chmod 600 $APP_DIR/frontend/.env

log_success "Permissions configurées"

# =============================================================================
# DÉMARRAGE DES SERVICES
# =============================================================================
log_info "🔄 Démarrage des services..."

# Recharger systemd
systemctl daemon-reload

# Démarrer le backend
systemctl enable abetoile-backend
systemctl start abetoile-backend

# Recharger Nginx
systemctl reload nginx

# Vérifier les statuts
sleep 3

if systemctl is-active --quiet abetoile-backend; then
    log_success "Backend démarré avec succès"
else
    log_error "Erreur de démarrage du backend"
    journalctl -u abetoile-backend --lines=20
    exit 1
fi

if systemctl is-active --quiet nginx; then
    log_success "Nginx fonctionne correctement"
else
    log_error "Erreur avec Nginx"
    exit 1
fi

# =============================================================================
# FINALISATION
# =============================================================================
clear
echo -e "${GREEN}"
echo "================================================================================"
echo "🎉 DÉPLOIEMENT TERMINÉ - ABETOILE RENTAL MANAGEMENT"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}📋 STATUT DES SERVICES:${NC}"
echo "   • Backend: $(systemctl is-active abetoile-backend)"
echo "   • Nginx: $(systemctl is-active nginx)"
echo "   • MongoDB: $(systemctl is-active mongod)"
echo ""

echo -e "${BLUE}🌐 ACCÈS À L'APPLICATION:${NC}"
echo "   • HTTP: http://$DOMAIN"
echo "   • HTTPS: https://$DOMAIN (après configuration SSL)"
echo "   • API: https://$DOMAIN/api/"
echo ""

echo -e "${YELLOW}🔒 CONFIGURATION SSL:${NC}"
echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""

echo -e "${BLUE}🔧 COMMANDES UTILES:${NC}"
echo "   • Logs backend: journalctl -u abetoile-backend -f"
echo "   • Logs nginx: tail -f /var/log/nginx/abetoile-rental.error.log"
echo "   • Redémarrer: abetoile-restart"
echo "   • Sauvegarder: abetoile-backup"
echo ""

echo -e "${GREEN}✅ Votre application Abetoile Rental est maintenant en ligne!${NC}"