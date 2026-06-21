@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "PYTHON_VERSION=3.11.9"
set "PYTHON_ZIP=python-%PYTHON_VERSION%-embed-amd64.zip"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_ZIP%"

if exist "%ROOT%python\python.exe" (
    echo Embedded Python already exists at %ROOT%python\python.exe
    exit /b 0
)

echo Downloading official Windows embeddable Python %PYTHON_VERSION% x64...
echo %PYTHON_URL%
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%ROOT%%PYTHON_ZIP%'"
if errorlevel 1 exit /b 1

echo Extracting to %ROOT%python\ ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force '%ROOT%%PYTHON_ZIP%' '%ROOT%python'"
if errorlevel 1 exit /b 1

echo Enabling project and vendored phply paths in embedded Python...
for %%F in ("%ROOT%python\python*._pth") do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$p='%%~fF'; $lines=Get-Content $p; $extra=@('..','..\vendor','import site'); Set-Content -Encoding ASCII $p ($lines + $extra | Select-Object -Unique)"
)

del "%ROOT%%PYTHON_ZIP%" >nul 2>nul

echo Done. Now run:
echo   decompile.bat input.opcodes.json -o output.php
exit /b 0
