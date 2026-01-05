@echo off
setlocal

REM === 위치 고정 (bat 기준) ===
set BASEDIR=%~dp0

REM === PowerShell 실행 ===
powershell.exe -NoProfile -ExecutionPolicy Bypass ^
  -File "%BASEDIR%ops_check.ps1"

REM === 창 유지 ===
echo.
echo [ops_check finished]
pause
