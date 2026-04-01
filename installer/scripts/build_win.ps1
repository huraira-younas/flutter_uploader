<# .SYNOPSIS
    Build Flutter Uploader Windows executables via PyInstaller.
.DESCRIPTION
    Creates a venv, installs runtime + dev dependencies, runs PyInstaller.
    Outputs:
        dist\FlutterUploader.exe     (GUI)
        dist\FlutterUploaderCLI.exe  (CLI)
.EXAMPLE
    .\installer\scripts\build_win.ps1
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RootDir

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r app\requirements.txt -r installer\requirements-dev.txt

if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path dist-installer) { Remove-Item -Recurse -Force dist-installer }

pyinstaller -y installer\packaging\flutter_uploader.spec

# Frozen builds resolve UPLOADER_DIR to the folder containing the .exe; bundled
# datas live inside the archive, so docs must sit next to the executables.
$DistDir = Join-Path $RootDir "dist"
@(
    @{ Src = "README.md"; Name = "README.md" }
    @{ Src = "app\ENVIRONMENT.md"; Name = "ENVIRONMENT.md" }
    @{ Src = "app\CLI_REFERENCE.md"; Name = "CLI_REFERENCE.md" }
) | ForEach-Object {
    $src = Join-Path $RootDir $_.Src
    if (-not (Test-Path -LiteralPath $src)) {
        Write-Error "Missing required file: $src"
    }
    Copy-Item -LiteralPath $src -Destination (Join-Path $DistDir $_.Name) -Force
}

Write-Host ""
Write-Host "Built:"
Write-Host "  dist\FlutterUploader.exe"
Write-Host "  dist\FlutterUploaderCLI.exe"
