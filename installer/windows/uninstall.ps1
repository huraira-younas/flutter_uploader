# Runs the Inno Setup uninstaller for Flutter Uploader (registry lookup).
# Usage (elevated prompt if needed for machine-wide install):
#   .\installer\windows\uninstall.ps1
#   .\installer\windows\uninstall.ps1 -Silent

param(
    [switch]$Silent
)

$DisplayName = 'Flutter Uploader'
$UninstallRoots = @(
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
)

$Entry = $null
foreach ($Pattern in $UninstallRoots) {
    $Entry = Get-ItemProperty -Path $Pattern -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -eq $DisplayName } |
        Select-Object -First 1
    if ($Entry) {
        break
    }
}

if (-not $Entry) {
    Write-Error "Flutter Uploader is not installed (no matching Programs and Features entry)."
    exit 1
}

$Command = if (
    $Silent -and
    ($Entry.PSObject.Properties.Name -contains 'QuietUninstallString') -and
    $Entry.QuietUninstallString
) {
    $Entry.QuietUninstallString
}
elseif ($Silent) {
    "$($Entry.UninstallString) /SILENT"
}
else {
    $Entry.UninstallString
}

if (-not $Command) {
    Write-Error "Registry entry is missing UninstallString."
    exit 1
}

$Proc = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', $Command) -Wait -PassThru
exit $Proc.ExitCode
