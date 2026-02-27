@echo off
REM EcoWipe - Run as Administrator
REM This batch file ensures the application runs with proper admin privileges

setlocal enabledelayedexpansion

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ============================================
    echo  EcoWipe - Administrator Elevation Required
    echo ============================================
    echo.
    echo This application requires Administrator privileges to detect
    echo and manage disk devices. Please grant admin access.
    echo.
    echo Attempting to elevate privileges...
    echo.
    
    REM Re-run the batch file as administrator
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

echo.
echo ============================================
echo  EcoWipe - Disk Sanitization Tool
echo ============================================
echo.
echo Application is running with Administrator privileges.
echo.

REM Find and run the EcoWipe executable
if exist "EcoWipe.exe" (
    start "" "EcoWipe.exe"
    exit /b 0
) else (
    echo ERROR: EcoWipe.exe not found in current directory!
    echo Please ensure EcoWipe.exe is in the same folder as this script.
    pause
    exit /b 1
)
