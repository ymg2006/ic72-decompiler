@echo off
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
set "IN=%~1"
set "OUT=%~2"
if "%IN%"=="" set "IN=."
if "%OUT%"=="" set "OUT=out"
if not exist "%OUT%" mkdir "%OUT%"

set "PYEXE=%ROOT%python\python.exe"
if exist "%PYEXE%" goto run
where py >nul 2>nul && set "PYEXE=py -3" && goto run
where python >nul 2>nul && set "PYEXE=python" && goto run
echo Python not found. Run setup_embedded_python.bat first, or install Python 3.
exit /b 1

:run
for %%F in ("%IN%\*.opcodes.json") do (
    echo Decompiling %%~nxF
    %PYEXE% "%ROOT%cfg_decompiler.py" "%%~fF" -o "%OUT%\%%~nF.php" --formatter python
)
