@echo off
title Sistema de Asistencia y Escaner QR - GEF Bermejo
cd /d "%~dp0"
echo ====================================================================
echo  SISTEMA DE ASISTENCIA Y CONTROL QR - TALLER GEF BERMEJO
echo ====================================================================
echo.
echo 1. Abriendo la aplicacion en tu navegador...
start "" "http://localhost:8000"
echo 2. Iniciando servidor web local...
echo.
python servidor.py
pause

