@echo off
rem Maré Alta Resort - modo portátil: saves, configurações e cache de shaders ficam nesta pasta (ex.: D:\Games\MareAltaResort\userdata)
set "APPDATA=%~dp0userdata"
if not exist "%APPDATA%" mkdir "%APPDATA%"
start "" "%~dp0MareAltaResort.exe" %*
