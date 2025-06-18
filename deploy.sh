#!/bin/bash

# 🚀 Script de déploiement automatique LCDI App
# Usage: ./deploy.sh [heroku|render|railway]

set -e

echo "🚀 === DÉPLOIEMENT LCDI APP ==="
echo ""

# Vérifier si Git est initialisé
if [ ! -d ".git" ]; then
    echo "❌ Erreur: Repository Git non initialisé"
    echo "💡 Exécutez: git init && git remote add origin YOUR_REPO_URL"
    exit 1
fi

# Vérifier les fichiers nécessaires
echo "🔍 Vérification des fichiers..."
required_files=("app.py" "requirements.txt" "Procfile" "runtime.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Fichier manquant: $file"
        exit 1
    fi
done
echo "✅ Tous les fichiers requis sont présents"

# Générer une clé secrète si nécessaire
if [ ! -f ".env" ]; then
    echo "🔐 Génération d'une clé secrète..."
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    echo "SECRET_KEY=$SECRET_KEY" > .env
    echo "FLASK_ENV=production" >> .env
    echo "✅ Fichier .env créé"
fi

# Commit des changements
echo "📝 Commit des changements..."
git add .
git status
read -p "📋 Description du commit: " commit_message
git commit -m "$commit_message" || echo "⚠️ Aucun changement à commiter"

# Push vers GitHub
echo "⬆️ Push vers GitHub..."
git push origin main

# Choix de la plateforme
PLATFORM=${1:-"heroku"}

case $PLATFORM in
    "heroku")
        echo "🔥 Déploiement sur Heroku..."
        
        # Vérifier Heroku CLI
        if ! command -v heroku &> /dev/null; then
            echo "❌ Heroku CLI non installé"
            echo "💡 Installez: https://devcenter.heroku.com/articles/heroku-cli"
            exit 1
        fi

        # Créer l'app si elle n'existe pas
        read -p "📱 Nom de l'app Heroku: " app_name
        heroku create $app_name 2>/dev/null || echo "⚠️ App existe déjà"

        # Configurer les variables d'environnement
        echo "🔧 Configuration des variables..."
        SECRET_KEY=$(grep SECRET_KEY .env | cut -d '=' -f2)
        heroku config:set SECRET_KEY="$SECRET_KEY" -a $app_name
        heroku config:set FLASK_ENV="production" -a $app_name
        heroku config:set MAX_CONTENT_LENGTH="50000000" -a $app_name

        # Déployer
        git push heroku main
        
        echo "🎉 Déploiement terminé!"
        echo "🌐 URL: https://$app_name.herokuapp.com"
        
        # Ouvrir l'app
        read -p "🚀 Ouvrir l'application? (y/N): " open_app
        if [ "$open_app" = "y" ] || [ "$open_app" = "Y" ]; then
            heroku open -a $app_name
        fi
        ;;
        
    "render")
        echo "🎨 Instructions pour Render:"
        echo "1. Allez sur https://render.com"
        echo "2. Connectez votre repository GitHub"
        echo "3. Choisissez 'Web Service'"
        echo "4. Configuration:"
        echo "   - Build Command: pip install -r requirements.txt"
        echo "   - Start Command: python app.py"
        echo "   - Variables d'environnement:"
        SECRET_KEY=$(grep SECRET_KEY .env | cut -d '=' -f2)
        echo "     SECRET_KEY=$SECRET_KEY"
        echo "     FLASK_ENV=production"
        ;;
        
    "railway")
        echo "🚂 Déploiement sur Railway..."
        
        if ! command -v railway &> /dev/null; then
            echo "❌ Railway CLI non installé"
            echo "💡 Installez: npm install -g @railway/cli"
            exit 1
        fi

        railway login
        railway init
        railway up
        
        echo "🎉 Déploiement terminé!"
        ;;
        
    *)
        echo "❌ Plateforme non supportée: $PLATFORM"
        echo "💡 Plateformes supportées: heroku, render, railway"
        exit 1
        ;;
esac

echo ""
echo "✅ === DÉPLOIEMENT TERMINÉ ==="
echo "📚 Consultez DEPLOY.md pour plus d'informations"
