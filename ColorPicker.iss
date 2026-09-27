; ColorPicker.iss
; Inno Setup script -- packages the already-built ColorPicker.exe
; into a real Windows installer (Setup.exe) with a Start Menu entry,
; optional desktop shortcut, and a proper uninstaller.
;
; Requires Inno Setup: https://jrsoftware.org/isinfo.php
; Open this file in Inno Setup and click "Compile", or run from the
; command line with: iscc ColorPicker.iss

#define MyAppName "ColorPicker"
#define MyAppVersion "1.0"
#define MyAppPublisher "Your Name"
#define MyAppExeName "ColorPicker.exe"

[Setup]
AppId={{B6C1E5E4-2D0E-4A2F-9B1E-COLORPICKER01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Output installer goes into a folder called "installer-output"
OutputDir=installer-output
OutputBaseFilename=ColorPicker-Setup
Compression=lzma
SolidCompression=yes
;SetupIconFile=icon.ico
WizardStyle=modern
; Regular user install (no admin required); switch to "admin" if you
; specifically want it installed for all users under Program Files.
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; Grabs the exe straight out of your existing PyInstaller dist folder.
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
