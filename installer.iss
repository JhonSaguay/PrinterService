[Setup]
AppName=POS Printer Server
AppVersion=1.0
DefaultDirName={pf}\POSPrinter
DefaultGroupName=POSPrinter
OutputDir=output
OutputBaseFilename=POSPrinterInstaller
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\POSPrinter.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "nssm\win64\nssm.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "certs\*"; DestDir: "{app}\certs"; Flags: recursesubdirs
Source: "logs\*"; DestDir: "{app}\logs"; Flags: recursesubdirs createallsubdirs

[Run]
; Instalar servicio
Filename: "{app}\nssm.exe"; Parameters: "install POSPrinter ""{app}\POSPrinter.exe"" --service"; Flags: runhidden

; Configurar carpeta de trabajo
Filename: "{app}\nssm.exe"; Parameters: "set POSPrinter AppDirectory ""{app}"""; Flags: runhidden

; Logs
Filename: "{app}\nssm.exe"; Parameters: "set POSPrinter AppStdout ""{app}\logs\output.log"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set POSPrinter AppStderr ""{app}\logs\error.log"""; Flags: runhidden

; Auto start
Filename: "{app}\nssm.exe"; Parameters: "set POSPrinter Start SERVICE_AUTO_START"; Flags: runhidden

; Iniciar servicio
Filename: "{app}\nssm.exe"; Parameters: "start POSPrinter"; Flags: runhidden