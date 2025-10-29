@echo off
echo ========================================
echo   AI Personal Journal - Django Server
echo ========================================
echo.

echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo.
echo Verification de la configuration Django...
python manage.py check

echo.
echo Demarrage du serveur de developpement...
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


