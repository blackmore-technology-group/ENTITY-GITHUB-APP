@echo off
setlocal
cd /d "%~dp0.."
set "PYTHONPATH=%CD%\src"
if "%ENTITY_GITHUB_WEBHOOK_SECRET%"=="" (
  echo ENTITY_GITHUB_WEBHOOK_SECRET is required.
  exit /b 2
)
if not exist state mkdir state
python -m entity_github_app serve --host 127.0.0.1 --port 8787 --db state\entity-github-app.sqlite
