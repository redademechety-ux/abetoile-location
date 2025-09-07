#!/bin/bash
set -e

echo "🔧 TEST ET CORRECTION ENDPOINT REGISTER"
echo "======================================="

# 1. Test de l'endpoint correct
echo ""
echo "🧪 Test endpoint correct /api/auth/register..."
RESPONSE=$(curl -s -X POST "http://127.0.0.1:8010/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "email": "test@example.com", 
    "password": "Test123!",
    "full_name": "Test User"
  }' 2>/dev/null)

echo "Réponse de l'API:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# 2. Vérifier les endpoints disponibles
echo ""
echo "🔍 Endpoints disponibles:"
curl -s "http://127.0.0.1:8010/api/docs" >/dev/null && echo "✅ Documentation API accessible" || echo "❌ Documentation API inaccessible"

# 3. Test des autres endpoints d'authentification
echo ""
echo "🔐 Test endpoints d'authentification:"
LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://127.0.0.1:8010/api/auth/login" -H "Content-Type: application/json" -d '{}' 2>/dev/null)
echo "  /api/auth/login: $LOGIN_STATUS"

# 4. Lister tous les endpoints disponibles via OpenAPI
echo ""
echo "📋 Tous les endpoints disponibles:"
curl -s "http://127.0.0.1:8010/openapi.json" 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    paths = data.get('paths', {})
    for path, methods in paths.items():
        for method, info in methods.items():
            print(f'  {method.upper()} {path} - {info.get(\"summary\", \"No description\")}')
except:
    print('Erreur lors de la lecture des endpoints')
" 2>/dev/null || echo "Impossible de lister les endpoints"

echo ""
echo "✅ DIAGNOSTIC TERMINÉ"
echo ""
echo "🎯 SOLUTION: Utilisez /api/auth/register au lieu de /api/register"