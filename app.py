# app.py
# Interfaz web para el generador de documentos Savage Worlds.
# Uso: python app.py  →  abre http://localhost:5000

from flask import Flask, render_template, jsonify, send_file, Response, request
from pathlib import Path
import io
import requests as req
from config import NOCODB_URL, API_TOKEN, TABLE_CONFIG
from nocodb_client import get_table
from jinja2 import Environment, FileSystemLoader

app = Flask(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"

# ── CONFIGURACIÓN DE DOCUMENTOS ────────────────────────────────────────────
# Agrupa los documentos por tabla. Para añadir un documento nuevo,
# añade una entrada en la tabla correspondiente.

DOCUMENTS = {
    "power": {
        "label": "Poderes",
        "icon": "✦",
        "docs": {
            "powers": {"label": "Manual de Poderes", "icon": "📖", "template": "powers_manual.html", "data_key": "powers"},
            "cards":        {"label": "Cartas de Poderes",        "icon": "🂠", "template": "power_cards.html",        "data_key": "powers"},
            "cards_mobile": {"label": "Cartas Móvil (PDF)",         "icon": "📱", "template": "power_cards_mobile.html", "data_key": "powers"},
        }
    },
    "edge": {
        "label": "Ventajas",
        "icon": "⚔",
        "docs": {
            "edges": {"label": "Manual de Ventajas", "icon": "📖", "template": "edges_manual.html", "data_key": "edges"},
        }
    },
    "hindrance": {
        "label": "Desventajas",
        "icon": "☠",
        "docs": {
            "hindrances": {"label": "Manual de Desventajas", "icon": "📖", "template": "hindrances_manual.html", "data_key": "hindrances"},
        }
    },
}


def render_document(doc_id: str, view_id: str | None = None) -> str:
    """Renderiza un documento y devuelve el HTML como string."""
    # Buscar el documento en cualquier tabla
    doc = None
    table_key = None
    for t_key, t_cfg in DOCUMENTS.items():
        if doc_id in t_cfg["docs"]:
            doc = t_cfg["docs"][doc_id]
            table_key = t_key
            break
    if not doc:
        raise ValueError(f"Documento '{doc_id}' no encontrado")

    data = get_table(table_key, view_id=view_id)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(doc["template"])
    return template.render(**{doc["data_key"]: data})


# ── RUTAS ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("ui/index.html", documents=DOCUMENTS)


@app.route("/api/status")
def status():
    """Devuelve el estado de NocoDB: cuántos registros hay en cada tabla."""
    headers = {"xc-token": API_TOKEN}
    counts = {}
    for key, cfg in TABLE_CONFIG.items():
        try:
            url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records?limit=1"
            r = req.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            counts[key] = r.json()["pageInfo"]["totalRows"]
        except Exception:
            counts[key] = None
    return jsonify(counts)


@app.route("/api/views/<table_key>")
def get_views(table_key: str):
    """Devuelve las vistas disponibles de una tabla desde NocoDB."""
    if table_key not in TABLE_CONFIG:
        return jsonify({"error": "Tabla no encontrada"}), 404
    table_id = TABLE_CONFIG[table_key]["table_id"]
    headers = {"xc-token": API_TOKEN}
    try:
        url = f"{NOCODB_URL}/api/v2/meta/tables/{table_id}/views"
        r = req.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        PREFIX = "pub:"  # Solo se muestran vistas cuyo nombre empiece por "pub:"
        all_views = r.json().get("list", [])
        views = [
            {"id": v["id"], "title": v["title"].removeprefix(PREFIX).strip()}
            for v in all_views
            if v["title"].startswith(PREFIX)
        ]
        return jsonify(views)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/preview/<doc_id>")
def preview(doc_id: str):
    """Previsualiza el documento en el navegador."""
    view_id = request.args.get("view_id") or None
    try:
        html = render_document(doc_id, view_id=view_id)
    except ValueError:
        return "Documento no encontrado", 404
    return Response(html, mimetype="text/html")


@app.route("/download/<doc_id>/html")
def download_html(doc_id: str):
    """Descarga el documento como HTML."""
    view_id = request.args.get("view_id") or None
    try:
        html = render_document(doc_id, view_id=view_id)
    except ValueError:
        return "Documento no encontrado", 404
    return Response(
        html,
        mimetype="text/html",
        headers={"Content-Disposition": f"attachment; filename={doc_id}.html"}
    )


@app.route("/download/<doc_id>/pdf")
def download_pdf(doc_id: str):
    """Descarga el documento como PDF."""
    view_id = request.args.get("view_id") or None
    try:
        from weasyprint import HTML
    except ImportError:
        return "WeasyPrint no instalado. Ejecuta: pip install weasyprint", 500
    try:
        html = render_document(doc_id, view_id=view_id)
    except ValueError:
        return "Documento no encontrado", 404
    pdf_bytes = HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{doc_id}.pdf"
    )


if __name__ == "__main__":
    print("🎲 Savage Worlds Generator")
    print("   http://localhost:5000")
    app.run(debug=True, port=5000)