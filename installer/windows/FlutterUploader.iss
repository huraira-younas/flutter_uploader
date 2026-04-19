; Inno Setup script — Flutter Uploader Windows installer.
;
; Creates an installer that:
;   - Wizard: user chooses install directory (default: Program Files\Flutter Uploader)
;   - Installs only the listed files; does not delete unrelated files in that folder
;   - Replaces existing app binaries if the same names are already present
;   - Optional Desktop shortcut (task checkbox)
;   - Start Menu entries (app, CLI, uninstall)
;   - Optionally launches the app on finish
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
SetupIconFile=..\..\app\assets\icon.ico

AppVersion=5.4
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowRootDirectory=no
AppendDefaultDirName=yes
DisableDirPage=no
DisableProgramGroupPage=yes
OutputDir=..\..\dist-installer
OutputBaseFilename=FlutterUploader-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
; Install only copies [Files] entries; it does not erase other files in the chosen folder.
SelectDirLabel2=Choose the folder where Setup should install [name].%n%nSetup will not delete your other files in that folder—it only adds or updates the application files listed in this installer.%n%nTo use a different folder, click Browse.

[Files]
Source: "..\..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\dist\{#CliExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\app\*.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}"; Permissions: users-modify
Name: "{app}\secrets"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\outputs"; Permissions: users-modify

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{group}\{#AppName} (CLI)"; Filename: "{cmd}"; Parameters: "/k """"{app}\{#CliExeName}"""""; WorkingDir: "{app}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: checkedonce

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files;          Name: "{app}\config.json"
Type: files;          Name: "{app}\config.json.tmp"
Type: filesandordirs; Name: "{app}\secrets"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\outputs"
Type: filesandordirs; Name: "{userappdata}\FlutterUploader"
