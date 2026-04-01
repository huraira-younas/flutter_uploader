Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
Set-Location $RootDir

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r app\requirements.txt -r installer\requirements-dev.txt

if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path dist-installer) { Remove-Item -Recurse -Force dist-installer }

pyinstaller -y installer\packaging\flutter_uploader.spec

Write-Host ""
Write-Host "Built:"
Write-Host "  dist\FlutterUploader.exe"
Write-Host "  dist\FlutterUploaderCLI.exe"

