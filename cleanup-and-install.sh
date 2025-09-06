#!/bin/bash

# =============================================================================
# 🧹 SCRIPT DE NETTOYAGE ET INSTALLATION - Abetoile Location
# =============================================================================
# Ce script nettoie les résidus PPA puis relance l'installation
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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier root
if [[ $EUID -ne 0 ]]; then
    log_error "Ce script doit être exécuté en tant que root (sudo)"
    exit 1
fi

clear
echo -e "${YELLOW}"
echo "================================================================================"
echo "🧹 NETTOYAGE SYSTÈME - SUPPRESSION PPA DEADSNAKES"
echo "================================================================================"
echo -e "${NC}"

# =============================================================================
# ÉTAPE 1: SUPPRESSION COMPLÈTE PPA DEADSNAKES
# =============================================================================
log_info "🗑️ Suppression complète du PPA deadsnakes..."

# Supprimer le fichier source deadsnakes
rm -f /etc/apt/sources.list.d/deadsnakes-*.list 2>/dev/null || true
rm -f /etc/apt/sources.list.d/deadsnakes*.list 2>/dev/null || true

# Supprimer les clés GPG deadsnakes
apt-key del F23C5A6CF475977595C89F51BA6932366A755776 2>/dev/null || true

# Supprimer le PPA via add-apt-repository si disponible
add-apt-repository --remove ppa:deadsnakes/ppa -y 2>/dev/null || true

log_success "PPA deadsnakes supprimé"

# =============================================================================
# ÉTAPE 2: NETTOYAGE COMPLET APT
# =============================================================================
log_info "🧽 Nettoyage complet du cache APT..."

# Nettoyer complètement APT
apt-get clean
apt-get autoclean
apt-get autoremove -y

# Supprimer les listes corrompues
rm -rf /var/lib/apt/lists/*

# Reconstruire les listes
apt-get update -y

log_success "Cache APT nettoyé et reconstruit"

# =============================================================================
# ÉTAPE 3: SUPPRIMER ANCIENNES INSTALLATIONS PARTIELLES
# =============================================================================
log_info "🗑️ Nettoyage des installations partielles..."

# Arrêter les services s'ils existent
systemctl stop abetoile-location-backend 2>/dev/null || true
systemctl disable abetoile-location-backend 2>/dev/null || true

# Supprimer les anciens fichiers de service
rm -f /etc/systemd/system/abetoile-location-backend.service 2>/dev/null || true
rm -f /etc/systemd/system/abetoile-backend.service 2>/dev/null || true

# Supprimer les anciens sites Nginx
rm -f /etc/nginx/sites-enabled/abetoile-location 2>/dev/null || true
rm -f /etc/nginx/sites-available/abetoile-location 2>/dev/null || true

# Recharger systemd
systemctl daemon-reload

log_success "Installations partielles nettoyées"

# =============================================================================
# ÉTAPE 4: INSTALLATION PROPRE - PYTHON SYSTÈME
# =============================================================================
log_info "🐍 Installation Python depuis les repos Ubuntu officiels..."

export DEBIAN_FRONTEND=noninteractive

# Installer Python avec toutes les dépendances depuis Ubuntu
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-distutils \
    python3-setuptools \
    python3-wheel \
    build-essential \
    pkg-config

# Vérifier la version Python
PYTHON_VERSION=$(python3 --version 2>&1)
log_success "$PYTHON_VERSION installé depuis Ubuntu repos"

# Mettre à jour pip
python3 -m pip install --upgrade pip

# =============================================================================
# ÉTAPE 5: INSTALLATION NODE.JS (PROPRE)
# =============================================================================
log_info "📦 Installation Node.js (méthode propre)..."

# Supprimer d'éventuels résidus NodeJS
apt-get remove -y nodejs npm 2>/dev/null || true

# Nettoyer les sources NodeJS existantes
rm -f /etc/apt/sources.list.d/nodesource.list 2>/dev/null || true

# Réinstaller NodeJS proprement
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Vérifier
NODE_VERSION=$(node --version 2>/dev/null)
log_success "Node.js $NODE_VERSION installé"

# =============================================================================
# ÉTAPE 6: INSTALLATION YARN (PROPRE)
# =============================================================================
log_info "🧶 Installation Yarn (méthode propre)..."

# Nettoyer Yarn existant
apt-get remove -y yarn 2>/dev/null || true
rm -f /etc/apt/sources.list.d/yarn.list 2>/dev/null || true
rm -f /usr/share/keyrings/yarn.gpg 2>/dev/null || true

# Réinstaller Yarn proprement
curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor -o /usr/share/keyrings/yarn.gpg
echo "deb [signed-by=/usr/share/keyrings/yarn.gpg] https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list
apt-get update -y
apt-get install -y yarn

YARN_VERSION=$(yarn --version 2>/dev/null)
log_success "Yarn $YARN_VERSION installé"

# =============================================================================
# ÉTAPE 7: INSTALLATION MONGODB (PROPRE)
# =============================================================================
log_info "🗄️ Installation MongoDB (méthode propre)..."

# Nettoyer MongoDB existant
systemctl stop mongod 2>/dev/null || true
apt-get remove -y mongodb-org* 2>/dev/null || true
rm -f /etc/apt/sources.list.d/mongodb-org-*.list 2>/dev/null || true
rm -f /usr/share/keyrings/mongodb-server-*.gpg 2>/dev/null || true

# Réinstaller MongoDB proprement
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg

# Utiliser le repo jammy pour Ubuntu récent (plucky/oracular)
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" > /etc/apt/sources.list.d/mongodb-org-7.0.list

apt-get update -y
apt-get install -y mongodb-org

# Démarrer MongoDB
systemctl start mongod
systemctl enable mongod

# Vérifier MongoDB
sleep 5
if systemctl is-active --quiet mongod; then
    log_success "MongoDB installé et actif"
else
    log_error "Problème avec MongoDB"
    exit 1
fi

# =============================================================================
# ÉTAPE 8: NGINX ET AUTRES SERVICES
# =============================================================================
log_info "🌐 Installation des services système..."

# Installer les autres services nécessaires
apt-get install -y \
    nginx \
    ufw \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    wget \
    htop \
    nano

# Démarrer les services
systemctl start nginx
systemctl enable nginx
systemctl start ufw
systemctl enable ufw

log_success "Services système installés"

# =============================================================================
# ÉTAPE 9: CONFIGURATION FINALE
# =============================================================================
log_info "⚙️ Configuration finale du système..."

# Configuration UFW basique
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 8001/tcp
ufw --force enable

# Créer les répertoires de base
mkdir -p /var/www/abetoile-location
mkdir -p /var/log/abetoile-location
mkdir -p /var/backups/abetoile-location

# Permissions
if ! id "www-data" &>/dev/null; then
    useradd -r -s /bin/false www-data
fi

chown -R www-data:www-data /var/www/abetoile-location
chown -R www-data:www-data /var/log/abetoile-location

log_success "Configuration de base terminée"

# =============================================================================
# RÉSULTAT FINAL
# =============================================================================
clear
echo -e "${GREEN}"
echo "================================================================================"
echo "✅ NETTOYAGE ET PRÉPARATION TERMINÉS"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}📋 SYSTÈME NETTOYÉ ET PRÉPARÉ:${NC}"
echo "   • Ubuntu: $(lsb_release -rs) ($(lsb_release -cs))"
echo "   • Python: $PYTHON_VERSION"
echo "   • Node.js: $NODE_VERSION"
echo "   • Yarn: $YARN_VERSION"
echo "   • MongoDB: Actif"
echo "   • Nginx: Actif"
echo ""

echo -e "${BLUE}📊 STATUT DES SERVICES:${NC}"
echo "   • MongoDB: $(systemctl is-active mongod)"
echo "   • Nginx: $(systemctl is-active nginx)"
echo "   • UFW: $(systemctl is-active ufw)"
echo ""

echo -e "${GREEN}🎉 SYSTÈME PRÊT POUR L'INSTALLATION ABETOILE LOCATION!${NC}"
echo ""
echo -e "${YELLOW}📋 PROCHAINE ÉTAPE:${NC}"
echo "Maintenant vous pouvez exécuter le script de déploiement:"
echo ""
echo -e "${BLUE}curl -sSL https://raw.githubusercontent.com/redademechety-ux/abetoile-location/main/deploy.sh | sudo bash${NC}"
echo ""

log_success "Prêt pour le déploiement!"