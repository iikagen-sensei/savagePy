@echo off
:: ── CONFIGURA ESTAS DOS VARIABLES ────────────────────────────
set WSL_DISTRO=Ubuntu-24.04
set PROJECT_PATH=/mnt/d/OneDrive/Proyectos/savagePy
:: ─────────────────────────────────────────────────────────────

start http://localhost:5000
wsl -d %WSL_DISTRO% -e bash -c "cd %PROJECT_PATH% && .venv/bin/python -c 'import app'"