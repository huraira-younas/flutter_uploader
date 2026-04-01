; Inno Setup script
; Creates an installer that:
; - Installs the GUI app + CLI in Program Files
; - Optionally adds Start Menu shortcuts
; - Creates a Desktop shortcut (so user launches by clicking it next time)
;
; Build (from repo root, on Windows):
;   1) .\installer\scripts\build_win.ps1
;   2) Compile this .iss with Inno Setup (ISCC.exe)
;      Example:
;        & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows\FlutterUploader.iss

#define AppName "Flutter Uploader"
#define AppPublisher "Senpai"
#define AppExeName "FlutterUploader.exe"
#define CliExeName "FlutterUploaderCLI.exe"

[Setup]
AppId={{3E75B6DA-7E22-4A6D-9E1E-6D4A4D5AE9A1}
AppName={#AppName}
AppVersion=5.4
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist-installer
OutputBaseFilename=FlutterUploader-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; PyInstaller outputs (built by build_win.ps1 into dist\)
Source: "..\..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\{#CliExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Ship a starter env example next to the exe (user can edit/copy)
Source: "..\..\app\.env.example"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{group}\{#AppName} (CLI)"; Filename: "{cmd}"; Parameters: "/k """"{app}\{#CliExeName}"""""; WorkingDir: "{app}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Runtime files next to the exes (see app/core/constants.py frozen UPLOADER_DIR)
Type: files; Name: "{app}\config.json"
Type: files; Name: "{app}\.env"
Type: filesandordirs; Name: "{app}\secrets"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\outputs"

