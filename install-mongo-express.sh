#!/bin/bash

# =============================================================================
# 🌐 INSTALLATION MONGO EXPRESS - Interface Web MongoDB
# =============================================================================
# Port: 8081
# Accès: http://votre-serveur:8081
# Sécurisé par authentification
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

# Configuration
MONGO_EXPRESS_PORT="8081"
MONGO_EXPRESS_USER="admin"
MONGO_EXPRESS_PASS=$(openssl rand -base64 12)

log_info "🌐 Installation de Mongo Express (Interface Web MongoDB)..."

# Vérifier que MongoDB fonctionne
if ! systemctl is-active --quiet mongod; then
    log_error "MongoDB n'est pas démarré. Veuillez d'abord installer MongoDB."
    exit 1
fi

# Vérifier que Node.js est installé
if ! command -v npm &> /dev/null; then
    log_error "Node.js/npm non trouvé. Veuillez d'abord installer Node.js."
    exit 1
fi

log_info "Création de l'utilisateur et répertoire pour Mongo Express..."

# Créer utilisateur dédié
if ! id "mongo-express" &>/dev/null; then
    useradd -r -s /bin/false -d /opt/mongo-express mongo-express
fi

# Créer répertoire
mkdir -p /opt/mongo-express
cd /opt/mongo-express

log_info "Installation de Mongo Express..."

# Installer mongo-express globalement
npm install -g mongo-express

# Créer fichier de configuration
cat > /opt/mongo-express/config.js << EOF
module.exports = {
  mongodb: {
    server: 'localhost',
    port: 27017,
    
    // Authentification MongoDB (correspond à Abetoile Location)
    auth: [
      {
        database: 'abetoile_location_prod',
        username: 'abetoile_user',
        password: 'Ab3t0il3L0c4t10n2024!'
      }
    ],
    
    // Connexion directe si pas d'auth
    connectionString: 'mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/abetoile_location_prod',
  },
  
  site: {
    baseUrl: '/',
    cookieKeyName: 'mongo-express',
    cookieSecret: '$(openssl rand -hex 32)',
    host: '0.0.0.0',
    port: $MONGO_EXPRESS_PORT,
    requestSizeLimit: '50mb',
    sessionSecret: '$(openssl rand -hex 32)',
    sslEnabled: false,
    sslCert: '',
    sslKey: '',
  },
  
  // IMPORTANT : Authentification Web obligatoire
  useBasicAuth: true,
  basicAuth: {
    username: '$MONGO_EXPRESS_USER',
    password: '$MONGO_EXPRESS_PASS'
  },
  
  options: {
    console: true,
    //documentsPerPage: 10,
    //editorTheme: 'rubyblue',
    // Maximum size of a single document to display (default 1000kb)
    maxPropSize: (100 * 1000), // 100KB
    // The options below aren't being used yet
    // cmdType: 'eval', // the type of command to use for execution
    // subQuery: {
    //     showFields: false
    // },
    // aggregate: {
    //     allowDiskUse: false
    // },
    // readPreference: 'primary',
    // collectionSortBy: 'name',
    // etc...
  },
  
  // Connexion healthcheck
  healthCheck: {
    path: '/status'
  },
  
  // Désactiver certaines opérations dangereuses en production
  // collapseBooleans: true,
  // noDelete: false, // set to true to disable delete operations
  // noTruncate: false, // set to true to disable truncate operations
};
EOF

# Permissions
chown -R mongo-express:mongo-express /opt/mongo-express
chmod 600 /opt/mongo-express/config.js

log_info "Création du service systemd..."

# Service systemd
cat > /etc/systemd/system/mongo-express.service << EOF
[Unit]
Description=Mongo Express Web Interface
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=mongo-express
Group=mongo-express
WorkingDirectory=/opt/mongo-express
Environment=NODE_ENV=production
Environment=ME_CONFIG_MONGODB_URL=mongodb://abetoile_user:Ab3t0il3L0c4t10n2024!@localhost:27017/abetoile_location_prod
Environment=ME_CONFIG_MONGODB_ENABLE_ADMIN=false
Environment=ME_CONFIG_BASICAUTH_USERNAME=$MONGO_EXPRESS_USER
Environment=ME_CONFIG_BASICAUTH_PASSWORD=$MONGO_EXPRESS_PASS
Environment=ME_CONFIG_OPTIONS_EDITORTHEME=default
Environment=ME_CONFIG_REQUEST_SIZE=100kb
ExecStart=/usr/bin/mongo-express --config /opt/mongo-express/config.js
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Démarrer le service
systemctl daemon-reload
systemctl enable mongo-express
systemctl start mongo-express

# Configurer le firewall
log_info "Configuration du firewall..."
ufw allow $MONGO_EXPRESS_PORT/tcp comment "Mongo Express Web Interface"

# Attendre le démarrage
sleep 5

# Vérifier le service
if systemctl is-active --quiet mongo-express; then
    log_success "Mongo Express démarré avec succès"
else
    log_error "Erreur de démarrage de Mongo Express"
    journalctl -u mongo-express --lines=10 --no-pager
    exit 1
fi

# Affichage des informations de connexion
clear
echo -e "${GREEN}"
echo "================================================================================"
echo "🎉 MONGO EXPRESS INSTALLÉ AVEC SUCCÈS"
echo "================================================================================"
echo -e "${NC}"

echo -e "${BLUE}🌐 ACCÈS WEB:${NC}"
echo "   • URL: http://$(hostname -I | awk '{print $1}'):$MONGO_EXPRESS_PORT"
echo "   • URL locale: http://localhost:$MONGO_EXPRESS_PORT"
echo ""

echo -e "${BLUE}🔐 AUTHENTIFICATION:${NC}"
echo "   • Utilisateur: $MONGO_EXPRESS_USER"
echo "   • Mot de passe: $MONGO_EXPRESS_PASS"
echo ""

echo -e "${YELLOW}📋 INFORMATIONS IMPORTANTES:${NC}"
echo "   • Base de données: abetoile_location_prod"
echo "   • Collections Abetoile: clients, vehicles, orders, invoices, etc."
echo "   • Service: systemctl status mongo-express"
echo "   • Logs: journalctl -u mongo-express -f"
echo ""

echo -e "${BLUE}🛠️ COMMANDES UTILES:${NC}"
echo "   • Redémarrer: sudo systemctl restart mongo-express"
echo "   • Arrêter: sudo systemctl stop mongo-express"
echo "   • Logs: sudo journalctl -u mongo-express -f"
echo ""

echo -e "${YELLOW}⚠️  SÉCURITÉ:${NC}"
echo "   • Interface protégée par authentification HTTP Basic"
echo "   • Accès limité au réseau local par défaut"
echo "   • Pour l'accès distant, configurez un reverse proxy avec SSL"
echo ""

echo -e "${GREEN}✅ Interface MongoDB accessible via navigateur web!${NC}"

# Sauvegarde des informations de connexion
cat > /opt/mongo-express/connexion-info.txt << EOF
=== MONGO EXPRESS - INFORMATIONS DE CONNEXION ===
URL: http://$(hostname -I | awk '{print $1}'):$MONGO_EXPRESS_PORT
Utilisateur: $MONGO_EXPRESS_USER
Mot de passe: $MONGO_EXPRESS_PASS
Base de données: abetoile_location_prod
Service: mongo-express
Fichier config: /opt/mongo-express/config.js
Logs: journalctl -u mongo-express -f
EOF

chmod 600 /opt/mongo-express/connexion-info.txt
chown mongo-express:mongo-express /opt/mongo-express/connexion-info.txt

log_success "Informations sauvegardées dans /opt/mongo-express/connexion-info.txt"