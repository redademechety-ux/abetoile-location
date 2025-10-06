#!/bin/bash

echo "🔧 Correction du problème d'upload de fichiers maintenance..."

# Vérifier que le dossier documents existe avec les bonnes permissions
echo "📁 Vérification du dossier documents..."
sudo mkdir -p /app/documents
sudo chmod 755 /app/documents
sudo chown -R root:root /app/documents

echo "📦 Reconstruction du frontend avec logs d'upload améliorés..."
cd /app/frontend
yarn build

if [ $? -eq 0 ]; then
    echo "✅ Build frontend réussie!"
    
    echo "🔄 Redémarrage des services..."
    sudo supervisorctl restart backend
    sudo supervisorctl restart frontend
    
    echo "✅ Correction appliquée avec succès!"
    echo ""
    echo "🔍 Améliorations apportées :"
    echo "   - Logs détaillés dans la console du navigateur"
    echo "   - Messages d'erreur plus précis"
    echo "   - Interface utilisateur améliorée"
    echo "   - Permissions fichiers vérifiées"
    
    echo ""
    echo "🧪 Pour tester :"
    echo "   1. Aller dans Maintenance → Créer un enregistrement"
    echo "   2. Sauvegarder l'enregistrement"
    echo "   3. Essayer d'ajouter un fichier PDF ou JPG"
    echo "   4. Ouvrir la console du navigateur (F12) pour voir les logs"
    
else
    echo "❌ Erreur lors de la build frontend"
    exit 1
fi