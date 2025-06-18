# Script de Construction d'Executable LCDI
# Usage: .\build-executable-fixed.ps1

Write-Host "=== CONSTRUCTION EXECUTABLE LCDI ===" -ForegroundColor Cyan
Write-Host ""

# Verifier que PyInstaller est installe
try {
    $pyinstallerVersion = python -m PyInstaller --version 2>$null
    Write-Host "PyInstaller detecte: $pyinstallerVersion" -ForegroundColor Green
} catch {
    Write-Host "PyInstaller non trouve. Installation en cours..." -ForegroundColor Red
    pip install pyinstaller
}

Write-Host ""
Write-Host "Verification des fichiers requis..." -ForegroundColor Blue

# Verifier les fichiers necessaires
$requiredFiles = @(
    "app_executable.py",
    "LCDI-Compta.spec",
    "templates/index.html",
    "templates/success.html"
)

$allPresent = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  $file" -ForegroundColor Green
    } else {
        Write-Host "  $file (MANQUANT)" -ForegroundColor Red
        $allPresent = $false
    }
}

if (-not $allPresent) {
    Write-Host "Erreur: Certains fichiers requis sont manquants" -ForegroundColor Red
    exit 1
}

Write-Host "Tous les fichiers requis sont presents" -ForegroundColor Green
Write-Host ""

# Nettoyer les anciens builds
Write-Host "Nettoyage des anciens builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "__pycache__") { Remove-Item -Recurse -Force "__pycache__" }

Write-Host "Nettoyage termine" -ForegroundColor Green
Write-Host ""

# Construction de l'executable
Write-Host "Construction de l'executable..." -ForegroundColor Blue
Write-Host "Cela peut prendre plusieurs minutes..." -ForegroundColor Yellow
Write-Host ""

try {
    # Utiliser le fichier .spec pour plus de controle
    python -m PyInstaller LCDI-Compta.spec
    
    if (Test-Path "dist/LCDI-Compta.exe") {
        $fileSize = (Get-Item "dist/LCDI-Compta.exe").Length / 1MB
        Write-Host ""
        Write-Host "Construction reussie!" -ForegroundColor Green
        Write-Host "Fichier cree: dist/LCDI-Compta.exe" -ForegroundColor Cyan
        Write-Host "Taille: $([math]::Round($fileSize, 1)) MB" -ForegroundColor Cyan
        Write-Host ""
        
        # Test rapide de l'executable
        Write-Host "Test de l'executable..." -ForegroundColor Blue
        $testProcess = Start-Process -FilePath "dist/LCDI-Compta.exe" -PassThru -WindowStyle Hidden
        Start-Sleep 3
        
        if (-not $testProcess.HasExited) {
            Stop-Process -Id $testProcess.Id -Force
            Write-Host "L'executable semble fonctionner" -ForegroundColor Green
        } else {
            Write-Host "L'executable s'est ferme rapidement" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Instructions d'utilisation:" -ForegroundColor Cyan
        Write-Host "1. Copiez le fichier dist/LCDI-Compta.exe" -ForegroundColor White
        Write-Host "2. Envoyez-le a vos utilisateurs" -ForegroundColor White
        Write-Host "3. Double-cliquez pour lancer l'application" -ForegroundColor White
        Write-Host "4. L'interface web s'ouvrira automatiquement" -ForegroundColor White
        Write-Host ""
        
        $openFolder = Read-Host "Ouvrir le dossier de destination? (y/N)"
        if ($openFolder -eq 'y' -or $openFolder -eq 'Y') {
            Invoke-Item "dist"
        }
        
    } else {
        Write-Host "Echec de la construction" -ForegroundColor Red
        Write-Host "Verifiez les logs ci-dessus pour plus de details" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "Erreur lors de la construction: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Processus termine" -ForegroundColor Cyan
