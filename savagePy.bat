@echo off
:: ============================================================
:: savagePy.bat — Lanzador de Savage Worlds Generator
:: ============================================================
::
:: Abre el servidor Flask en WSL y lanza el navegador.
::
:: CONFIGURACIÓN
:: -------------
:: Ajusta las dos variables de abajo si mueves el proyecto
:: o lo instalas en otro equipo:
::
::   WSL_DISTRO   Nombre exacto de tu distribución WSL.
::                Para ver las disponibles ejecuta en PowerShell:
::                  wsl --list
::                Ejemplos: Ubuntu-24.04  Debian  Ubuntu
::
::   PROJECT_PATH Ruta al proyecto en formato WSL (/mnt/...).
::                Tu disco C: es /mnt/c, el D: es /mnt/d, etc.
::                Ejemplo para C:\Proyectos\savagePy:
::                  /mnt/c/Proyectos/savagePy
::
:: REQUISITOS
:: ----------
::   - WSL instalado con la distribución indicada en WSL_DISTRO
::   - Entorno virtual Python creado en PROJECT_PATH/.venv
::     (si no existe: wsl -d <distro> -e bash -c "cd <path> && python -m venv .venv && .venv/bin/pip install -r requirements.txt")
::   - Archivo .env configurado en PROJECT_PATH/
::     (copia .env.example a .env y rellena los valores)
::
:: ============================================================

:: ── CONFIGURA ESTAS DOS VARIABLES ────────────────────────────
set WSL_DISTRO=Ubuntu-24.04
set PROJECT_PATH=/mnt/d/OneDrive/Proyectos/savagePy
:: ─────────────────────────────────────────────────────────────

start http://localhost:5000
wsl -d %WSL_DISTRO% -e bash -c "cd %PROJECT_PATH% && .venv/bin/python app.py"