@echo off
echo ========================================
echo    LCDI - Generateur de Facturation
echo ========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installé ou n'est pas dans le PATH
    echo Veuillez installer Python depuis https://python.org
    pause
    exit /b 1
)

REM Vérifier si pip est disponible
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: pip n'est pas disponible
    pause
    exit /b 1
)

echo Installation des dépendances...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERREUR: Impossible d'installer les dépendances
    pause
    exit /b 1
)

echo.
echo Démarrage de l'application...
echo.
echo L'application sera accessible à: http://localhost:5000
echo.
echo Appuyez sur Ctrl+C pour arrêter l'application
echo.

python app.py

pause
