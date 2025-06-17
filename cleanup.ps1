@echo off
echo Nettoyage de l'application LCDI...

REM Supprimer les fichiers de test et debug
del /q analyze*.py 2>nul
del /q debug*.py 2>nul
del /q diagnostic*.py 2>nul
del /q test_*.py 2>nul
del /q verify_*.py 2>nul
del /q fix_*.py 2>nul
del /q generate*.py 2>nul
del /q compare*.py 2>nul
del /q check*.py 2>nul
del /q patch*.py 2>nul
del /q generer*.py 2>nul
del /q replace*.py 2>nul
del /q verifier*.py 2>nul

REM Supprimer des fichiers spécifiques
del /q analyser_references_multiples.py 2>nul
del /q docker-compose.yml 2>nul
del /q Dockerfile 2>nul
del /q .env.example 2>nul
del /q gitignore 2>nul

echo Nettoyage termine!
echo Fichiers conserves: app.py, requirements.txt, README.md, start.bat, templates/, output/
pause
