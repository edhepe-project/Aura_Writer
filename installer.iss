; ═══════════════════════════════════════════════════════════════════════════
; Aura Writer — Script Inno Setup 6
; La versión (#MyAppVersion) se inyecta automáticamente desde build_windows.bat
; ═══════════════════════════════════════════════════════════════════════════

#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#define MyAppName       "Aura Writer"
#define MyAppPublisher  "Aura Studio"
#define MyAppURL        "https://github.com/edhepe-project/Aura_Writer"
#define MyAppExeName    "AuraWriter.exe"
#define MyAppAssocName  MyAppName + " Project"
#define MyAppAssocExt   ".aura"
#define MyAppAssocKey   StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; AppId identifica de forma única esta aplicación. No lo cambies entre versiones.
AppId={{D37B4D5A-617F-4B1C-B7D4-486981A7A912}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Instala sin privilegios de administrador (por defecto en carpeta del usuario)
DefaultDirName={autopf}\{#MyAppName}
ChangesAssociations=yes
DisableProgramGroupPage=yes

; Permite actualizar versiones anteriores limpiamente
CloseApplications=yes
CloseApplicationsFilter=*.exe,*.dll
RestartApplications=no

OutputDir=installer_output
OutputBaseFilename=AuraWriter_Setup_v{#MyAppVersion}
SetupIconFile=aura_writer.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Permite instalar sin ser administrador, pero ofrece la opción de elevarse
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Información mostrada en Agregar/Quitar programas
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName} {#MyAppVersion}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "assocfiles";  Description: "Abrir archivos .aura con {#MyAppName}"; GroupDescription: "Asociación de archivos:"

[Files]
; Ejecutable principal
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Ícono (para accesos directos)
Source: "aura_writer.ico"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
; Asociación de archivos .aura → sólo si el usuario eligió la tarea
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assocfiles
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey; Tasks: assocfiles
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: assocfiles
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: assocfiles
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: "{#MyAppAssocExt}"; ValueData: ""; Tasks: assocfiles

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\aura_writer.ico"
Name: "{autodesktop}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\aura_writer.ico"; Tasks: desktopicon

[Run]
; Opción de lanzar la app al terminar la instalación
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; No hay procesos adicionales que matar al desinstalar

[Code]
// ─────────────────────────────────────────────────────────────────────────────
// Detecta si hay una versión anterior instalada y la cierra antes de instalar
// ─────────────────────────────────────────────────────────────────────────────
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then begin
    // Asegurarse de que no queden archivos del instalador anterior colgados
  end;
end;
