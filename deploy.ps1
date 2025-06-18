# 🚀 Script de déploiement PowerShell - LCDI App
# Usage: .\deploy.ps1 [heroku|render|railway]

param(
    [string]$Platform = "heroku"
)

Write-Host "🚀 === DÉPLOIEMENT LCDI APP ===" -ForegroundColor Green
Write-Host ""

# Vérifier si Git est initialisé
if (-not (Test-Path ".git")) {
    Write-Host "❌ Erreur: Repository Git non initialisé" -ForegroundColor Red
    Write-Host "💡 Exécutez: git init && git remote add origin YOUR_REPO_URL" -ForegroundColor Yellow
    exit 1
}

# Vérifier les fichiers nécessaires
Write-Host "🔍 Vérification des fichiers..." -ForegroundColor Cyan
$requiredFiles = @("app.py", "requirements.txt", "Procfile", "runtime.txt")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Fichier manquant: $file" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ Tous les fichiers requis sont présents" -ForegroundColor Green

# Générer une clé secrète si nécessaire
if (-not (Test-Path ".env")) {
    Write-Host "🔐 Génération d'une clé secrète..." -ForegroundColor Cyan
    $secretKey = -join ((1..64) | ForEach-Object {'{0:X}' -f (Get-Random -Max 16)})
    @"
SECRET_KEY=$secretKey
FLASK_ENV=production
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Fichier .env créé" -ForegroundColor Green
}

# Commit des changements
Write-Host "📝 Commit des changements..." -ForegroundColor Cyan
git add .
git status
$commitMessage = Read-Host "📋 Description du commit"
try {
    git commit -m $commitMessage
} catch {
    Write-Host "⚠️ Aucun changement à commiter" -ForegroundColor Yellow
}

# Push vers GitHub
Write-Host "⬆️ Push vers GitHub..." -ForegroundColor Cyan
git push origin main

# Choix de la plateforme
switch ($Platform.ToLower()) {
    "heroku" {
        Write-Host "🔥 Déploiement sur Heroku..." -ForegroundColor Magenta
        
        # Vérifier Heroku CLI
        if (-not (Get-Command heroku -ErrorAction SilentlyContinue)) {
            Write-Host "❌ Heroku CLI non installé" -ForegroundColor Red
            Write-Host "💡 Installez: https://devcenter.heroku.com/articles/heroku-cli" -ForegroundColor Yellow
            exit 1
        }

        # Créer l'app si elle n'existe pas
        $appName = Read-Host "📱 Nom de l'app Heroku"
        try {
            heroku create $appName 2>$null
        } catch {
            Write-Host "⚠️ App existe déjà" -ForegroundColor Yellow
        }

        # Configurer les variables d'environnement
        Write-Host "🔧 Configuration des variables..." -ForegroundColor Cyan
        $secretKey = (Get-Content .env | Where-Object { $_ -match "SECRET_KEY=" }).Split("=")[1]
        heroku config:set SECRET_KEY="$secretKey" -a $appName
        heroku config:set FLASK_ENV="production" -a $appName
        heroku config:set MAX_CONTENT_LENGTH="50000000" -a $appName

        # Déployer
        git push heroku main
        
        Write-Host "🎉 Déploiement terminé!" -ForegroundColor Green
        Write-Host "🌐 URL: https://$appName.herokuapp.com" -ForegroundColor Cyan
        
        # Ouvrir l'app
        $openApp = Read-Host "🚀 Ouvrir l'application? (y/N)"
        if ($openApp -eq "y" -or $openApp -eq "Y") {
            heroku open -a $appName
        }
    }
    
    "render" {
        Write-Host "🎨 Instructions pour Render:" -ForegroundColor Magenta
        Write-Host "1. Allez sur https://render.com" -ForegroundColor White
        Write-Host "2. Connectez votre repository GitHub" -ForegroundColor White
        Write-Host "3. Choisissez 'Web Service'" -ForegroundColor White
        Write-Host "4. Configuration:" -ForegroundColor White
        Write-Host "   - Build Command: pip install -r requirements.txt" -ForegroundColor Gray
        Write-Host "   - Start Command: python app.py" -ForegroundColor Gray
        Write-Host "   - Variables d'environnement:" -ForegroundColor Gray
        $secretKey = (Get-Content .env | Where-Object { $_ -match "SECRET_KEY=" }).Split("=")[1]
        Write-Host "     SECRET_KEY=$secretKey" -ForegroundColor Gray
        Write-Host "     FLASK_ENV=production" -ForegroundColor Gray
    }
    
    "railway" {
        Write-Host "🚂 Déploiement sur Railway..." -ForegroundColor Magenta
        
        if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
            Write-Host "❌ Railway CLI non installé" -ForegroundColor Red
            Write-Host "💡 Installez: npm install -g @railway/cli" -ForegroundColor Yellow
            exit 1
        }

        railway login
        railway init
        railway up
        
        Write-Host "🎉 Déploiement terminé!" -ForegroundColor Green
    }
    
    default {
        Write-Host "❌ Plateforme non supportée: $Platform" -ForegroundColor Red
        Write-Host "💡 Plateformes supportées: heroku, render, railway" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "✅ === DÉPLOIEMENT TERMINÉ ===" -ForegroundColor Green
Write-Host "📚 Consultez DEPLOY.md pour plus d'informations" -ForegroundColor Cyan
