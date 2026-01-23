@echo off
REM JARVIS Database Setup Script (Windows)
REM This script initializes the Django database and runs migrations

echo ================================
echo JARVIS Database Setup
echo ================================
echo.

REM Check if we're in the correct directory
if not exist "manage.py" (
    echo Error: manage.py not found. Please run this script from the back-end directory.
    pause
    exit /b 1
)

REM Remove existing database if it exists
if exist "db.sqlite3" (
    echo Removing existing database...
    del /f db.sqlite3
    echo Database removed successfully.
)

REM Remove existing Celery databases if they exist
if exist "celery_broker.db" (
    echo Removing existing Celery broker database...
    del /f celery_broker.db
)

if exist "celery_results.db" (
    echo Removing existing Celery results database...
    del /f celery_results.db
)

REM Remove migration files (keep __init__.py)
echo Cleaning up old migrations...
for /r %%i in (migrations\*.py) do (
    if not "%%~nxi"=="__init__.py" del /f "%%i"
)
for /r %%i in (migrations\*.pyc) do del /f "%%i"
echo Migrations cleaned successfully.

REM Create fresh migrations
echo Creating fresh migrations...
python manage.py makemigrations
if errorlevel 1 (
    echo ERROR: Error creating migrations
    pause
    exit /b 1
)
echo Migrations created successfully.

REM Apply migrations
echo Applying migrations...
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Error applying migrations
    pause
    exit /b 1
)
echo Migrations applied successfully.

REM Create superuser (optional)
echo.
set /p create_superuser="Do you want to create a superuser? (y/n): "
if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
)

REM Setup periodic tasks for Celery
echo Setting up periodic tasks...
python manage.py setup_periodic_tasks
if errorlevel 1 (
    echo WARNING: Could not setup periodic tasks automatically
    echo You can set them up manually in Django admin
) else (
    echo Periodic tasks configured successfully.
)

echo.
echo ================================
echo Database setup complete!
echo ================================
echo.
echo Next steps:
echo 1. Run the server: python manage.py runserver
echo 2. (Optional) Start Redis: redis-server
echo 3. (Optional) Start Celery worker: celery -A jarvis_backend worker --loglevel=info
echo 4. (Optional) Start Celery beat: celery -A jarvis_backend beat --loglevel=info
echo.
pause