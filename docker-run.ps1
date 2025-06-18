# 🐳 Script PowerShell de gestion Docker pour LCDI App
# Usage: .\docker-run.ps1 [build|start|stop|restart|logs|shell|status|cleanup|dev|help]

param(
    [string]$Command = "help"
)

$APP_NAME = "lcdi-compta-app"
$COMPOSE_FILE = "docker-compose.yml"

Write-Host "🐳 === GESTION DOCKER LCDI APP ===" -ForegroundColor Cyan
Write-Host ""

# Fonctions pour les messages colorés
function Write-Status($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success($Message) {
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning($Message) {
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error($Message) {
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Vérifier si Docker est installé
function Test-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker n'est pas installé. Installez Docker Desktop."
        exit 1
    }
    
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error "Docker Compose n'est pas installé."
        exit 1
    }
}

# Générer le fichier .env s'il n'existe pas
function Initialize-Environment {
    if (-not (Test-Path ".env")) {
        Write-Warning "Fichier .env manquant. Création depuis .env.example..."
        Copy-Item ".env.example" ".env"
        
        # Générer une clé secrète
        $secretKey = -join ((1..64) | ForEach-Object {'{0:X}' -f (Get-Random -Max 16)})
        (Get-Content ".env") -replace "your-super-secret-key-here-change-me-in-production", $secretKey | Set-Content ".env"
        
        Write-Success "Fichier .env créé avec une clé secrète générée"
        Write-Warning "Vérifiez et modifiez le fichier .env selon vos besoins"
    }
}

# Construire l'image Docker
function New-DockerImage {
    Write-Status "Construction de l'image Docker..."
    docker-compose build --no-cache
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Image construite avec succès"
    } else {
        Write-Error "Erreur lors de la construction"
        exit 1
    }
}

# Démarrer l'application
function Start-Application {
    Write-Status "Démarrage de l'application LCDI..."
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Application démarrée"
        Write-Status "Accès: http://localhost:5000"
        
        # Attendre que l'application soit prête
        Write-Status "Vérification de l'état de l'application..."
        Start-Sleep -Seconds 5
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Success "✅ Application accessible sur http://localhost:5000"
            }
        } catch {
            Write-Warning "⚠️ L'application met du temps à démarrer. Vérifiez les logs: .\docker-run.ps1 logs"
        }
    } else {
        Write-Error "Erreur lors du démarrage"
        exit 1
    }
}

# Arrêter l'application
function Stop-Application {
    Write-Status "Arrêt de l'application..."
    docker-compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Application arrêtée"
    }
}

# Redémarrer l'application
function Restart-Application {
    Write-Status "Redémarrage de l'application..."
    docker-compose restart
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Application redémarrée"
    }
}

# Afficher les logs
function Show-Logs {
    Write-Status "Affichage des logs (Ctrl+C pour quitter)..."
    docker-compose logs -f
}

# Ouvrir un shell dans le conteneur
function Open-Shell {
    Write-Status "Ouverture d'un shell dans le conteneur..."
    docker exec -it $APP_NAME /bin/bash
}

# Nettoyer les ressources Docker
function Invoke-Cleanup {
    Write-Status "Nettoyage des ressources Docker..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    Write-Success "Nettoyage terminé"
}

# Afficher le statut
function Show-Status {
    Write-Status "Statut des conteneurs:"
    docker-compose ps
    
    Write-Status "`nUtilisation des ressources:"
    try {
        docker stats --no-stream $APP_NAME
    } catch {
        Write-Warning "Conteneur non démarré"
    }
}

# Démarrage en mode développement
function Start-Development {
    Write-Status "Démarrage en mode développement avec rechargement automatique..."
    docker-compose up --build
}

# Menu principal
switch ($Command.ToLower()) {
    "build" {
        Test-Docker
        Initialize-Environment
        New-DockerImage
    }
    "start" {
        Test-Docker
        Initialize-Environment
        Start-Application
    }
    "stop" {
        Test-Docker
        Stop-Application
    }
    "restart" {
        Test-Docker
        Restart-Application
    }
    "logs" {
        Test-Docker
        Show-Logs
    }
    "shell" {
        Test-Docker
        Open-Shell
    }
    "status" {
        Test-Docker
        Show-Status
    }
    "cleanup" {
        Test-Docker
        Invoke-Cleanup
    }
    "dev" {
        Test-Docker
        Initialize-Environment
        Start-Development
    }
    default {
        Write-Host ""
        Write-Host "🐳 Commandes disponibles:" -ForegroundColor Cyan
        Write-Host "  .\docker-run.ps1 build     - Construire l'image Docker" -ForegroundColor White
        Write-Host "  .\docker-run.ps1 start     - Démarrer l'application en arrière-plan" -ForegroundColor White
        Write-Host "  .\docker-run.ps1 stop      - Arrêter l'application" -ForegroundColor White
        Write-Host "  .\docker-run.ps1 restart   - Redémarrer l'application" -ForegroundColor White
        Write-Host "  .\docker-run.ps1 logs      - Afficher les logs en temps réel" -ForegroundColor White
        Write-Host "  .\docker-run.ps1 shell     - Ouvrir un shell dans le conteneur" -ForegroundColor White
        Write-Host "  .\docker-run.ps1 status    - Afficher le statut et les ressources" -ForegroundColor White
        Write-Host "  .\docker-run.ps1 cleanup   - Nettoyer les ressources Docker" -ForegroundColor White
        Write-Host "  .\docker-run.ps1 dev       - Mode développement (premier plan)" -ForegroundColor White
        Write-Host "  .\docker-run.ps1 help      - Afficher cette aide" -ForegroundColor White
        Write-Host ""
        Write-Host "🚀 Démarrage rapide:" -ForegroundColor Green
        Write-Host "  .\docker-run.ps1 build; .\docker-run.ps1 start" -ForegroundColor Gray
        Write-Host ""
    }
}
