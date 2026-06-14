@echo off
setlocal

if /I "%~1"=="--check" goto check

if not exist dist\URLift.exe (
    echo dist\URLift.exe was not found. Run build.bat first.
    exit /b 1
)

where iscc >nul 2>nul
if errorlevel 1 (
    echo Inno Setup Compiler ^(iscc^) was not found on PATH.
    echo Install Inno Setup, then run build_installer.bat again.
    exit /b 1
)

iscc installer\URLift.iss
exit /b %errorlevel%

:check
if not exist installer\URLift.iss (
    echo installer\URLift.iss was not found.
    exit /b 1
)
if not exist assets\icon.ico (
    echo assets\icon.ico was not found.
    exit /b 1
)
echo Installer script files are present.
exit /b 0
