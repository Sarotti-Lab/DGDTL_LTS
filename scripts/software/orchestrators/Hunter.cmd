@echo off
setlocal DisableDelayedExpansion
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\launchers\windows\Start-DGDTL.ps1" -Mode Hunter %*
exit /b %errorlevel%
