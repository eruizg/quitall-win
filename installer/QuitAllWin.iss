; QuitAllWin.iss — Inno Setup script.
;
; Compile with:  iscc installer\QuitAllWin.iss
; Output:        dist\installer\QuitAllWin-Setup-<version>.exe
;
; Install Inno Setup once with:  winget install --id JRSoftware.InnoSetup

#define MyAppName       "QuitAll-Win"
#define MyAppVersion    "0.1.0"
#define MyAppPublisher  "Esteban"
#define MyAppURL        "https://github.com/eruizg/quitall-win"
#define MyAppExeName    "QuitAllWin.exe"

[Setup]
; A *unique* GUID identifies this product across versions. NEVER reuse this
; one for another app — generate a fresh GUID per project.
AppId={{4F8F2B1E-8C9E-4B4F-A3D2-7E5F1C9B2A4D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Per-user install — no UAC prompt, no admin needed.
DefaultDirName={localappdata}\Programs\QuitAllWin
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

DisableProgramGroupPage=yes
DisableDirPage=auto
LicenseFile=..\LICENSE

OutputDir=..\dist\installer
OutputBaseFilename=QuitAllWin-Setup-{#MyAppVersion}
SetupIconFile=
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon";   Description: "Create a &desktop shortcut";  GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startupicon";   Description: "Start {#MyAppName} when Windows starts"; GroupDescription: "Auto-start:"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: postinstall nowait skipifsilent runasoriginaluser

[UninstallDelete]
; The app stores config in %APPDATA%\QuitAllWin — leave it on uninstall by
; default (users hate losing settings) but offer to clean it up if needed
; via a custom uninstall step in a future version.
