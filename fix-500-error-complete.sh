#!/bin/bash

echo "🔧 CORRECTION COMPLÈTE: Erreur 500 upload maintenance"

# Détecter le bon répertoire de l'application
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
echo "🔍 1. Diagnostic des logs backend..."
echo "════════════════════════════════════════"
echo "Dernières erreurs backend:"
tail -n 10 /var/log/supervisor/backend*.log 2>/dev/null | grep -i error || echo "Pas d'erreurs récentes trouvées"

echo ""
echo "🔧 2. Configuration du dossier documents..."
echo "════════════════════════════════════════"
sudo mkdir -p $APP_ROOT/documents
sudo chmod 755 $APP_ROOT/documents
sudo chown -R www-data:www-data $APP_ROOT/documents 2>/dev/null || sudo chown -R root:root $APP_ROOT/documents
echo "✅ Dossier documents configuré"

echo ""
echo "🔄 3. Redémarrage du backend..."
echo "════════════════════════════════════════"
sudo supervisorctl restart backend 2>/dev/null || sudo systemctl restart backend
sleep 2
echo "✅ Backend redémarré"

echo ""
echo "📦 4. Reconstruction du frontend avec gestion d'erreurs améliorée..."
echo "════════════════════════════════════════"
cd $APP_ROOT/frontend

if [ ! -f "package.json" ]; then
    echo "❌ package.json non trouvé dans $APP_ROOT/frontend"
    exit 1
fi

yarn build

if [ $? -eq 0 ]; then
    echo "✅ Build frontend réussie!"
    
    echo ""
    echo "🔄 5. Redémarrage des services frontend..."
    echo "════════════════════════════════════════"
    sudo supervisorctl restart frontend 2>/dev/null || sudo systemctl restart nginx
    
    echo ""
    echo "✅ CORRECTION APPLIQUÉE AVEC SUCCÈS!"
    echo ""
    echo "🎯 Améliorations apportées :"
    echo "   ✅ Gestion d'erreurs détaillée (400, 401, 403, 404, 413, 422, 500)"
    echo "   ✅ Messages d'erreur français explicites"
    echo "   ✅ Logs détaillés dans la console navigateur"
    echo "   ✅ Permissions documents vérifiées"
    echo "   ✅ Services redémarrés"
    echo ""
    echo "🧪 MAINTENANT TESTEZ :"
    echo "   1. Ouvrez la console du navigateur (F12 → Console)"
    echo "   2. Allez dans Maintenance → Modifier un enregistrement"
    echo "   3. Sélectionnez un fichier PDF/JPG (< 10MB)"
    echo "   4. Cliquez sur Télécharger"
    echo "   5. Regardez le message d'erreur EXACT dans l'interface"
    echo "   6. Vérifiez les logs détaillés dans la console"
    echo ""
    echo "📊 Si l'erreur persiste, vous aurez maintenant :"
    echo "   → Le code d'erreur HTTP exact (pas juste 500)"
    echo "   → Le message d'erreur précis du serveur"
    echo "   → Les détails du fichier dans les logs console"
    
else
    echo "❌ Erreur lors de la build frontend"
    exit 1
fi