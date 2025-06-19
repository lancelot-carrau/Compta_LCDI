@echo off
echo ====================================
echo    LCDI Comptabilite - Demarrage
echo ====================================
echo.
echo Lancement de l'application...
echo L'application sera accessible sur : http://127.0.0.1:5000
echo.
echo IMPORTANT: Ne fermez pas cette fenetre tant que vous utilisez l'application !
echo           Pour arreter l'application, appuyez sur Ctrl+C
echo.
echo ====================================
echo.

cd /d "%~dp0dist\LCDI_Comptabilite"
LCDI_Comptabilite.exe

echo.
echo ====================================
echo L'application s'est arretee.
echo Appuyez sur une touche pour fermer...
echo ====================================
pause >nul
