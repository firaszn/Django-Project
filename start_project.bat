@echo off
echo ========================================
echo   AI Personal Journal - Django Project
echo ========================================
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Checking Django installation...
python manage.py check

echo.
echo Starting Django development server...
echo The server will be available at: http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver


