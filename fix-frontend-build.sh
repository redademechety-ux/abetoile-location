#!/bin/bash

echo "🔧 Correction de l'erreur de build frontend..."

# Aller dans le répertoire frontend
cd /app/frontend

echo "📦 Reconstruction du frontend..."
yarn build

if [ $? -eq 0 ]; then
    echo "✅ Build frontend réussie!"
    
    echo "🔄 Redémarrage des services..."
    sudo supervisorctl restart frontend
    sudo supervisorctl restart backend
    
    echo "✅ Application mise à jour avec succès!"
    echo ""
    echo "🎉 Nouvelles fonctionnalités disponibles :"
    echo "   - Dashboard : CA mois/année"
    echo "   - Maintenance : Menu + gestion complète"
    echo "   - Type VAN : Disponible pour véhicules"
    
else
    echo "❌ Erreur lors de la build frontend"
    exit 1
fi