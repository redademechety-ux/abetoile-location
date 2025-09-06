#!/bin/bash

# =============================================================================
# 🚀 SCRIPT DE SETUP GITHUB - Abetoile Location Management
# =============================================================================
# Ce script prépare le repository GitHub pour votre application
# =============================================================================

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

clear
echo -e "${GREEN}"
echo "================================================================================"
echo "🚀 SETUP GITHUB - ABETOILE LOCATION MANAGEMENT"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}📋 STRUCTURE DU PROJET PRÊTE POUR GITHUB:${NC}"
echo ""

# Lister les fichiers importants
echo -e "${YELLOW}📁 Fichiers et dossiers à uploader sur GitHub:${NC}"
echo ""
echo "✅ backend/"
echo "   ├── server.py (API FastAPI complète)"
echo "   ├── pdf_generator.py (Génération PDF + IA)"
echo "   ├── accounting.py (Comptabilité française)"
echo "   ├── requirements.txt (Dépendances Python)"
echo "   └── .env (À MODIFIER avec vos paramètres)"
echo ""
echo "✅ frontend/"
echo "   ├── src/components/ (Tous les composants React)"
echo "   ├── src/App.js (Application principale)"
echo "   ├── src/App.css (Styles globaux)"
echo "   ├── package.json (Dépendances Node.js)"
echo "   └── .env (À MODIFIER avec votre domaine)"
echo ""
echo "✅ Scripts d'installation:"
echo "   ├── install.sh (Installation serveur automatique)"
echo "   ├── deploy.sh (Déploiement automatique)"
echo "   └── setup-github.sh (Ce script)"
echo ""
echo "✅ Documentation:"
echo "   ├── README.md (Documentation complète)"
echo "   ├── package.json (Configuration projet)"
echo "   └── .gitignore (Exclusions Git)"
echo ""

echo -e "${BLUE}🔧 ÉTAPES POUR CRÉER VOTRE REPOSITORY GITHUB:${NC}"
echo ""
echo "1. 📱 Allez sur https://github.com"
echo "2. ➕ Cliquez sur 'New repository'"
echo "3. 📝 Nom du repository: abetoile-location"
echo "4. 📄 Description: Système de gestion de location de véhicules avec IA"
echo "5. 🔒 Visibilité: Private (recommandé pour un projet commercial)"
echo "6. ✅ Cochez 'Add a README file' (sera remplacé)"
echo "7. 🚀 Cliquez sur 'Create repository'"
echo ""

echo -e "${BLUE}📤 COMMANDES POUR UPLOADER LE CODE:${NC}"
echo ""
echo -e "${YELLOW}# Sur votre machine locale:${NC}"
echo "git clone https://github.com/VOTRE-USERNAME/abetoile-location.git"
echo "cd abetoile-location"
echo ""
echo -e "${YELLOW}# Copier tous les fichiers depuis /app vers votre dossier local${NC}"
echo "# Puis exécuter:"
echo "git add ."
echo "git commit -m '🚀 Initial commit - Abetoile Location Management System'"
echo "git push origin main"
echo ""

echo -e "${BLUE}🌐 URL D'INSTALLATION POUR VOTRE SERVEUR:${NC}"
echo ""
echo -e "${GREEN}# Installation complète en une commande:${NC}"
echo "curl -sSL https://raw.githubusercontent.com/VOTRE-USERNAME/abetoile-location/main/install.sh | sudo bash"
echo ""
echo -e "${GREEN}# Déploiement du code:${NC}"
echo "curl -sSL https://raw.githubusercontent.com/VOTRE-USERNAME/abetoile-location/main/deploy.sh | sudo bash"
echo ""

echo -e "${YELLOW}⚠️  IMPORTANT - SÉCURITÉ:${NC}"
echo ""
echo "❌ NE PAS COMMITER les fichiers .env avec vos mots de passe réels"
echo "✅ Les fichiers .env sont dans .gitignore (exclus automatiquement)"
echo "✅ Les scripts génèrent automatiquement les bons .env sur le serveur"
echo ""

echo -e "${BLUE}🔐 VARIABLES À CONFIGURER DANS VOS .ENV:${NC}"
echo ""
echo -e "${YELLOW}Backend (.env):${NC}"
echo "• MONGO_URL avec votre mot de passe MongoDB"
echo "• SECRET_KEY généré automatiquement par le script"
echo "• EMERGENT_LLM_KEY (déjà configuré)"
echo ""
echo -e "${YELLOW}Frontend (.env):${NC}"
echo "• REACT_APP_BACKEND_URL=https://abetoile-location.fr"
echo ""

echo -e "${GREEN}✅ VOTRE PROJET EST PRÊT POUR GITHUB !${NC}"
echo ""
echo -e "${BLUE}📋 RÉCAPITULATIF:${NC}"
echo "• 🌐 Domaine: abetoile-location.fr"
echo "• 🔌 Backend: Port 8001"
echo "• 🗄️ Base: abetoile_location_prod"
echo "• 🤖 IA: Génération PDF automatique"
echo "• 📊 Comptabilité: Française (PCG)"
echo "• 🔄 Déploiement: Automatique"
echo ""

echo -e "${YELLOW}🚀 PROCHAINES ÉTAPES:${NC}"
echo "1. Créez votre repository GitHub"
echo "2. Uploadez tous les fichiers de /app"
echo "3. Modifiez l'URL GitHub dans les scripts"
echo "4. Exécutez les scripts sur votre serveur"
echo "5. Configurez SSL avec certbot"
echo "6. Testez votre application !"
echo ""

echo -e "${GREEN}🎉 Bon déploiement avec Abetoile Location !${NC}"