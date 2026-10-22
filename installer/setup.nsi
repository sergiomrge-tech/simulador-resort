Unicode true
!include "MUI2.nsh"
!define APP "Maré Alta Resort"
!define VER "1.0.1"
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
  ; já instalado? usa a mesma pasta (para atualizar por cima e manter os saves)
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort" "InstallLocation"
  StrCmp $0 "" 0 found
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort" "UninstallString"
  StrCmp $0 "" default
  StrCpy $0 $0 "" 1          ; tira a aspa inicial
  StrLen $1 $0
  IntOp $1 $1 - 17           ; tira \Desinstalar.exe" do fim
  StrCpy $0 $0 $1
  found:
    StrCpy $INSTDIR $0
    Return
  default:
    IfFileExists "D:\*.*" +2 0
      StrCpy $INSTDIR "$LOCALAPPDATA\Programs\MareAltaResort"
FunctionEnd

Function RunGame
  ExecShell "" "$SYSDIR\wscript.exe" '"$INSTDIR\Jogar.vbs"'
FunctionEnd

Section "Jogo" SecMain
  SetOutPath "$INSTDIR"
  ; v1.0: instalação completa por cima de uma versão com patches. Os patch_*.pck antigos e o carregador
  ; montariam arquivos velhos por cima do jogo novo, então são removidos (os saves em userdata ficam).
  Delete "$INSTDIR\patch_*.pck"
  Delete "$INSTDIR\patch_loader.gd"
  IfFileExists "$INSTDIR\override.cfg" 0 +3
    DeleteINIStr "$INSTDIR\override.cfg" "autoload" "Patch"
    DeleteINIStr "$INSTDIR\override.cfg" "application" "config/version"
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
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort" "InstallLocation" "$INSTDIR"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\MareAltaResort.exe"
  Delete "$INSTDIR\MareAltaResort.pck"
  Delete "$INSTDIR\Jogar.vbs"
  Delete "$INSTDIR\icon.ico"
  Delete "$INSTDIR\LEIA-ME.txt"
  Delete "$INSTDIR\Desinstalar.exe"
  Delete "$INSTDIR\patch_*.pck"
  Delete "$INSTDIR\patch_loader.gd"
  Delete "$DESKTOP\${APP}.lnk"
  RMDir /r "$SMPROGRAMS\${APP}"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort"
  ; os saves (userdata) ficam guardados de propósito
SectionEnd
