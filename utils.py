# utils.py
# Diagnóstico de entorno y preparación de recursos. Llamar al inicio de app.py.

import importlib
import re
import subprocess
import sys
from pathlib import Path

FONTS_CACHE_DIR = Path(__file__).parent / "static" / "fonts" / "cache"
FONTS_HEADERS   = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

# Todas las fuentes que usa el proyecto (UI + templates de documentos).
# Si un template nuevo usa fuentes distintas, añadir la URL aquí.
REQUIRED_FONTS = [
    # UI (base.html) + character_sheet, bestiary_mobile, edge_cards...
    "https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Rajdhani:wght@400;500;600;700&display=swap",
    # Variante con Rajdhani 500;600;700 (power_cards, rules_manual...)
    "https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=Rajdhani:wght@500;600;700&display=swap",
    # Variante con Cinzel 900 y EB Garamond 600 (treasure_cards, equipment_cards...)
    "https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700;900&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Rajdhani:wght@500;600;700&display=swap",
    # Variante con Crimson Pro (powers_manual, edges_manual...)
    "https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap",
    # Variante EB Garamond sin Rajdhani (algunos manuales)
    "https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap",
]


def check_environment():
    """Valida dependencias Python, herramientas de sistema y descarga fuentes. Aborta si falta algo."""
    _check_dependencies()
    _ensure_fonts()
    print("[OK] Entorno listo.\n")


# ── DEPENDENCIAS ───────────────────────────────────────────────────────────

def _check_dependencies():
    required = {
        "Flask":         "flask",
        "requests":      "requests",
        "weasyprint":    "weasyprint",
        "python-docx":   "docx",
        "docxtpl":       "docxtpl",
        "pypandoc":      "pypandoc",
        "python-dotenv": "dotenv",
        "markdown":      "markdown",
    }
    missing = [pkg for pkg, mod in required.items() if not _can_import(mod)]
    if missing:
        print(f"[!] Faltan paquetes Python: {', '.join(missing)}")
        print("    Ejecuta: pip install -r requirements.txt")
        sys.exit(1)

    try:
        subprocess.check_output(["pandoc", "--version"], stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[!] Falta 'pandoc' en el sistema (necesario para exportar Word desde Markdown).")
        print("    Instálalo desde: https://pandoc.org/installing.html")
        sys.exit(1)


def _can_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


# ── FUENTES ────────────────────────────────────────────────────────────────

def _ensure_fonts():
    """Descarga todas las fuentes de REQUIRED_FONTS al caché local si no están ya.
    No modifica ningún template — la sustitución de rutas se hace en memoria al renderizar."""
    import requests as req

    for url in REQUIRED_FONTS:
        slug = re.sub(r'[^a-z0-9]', '_', url.lower())[:60]
        cache_dir = FONTS_CACHE_DIR / slug
        css_path  = cache_dir / "fonts.css"

        if css_path.exists():
            continue  # ya está, no hacer nada

        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            css = req.get(url, headers=FONTS_HEADERS, timeout=10).text
            font_faces = []
            for face in re.findall(r'(@font-face\s*\{[^}]+\})', css, re.DOTALL):
                woff_match = re.search(r'url\((https://[^)]+\.woff2)\)', face)
                if not woff_match:
                    continue
                woff_url = woff_match.group(1)
                fname = woff_url.split("/")[-1].split("?")[0]
                local_path = cache_dir / fname
                if not local_path.exists():
                    local_path.write_bytes(req.get(woff_url, timeout=10).content)
                    print(f"  ↓ {fname}")
                face_local = face.replace(woff_url, f"/static/fonts/cache/{slug}/{fname}")
                face_local = re.sub(r'\s*format\([^)]+\)', '', face_local)
                font_faces.append(face_local)
            css_path.write_text("\n\n".join(font_faces), encoding="utf-8")
            print(f"  [✓] Fuentes cacheadas: {slug}")
        except Exception as e:
            print(f"  [!] No se pudieron descargar las fuentes de {url}: {e}")
