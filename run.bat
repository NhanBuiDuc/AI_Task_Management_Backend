@echo off
REM JARVIS Master Run Script (Windows)
REM Orchestrates database setup, API testing, and optional teardown

setlocal enabledelayedexpansion

echo ================================
echo JARVIS Development Environment
echo ================================
echo.

REM Check if we're in the correct directory
if not exist "manage.py" (
    echo Error: This script must be run from the back-end directory.
    echo Usage: cd back-end ^& run.bat
    pause
    exit /b 1
)

REM Parse command line arguments
set RUN_TESTS=yes
set RUN_UNIT_TESTS=yes
set SHOW_SCHEDULE=yes
set RUN_LLM_DEMO=yes
set RUN_AI_CHAT=yes
set AUTO_TEARDOWN=no
set KEEP_SERVER_RUNNING=no

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--no-tests" (
    set RUN_TESTS=no
    shift
    goto parse_args
)
if /i "%~1"=="--no-unit-tests" (
    set RUN_UNIT_TESTS=no
    shift
    goto parse_args
)
if /i "%~1"=="--no-schedule" (
    set SHOW_SCHEDULE=no
    shift
    goto parse_args
)
if /i "%~1"=="--no-llm" (
    set RUN_LLM_DEMO=no
    shift
    goto parse_args
)
if /i "%~1"=="--no-ai-chat" (
    set RUN_AI_CHAT=no
    shift
    goto parse_args
)
if /i "%~1"=="--auto-teardown" (
    set AUTO_TEARDOWN=yes
    shift
    goto parse_args
)
if /i "%~1"=="--keep-server" (
    set KEEP_SERVER_RUNNING=yes
    shift
    goto parse_args
)
if /i "%~1"=="--help" (
    echo Usage: run.bat [OPTIONS]
    echo.
    echo Options:
    echo   --no-tests         Skip API testing
    echo   --no-unit-tests    Skip Django unit tests (scheduler, models, etc.)
    echo   --no-schedule      Skip schedule visualization
    echo   --no-llm           Skip LLM task extraction demo
    echo   --no-ai-chat       Skip AI chat endpoint tests
    echo   --auto-teardown    Automatically tear down database on exit
    echo   --keep-server      Keep Django server running after tests
    echo   --help             Show this help message
    echo.
    pause
    exit /b 0
)
echo Unknown option: %~1
echo Use --help for usage information
pause
exit /b 1

:args_done

REM Step 1: Setup Database
echo Step 1: Setting up database...
call setup_db.bat
if errorlevel 1 (
    echo ERROR: Database setup failed
    pause
    exit /b 1
)
echo Database setup completed successfully!
echo.

REM Step 2: Start Django Server
echo Step 2: Starting Django server...

REM Check if port 8000 is already in use
netstat -ano | findstr :8000 | findstr LISTENING >nul 2>&1
if %errorlevel%==0 (
    echo WARNING: Port 8000 is already in use. Using existing server.
    set DJANGO_STARTED=no
) else (
    echo Starting server in background...
    start /b python manage.py runserver 0.0.0.0:8000 > django.log 2>&1
    set DJANGO_STARTED=yes

    REM Wait for server to be ready
    echo Waiting for server to be ready...
    timeout /t 3 /nobreak >nul

    REM Check if server started by looking at django.log
    findstr /C:"Starting development server" django.log >nul 2>&1
    if errorlevel 1 (
        REM Wait a bit more and try again
        timeout /t 5 /nobreak >nul
        findstr /C:"Starting development server" django.log >nul 2>&1
        if errorlevel 1 (
            echo ERROR: Failed to start Django server
            echo ERROR: Check django.log for errors
            type django.log
            pause
            exit /b 1
        )
    )
    echo SUCCESS: Server is ready on http://localhost:8000
)
echo.

REM Step 3: Run API Tests
if /i "%RUN_TESTS%"=="yes" (
    echo Step 3: Running API tests...
    timeout /t 1 /nobreak >nul
    python test_apis.py
    set TEST_EXIT_CODE=!errorlevel!
    echo.
) else (
    set TEST_EXIT_CODE=0
)

REM Step 4: Run Django Unit Tests (Scheduler, Models, etc.)
if /i "%RUN_UNIT_TESTS%"=="yes" (
    echo Step 4: Running Django unit tests...
    echo.
    echo --- Scheduler Tests ---
    python manage.py test tasks_api.tests_scheduler --verbosity=1
    set UNIT_TEST_EXIT_CODE=!errorlevel!

    if !UNIT_TEST_EXIT_CODE! neq 0 (
        echo.
        echo WARNING: Some unit tests failed!
        set TEST_EXIT_CODE=!UNIT_TEST_EXIT_CODE!
    ) else (
        echo.
        echo SUCCESS: All unit tests passed!
    )
    echo.
) else (
    echo Step 4: Skipping unit tests...
    echo.
)

REM Step 5: Show Schedule Visualization
if /i "%SHOW_SCHEDULE%"=="yes" (
    echo Step 5: Displaying schedule visualization...
    echo.
    python visualize_schedule.py --simple --days 7
    echo.
) else (
    echo Step 5: Skipping schedule visualization...
    echo.
)

REM Step 6: LLM Task Extraction + Scheduling Demo
if /i "%RUN_LLM_DEMO%"=="yes" (
    echo Step 6: Running LLM Task Extraction + Scheduling Demo...
    echo.
    echo This demo takes natural language input, extracts tasks using LLM,
    echo and generates an optimized schedule.
    echo.

    REM Check if Ollama is running
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if errorlevel 1 (
        echo WARNING: Ollama is not running. Skipping LLM demo.
        echo To run this demo, start Ollama with: ollama serve
        echo.
    ) else (
        python test_llm_to_schedule.py
        echo.
    )
) else (
    echo Step 6: Skipping LLM demo...
    echo.
)

REM Step 7: AI Chat Endpoint Tests
if /i "%RUN_AI_CHAT%"=="yes" (
    echo Step 7: Running AI Chat endpoint tests...
    echo.
    python test_ai_chat.py
    set AI_CHAT_EXIT_CODE=!errorlevel!
    if !AI_CHAT_EXIT_CODE! neq 0 (
        echo.
        echo WARNING: Some AI chat tests failed!
    )
    echo.
) else (
    echo Step 7: Skipping AI chat tests...
    echo.
)

REM Step 8: Keep server running or stop (renumbered)
if /i "%KEEP_SERVER_RUNNING%"=="yes" (
    if /i "%DJANGO_STARTED%"=="yes" (
        echo.
        echo ================================
        echo Server is running!
        echo ================================
        echo.
        echo Access the application at:
        echo   * API: http://localhost:8000/api/
        echo   * Admin: http://localhost:8000/admin/
        echo.
        echo Press Ctrl+C to stop the server
        echo.

        REM Keep script running
        pause
    )
) else (
    if /i "%DJANGO_STARTED%"=="yes" (
        echo Stopping Django server...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
            taskkill /F /PID %%a >nul 2>&1
        )
        echo Django server stopped successfully.
    )
)

REM Step 9: Database teardown
if /i "%AUTO_TEARDOWN%"=="yes" (
    echo.
    echo Running database teardown...
    call teardown_db.bat
) else (
    echo.
    set /p teardown_choice="Do you want to tear down the database? (y/n): "
    if /i "!teardown_choice!"=="y" (
        call teardown_db.bat
    ) else (
        echo Database preserved. Run 'teardown_db.bat' manually to clean up.
    )
)

echo.
echo Done!
pause
exit /b %TEST_EXIT_CODE%