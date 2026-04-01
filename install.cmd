@echo off
setlocal
cd /d "%~dp0"

echo Flutter Uploader installer build (Windows)
echo.
echo 1) Building app binaries into dist\
powershell -NoProfile -ExecutionPolicy Bypass -File "installer\scripts\build_win.ps1"
echo.
echo 2) Create the installer EXE using Inno Setup:
echo    - Open installer\windows\FlutterUploader.iss in Inno Setup and click Compile
echo    - OR run:
echo      "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows\FlutterUploader.iss
echo.
echo Output will be in dist-installer\
echo.

