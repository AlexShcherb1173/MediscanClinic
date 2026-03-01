@echo off
setlocal

REM Переходим в backend (рядом с manage.py), независимо от того, откуда запустили .bat
cd /d "%~dp0backend" || (echo Cannot cd to backend & exit /b 1)

REM Основная папка с Django apps
set TARGET=apps

if not exist "%TARGET%" (
  echo Folder "%TARGET%" not found in: %CD%
  echo Check your project structure.
  dir
  exit /b 1
)

echo Running black...
python -m black "%TARGET%" --exclude "(/migrations/|\\migrations\\)"
if errorlevel 1 exit /b 1

echo Running isort...
python -m isort "%TARGET%" --skip migrations
if errorlevel 1 exit /b 1

echo Running flake8...
python -m flake8 "%TARGET%" --exclude=migrations
if errorlevel 1 exit /b 1

echo Running mypy...
python -m mypy "%TARGET%" --exclude "(/migrations/|\\migrations\\)"
if errorlevel 1 exit /b 1

echo Done.
pause
endlocal