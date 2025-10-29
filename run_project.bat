@echo off
title AI Personal Journal - Django Server
color 0A

echo.
echo ========================================
echo   AI Personal Journal - Django Server
echo ========================================
echo.

echo [1/3] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo.
echo [2/3] Verification de la configuration...
python manage.py check
if %errorlevel% neq 0 (
    echo.
    echo ERREUR: Configuration Django invalide
    echo Verifiez les erreurs ci-dessus
    pause
    exit /b 1
)

echo.
echo [3/3] Demarrage du serveur...
echo.
echo ========================================
echo   SERVEUR DISPONIBLE A:
echo   http://127.0.0.1:8000/
echo   http://localhost:8000/
echo ========================================
echo.
echo Comptes disponibles:
echo - Admin: admin@journal.com / admin123
echo - Interface admin: http://127.0.0.1:8000/admin/
echo.
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.

python manage.py runserver 127.0.0.1:8000

