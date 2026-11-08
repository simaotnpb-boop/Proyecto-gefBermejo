@echo off
title Sistema de Asistencia y Escaner QR - GEF Bermejo
cd /d "%~dp0Pagina we-Supabase"
echo ====================================================================
echo  SISTEMA DE ASISTENCIA Y CONTROL QR - TALLER GEF BERMEJO
echo ====================================================================
echo.
echo Abriendo la aplicacion en tu navegador...
start "" "http://localhost:8000"
echo Iniciando servidor web...
echo.
python servidor.py
pause

