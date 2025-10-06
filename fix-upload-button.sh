#!/bin/bash

echo "🔧 CORRECTION: Ajout du bouton d'upload manquant dans Maintenance..."

# S'assurer qu'on est dans le bon répertoire
echo "📁 Vérification du répertoire de travail..."
if [ ! -d "/app" ]; then
    echo "❌ Répertoire /app introuvable"
    exit 1
fi

cd /app

if [ ! -d "/app/frontend" ]; then
    echo "❌ Répertoire /app/frontend introuvable"
    exit 1
fi

echo "📦 Reconstruction du frontend avec le bouton d'upload..."
cd /app/frontend

if [ ! -f "package.json" ]; then
    echo "❌ Fichier package.json introuvable dans /app/frontend"
    ls -la
    exit 1
fi

yarn build

if [ $? -eq 0 ]; then
    echo "✅ Build frontend réussie!"
    
    echo "🔄 Redémarrage des services..."
    sudo supervisorctl restart frontend
    
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