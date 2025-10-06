#!/bin/bash

echo "🔍 DIAGNOSTIC: Erreur 500 upload maintenance - Debug complet"

# Adapter le chemin selon la vraie structure 
if [ -d "/var/www/abetoile-location" ]; then
    APP_ROOT="/var/www/abetoile-location"
    echo "📁 Application trouvée dans: $APP_ROOT"
elif [ -d "/app" ]; then
    APP_ROOT="/app"
    echo "📁 Application trouvée dans: $APP_ROOT"
else
    echo "❌ Application non trouvée"
    exit 1
fi

echo ""
echo "🔍 1. Vérification des logs backend..."
echo "════════════════════════════════════════"
tail -n 20 /var/log/supervisor/backend*.log 2>/dev/null || \
tail -n 20 /var/log/backend.log 2>/dev/null || \
journalctl -u backend -n 20 --no-pager 2>/dev/null || \
echo "Logs backend non trouvés - vérifiez manuellement"

echo ""
echo "🔍 2. Vérification du dossier documents..."
echo "════════════════════════════════════════"
ls -la $APP_ROOT/documents/ 2>/dev/null || echo "Dossier documents non trouvé"
echo "Permissions du dossier documents:"
stat $APP_ROOT/documents/ 2>/dev/null || echo "Impossible de vérifier les permissions"

echo ""
echo "🔍 3. Test de l'endpoint maintenance..."
echo "════════════════════════════════════════"
curl -f -s -o /dev/null "http://localhost:8001/api/maintenance" && \
echo "✅ API maintenance accessible" || \
echo "❌ API maintenance non accessible"

echo ""
echo "🔍 4. Vérification du service backend..."
echo "════════════════════════════════════════"
sudo supervisorctl status backend 2>/dev/null || \
systemctl status backend --no-pager -l 2>/dev/null || \
echo "Service backend non trouvé"

echo ""
echo "🔧 5. Création du dossier documents si nécessaire..."
echo "════════════════════════════════════════"
sudo mkdir -p $APP_ROOT/documents
sudo chmod 755 $APP_ROOT/documents
sudo chown -R www-data:www-data $APP_ROOT/documents 2>/dev/null || \
sudo chown -R root:root $APP_ROOT/documents
echo "✅ Dossier documents configuré"

echo ""
echo "📊 RÉSUMÉ DU DIAGNOSTIC:"
echo "════════════════════════════════════════"
echo "- App path: $APP_ROOT"
echo "- Logs vérifiés pour erreurs 500"
echo "- Permissions documents vérifiées"
echo "- API maintenance testée"
echo ""
echo "🧪 PROCHAINES ÉTAPES:"
echo "1. Vérifiez la console du navigateur (F12) pour l'erreur exacte"
echo "2. Testez avec un petit fichier PDF (< 1MB)"
echo "3. Assurez-vous d'être connecté et sur un enregistrement sauvegardé"
echo "4. Vérifiez le type de fichier (PDF/JPG/PNG uniquement)"