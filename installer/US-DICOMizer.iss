#define MyAppName "US-DICOMizer"
#define MyAppPublisher "ThrombUS+"
#define MyAppURL "https://github.com/thrombusplus/US-DICOMizer"
#ifndef AppVersion
#define AppVersion "0.0"
#endif
#ifndef SourceDir
#define SourceDir "..\dist"
#endif

[Setup]
AppId={{8D78B5B4-5B80-4D4F-9A54-3C13728EAFB0}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableDirPage=yes
DisableProgramGroupPage=yes
UsePreviousAppDir=no
UninstallDisplayIcon={app}\US-DICOMizer.exe
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=US-DICOMizer-Setup-v{#AppVersion}
SetupIconFile=..\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "{#SourceDir}\US-DICOMizer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\US-DICOMizer-Updater.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Logo_Blue_Green_small.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\US-DICOMizer_manual.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\VERSION"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\RELEASE_DATE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\US-DICOMizer.exe"; WorkingDir: "{app}"

