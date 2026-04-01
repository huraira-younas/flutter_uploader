@echo off
setlocal
cd /d "%~dp0"

echo Flutter Uploader - Windows full build (app + installer wizard)
echo.
echo End users only run the generated FlutterUploader-Setup.exe - they never install Inno Setup.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "installer\scripts\build_win.ps1"
if errorlevel 1 exit /b 1

if exist .venv (
    echo.
    echo Cleaning up build venv...
    rmdir /s /q .venv
)

echo.
echo Done.
echo   App:        dist\FlutterUploader.exe
echo   Installer:  dist-installer\FlutterUploader-Setup.exe  (single-click wizard for users)
echo.
pause
