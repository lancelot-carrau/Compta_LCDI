@echo off
echo ========================================
echo    COMPILATION LCDI APP - PyInstaller
echo ========================================
echo.

echo Nettoyage des anciennes compilations...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "LCDI_Comptabilite.exe" del "LCDI_Comptabilite.exe"

echo.
echo Compilation avec PyInstaller (mode verbose)...
echo.

C:/Users/Malo/AppData/Local/Programs/Python/Python313/python.exe -m PyInstaller ^
    --log-level=DEBUG ^
    --clean ^
    --noconfirm ^
    lcdi_app.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo    COMPILATION REUSSIE !
    echo ========================================
    echo.
    echo L'executable se trouve dans: dist\LCDI_Comptabilite\
    echo.
    echo Fichiers inclus:
    dir /b "dist\LCDI_Comptabilite\"
    echo.
    echo Pour tester l'executable:
    echo cd dist\LCDI_Comptabilite
    echo LCDI_Comptabilite.exe
    echo.
) else (
    echo.
    echo ========================================
    echo    ERREUR DE COMPILATION !
    echo ========================================
    echo.
    echo Consultez les logs ci-dessus pour plus de details.
    echo.
)

pause
