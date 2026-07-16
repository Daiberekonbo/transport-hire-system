#define MyAppName "Transport Hire Management System"
#define MyAppVersion "1.0"
#define MyAppPublisher "Daiberekonbo"
#define MyAppExeName "run.exe"

[Setup]
AppId={{A6C71A8A-9A3F-47F8-B1C5-THMS001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\THMS
DefaultGroupName=THMS
OutputDir=Output
OutputBaseFilename=THMS_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

SetupIconFile=THMS.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create Desktop Shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "run\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "THMS.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\THMS"; Filename: "{app}\run.exe"
Name: "{autodesktop}\THMS"; Filename: "{app}\run.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\run.exe"; Description: "Launch THMS"; Flags: nowait postinstall skipifsilent