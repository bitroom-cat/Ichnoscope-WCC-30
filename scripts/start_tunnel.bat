@echo off
title Ichnoscope Public Tunnel
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_tunnel.ps1" -Standalone %*
pause
