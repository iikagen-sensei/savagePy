# generate.py
# Lógica de generación de documentos.
# Usado por app.py (Flask) y por línea de comandos.
#
# Uso CLI:
#   python generate.py power.manual_print
#   python generate.py power.manual_print --view-id vwxxxxxxxx
#   python generate.py rule.manual_print --output mi_doc.pdf

import argparse
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from config import NOCODB_URL, API_TOKEN, TABLE_CONFIG, DOCUMENTS
from nocodb_client import get_table, get_characters, get_bestiary_entries
import markdown as _markdown_lib
import requests as req


BASE_DIR        = Path(__file__).parent
TEMPLATES_DIR   = BASE_DIR / "templates"
DOCUMENTS_DIR   = TEMPLATES_DIR / "documents"
STATIC_DIR      = BASE_DIR / "static"
FONTS_CACHE_DIR = STATIC_DIR / "fonts" / "cache"
FONTS_HEADERS   = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


# ── DOCUMENTOS ─────────────────────────────────────────────────────────────

def find_doc(doc_id: str):
    """Busca un documento por 'grupo.clave'. Devuelve (doc, table_key) o (None, None)."""
    parts = doc_id.split(".", 1)
    if len(parts) != 2:
        return None, None
    group_key, doc_key = parts
    group = DOCUMENTS.get(group_key, {})
    doc = group.get("docs", {}).get(doc_key)
    if not doc:
        return None, None
    return doc, doc.get("table_key") or group_key


def doc_type(doc: dict) -> str:
    """Devuelve 'html', 'docx' o 'md' según la extensión del template."""
    return Path(doc["template"]).suffix.lstrip(".")


def make_jinja_env() -> Environment:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    env.filters["markdown"] = lambda text: _markdown_lib.markdown(
        text or "", extensions=["tables", "nl2br"]
    )
    return env


def resolve_view_name(table_key: str, view_id: str | None) -> str:
    if not view_id:
        return ""
    try:
        table_id = TABLE_CONFIG[table_key]["table_id"]
        r = req.get(f"{NOCODB_URL}/api/v2/meta/tables/{table_id}/views",
                    headers={"xc-token": API_TOKEN}, timeout=5)
        r.raise_for_status()
        for v in r.json().get("list", []):
            if v["id"] == view_id:
                return v["title"].removeprefix("pub:").strip()
    except Exception:
        pass
    return ""


def get_data(table_key: str, view_id: str | None) -> list:
    """Devuelve los datos de una tabla listos para el template."""
    if table_key == "character":
        return [r for r in get_characters(view_id=view_id, full=True) if r.get("data")]
    if table_key == "bestiary":
        return get_bestiary_entries(view_id=view_id, full=True)
    return get_table(table_key, view_id=view_id)


def output_filename(doc_id: str, fmt: str, view_name: str = "") -> str:
    base = doc_id.replace(".", "_")
    suffix = f"_{view_name}" if view_name else ""
    return f"{base}{suffix}.{fmt}"


# ── FUENTES ────────────────────────────────────────────────────────────────

def _slug(google_fonts_url: str) -> str:
    return re.sub(r'[^a-z0-9]', '_', google_fonts_url.lower())[:60]


def _patch_fonts(html: str, for_weasyprint: bool = False) -> str:
    """Sustituye <link> y @import de Google Fonts por la caché local.

    for_weasyprint=False (navegador):
        <link href="/static/fonts/cache/{slug}/fonts.css">
        El navegador los resuelve vía Flask sin problema.

    for_weasyprint=True (PDF):
        Lee el fonts.css del disco, sustituye /static/ → file:// dentro del CSS
        e incrusta el resultado como <style> en el HTML.
        Así WeasyPrint no necesita resolver ningún archivo externo.
    """
    def _browser_href(url):
        return f"/static/fonts/cache/{_slug(url)}/fonts.css"

    def _inline_css(url):
        css_path = FONTS_CACHE_DIR / _slug(url) / "fonts.css"
        if not css_path.exists():
            return ""
        css = css_path.read_text(encoding="utf-8")
        # /static/fonts/cache/... → file:///ruta/absoluta/static/fonts/cache/...
        return css.replace("/static/", f"{STATIC_DIR.as_uri()}/")

    if for_weasyprint:
        def replace_link(m):
            return f"<style>{_inline_css(m.group(1))}</style>"
        def replace_import(m):
            return _inline_css(m.group(1))
    else:
        def replace_link(m):
            return f'<link rel="stylesheet" href="{_browser_href(m.group(1))}">'
        def replace_import(m):
            return f"@import url('{_browser_href(m.group(1))}');"

    html = re.sub(
        r'<link[^>]+href="(https://fonts\.googleapis\.com/[^"]+)"[^>]*>',
        replace_link, html
    )
    html = re.sub(
        r"@import url\('(https://fonts\.googleapis\.com/[^']+)'\);",
        replace_import, html
    )
    return html


# ── GENERADORES ────────────────────────────────────────────────────────────

def render_html(doc_id: str, view_id: str | None = None) -> str:
    """Renderiza un documento HTML con fuentes en /static/ (para el navegador)."""
    doc, table_key = find_doc(doc_id)
    if not doc:
        raise ValueError(f"Documento '{doc_id}' no encontrado")
    data = get_data(table_key, view_id)
    view_name = resolve_view_name(table_key, view_id)
    env = make_jinja_env()
    template = env.get_template(doc["template"])
    context = {"view_name": view_name, "nocodb_url": NOCODB_URL}
    if doc.get("data_key"):
        context[doc["data_key"]] = data
    return _patch_fonts(template.render(**context), for_weasyprint=False)


def render_pdf(doc_id: str, view_id: str | None = None) -> bytes:
    """Genera un PDF con fuentes incrustadas como <style file://> para WeasyPrint."""
    doc, table_key = find_doc(doc_id)
    if not doc:
        raise ValueError(f"Documento '{doc_id}' no encontrado")
    if doc_type(doc) != "html":
        raise ValueError(f"'{doc_id}' no es un documento HTML")
    from weasyprint import HTML
    data = get_data(table_key, view_id)
    view_name = resolve_view_name(table_key, view_id)
    env = make_jinja_env()
    template = env.get_template(doc["template"])
    context = {"view_name": view_name, "nocodb_url": NOCODB_URL}
    if doc.get("data_key"):
        context[doc["data_key"]] = data
    html = _patch_fonts(template.render(**context), for_weasyprint=True)
    return HTML(string=html, base_url=str(BASE_DIR)).write_pdf()


def render_docx(doc_id: str, view_id: str | None = None) -> bytes:
    """Genera un .docx a partir de un template .docx (docxtpl) o .md (Jinja2+pypandoc)."""
    from docx_generator import render_docx_template, render_md_template
    doc, table_key = find_doc(doc_id)
    if not doc:
        raise ValueError(f"Documento '{doc_id}' no encontrado")
    dtype = doc_type(doc)
    if dtype not in ("docx", "md"):
        raise ValueError(f"'{doc_id}' no es un documento Word")
    data = get_data(table_key, view_id)
    view_name = resolve_view_name(table_key, view_id)
    context = {doc["data_key"]: data, "view_name": view_name, "titulo": doc["label"]}
    template_path = DOCUMENTS_DIR / Path(doc["template"]).name
    if dtype == "md":
        return render_md_template(template_path, context)
    return render_docx_template(template_path, context)


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generador de documentos Savage Worlds")
    parser.add_argument("doc_id", help="ID del documento (formato grupo.clave, ej: power.manual_print)")
    parser.add_argument("--view-id", default=None, help="ID de vista NocoDB (opcional)")
    parser.add_argument("--output", default=None, help="Ruta de salida (opcional)")
    args = parser.parse_args()

    doc, table_key = find_doc(args.doc_id)
    if not doc:
        print(f"[!] Documento '{args.doc_id}' no encontrado en config.py")
        return

    view_name = resolve_view_name(table_key, args.view_id)
    dtype = doc_type(doc)

    if dtype == "html":
        fmt, data = "pdf", render_pdf(args.doc_id, view_id=args.view_id)
    elif dtype in ("docx", "md"):
        fmt, data = "docx", render_docx(args.doc_id, view_id=args.view_id)
    else:
        print(f"[!] Tipo de template desconocido: {dtype}")
        return

    out_path = Path(args.output) if args.output else Path(output_filename(args.doc_id, fmt, view_name))
    out_path.write_bytes(data)
    print(f"[OK] {out_path.resolve()}")


if __name__ == "__main__":
    main()
