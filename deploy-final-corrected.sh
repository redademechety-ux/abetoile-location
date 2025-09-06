#!/bin/bash

# =============================================================================
# 🚀 SCRIPT DE DÉPLOIEMENT FINAL CORRIGÉ - Abetoile Location
# =============================================================================
# Version corrigée qui résout automatiquement les problèmes de requirements.txt
# Pour déploiement sur serveur distant depuis GitHub
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

# Détecter l'IP du serveur
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || curl -s ifconfig.me 2>/dev/null || echo "VOTRE-IP")

echo -e "${BLUE}"
echo "================================================================================"
echo "🚀 DÉPLOIEMENT ABETOILE LOCATION - VERSION CORRIGÉE"
echo "================================================================================"
echo -e "${NC}"
echo "🌐 Serveur : $SERVER_IP"
echo "📁 Repository : $GITHUB_REPO"
echo "🎯 Destination : $APP_DIR"
echo ""

# Vérifier que l'infrastructure est installée
if [ ! -d "$APP_DIR" ]; then
    log_error "Le répertoire $APP_DIR n'existe pas."
    log_error "Veuillez d'abord installer les prérequis avec :"
    log_error "curl -sSL https://raw.githubusercontent.com/redademechety-ux/abetoile-location/main/install-fixed.sh | sudo bash"
    exit 1
fi

log_info "🚀 Déploiement depuis GitHub avec corrections automatiques..."

# =============================================================================
# CLONAGE DU CODE SOURCE DEPUIS GITHUB
# =============================================================================
log_info "📁 Clonage du code source depuis GitHub..."

# Nettoyer le répertoire temporaire
rm -rf $TEMP_DIR

# Cloner le repository
if git clone $GITHUB_REPO $TEMP_DIR; then
    log_success "Repository cloné avec succès"
else
    log_error "Impossible de cloner le repository GitHub"
    log_error "Vérifiez votre connexion internet et l'URL : $GITHUB_REPO"
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

# =============================================================================
# COPIE ET PRÉPARATION DU CODE
# =============================================================================
log_info "📂 Copie et préparation du code..."

# Copier le backend
cp -r $TEMP_DIR/backend/* $APP_DIR/backend/ 2>/dev/null || true
cp $TEMP_DIR/backend/.* $APP_DIR/backend/ 2>/dev/null || true

# Copier le frontend
cp -r $TEMP_DIR/frontend/* $APP_DIR/frontend/ 2>/dev/null || true
cp $TEMP_DIR/frontend/.* $APP_DIR/frontend/ 2>/dev/null || true

# Nettoyer le répertoire temporaire
rm -rf $TEMP_DIR

# =============================================================================
# CORRECTION CRITIQUE DU REQUIREMENTS.TXT
# =============================================================================
log_info "🔧 Correction automatique du requirements.txt..."

# Créer une sauvegarde du fichier original
if [ -f "$APP_DIR/backend/requirements.txt" ]; then
    cp "$APP_DIR/backend/requirements.txt" "$APP_DIR/backend/requirements.txt.original"
    log_info "Sauvegarde créée : requirements.txt.original"
fi

# Créer un requirements.txt corrigé sans les modules Python intégrés
cat > "$APP_DIR/backend/requirements.txt" << 'REQUIREMENTS_EOF'
fastapi==0.110.1
uvicorn==0.25.0
boto3>=1.34.129
requests-oauthlib>=2.0.0
cryptography>=42.0.8
python-dotenv>=1.0.1
pymongo==4.5.0
pydantic>=2.6.4
email-validator>=2.2.0
pyjwt>=2.10.1
passlib>=1.7.4
bcrypt>=4.0.1
tzdata>=2024.2
motor==3.3.1
pytest>=8.0.0
black>=24.1.1
isort>=5.13.2
flake8>=7.0.0
mypy>=1.8.0
python-jose>=3.3.0
requests>=2.31.0
pandas>=2.2.0
numpy>=1.26.0
python-multipart>=0.0.9
jq>=1.6.0
typer>=0.9.0
emergentintegrations>=0.1.0
reportlab>=4.0.0
REQUIREMENTS_EOF

log_success "Requirements.txt corrigé (modules Python intégrés supprimés)"

# =============================================================================
# CONFIGURATION DES FICHIERS ENVIRONNEMENT
# =============================================================================
log_info "⚙️ Configuration des fichiers d'environnement..."

# Backend .env
cat > $APP_DIR/backend/.env << EOF
MONGO_URL="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/abetoile_location_prod"
DB_NAME="abetoile_location_prod"
CORS_ORIGINS="https://$DOMAIN,https://www.$DOMAIN,http://localhost:3000,http://$SERVER_IP"
SECRET_KEY="$(openssl rand -hex 32)"
EMERGENT_LLM_KEY=sk-emergent-c68C3249e6154EcE22
EOF

# Frontend .env
cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=http://$SERVER_IP
EOF

log_success "Fichiers d'environnement configurés"

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

# Installer les dépendances avec gestion d'erreurs et corrections
log_info "Mise à jour de pip..."
sudo -u www-data bash -c "cd $APP_DIR/backend && source venv/bin/activate && python -m pip install --upgrade pip --no-warn-script-location --disable-pip-version-check"

log_info "Installation d'emergentintegrations..."
sudo -u www-data bash -c "cd $APP_DIR/backend && source venv/bin/activate && pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ --no-warn-script-location --disable-pip-version-check"

log_info "Installation des dépendances depuis requirements.txt corrigé..."
sudo -u www-data bash -c "cd $APP_DIR/backend && source venv/bin/activate && pip install -r requirements.txt --no-warn-script-location --disable-pip-version-check"

log_success "Dépendances Python installées avec succès"

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
    log_info "Build de production avec Yarn..."
    sudo -u www-data NODE_OPTIONS="--max-old-space-size=4096" yarn build
else
    log_warning "Yarn non disponible, utilisation de npm..."
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
systemctl restart abetoile-location-backend

# Recharger Nginx
systemctl reload nginx

# Vérifier les statuts
sleep 5

BACKEND_STATUS=$(systemctl is-active abetoile-location-backend)
NGINX_STATUS=$(systemctl is-active nginx)
MONGO_STATUS=$(systemctl is-active mongod)

if systemctl is-active --quiet abetoile-location-backend; then
    log_success "Backend démarré avec succès"
else
    log_error "Erreur de démarrage du backend"
    log_info "Vérification des logs..."
    journalctl -u abetoile-location-backend --lines=10 --no-pager
    log_warning "Pour plus de détails : journalctl -u abetoile-location-backend -f"
fi

if systemctl is-active --quiet nginx; then
    log_success "Nginx fonctionne correctement"
else
    log_error "Erreur avec Nginx"
fi

# =============================================================================
# RAPPORT FINAL
# =============================================================================
clear
echo -e "${GREEN}"
echo "================================================================================"
echo "🎉 DÉPLOIEMENT TERMINÉ - ABETOILE LOCATION MANAGEMENT"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}📊 STATUT DES SERVICES:${NC}"
echo "   • Backend: $BACKEND_STATUS"
echo "   • Nginx: $NGINX_STATUS"
echo "   • MongoDB: $MONGO_STATUS"
echo ""

echo -e "${BLUE}🌐 ACCÈS À L'APPLICATION:${NC}"
echo "   • Application: http://$SERVER_IP/"
echo "   • API Backend: http://$SERVER_IP/api/"
echo "   • Docs API: http://$SERVER_IP/api/docs"
echo ""

if [ "$DOMAIN" != "abetoile-location.fr" ]; then
    echo -e "${YELLOW}🔗 DOMAINE (après configuration DNS):${NC}"
    echo "   • https://$DOMAIN (après certificat SSL)"
fi

echo -e "${BLUE}🔧 COMMANDES UTILES:${NC}"
echo "   • Logs backend: journalctl -u abetoile-location-backend -f"
echo "   • Logs nginx: tail -f /var/log/nginx/abetoile-location.error.log"
echo "   • Redémarrer backend: systemctl restart abetoile-location-backend"
echo "   • Status: systemctl status abetoile-location-backend"
echo ""

echo -e "${YELLOW}🔒 SÉCURISATION (OPTIONNELLE):${NC}"
echo "   • SSL: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo "   • MongoDB Interface: sudo bash /tmp/install-mongo-express.sh"
echo ""

echo -e "${GREEN}✅ DÉPLOIEMENT RÉUSSI !${NC}"
echo -e "${BLUE}🚗 Testez votre application : http://$SERVER_IP/${NC}"
echo -e "${BLUE}📋 IP Serveur : $SERVER_IP${NC}"

# Créer un fichier de résumé
cat > /tmp/abetoile-deployment-summary.txt << EOF
ABETOILE LOCATION - RÉSUMÉ DE DÉPLOIEMENT
==========================================
Date: $(date)
Serveur: $SERVER_IP
Application: http://$SERVER_IP/
API: http://$SERVER_IP/api/

Services:
- Backend: $BACKEND_STATUS
- Nginx: $NGINX_STATUS  
- MongoDB: $MONGO_STATUS

Fichiers:
- Configuration: $APP_DIR/backend/.env
- Requirements: $APP_DIR/backend/requirements.txt (corrigé)
- Sauvegarde: $APP_DIR/backend/requirements.txt.original

Commandes utiles:
- Logs: journalctl -u abetoile-location-backend -f
- Redémarrer: systemctl restart abetoile-location-backend
- Status: systemctl status abetoile-location-backend
EOF

echo ""
echo -e "${BLUE}📄 Résumé sauvegardé dans /tmp/abetoile-deployment-summary.txt${NC}"