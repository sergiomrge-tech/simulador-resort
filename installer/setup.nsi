Unicode true
!include "MUI2.nsh"
!define APP "Maré Alta Resort"
!define VER "0.9.5"
Name "${APP} ${VER}"
!ifdef LITE
OutFile "Instalar_MareAltaResort_v${VER}_Leve.exe"
!else
OutFile "Instalar_MareAltaResort_v${VER}.exe"
!endif
RequestExecutionLevel user
SetCompressor /SOLID lzma
InstallDir "D:\Games\MareAltaResort"
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"
!define MUI_WELCOMEPAGE_TITLE "Instalar ${APP} ${VER}"
!define MUI_WELCOMEPAGE_TEXT "Este assistente instala o jogo no seu PC (padrão: D:\Games\MareAltaResort — nada vai para o disco C:).$\r$\n$\r$\nSaves, configurações e cache de shaders ficam dentro da pasta do jogo."
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Jogar agora"
!define MUI_FINISHPAGE_RUN_FUNCTION RunGame
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "PortugueseBR"

Function .onInit
  IfFileExists "D:\*.*" +2 0
    StrCpy $INSTDIR "$LOCALAPPDATA\Programs\MareAltaResort"
FunctionEnd

Function RunGame
  ExecShell "" "$SYSDIR\wscript.exe" '"$INSTDIR\Jogar.vbs"'
FunctionEnd

Section "Jogo" SecMain
  SetOutPath "$INSTDIR"
  File "MareAltaResort.exe"
  File "MareAltaResort.pck"
  File "Jogar.vbs"
  File "icon.ico"
  File "LEIA-ME.txt"
  CreateDirectory "$INSTDIR\userdata"
  CreateShortcut "$DESKTOP\${APP}.lnk" "$SYSDIR\wscript.exe" '"$INSTDIR\Jogar.vbs"' "$INSTDIR\icon.ico" 0
  CreateDirectory "$SMPROGRAMS\${APP}"
  CreateShortcut "$SMPROGRAMS\${APP}\${APP}.lnk" "$SYSDIR\wscript.exe" '"$INSTDIR\Jogar.vbs"' "$INSTDIR\icon.ico" 0
  CreateShortcut "$SMPROGRAMS\${APP}\Desinstalar.lnk" "$INSTDIR\Desinstalar.exe"
  WriteUninstaller "$INSTDIR\Desinstalar.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort" "DisplayName" "${APP}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort" "DisplayVersion" "${VER}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort" "Publisher" "Sergio Games"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort" "DisplayIcon" "$INSTDIR\icon.ico"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort" "UninstallString" '"$INSTDIR\Desinstalar.exe"'
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\MareAltaResort.exe"
  Delete "$INSTDIR\MareAltaResort.pck"
  Delete "$INSTDIR\Jogar.vbs"
  Delete "$INSTDIR\icon.ico"
  Delete "$INSTDIR\LEIA-ME.txt"
  Delete "$INSTDIR\Desinstalar.exe"
  Delete "$DESKTOP\${APP}.lnk"
  RMDir /r "$SMPROGRAMS\${APP}"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort"
  ; os saves (userdata) ficam guardados de propósito
SectionEnd
