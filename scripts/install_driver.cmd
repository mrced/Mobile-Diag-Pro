@echo off
title Instalador de Driver Fastboot / ADB - Mobile-Diag-Pro
color 0b
echo ============================================================
echo   MOBILE-DIAG-PRO - INSTALADOR DE DRIVER FASTBOOT / WINUSB
echo ============================================================
echo.
echo Solicitando privilegios de Administrador...
echo.

:: Verificar se tem privilegios de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Elevando privilegios via UAC...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo Privilegios administrativos confirmados!
echo.
echo Instalando driver Fastboot (JLQ / POCO C40 / Google WinUSB)...
set "INF_PATH=%~dp0..\fastboot_jlq.inf"
if not exist "%INF_PATH%" (
    set "INF_PATH=%~dp0fastboot_jlq.inf"
)

if exist "%INF_PATH%" (
    echo Localizado: %INF_PATH%
    pnputil /add-driver "%INF_PATH%" /install
    echo.
    echo Reiniciando enumeracao de dispositivos USB...
    pnputil /scan-devices
    echo.
    echo ============================================================
    echo   DRIVER INSTALADO COM SUCESSO!
    echo   O aparelho agora sera reconhecido no modo Fastboot.
    echo ============================================================
) else (
    echo Erro: Arquivo INF nao encontrado em %INF_PATH%
)

echo.
pause
