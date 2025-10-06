#!/bin/bash

echo "🔧 CORRECTION: Ajout du bouton d'upload - Serveur Production"

# Chemins corrects pour votre serveur
APP_ROOT="/var/www/abetoile-location"
FRONTEND_DIR="$APP_ROOT/frontend"

echo "📁 Vérification de la structure du serveur..."
if [ ! -d "$APP_ROOT" ]; then
    echo "❌ Répertoire $APP_ROOT introuvable"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Répertoire $FRONTEND_DIR introuvable"
    exit 1
fi

cd "$FRONTEND_DIR"

if [ ! -f "package.json" ]; then
    echo "❌ Fichier package.json introuvable dans $FRONTEND_DIR"
    ls -la
    exit 1
fi

echo "📦 Reconstruction du frontend avec le bouton d'upload..."
echo "   Répertoire: $(pwd)"

yarn build

if [ $? -eq 0 ]; then
    echo "✅ Build frontend réussie!"
    
    echo "🔄 Redémarrage des services..."
    sudo supervisorctl restart frontend 2>/dev/null || sudo systemctl restart nginx
    
    echo "✅ Bouton d'upload ajouté avec succès!"
    echo ""
    echo "🎯 Nouveau comportement :"
    echo "   1. Sélectionnez un fichier → ✅ Le fichier est validé"
    echo "   2. Une zone verte apparaît → ✅ Avec les détails du fichier"  
    echo "   3. Bouton 'Télécharger' visible → ✅ Cliquez pour uploader"
    echo "   4. Upload en cours → ✅ Bouton devient 'Upload...'"
    echo "   5. Succès → ✅ Document ajouté à la liste"
    echo ""
    echo "🧪 Test maintenant :"
    echo "   → Maintenance → Modifier un enregistrement → Documents"
    echo "   → Le bouton d'upload apparaît après sélection du fichier"
    
else
    echo "❌ Erreur lors de la build frontend"
    exit 1
fi