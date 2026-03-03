@echo off
setlocal EnableExtensions

echo ==================================================
echo MediscanClinic: lint ^& format
echo ==================================================

REM Переходим в backend (рядом с manage.py)
cd /d "%~dp0backend" || (echo Cannot cd to backend & exit /b 1)

set TARGETS=apps config

echo Workdir: %CD%
echo Targets: %TARGETS%
echo --------------------------------------------------

echo [1/4] Running black...
python -m black %TARGETS%
if errorlevel 1 exit /b 1

echo [2/4] Running isort...
python -m isort %TARGETS%
if errorlevel 1 exit /b 1

echo [3/4] Running flake8...
python -m flake8 %TARGETS% --config .flake8
if errorlevel 1 exit /b 1

echo [4/4] Running mypy...
python -m mypy %TARGETS%
if errorlevel 1 exit /b 1

echo Done.
pause
endlocal