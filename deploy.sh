#!/bin/bash

# =============================================================================
# 🚀 SCRIPT DE DÉPLOIEMENT - Abetoile Location Management
# =============================================================================
# Ce script copie automatiquement le code source et démarre l'application
# =============================================================================

set -e

# Configuration
APP_DIR="/var/www/abetoile-location"
DOMAIN="abetoile-location.fr"

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

log_info "🚀 Déploiement du code source Abetoile Location..."

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
MONGO_URL="mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/abetoile_location_prod"
DB_NAME="abetoile_location_prod"
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
# MISE À JOUR DU TITRE DE L'APPLICATION
# =============================================================================
log_info "🎨 Mise à jour du branding pour Abetoile Location..."

# Mettre à jour le titre dans l'App.js
if [ -f "$APP_DIR/frontend/src/App.js" ]; then
    sed -i 's/AutoPro Rental/Abetoile Location/g' $APP_DIR/frontend/src/App.js
fi

# Mettre à jour la navigation
if [ -f "$APP_DIR/frontend/src/components/Navigation.js" ]; then
    sed -i 's/AutoPro Rental/Abetoile Location/g' $APP_DIR/frontend/src/components/Navigation.js
fi

# Mettre à jour le server.py
if [ -f "$APP_DIR/backend/server.py" ]; then
    sed -i 's/AutoPro Rental Management/Abetoile Location Management/g' $APP_DIR/backend/server.py
    sed -i 's/autopro_rental/abetoile_location/g' $APP_DIR/backend/server.py
fi

# Mettre à jour les paramètres par défaut
if [ -f "$APP_DIR/backend/server.py" ]; then
    sed -i 's/company_name: str = "AutoPro Rental"/company_name: str = "Abetoile Location"/g' $APP_DIR/backend/server.py
fi

log_success "Branding mis à jour pour Abetoile Location"

# =============================================================================
# INSTALLATION DES DÉPENDANCES BACKEND (ENVIRONNEMENT VIRTUEL)
# =============================================================================
log_info "🐍 Installation des dépendances Python dans l'environnement virtuel..."

cd $APP_DIR/backend

# Utiliser l'environnement virtuel créé par install-final.sh
if [ ! -d "venv" ]; then
    log_info "Création de l'environnement virtuel Python..."
    sudo -u www-data python3 -m venv venv
fi

# Activer et installer les dépendances dans l'environnement virtuel
log_info "Installation des dépendances dans l'environnement virtuel..."
sudo -u www-data bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u www-data bash -c "source venv/bin/activate && pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/"
sudo -u www-data bash -c "source venv/bin/activate && pip install -r requirements.txt"

log_success "Dépendances Python installées dans l'environnement virtuel"

# =============================================================================
# INSTALLATION DES DÉPENDANCES FRONTEND
# =============================================================================
log_info "⚛️  Installation des dépendances Frontend..."

cd $APP_DIR/frontend

# Mettre à jour le package.json avec le bon nom
cat > package.json << 'EOF'
{
  "name": "abetoile-location-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "@hookform/resolvers": "^5.0.1",
    "@radix-ui/react-accordion": "^1.2.8",
    "@radix-ui/react-alert-dialog": "^1.1.11",
    "@radix-ui/react-aspect-ratio": "^1.1.4",
    "@radix-ui/react-avatar": "^1.1.7",
    "@radix-ui/react-checkbox": "^1.2.3",
    "@radix-ui/react-collapsible": "^1.1.8",
    "@radix-ui/react-context-menu": "^2.2.12",
    "@radix-ui/react-dialog": "^1.1.11",
    "@radix-ui/react-dropdown-menu": "^2.1.12",
    "@radix-ui/react-hover-card": "^1.1.11",
    "@radix-ui/react-label": "^2.1.4",
    "@radix-ui/react-menubar": "^1.1.12",
    "@radix-ui/react-navigation-menu": "^1.2.10",
    "@radix-ui/react-popover": "^1.1.11",
    "@radix-ui/react-progress": "^1.1.4",
    "@radix-ui/react-radio-group": "^1.3.4",
    "@radix-ui/react-scroll-area": "^1.2.6",
    "@radix-ui/react-select": "^2.2.2",
    "@radix-ui/react-separator": "^1.1.4",
    "@radix-ui/react-slider": "^1.3.2",
    "@radix-ui/react-slot": "^1.2.0",
    "@radix-ui/react-switch": "^1.2.2",
    "@radix-ui/react-tabs": "^1.1.9",
    "@radix-ui/react-toast": "^1.2.11",
    "@radix-ui/react-toggle": "^1.1.6",
    "@radix-ui/react-toggle-group": "^1.1.7",
    "@radix-ui/react-tooltip": "^1.2.4",
    "axios": "^1.8.4",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "cmdk": "^1.1.1",
    "cra-template": "1.2.0",
    "date-fns": "^4.1.0",
    "embla-carousel-react": "^8.6.0",
    "input-otp": "^1.4.2",
    "lucide-react": "^0.507.0",
    "next-themes": "^0.4.6",
    "react": "^19.0.0",
    "react-day-picker": "8.10.1",
    "react-dom": "^19.0.0",
    "react-hook-form": "^7.56.2",
    "react-resizable-panels": "^3.0.1",
    "react-router-dom": "^7.5.1",
    "react-scripts": "5.0.1",
    "sonner": "^2.0.3",
    "tailwind-merge": "^3.2.0",
    "tailwindcss-animate": "^1.0.7",
    "vaul": "^1.1.2",
    "zod": "^3.24.4"
  },
  "scripts": {
    "start": "craco start",
    "build": "craco build",
    "test": "craco test"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "@craco/craco": "^7.1.0",
    "@eslint/js": "9.23.0",
    "autoprefixer": "^10.4.20",
    "eslint": "9.23.0",
    "eslint-plugin-import": "2.31.0",
    "eslint-plugin-jsx-a11y": "6.10.2",
    "eslint-plugin-react": "7.37.4",
    "globals": "15.15.0",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17"
  }
}
EOF

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
systemctl enable abetoile-location-backend
systemctl start abetoile-location-backend

# Recharger Nginx
systemctl reload nginx

# Vérifier les statuts
sleep 3

if systemctl is-active --quiet abetoile-location-backend; then
    log_success "Backend démarré avec succès"
else
    log_error "Erreur de démarrage du backend"
    journalctl -u abetoile-location-backend --lines=20
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
echo "🎉 DÉPLOIEMENT TERMINÉ - ABETOILE LOCATION MANAGEMENT"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}📋 STATUT DES SERVICES:${NC}"
echo "   • Backend: $(systemctl is-active abetoile-location-backend)"
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
echo "   • Logs backend: journalctl -u abetoile-location-backend -f"
echo "   • Logs nginx: tail -f /var/log/nginx/abetoile-location.error.log"
echo "   • Redémarrer: abetoile-location-restart"
echo "   • Sauvegarder: abetoile-location-backup"
echo ""

echo -e "${GREEN}✅ Votre application Abetoile Location est maintenant en ligne!${NC}"
echo -e "${BLUE}🚗 Système de gestion de location de véhicules prêt à l'emploi${NC}"