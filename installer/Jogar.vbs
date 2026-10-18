' Maré Alta Resort - abre o jogo guardando saves, configurações e cache na pasta da instalação (userdata)
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
If Not fso.FolderExists(dir & "\userdata") Then fso.CreateFolder(dir & "\userdata")
sh.Environment("PROCESS")("APPDATA") = dir & "\userdata"
sh.CurrentDirectory = dir
sh.Run """" & dir & "\MareAltaResort.exe""", 1, False
