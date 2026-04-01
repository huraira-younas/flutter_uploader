@echo off
setlocal
cd /d "%~dp0"

echo Flutter Uploader - Windows Installer Build
echo.
echo Step 1: Building app binaries...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "installer\scripts\build_win.ps1"

echo.
echo Step 2: Creating installer EXE with Inno Setup...
echo.

where ISCC.exe >nul 2>&1 && (
    ISCC.exe installer\windows\FlutterUploader.iss
) || (
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows\FlutterUploader.iss
    ) else (
        echo.
        echo Inno Setup not found. Install it from https://jrsoftware.org/isinfo.php
        echo Then compile manually:
        echo   "C:\Program Files ^(x86^)\Inno Setup 6\ISCC.exe" installer\windows\FlutterUploader.iss
        echo.
        echo Binaries are ready in dist\
    )
)

if exist .venv (
    echo.
    echo Cleaning up build venv...
    rmdir /s /q .venv
)

echo.
echo Done! Installer: dist-installer\FlutterUploader-Setup.exe
echo.
pause
