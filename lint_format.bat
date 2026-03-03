@echo off
setlocal enabledelayedexpansion

REM --- Переходим в backend (рядом с manage.py), независимо от места запуска ---
cd /d "%~dp0backend" || (echo [ERROR] Cannot cd to backend & exit /b 1)

REM --- Что проверяем ---
set TARGETS=apps config

for %%D in (%TARGETS%) do (
  if not exist "%%D" (
    echo [ERROR] Folder "%%D" not found in: %CD%
    dir
    exit /b 1
  )
)

echo ==================================================
echo MediscanClinic: lint ^& format
echo Workdir: %CD%
echo Targets: %TARGETS%
echo ==================================================

echo.
echo [1/4] Running black...
python -m black %TARGETS% --extend-exclude "migrations"
if errorlevel 1 exit /b 1

echo.
echo [2/4] Running isort...
python -m isort %TARGETS% --skip migrations
if errorlevel 1 exit /b 1

echo.
echo [3/4] Running flake8...
python -m flake8 %TARGETS% --config "%CD%\.flake8" --exclude=migrations
if errorlevel 1 exit /b 1

echo.
echo [4/4] Running mypy...
REM ВАЖНО: лучше настроить mypy в pyproject.toml / mypy.ini и не городить exclude в батнике
python -m mypy %TARGETS%
if errorlevel 1 exit /b 1

echo.
echo ✅ Done.

REM Пауза только если запущено в интерактивной консоли
if "%CI%"=="" pause

endlocal