@echo off
title Servidor Web - Generador de Codigos QR
cd /d "%~dp0"
echo ==================================================================
echo   Iniciando Generador Pro de Codigos QR (Version Web)
echo ==================================================================
echo.
echo Abriendo tu navegador en http://localhost:5000 ...
start http://localhost:5000
python web_app.py
pause

