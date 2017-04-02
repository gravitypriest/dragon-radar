@echo off
SetLocal EnableDelayedExpansion

rem Blast dist folder
rmdir /s /q dist

rem Save dev config & prep blank release config
ren dragon-radar.ini dragon-radar.ini.bak
ren dragon-radar.ini.release dragon-radar.ini

rem Build & zip
python setup.py py2exe
for /f %%o in ('python constants.py') do set VERSION=%%o
7z a dragon-radar-%VERSION%.zip ./dist/*

rem Restore configs
ren dragon-radar.ini dragon-radar.ini.release
ren dragon-radar.ini.bak dragon-radar.ini
