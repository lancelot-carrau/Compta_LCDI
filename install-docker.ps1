# 🐳 Script d'Installation Docker Desktop pour Windows
# Usage: .\install-docker.ps1

Write-Host "🐳 === INSTALLATION DOCKER DESKTOP ===" -ForegroundColor Cyan
Write-Host ""

# Vérifier si Docker est déjà installé
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "✅ Docker est déjà installé !" -ForegroundColor Green
    docker --version
    Write-Host ""
    Write-Host "🚀 Vous pouvez maintenant utiliser:" -ForegroundColor Yellow
    Write-Host "  .\docker-run.ps1 build" -ForegroundColor White
    Write-Host "  .\docker-run.ps1 start" -ForegroundColor White
    exit 0
}

Write-Host "📥 Docker Desktop n'est pas installé. Installation en cours..." -ForegroundColor Yellow
Write-Host ""

# Vérifier les prérequis système
$osVersion = [System.Environment]::OSVersion.Version
if ($osVersion.Major -lt 10) {
    Write-Host "❌ Windows 10 ou supérieur requis pour Docker Desktop" -ForegroundColor Red
    exit 1
}

# Vérifier si WSL2 est activé (requis pour Docker Desktop)
try {
    $wslStatus = wsl --list --verbose 2>$null
    if (-not $wslStatus) {
        Write-Host "⚠️ WSL2 n'est pas configuré. Configuration automatique..." -ForegroundColor Yellow
        
        # Activer WSL
        dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
        dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
        
        Write-Host "⚠️ Redémarrage requis pour activer WSL2" -ForegroundColor Yellow
        Write-Host "Après redémarrage, exécutez à nouveau ce script" -ForegroundColor Yellow
        
        $restart = Read-Host "Redémarrer maintenant ? (y/N)"
        if ($restart -eq 'y' -or $restart -eq 'Y') {
            Restart-Computer
        }
        exit 0
    }
} catch {
    Write-Host "⚠️ Impossible de vérifier WSL2. Continuons..." -ForegroundColor Yellow
}

# URL de téléchargement Docker Desktop
$dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$installerPath = "$env:TEMP\DockerDesktopInstaller.exe"

try {
    # Télécharger Docker Desktop
    Write-Host "📥 Téléchargement de Docker Desktop..." -ForegroundColor Blue
    Invoke-WebRequest -Uri $dockerUrl -OutFile $installerPath -UseBasicParsing
    
    Write-Host "✅ Téléchargement terminé" -ForegroundColor Green
    
    # Lancer l'installation
    Write-Host "🚀 Lancement de l'installation Docker Desktop..." -ForegroundColor Blue
    Write-Host "⚠️ L'installation peut prendre plusieurs minutes" -ForegroundColor Yellow
    
    Start-Process -FilePath $installerPath -ArgumentList "install", "--quiet" -Wait
    
    # Nettoyer le fichier d'installation
    Remove-Item $installerPath -Force
    
    Write-Host "✅ Installation terminée !" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Étapes suivantes :" -ForegroundColor Cyan
    Write-Host "1. Redémarrez votre ordinateur" -ForegroundColor White
    Write-Host "2. Lancez Docker Desktop depuis le menu Démarrer" -ForegroundColor White
    Write-Host "3. Attendez que Docker soit complètement démarré" -ForegroundColor White
    Write-Host "4. Exécutez: .\docker-run.ps1 build" -ForegroundColor White
    Write-Host ""
    
    $restart = Read-Host "Redémarrer maintenant ? (y/N)"
    if ($restart -eq 'y' -or $restart -eq 'Y') {
        Restart-Computer
    }
    
} catch {
    Write-Host "❌ Erreur lors de l'installation : $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Installation manuelle :" -ForegroundColor Yellow
    Write-Host "1. Allez sur https://www.docker.com/products/docker-desktop" -ForegroundColor White
    Write-Host "2. Téléchargez Docker Desktop pour Windows" -ForegroundColor White
    Write-Host "3. Exécutez l'installateur" -ForegroundColor White
    Write-Host "4. Redémarrez votre ordinateur" -ForegroundColor White
}

Write-Host ""
Write-Host "📚 Documentation complète : DOCKER.md" -ForegroundColor Cyan
