@echo off
setlocal

set PYTHON_CMD=python
if exist .venv\Scripts\python.exe set PYTHON_CMD=.venv\Scripts\python.exe

if exist assets\icon.ico (
    "%PYTHON_CMD%" -m PyInstaller --noconfirm --clean --onefile --windowed --name URLift --icon assets\icon.ico --add-data "Logo.png;." --collect-data imageio_ffmpeg main.py
) else (
    echo assets\icon.ico not found. Building URLift without a custom icon.
    "%PYTHON_CMD%" -m PyInstaller --noconfirm --clean --onefile --windowed --name URLift --add-data "Logo.png;." --collect-data imageio_ffmpeg main.py
)
