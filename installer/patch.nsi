Unicode true
!include "MUI2.nsh"
!define APP "Maré Alta Resort"
; VER e BASE vêm do build_patch.sh (-DVER=... -DBASE=...)
Name "${APP} - atualização ${VER}"
OutFile "Atualizar_MareAltaResort_v${VER}.exe"
RequestExecutionLevel user
SetCompressor /SOLID lzma
InstallDir "D:\Games\MareAltaResort"
!define MUI_ICON "icon.ico"
!define MUI_WELCOMEPAGE_TITLE "Atualizar ${APP} para ${VER}"
!define MUI_WELCOMEPAGE_TEXT "Este assistente atualiza o jogo já instalado (versão ${BASE} ou mais nova) para a ${VER}, sem baixar o jogo inteiro de novo.$\r$\n$\r$\nEscolha a mesma pasta onde o jogo está instalado. Os saves são mantidos."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "PortugueseBR"

Function .onInit
  IfFileExists "D:\Games\MareAltaResort\MareAltaResort.pck" done 0
  IfFileExists "$LOCALAPPDATA\Programs\MareAltaResort\MareAltaResort.pck" 0 done
    StrCpy $INSTDIR "$LOCALAPPDATA\Programs\MareAltaResort"
  done:
FunctionEnd

Function .onVerifyInstDir
  IfFileExists "$INSTDIR\MareAltaResort.pck" +2 0
    Abort
FunctionEnd

Section "Atualizar"
  SetOutPath "$INSTDIR"
  File "patch_${VER}.pck"
  File "patch_loader.gd"
  ; caminho da pasta com barras normais para o override.cfg da Godot
  StrCpy $0 "$INSTDIR"
  StrCpy $1 ""
  StrCpy $2 0
  loop:
    StrCpy $3 $0 1 $2
    StrCmp $3 "" fim
    StrCmp $3 "\" 0 +3
      StrCpy $1 "$1/"
      Goto next
    StrCpy $1 "$1$3"
  next:
    IntOp $2 $2 + 1
    Goto loop
  fim:
  WriteINIStr "$INSTDIR\override.cfg" "autoload" "Patch" '"*$1/patch_loader.gd"'
  WriteINIStr "$INSTDIR\override.cfg" "application" "config/version" '"${VER}"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\MareAltaResort" "DisplayVersion" "${VER}"
SectionEnd
