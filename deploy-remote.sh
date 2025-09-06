#!/bin/bash

# =============================================================================
# 🚀 DÉPLOIEMENT DISTANT - Abetoile Location (depuis GitHub)
# =============================================================================
# Ce script clone le code depuis GitHub et installe l'application
# Pour serveur de production distant
# =============================================================================

set -e

# Configuration
APP_DIR="/var/www/abetoile-location"
DOMAIN="abetoile-location.fr"
GITHUB_REPO="https://github.com/redademechety-ux/abetoile-location.git"
TEMP_DIR="/tmp/abetoile-deploy-$$"

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

# Vérifier que l'infrastructure est installée
if [ ! -d "$APP_DIR" ]; then
    log_error "Le répertoire $APP_DIR n'existe pas."
    log_error "Veuillez d'abord installer les prérequis avec install-fixed.sh"
    exit 1
fi

log_info "🚀 Déploiement distant Abetoile Location depuis GitHub..."
log_info "Repository: $GITHUB_REPO"

# =============================================================================
# CLONAGE DU CODE SOURCE DEPUIS GITHUB
# =============================================================================
log_info "📁 Clonage du code source depuis GitHub..."

# Nettoyer le répertoire temporaire
rm -rf $TEMP_DIR

# Cloner le repository
log_info "Clone depuis: $GITHUB_REPO"
if git clone $GITHUB_REPO $TEMP_DIR; then
    log_success "Repository cloné avec succès"
else
    log_error "Impossible de cloner le repository GitHub"
    log_info "Vérifiez que l'URL est correcte : $GITHUB_REPO"
    exit 1
fi

# Vérifier que les répertoires essentiels existent
if [ ! -d "$TEMP_DIR/backend" ] || [ ! -d "$TEMP_DIR/frontend" ]; then
    log_error "Structure du repository incorrecte"
    log_info "Contenu du repository cloné :"
    ls -la $TEMP_DIR/
    rm -rf $TEMP_DIR
    exit 1
fi

log_success "Structure du code source vérifiée"

# =============================================================================
# COPIE DU CODE VERS LE RÉPERTOIRE DE PRODUCTION
# =============================================================================
log_info "📂 Copie du code vers le répertoire de production..."

# Copier le backend
log_info "Copie du backend..."
cp -r $TEMP_DIR/backend/* $APP_DIR/backend/ 2>/dev/null || true
cp $TEMP_DIR/backend/.* $APP_DIR/backend/ 2>/dev/null || true

# Copier le frontend
log_info "Copie du frontend..."
cp -r $TEMP_DIR/frontend/* $APP_DIR/frontend/ 2>/dev/null || true
cp $TEMP_DIR/frontend/.* $APP_DIR/frontend/ 2>/dev/null || true

# Nettoyer le répertoire temporaire
rm -rf $TEMP_DIR

log_success "Code source copié"

# =============================================================================
# CONFIGURATION DES FICHIERS ENVIRONNEMENT
# =============================================================================
log_info "⚙️ Configuration des fichiers d'environnement..."

# Backend .env
cat > $APP_DIR/backend/.env << EOF
MONGO_URL="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/abetoile_location_prod"
DB_NAME="abetoile_location_prod"
CORS_ORIGINS="https://$DOMAIN,https://www.$DOMAIN,http://localhost:3000"
SECRET_KEY="$(openssl rand -hex 32)"
EMERGENT_LLM_KEY=sk-emergent-c68C3249e6154EcE22
EOF

# Frontend .env
cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF

log_success "Fichiers d'environnement configurés"

# =============================================================================
# VÉRIFICATION DES FICHIERS CRITIQUES
# =============================================================================
log_info "🔍 Vérification des fichiers critiques..."

if [ ! -f "$APP_DIR/backend/requirements.txt" ]; then
    log_error "Fichier requirements.txt manquant!"
    log_info "Contenu backend:"
    ls -la $APP_DIR/backend/
    exit 1
fi

if [ ! -f "$APP_DIR/frontend/package.json" ]; then
    log_error "Fichier package.json manquant!"
    log_info "Contenu frontend:"
    ls -la $APP_DIR/frontend/
    exit 1
fi

if [ ! -f "$APP_DIR/backend/server.py" ]; then
    log_error "Fichier server.py manquant!"
    exit 1
fi

log_success "Fichiers critiques présents"

# =============================================================================
# MISE À JOUR DU BRANDING
# =============================================================================
log_info "🎨 Mise à jour du branding pour Abetoile Location..."

# Mettre à jour le titre dans l'App.js
if [ -f "$APP_DIR/frontend/src/App.js" ]; then
    sed -i 's/AutoPro Rental/Abetoile Location/g' $APP_DIR/frontend/src/App.js
fi

# Mettre à jour le server.py
if [ -f "$APP_DIR/backend/server.py" ]; then
    sed -i 's/AutoPro Rental Management/Abetoile Location Management/g' $APP_DIR/backend/server.py
    sed -i 's/autopro_rental/abetoile_location/g' $APP_DIR/backend/server.py
    sed -i 's/company_name: str = "AutoPro Rental"/company_name: str = "Abetoile Location"/g' $APP_DIR/backend/server.py
fi

log_success "Branding mis à jour"

# =============================================================================
# INSTALLATION DES DÉPENDANCES BACKEND
# =============================================================================
log_info "🐍 Installation des dépendances Python..."

cd $APP_DIR/backend

# Créer l'environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    log_info "Création de l'environnement virtuel Python..."
    sudo -u www-data python3 -m venv venv
    
    if [[ ! -f "$APP_DIR/backend/venv/bin/activate" ]]; then
        log_error "Échec création environnement virtuel"
        exit 1
    fi
    log_success "Environnement virtuel créé"
fi

# Installer les dépendances avec gestion d'erreurs
log_info "Mise à jour de pip..."
sudo -u www-data bash -c "cd $APP_DIR/backend && source venv/bin/activate && python -m pip install --upgrade pip --no-warn-script-location --disable-pip-version-check"

log_info "Installation d'emergentintegrations..."
sudo -u www-data bash -c "cd $APP_DIR/backend && source venv/bin/activate && pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ --no-warn-script-location --disable-pip-version-check"

log_info "Installation des dépendances depuis requirements.txt..."
sudo -u www-data bash -c "cd $APP_DIR/backend && source venv/bin/activate && pip install -r requirements.txt --no-warn-script-location --disable-pip-version-check"

log_success "Dépendances Python installées"

# =============================================================================
# INSTALLATION DES DÉPENDANCES FRONTEND
# =============================================================================
log_info "⚛️  Installation des dépendances Frontend..."

cd $APP_DIR/frontend

# Installer les dépendances avec gestion des erreurs
if command -v yarn &> /dev/null; then
    log_info "Installation avec Yarn..."
    sudo -u www-data yarn install --frozen-lockfile --network-timeout 600000
    # Builder pour production
    log_info "Build de production..."
    sudo -u www-data NODE_OPTIONS="--max-old-space-size=4096" yarn build
else
    log_info "Yarn non disponible, utilisation de npm..."
    sudo -u www-data npm install
    sudo -u www-data npm run build
fi

# Vérifier que le build existe
if [[ ! -d "$APP_DIR/frontend/build" ]]; then
    log_error "Le build du frontend a échoué"
    exit 1
fi

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
systemctl enable abetoile-location-backend
systemctl start abetoile-location-backend

# Recharger Nginx
systemctl reload nginx

# Vérifier les statuts
sleep 5

if systemctl is-active --quiet abetoile-location-backend; then
    log_success "Backend démarré avec succès"
else
    log_error "Erreur de démarrage du backend"
    log_info "Logs du backend :"
    journalctl -u abetoile-location-backend --lines=10 --no-pager
    log_warning "Pour plus de détails : journalctl -u abetoile-location-backend -f"
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
echo "🎉 DÉPLOIEMENT DISTANT TERMINÉ - ABETOILE LOCATION"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}📋 STATUT DES SERVICES:${NC}"
echo "   • Backend: $(systemctl is-active abetoile-location-backend)"
echo "   • Nginx: $(systemctl is-active nginx)"
echo "   • MongoDB: $(systemctl is-active mongod)"
echo ""

echo -e "${BLUE}🌐 ACCÈS À L'APPLICATION:${NC}"
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || curl -s ifconfig.me 2>/dev/null || echo "VOTRE-IP")
echo "   • HTTP: http://$SERVER_IP/"
echo "   • API: http://$SERVER_IP/api/"
if [ "$DOMAIN" != "abetoile-location.fr" ]; then
    echo "   • Domaine (après DNS): https://$DOMAIN"
fi
echo ""

echo -e "${YELLOW}🔒 CONFIGURATION SSL (RECOMMANDÉE):${NC}"
echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""

echo -e "${BLUE}🔧 COMMANDES UTILES:${NC}"
echo "   • Logs backend: journalctl -u abetoile-location-backend -f"
echo "   • Logs nginx: tail -f /var/log/nginx/abetoile-location.error.log"
echo "   • Redémarrer backend: systemctl restart abetoile-location-backend"
echo "   • Status complet: systemctl status abetoile-location-backend"
echo ""

echo -e "${GREEN}✅ Votre application Abetoile Location est maintenant en ligne!${NC}"
echo -e "${BLUE}🚗 Testez l'application sur : http://$SERVER_IP/${NC}"
echo -e "${BLUE}🌐 IP du serveur : $SERVER_IP${NC}"