@echo off
setlocal

if exist assets\icon.ico (
    pyinstaller --onefile --windowed --name URLift --icon assets\icon.ico --add-data "Logo.png;." main.py
) else (
    echo assets\icon.ico not found. Building URLift without a custom icon.
    pyinstaller --onefile --windowed --name URLift --add-data "Logo.png;." main.py
)
