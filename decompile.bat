@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "PYTHON_EXE=%ROOT%python\python.exe"

if exist "%PYTHON_EXE%" goto run

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PYTHON_EXE=py -3"
    goto run
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PYTHON_EXE=python"
    goto run
)

echo.
echo Could not find Python.
echo Put the official Windows embeddable Python runtime in:
echo   %ROOT%python\python.exe
echo or run setup_embedded_python.bat once to download it from python.org.
echo.
exit /b 1

:run
if "%~1"=="" (
    echo Usage:
    echo   decompile.bat input.opcodes.json -o output.php
    echo.
    echo Examples:
    echo   decompile.bat accessdenied.opcodes.json -o accessdenied.php
    echo   decompile.bat accessdenied.opcodes.json -o accessdenied.php --formatter phply
    echo   decompile.bat accessdenied.opcodes.json -o accessdenied.php --formatter none
    exit /b 2
)

%PYTHON_EXE% "%ROOT%cfg_decompiler.py" %*
exit /b %ERRORLEVEL%
