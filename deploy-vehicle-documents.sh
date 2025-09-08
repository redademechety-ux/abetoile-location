#!/bin/bash
set -e

echo "🚀 DÉPLOIEMENT FONCTIONNALITÉS DOCUMENTS VÉHICULES"
echo "=================================================="

# 1. Arrêter le backend
echo "🛑 Arrêt du backend..."
systemctl stop abetoile-location-backend

# 2. Copier les nouveaux fichiers frontend
echo "📁 Copie des fichiers frontend..."
cp /app/frontend/src/components/VehicleDocuments.js /var/www/abetoile-location/frontend/src/components/
cp /app/frontend/src/components/VehicleForm.js /var/www/abetoile-location/frontend/src/components/

# 3. Copier le fichier backend mis à jour
echo "📁 Copie du fichier backend..."
cp /app/backend/server.py /var/www/abetoile-location/backend/

# 4. Créer les répertoires d'upload nécessaires
echo "📁 Création répertoires d'upload..."
mkdir -p /var/www/abetoile-location/uploads/vehicles
mkdir -p /var/www/abetoile-location/uploads/clients
chown -R www-data:www-data /var/www/abetoile-location/uploads
chmod -R 755 /var/www/abetoile-location/uploads

# 5. Vérifier et installer les dépendances Python nécessaires
echo "🐍 Vérification dépendances Python..."
cd /var/www/abetoile-location/backend

# Ajouter python-multipart si pas présent
if ! grep -q "python-multipart" requirements.txt; then
    echo "python-multipart>=0.0.9" >> requirements.txt
    echo "✅ python-multipart ajouté au requirements.txt"
fi

# Installer les dépendances
sudo -u www-data bash -c "source venv/bin/activate && pip install python-multipart --no-warn-script-location --disable-pip-version-check"

# 6. Configuration Nginx pour les uploads
echo "🌐 Configuration Nginx..."
if ! grep -q "client_max_body_size" /etc/nginx/sites-available/abetoile-location; then
    # Sauvegarder la config
    cp /etc/nginx/sites-available/abetoile-location /etc/nginx/sites-available/abetoile-location.bak
    
    # Ajouter la configuration upload après server_name
    sed -i '/server_name/a \ \ \ \ client_max_body_size 50M;' /etc/nginx/sites-available/abetoile-location
    echo "✅ Limite upload 50MB ajoutée à Nginx"
fi

# Tester et recharger Nginx
if nginx -t; then
    systemctl reload nginx
    echo "✅ Configuration Nginx rechargée"
else
    echo "❌ Erreur config Nginx, restauration..."
    cp /etc/nginx/sites-available/abetoile-location.bak /etc/nginx/sites-available/abetoile-location
    nginx -t && systemctl reload nginx
fi

# 7. Rebuilder le frontend
echo "⚛️  Rebuild du frontend..."
cd /var/www/abetoile-location/frontend

# Installer les nouvelles dépendances si nécessaire
sudo -u www-data yarn install --silent

# Builder
sudo -u www-data NODE_OPTIONS="--max-old-space-size=4096" yarn build

# 8. Ajuster les permissions
echo "🔒 Ajustement des permissions..."
chown -R www-data:www-data /var/www/abetoile-location
chmod -R 755 /var/www/abetoile-location

# 9. Redémarrer le backend
echo "🚀 Redémarrage du backend..."
systemctl start abetoile-location-backend

# Attendre le démarrage
sleep 5

# 10. Tests finaux
echo ""
echo "🧪 TESTS FINAUX"
echo "==============="

# Test status des services
echo "📊 Status services:"
echo "  Backend: $(systemctl is-active abetoile-location-backend)"
echo "  Nginx: $(systemctl is-active nginx)"
echo "  MongoDB: $(systemctl is-active mongod)"

# Test endpoints documents
echo ""
echo "🔍 Test endpoints documents:"

# Test liste documents (doit retourner 404 ou 200 avec liste vide)
DOCS_LIST_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8010/api/vehicles/test-id/documents" 2>/dev/null)
echo "  GET /api/vehicles/{id}/documents: $DOCS_LIST_STATUS"

# Test endpoint docs API
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8010/docs" 2>/dev/null)
echo "  GET /docs: $DOCS_STATUS"

# Vérifier les répertoires
echo ""
echo "📁 Répertoires créés:"
ls -la /var/www/abetoile-location/uploads/ 2>/dev/null || echo "Répertoire uploads non accessible"

# Logs récents
echo ""
echo "📋 Logs backend (5 dernières lignes):"
journalctl -u abetoile-location-backend --lines=5 --no-pager

echo ""
echo "==============================================="
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "==============================================="
echo ""
echo "🎯 FONCTIONNALITÉS DÉPLOYÉES:"
echo "  ✅ Upload de documents véhicules avec libellés"
echo "  ✅ Visualisation des documents uploadés"
echo "  ✅ Modification des libellés"
echo "  ✅ Téléchargement des documents"
echo "  ✅ Suppression des documents"
echo "  ✅ Types de documents (carte grise, assurance, etc.)"
echo ""
echo "🌐 Testez sur: https://abetoile-location.fr/"
echo "   1. Allez dans Véhicules"
echo "   2. Éditez un véhicule existant ou créez-en un nouveau"
echo "   3. Cliquez sur l'onglet 'Documents'"
echo "   4. Utilisez 'Ajouter un document' pour uploader"
echo ""
echo "📋 FORMATS SUPPORTÉS:"
echo "   • PDF, JPG, PNG, GIF"
echo "   • Taille max: 50MB"
echo "   • Stockage: /var/www/abetoile-location/uploads/vehicles/"