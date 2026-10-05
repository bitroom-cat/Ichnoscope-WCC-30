@echo off
title Ichnoscope Dev Runner
echo ==================================================================
echo              ICHNOSCOPE - Unified Development Runner              
echo ==================================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_dev.ps1" %*
pause
