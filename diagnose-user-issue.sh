#!/bin/bash

echo "🔍 DIAGNOSTIC - Problème création utilisateur Abetoile Location"
echo "==============================================================="

# 1. Vérifier le statut des services
echo ""
echo "📊 STATUS DES SERVICES:"
echo "  Backend: $(systemctl is-active abetoile-location-backend)"
echo "  MongoDB: $(systemctl is-active mongod)"
echo "  Nginx: $(systemctl is-active nginx)"

# 2. Vérifier les logs du backend (dernières erreurs)
echo ""
echo "🔍 LOGS BACKEND (dernières 20 lignes):"
echo "---------------------------------------"
journalctl -u abetoile-location-backend --lines=20 --no-pager

# 3. Vérifier la connectivité MongoDB
echo ""
echo "🗄️ TEST CONNEXION MONGODB:"
echo "----------------------------"
if mongosh --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; then
    echo "✅ MongoDB accessible"
else
    echo "❌ MongoDB non accessible"
fi

# 4. Vérifier les utilisateurs existants dans la base
echo ""
echo "👤 UTILISATEURS EXISTANTS:"
echo "-------------------------"
mongosh abetoile_location_prod --eval "
try {
    print('Collections disponibles:');
    db.getCollectionNames().forEach(function(collection) {
        print('  - ' + collection);
    });
    
    print('\\nNombre d\\'utilisateurs dans la base:');
    if (db.users) {
        var userCount = db.users.countDocuments();
        print('  Utilisateurs: ' + userCount);
        
        if (userCount > 0) {
            print('\\nUtilisateurs existants (sans mots de passe):');
            db.users.find({}, {password: 0, hashed_password: 0}).forEach(function(user) {
                print('  - Username: ' + user.username + ', Email: ' + (user.email || 'N/A') + ', ID: ' + user.id);
            });
        }
    } else {
        print('  Collection users n\\'existe pas encore');
    }
} catch(e) {
    print('Erreur: ' + e);
}" --quiet 2>/dev/null || echo "❌ Erreur accès base de données"

# 5. Test API backend
echo ""
echo "🌐 TEST API BACKEND:"
echo "-------------------"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8003/api/ 2>/dev/null)
echo "  Status API: $BACKEND_STATUS"

if [ "$BACKEND_STATUS" = "200" ]; then
    # Test endpoint docs
    DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8003/api/docs 2>/dev/null)
    echo "  Status Docs: $DOCS_STATUS"
    
    # Test endpoint register (doit retourner 405 ou 422, pas 500)
    REGISTER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8003/api/register 2>/dev/null)
    echo "  Status Register (GET): $REGISTER_STATUS"
else
    echo "❌ Backend API non accessible"
fi

# 6. Vérifier les permissions des fichiers
echo ""
echo "🔒 PERMISSIONS FICHIERS:"
echo "------------------------"
echo "Backend directory:"
ls -la /var/www/abetoile-location/backend/ | head -5

echo ""
echo "Database files:"
ls -la /var/lib/mongodb/ 2>/dev/null | head -3 || echo "Répertoire MongoDB non accessible"

# 7. Test de création d'utilisateur via API
echo ""
echo "🧪 TEST CRÉATION UTILISATEUR VIA API:"
echo "-------------------------------------"
TEST_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8003/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_diagnostic",
    "password": "Test123!",
    "email": "test@example.com"
  }' 2>/dev/null)

echo "Réponse de l'API:"
echo "$TEST_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TEST_RESPONSE"

echo ""
echo "==============================================================="
echo "🏁 DIAGNOSTIC TERMINÉ"
echo "==============================================================="