@echo off
title Generador Pro de Codigos QR
cd /d "%~dp0"
echo ======================================================
echo   Iniciando Generador Pro de Codigos QR Personalizados
echo ======================================================
echo.
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    echo Asegurate de tener Python instalado.
    pause
)

