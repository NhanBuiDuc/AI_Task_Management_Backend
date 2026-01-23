@echo off
REM Schedule Visualizer - Displays tasks and calendar view
REM Usage: visualize_schedule.bat [OPTIONS]

setlocal enabledelayedexpansion

REM Enable ANSI colors in Windows terminal
for /f "tokens=2 delims=:" %%a in ('ver') do set "ver=%%a"

REM Check if we're in the correct directory
if not exist "manage.py" (
    echo Error: This script must be run from the back-end directory.
    echo Usage: cd back-end ^& visualize_schedule.bat
    pause
    exit /b 1
)

REM Parse command line arguments
set DAYS=7
set USE_MOCK=
set SIMPLE_MODE=

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--days" (
    set DAYS=%~2
    shift
    shift
    goto parse_args
)
if /i "%~1"=="-d" (
    set DAYS=%~2
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--mock" (
    set USE_MOCK=--mock
    shift
    goto parse_args
)
if /i "%~1"=="-m" (
    set USE_MOCK=--mock
    shift
    goto parse_args
)
if /i "%~1"=="--simple" (
    set SIMPLE_MODE=--simple
    shift
    goto parse_args
)
if /i "%~1"=="-s" (
    set SIMPLE_MODE=--simple
    shift
    goto parse_args
)
if /i "%~1"=="--help" (
    echo.
    echo ===================================================
    echo   SCHEDULE VISUALIZER - Help
    echo ===================================================
    echo.
    echo Usage: visualize_schedule.bat [OPTIONS]
    echo.
    echo Options:
    echo   --days N, -d N     Number of days to display (default: 7)
    echo   --mock, -m         Use mock data instead of database
    echo   --simple, -s       Use simple ASCII output (better compatibility)
    echo   --help             Show this help message
    echo.
    echo Examples:
    echo   visualize_schedule.bat                    Show 7 days from database
    echo   visualize_schedule.bat --mock             Show 7 days with mock data
    echo   visualize_schedule.bat --days 14         Show 14 days
    echo   visualize_schedule.bat -d 7 -m -s        Simple view, mock data, 7 days
    echo.
    echo Output:
    echo   Left panel:  Task list with priorities, durations, and due dates
    echo   Right panel: Calendar view showing scheduled tasks by time slot
    echo.
    echo   Time Slots:
    echo     Morning   : 06:00 - 12:00 (180 min capacity)
    echo     Afternoon : 12:00 - 17:00 (150 min capacity)
    echo     Evening   : 17:00 - 22:00 (120 min capacity)
    echo.
    echo   Priority Colors:
    echo     Emergency : Red (highest)
    echo     Urgent    : Red
    echo     High      : Yellow
    echo     Medium    : Cyan
    echo     Low       : Gray (lowest)
    echo.
    pause
    exit /b 0
)
echo Unknown option: %~1
echo Use --help for usage information
pause
exit /b 1

:args_done

echo.
echo ===================================================
echo   SCHEDULE VISUALIZER
echo ===================================================
echo.
echo Configuration:
echo   Days to display: %DAYS%
echo   Data source: %USE_MOCK:--mock=Mock Data%
if "%USE_MOCK%"=="" echo   Data source: Database
echo   Output mode: %SIMPLE_MODE:--simple=Simple ASCII%
if "%SIMPLE_MODE%"=="" echo   Output mode: Full Color
echo.
echo ---------------------------------------------------
echo.

REM Run the Python visualization script
python visualize_schedule.py --days %DAYS% %USE_MOCK% %SIMPLE_MODE%

if errorlevel 1 (
    echo.
    echo ERROR: Visualization failed. Check the error message above.
    pause
    exit /b 1
)

echo.
pause
exit /b 0
