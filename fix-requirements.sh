#!/bin/bash

# =============================================================================
# 🔧 CORRECTION REQUIREMENTS.TXT - Abetoile Location
# =============================================================================
# Supprime les modules intégrés Python qui causent des erreurs
# =============================================================================

set -e

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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

APP_DIR="/var/www/abetoile-location"
REQUIREMENTS_FILE="$APP_DIR/backend/requirements.txt"

log_info "🔧 Correction du fichier requirements.txt..."

# Vérifier que le fichier existe
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    log_error "Fichier requirements.txt non trouvé dans $APP_DIR/backend/"
    exit 1
fi

log_info "Fichier trouvé : $REQUIREMENTS_FILE"

# Créer une sauvegarde
cp "$REQUIREMENTS_FILE" "$REQUIREMENTS_FILE.backup"
log_info "Sauvegarde créée : $REQUIREMENTS_FILE.backup"

# Corriger le fichier en supprimant les modules intégrés
cat > "$REQUIREMENTS_FILE" << 'EOF'
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
EOF

log_success "Requirements.txt corrigé (modules intégrés 'io' et 'base64' supprimés)"

# Réinstaller les dépendances avec le fichier corrigé
log_info "🐍 Réinstallation des dépendances Python..."

cd $APP_DIR/backend

if [ -d "venv" ]; then
    log_info "Environnement virtuel trouvé, réinstallation..."
    
    # Installer les dépendances corrigées
    log_info "Installation d'emergentintegrations..."
    sudo -u www-data bash -c "cd $APP_DIR/backend && source venv/bin/activate && pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ --no-warn-script-location --disable-pip-version-check"
    
    log_info "Installation des dépendances depuis requirements.txt corrigé..."
    sudo -u www-data bash -c "cd $APP_DIR/backend && source venv/bin/activate && pip install -r requirements.txt --no-warn-script-location --disable-pip-version-check"
    
    log_success "Dépendances Python réinstallées avec succès"
    
    # Redémarrer le backend
    log_info "🔄 Redémarrage du backend..."
    systemctl restart abetoile-location-backend
    
    sleep 3
    
    if systemctl is-active --quiet abetoile-location-backend; then
        log_success "Backend redémarré avec succès"
    else
        log_error "Erreur de redémarrage du backend"
        log_info "Logs du backend :"
        journalctl -u abetoile-location-backend --lines=10 --no-pager
    fi
    
else
    log_error "Environnement virtuel non trouvé dans $APP_DIR/backend/venv"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ CORRECTION TERMINÉE${NC}"
echo -e "${BLUE}🔧 Fichier corrigé : $REQUIREMENTS_FILE${NC}"
echo -e "${BLUE}💾 Sauvegarde : $REQUIREMENTS_FILE.backup${NC}"
echo -e "${BLUE}🚀 Backend : $(systemctl is-active abetoile-location-backend)${NC}"
echo ""
echo -e "${GREEN}Votre application devrait maintenant fonctionner correctement !${NC}"