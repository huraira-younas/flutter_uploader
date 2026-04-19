<# .SYNOPSIS
    Build Flutter Uploader Windows executables and (if Inno Setup is present) the Setup wizard EXE.
.DESCRIPTION
    Creates a venv, installs runtime + dev dependencies, runs PyInstaller, copies docs next to the
    EXEs, then runs the Inno Setup compiler (ISCC) when found so you get dist-installer\FlutterUploader-Setup.exe
    in one shot.

    Inno Setup is only required on the machine that *builds* the installer - not on end users' PCs.
    If ISCC.exe is missing, this script tries: winget install -e --id JRSoftware.InnoSetup (silent).
.EXAMPLE
    .\installer\scripts\build_win.ps1
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-InnoSetupCompilerPath {
    foreach ($p in @(
            (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
            (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 5\ISCC.exe"),
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
            "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            "C:\Program Files\Inno Setup 6\ISCC.exe",
            "C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            "C:\Program Files\Inno Setup 5\ISCC.exe"
        )) {
        if ($p -and (Test-Path -LiteralPath $p)) {
            return $p
        }
    }
    foreach ($name in @("ISCC.exe", "iscc.exe")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and (Test-Path -LiteralPath $cmd.Source)) {
            return $cmd.Source
        }
    }
    # Use cmd so where.exe stderr is not mapped to PowerShell errors ($ErrorActionPreference = Stop).
    $line = cmd /c "where ISCC.exe 2>nul" | Select-Object -First 1
    if ($line) {
        $trimmed = $line.Trim()
        if ($trimmed -and (Test-Path -LiteralPath $trimmed)) {
            return $trimmed
        }
    }
    return $null
}

function Install-InnoSetupWithWinget {
    $wingetCmd = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $wingetCmd) {
        Write-Warning "winget.exe not found. Cannot auto-install Inno Setup."
        return
    }
    Write-Host "Inno Setup not found. Installing via winget (this build machine only)..."
    # Use --source winget only so a broken or offline msstore source does not fail the install.
    $wingetArgs = @(
        "install",
        "-e",
        "--id", "JRSoftware.InnoSetup",
        "--source", "winget",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--silent"
    )
    $proc = Start-Process -ArgumentList $wingetArgs -FilePath $wingetCmd.Source -NoNewWindow -PassThru -Wait
    $code = $proc.ExitCode
    # "No applicable upgrade" / already installed often returns non-zero (-1978335189); not a hard failure.
    $benign = ($code -eq 0) -or ($code -eq -1978335189)
    if (-not $benign) {
        Write-Warning "winget exited with code $code. Run the build elevated or install Inno Setup manually."
    }
}

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

$Iss = Join-Path $RootDir "installer\windows\FlutterUploader.iss"
$Iscc = Get-InnoSetupCompilerPath
if (-not $Iscc) {
    Install-InnoSetupWithWinget
    $Iscc = Get-InnoSetupCompilerPath
}

Write-Host ""
if ($Iscc) {
    Write-Host "Building Windows installer wizard (Inno Setup)..."
    
    # Extract version from Python helper
    $AppVersion = python -c "import sys; sys.path.append('app'); from helpers.version_info import UPLOADER_APP_VERSION; print(UPLOADER_APP_VERSION)"
    if ($LASTEXITCODE -ne 0 -or -not $AppVersion) {
        Write-Warning "Could not extract version from Python. Falling back to 0.0.0"
        $AppVersion = "0.0.0"
    }

    & $Iscc "/DAppVersion=$AppVersion" $Iss
    Write-Host ""
} else {
    Write-Warning "Inno Setup compiler (ISCC.exe) still not found - skipped FlutterUploader-Setup.exe."
    Write-Host "On this build PC only: run an elevated shell and install Inno, then re-run:"
    Write-Host "  winget install -e --id JRSoftware.InnoSetup --source winget --accept-package-agreements"
    Write-Host "Or: https://jrsoftware.org/isinfo.php"
    Write-Host ""
}

Write-Host "Built:"
Write-Host "  dist\FlutterUploader.exe"
Write-Host "  dist\FlutterUploaderCLI.exe"
if ($Iscc) {
    Write-Host "  dist-installer\FlutterUploader-Setup.exe   (double-click installer for users)"
}
