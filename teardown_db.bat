@echo off
REM JARVIS Database Teardown Script (Windows)
REM This script cleans up the database when the program stops

echo ================================
echo JARVIS Database Teardown
echo ================================
echo.

REM Check if we're in the correct directory
if not exist "manage.py" (
    echo Error: manage.py not found. Please run this script from the back-end directory.
    pause
    exit /b 1
)

REM Remove database files
if exist "db.sqlite3" (
    echo Removing main database...
    del /f db.sqlite3
    echo [32m√ Main database removed[0m
) else (
    echo No main database found
)

REM Remove Celery databases
if exist "celery_broker.db" (
    echo Removing Celery broker database...
    del /f celery_broker.db
    echo [32m√ Celery broker database removed[0m
)

if exist "celery_results.db" (
    echo Removing Celery results database...
    del /f celery_results.db
    echo [32m√ Celery results database removed[0m
)

REM Remove migration files (keep __init__.py)
echo Cleaning up migrations...
for /r %%i in (migrations\*.py) do (
    if not "%%~nxi"=="__init__.py" del /f "%%i"
)
for /r %%i in (migrations\*.pyc) do del /f "%%i"
echo [32m√ Migrations cleaned[0m

REM Remove Python cache files
echo Cleaning up Python cache...
for /d /r %%i in (__pycache__) do (
    if exist "%%i" rmdir /s /q "%%i" 2>nul
)
for /r %%i in (*.pyc) do del /f "%%i" 2>nul
echo [32m√ Python cache cleaned[0m

REM Remove log files
if exist "agent.log" (
    echo Removing log files...
    del /f agent.log
    echo [32m√ Log files removed[0m
)

if exist "django.log" (
    del /f django.log
)

echo.
echo ================================
echo Database teardown complete!
echo ================================
echo.
pause