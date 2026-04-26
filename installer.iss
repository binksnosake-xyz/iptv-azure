; installer.iss - Inno Setup pour IPTV Azure
; Genere un installeur Windows professionnel avec raccourci bureau

[Setup]
AppName=IPTV Azure
AppVersion=1.0.0
AppPublisher=IPTV Azure
AppPublisherURL=https://github.com/binksnosake-xyz/iptv-azure
DefaultDirName={autopf}\IPTV Azure
DefaultGroupName=IPTV Azure
OutputDir=Output
OutputBaseFilename=IPTV-Azure-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\IPTV-Azure.exe
ChangesAssociations=no

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\IPTV-Azure\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\IPTV Azure"; Filename: "{app}\IPTV-Azure.exe"
Name: "{group}\{cm:UninstallProgram,IPTV Azure}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\IPTV Azure"; Filename: "{app}\IPTV-Azure.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\IPTV Azure"; Filename: "{app}\IPTV-Azure.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\IPTV-Azure.exe"; Description: "{cm:LaunchProgram,IPTV Azure}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
