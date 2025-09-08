#!/bin/bash
set -e

echo "🚀 MISE À JOUR COMPLÈTE - ABETOILE LOCATION MANAGEMENT"
echo "====================================================="
echo "🌐 Serveur: $(hostname -I | awk '{print $1}')"
echo "📅 Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Configuration
APP_DIR="/var/www/abetoile-location"
BACKUP_DIR="/var/backups/abetoile-location-$(date +%Y%m%d-%H%M%S)"
GITHUB_REPO="https://github.com/redademechety-ux/abetoile-location.git"
TEMP_DIR="/tmp/abetoile-update-$$"

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

# Fonction de rollback en cas d'erreur
rollback() {
    log_error "Erreur détectée, rollback en cours..."
    if [ -d "$BACKUP_DIR" ]; then
        systemctl stop abetoile-location-backend 2>/dev/null || true
        rm -rf $APP_DIR/*
        cp -r $BACKUP_DIR/* $APP_DIR/
        chown -R www-data:www-data $APP_DIR
        systemctl start abetoile-location-backend
        log_warning "Rollback terminé - application restaurée"
    fi
    rm -rf $TEMP_DIR 2>/dev/null || true
    exit 1
}

# Piège pour les erreurs
trap rollback ERR

# =============================================================================
# 1. VÉRIFICATIONS PRÉLIMINAIRES
# =============================================================================
log_info "🔍 Vérifications préliminaires..."

if [ ! -d "$APP_DIR" ]; then
    log_error "Répertoire application $APP_DIR non trouvé"
    exit 1
fi

# Vérifier les services
BACKEND_STATUS=$(systemctl is-active abetoile-location-backend 2>/dev/null || echo "inactive")
NGINX_STATUS=$(systemctl is-active nginx 2>/dev/null || echo "inactive")
MONGO_STATUS=$(systemctl is-active mongod 2>/dev/null || echo "inactive")

echo "📊 Status actuel des services:"
echo "  Backend: $BACKEND_STATUS"
echo "  Nginx: $NGINX_STATUS"
echo "  MongoDB: $MONGO_STATUS"

if [ "$MONGO_STATUS" != "active" ]; then
    log_error "MongoDB n'est pas actif - mise à jour impossible"
    exit 1
fi

# =============================================================================
# 2. SAUVEGARDE DE L'APPLICATION ACTUELLE
# =============================================================================
log_info "💾 Sauvegarde de l'application actuelle..."

mkdir -p "$BACKUP_DIR"
cp -r $APP_DIR/* $BACKUP_DIR/
log_success "Sauvegarde créée dans $BACKUP_DIR"

# Sauvegarde de la base de données
log_info "💾 Sauvegarde de la base de données..."
mongodump --db abetoile_location_prod --out "$BACKUP_DIR/mongodb-backup" --quiet
log_success "Base de données sauvegardée"

# =============================================================================
# 3. ARRÊT DES SERVICES
# =============================================================================
log_info "🛑 Arrêt des services..."
systemctl stop abetoile-location-backend

# =============================================================================
# 4. TÉLÉCHARGEMENT DE LA NOUVELLE VERSION
# =============================================================================
log_info "📥 Téléchargement de la nouvelle version..."

rm -rf $TEMP_DIR
if git clone $GITHUB_REPO $TEMP_DIR; then
    log_success "Code source téléchargé depuis GitHub"
else
    log_error "Impossible de télécharger depuis GitHub"
    exit 1
fi

# Vérifier la structure
if [ ! -d "$TEMP_DIR/backend" ] || [ ! -d "$TEMP_DIR/frontend" ]; then
    log_error "Structure du repository incorrecte"
    exit 1
fi

# =============================================================================
# 5. MISE À JOUR DU BACKEND
# =============================================================================
log_info "🐍 Mise à jour du backend..."

# Copier les nouveaux fichiers backend
cp -r $TEMP_DIR/backend/* $APP_DIR/backend/

# Préserver le fichier .env existant
if [ -f "$BACKUP_DIR/backend/.env" ]; then
    cp "$BACKUP_DIR/backend/.env" "$APP_DIR/backend/.env"
    log_success "Configuration .env préservée"
fi

# Mise à jour des dépendances Python
cd $APP_DIR/backend

# Vérifier et ajouter les nouvelles dépendances
if ! grep -q "python-multipart" requirements.txt; then
    echo "python-multipart>=0.0.9" >> requirements.txt
    log_info "python-multipart ajouté aux dépendances"
fi

# Installer/mettre à jour les dépendances
log_info "Installation des dépendances Python..."
sudo -u www-data bash -c "source venv/bin/activate && pip install --upgrade pip --no-warn-script-location --disable-pip-version-check"
sudo -u www-data bash -c "source venv/bin/activate && pip install -r requirements.txt --no-warn-script-location --disable-pip-version-check"

log_success "Backend mis à jour"

# =============================================================================
# 6. MISE À JOUR DU FRONTEND
# =============================================================================
log_info "⚛️  Mise à jour du frontend..."

# Copier les nouveaux fichiers frontend
cp -r $TEMP_DIR/frontend/* $APP_DIR/frontend/

# Préserver le fichier .env existant
if [ -f "$BACKUP_DIR/frontend/.env" ]; then
    cp "$BACKUP_DIR/frontend/.env" "$APP_DIR/frontend/.env"
    log_success "Configuration frontend .env préservée"
fi

# Mise à jour des dépendances et rebuild
cd $APP_DIR/frontend

log_info "Installation des dépendances frontend..."
sudo -u www-data yarn install --silent

log_info "Build de production..."
sudo -u www-data NODE_OPTIONS="--max-old-space-size=4096" yarn build

if [ ! -d "build" ]; then
    log_error "Échec du build frontend"
    exit 1
fi

log_success "Frontend mis à jour et buildé"

# =============================================================================
# 7. MISE À JOUR DE LA CONFIGURATION SYSTÈME
# =============================================================================
log_info "⚙️ Mise à jour configuration système..."

# Créer les répertoires d'upload
mkdir -p $APP_DIR/uploads/{vehicles,clients}
chown -R www-data:www-data $APP_DIR/uploads
chmod -R 755 $APP_DIR/uploads

# Vérifier et mettre à jour la configuration Nginx
if ! grep -q "client_max_body_size" /etc/nginx/sites-available/abetoile-location; then
    cp /etc/nginx/sites-available/abetoile-location /etc/nginx/sites-available/abetoile-location.bak.$(date +%Y%m%d)
    sed -i '/server_name/a \ \ \ \ client_max_body_size 50M;' /etc/nginx/sites-available/abetoile-location
    log_info "Configuration Nginx upload mise à jour (50MB)"
fi

# Tester et recharger Nginx
if nginx -t; then
    systemctl reload nginx
    log_success "Configuration Nginx rechargée"
else
    log_warning "Erreur configuration Nginx - restauration de la sauvegarde"
    cp /etc/nginx/sites-available/abetoile-location.bak.$(date +%Y%m%d) /etc/nginx/sites-available/abetoile-location
    nginx -t && systemctl reload nginx
fi

# =============================================================================
# 8. AJUSTEMENT DES PERMISSIONS
# =============================================================================
log_info "🔒 Ajustement des permissions..."

chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod 600 $APP_DIR/backend/.env 2>/dev/null || true
chmod 600 $APP_DIR/frontend/.env 2>/dev/null || true

# =============================================================================
# 9. REDÉMARRAGE DES SERVICES
# =============================================================================
log_info "🚀 Redémarrage des services..."

systemctl daemon-reload
systemctl start abetoile-location-backend

# Attendre le démarrage
sleep 8

# =============================================================================
# 10. VÉRIFICATIONS POST-MISE À JOUR
# =============================================================================
log_info "🧪 Vérifications post-mise à jour..."

# Vérifier les services
BACKEND_STATUS_NEW=$(systemctl is-active abetoile-location-backend)
NGINX_STATUS_NEW=$(systemctl is-active nginx)

echo "📊 Status après mise à jour:"
echo "  Backend: $BACKEND_STATUS_NEW"
echo "  Nginx: $NGINX_STATUS_NEW"
echo "  MongoDB: $(systemctl is-active mongod)"

# Test des endpoints critiques
log_info "Test des endpoints..."

# Test docs
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8010/docs" 2>/dev/null)
echo "  Documentation API: $DOCS_STATUS"

# Test authentification
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:8010/api/auth/register" -H "Content-Type: application/json" -d '{}' 2>/dev/null)
echo "  Endpoint auth: $AUTH_STATUS"

# Test documents véhicules
VEHICLE_DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8010/api/vehicles/test/documents" 2>/dev/null)
echo "  Documents véhicules: $VEHICLE_DOCS_STATUS"

# Test documents clients
CLIENT_DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8010/api/clients/test/documents" 2>/dev/null)
echo "  Documents clients: $CLIENT_DOCS_STATUS"

# Vérifier les logs récents
log_info "Logs récents du backend:"
journalctl -u abetoile-location-backend --lines=5 --no-pager | tail -5

# =============================================================================
# 11. NETTOYAGE
# =============================================================================
log_info "🧹 Nettoyage..."

rm -rf $TEMP_DIR

# Nettoyer les anciennes sauvegardes (garder les 5 plus récentes)
find /var/backups -name "abetoile-location-*" -type d | sort -r | tail -n +6 | xargs rm -rf 2>/dev/null || true

# =============================================================================
# 12. RAPPORT FINAL
# =============================================================================
clear
echo -e "${GREEN}"
echo "================================================================================"
echo "🎉 MISE À JOUR COMPLÈTE TERMINÉE AVEC SUCCÈS"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}📋 RÉSUMÉ DE LA MISE À JOUR:${NC}"
echo "  • ✅ Backend mis à jour avec nouvelles fonctionnalités"
echo "  • ✅ Frontend mis à jour et rebuilé"
echo "  • ✅ Gestion complète des documents clients et véhicules"
echo "  • ✅ Correction visualisation PDF dans navigateur"
echo "  • ✅ Configuration Nginx optimisée pour uploads"
echo "  • ✅ Permissions et sécurité ajustées"
echo ""

echo -e "${BLUE}🎯 NOUVELLES FONCTIONNALITÉS:${NC}"
echo "  • 📁 Upload de documents avec libellés pour véhicules"
echo "  • 📁 Upload de documents avec libellés pour clients"
echo "  • 👁️ Visualisation PDF améliorée dans le navigateur"
echo "  • ✏️ Modification des libellés de documents"
echo "  • 🗑️ Suppression de documents"
echo "  • 📥 Téléchargement de documents"
echo "  • 🏷️ Types de documents automatiques"
echo "  • 📑 Interface avec onglets (Informations/Documents)"
echo ""

echo -e "${BLUE}📊 STATUS FINAL:${NC}"
echo "  • Backend: $BACKEND_STATUS_NEW"
echo "  • Nginx: $NGINX_STATUS_NEW"
echo "  • MongoDB: $(systemctl is-active mongod)"
echo ""

echo -e "${BLUE}🌐 ACCÈS À L'APPLICATION:${NC}"
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "  • Site web: https://abetoile-location.fr/"
echo "  • IP directe: http://$SERVER_IP/"
echo "  • Documentation API: https://abetoile-location.fr/api/docs"
echo ""

echo -e "${BLUE}📂 SAUVEGARDE:${NC}"
echo "  • Application: $BACKUP_DIR"
echo "  • Base de données: $BACKUP_DIR/mongodb-backup"
echo ""

echo -e "${BLUE}🔧 COMMANDES UTILES:${NC}"
echo "  • Logs backend: journalctl -u abetoile-location-backend -f"
echo "  • Redémarrer: systemctl restart abetoile-location-backend"
echo "  • Status: systemctl status abetoile-location-backend"
echo ""

echo -e "${YELLOW}📋 TESTS RECOMMANDÉS:${NC}"
echo "  1. 🚗 Créer/éditer un véhicule → onglet Documents → uploader"
echo "  2. 👤 Créer/éditer un client → onglet Documents → uploader"
echo "  3. 👁️ Tester la visualisation PDF dans navigateur"
echo "  4. ✏️ Modifier les libellés des documents"
echo "  5. 📥 Télécharger et supprimer des documents"
echo ""

if [ "$BACKEND_STATUS_NEW" = "active" ] && [ "$NGINX_STATUS_NEW" = "active" ]; then
    echo -e "${GREEN}✅ MISE À JOUR RÉUSSIE - VOTRE APPLICATION EST OPÉRATIONNELLE !${NC}"
else
    echo -e "${YELLOW}⚠️  VÉRIFICATION REQUISE - CERTAINS SERVICES PEUVENT NÉCESSITER UNE ATTENTION${NC}"
fi

echo ""
echo -e "${BLUE}🚗 Profitez de votre système de gestion Abetoile Location mis à jour !${NC}"