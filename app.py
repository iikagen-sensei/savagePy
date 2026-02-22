# app.py
# Interfaz web para el generador de documentos Savage Worlds.
# Uso: python app.py  →  abre http://localhost:5000

from flask import Flask, render_template, jsonify, send_file, Response, request, redirect, url_for
from pathlib import Path
import io
import json
import requests as req
from config import NOCODB_URL, API_TOKEN, TABLE_CONFIG
from nocodb_client import get_table, get_characters, get_character
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
            "edge_cards_mobile": {"label": "Cartas Móvil", "icon": "📱", "template": "edge_cards_mobile.html", "data_key": "edges"},
        }
    },
    "hindrance": {
        "label": "Desventajas",
        "icon": "☠",
        "docs": {
            "hindrances": {"label": "Manual de Desventajas", "icon": "📖", "template": "hindrances_manual.html", "data_key": "hindrances"},
        }
    },
    "character": {
        "label": "Personajes",
        "icon": "🧙",
        "docs": {
            "character_sheet": {"label": "Ficha de Personaje", "icon": "📄", "template": "character_sheet.html", "data_key": None},
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


# ── PERSONAJES ────────────────────────────────────────────────────────────

@app.route("/preview/characters")
def preview_characters():
    """Previsualiza las fichas de todos los personajes de una vista."""
    view_id = request.args.get("view_id") or None
    try:
        char_list = get_characters(view_id=view_id)
    except Exception as e:
        return f"Error al cargar personajes: {e}", 500
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("character_sheet.html")
    # Renderizar cada personaje y concatenar
    pages = []
    for record in char_list:
        result = get_character(record["Id"])
        if not result["character"]:
            continue
        pages.append(template.render(
            character=result["character"],
            image_url=result["image_url"]
        ))
    if not pages:
        return "No hay personajes con datos en esta vista", 404
    combined = "\n".join(pages)
    return Response(combined, mimetype="text/html")


@app.route("/download/characters/pdf")
def download_characters_pdf():
    """Descarga las fichas de todos los personajes de una vista como un solo PDF."""
    view_id = request.args.get("view_id") or None
    try:
        from weasyprint import HTML as WeasyprintHTML
    except ImportError:
        return "WeasyPrint no instalado. Ejecuta: pip install weasyprint", 500
    try:
        char_list = get_characters(view_id=view_id)
    except Exception as e:
        return f"Error al cargar personajes: {e}", 500
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("character_sheet.html")
    pages = []
    for record in char_list:
        result = get_character(record["Id"])
        if not result["character"]:
            continue  # saltar registros sin datos
        pages.append(template.render(
            character=result["character"],
            image_url=result["image_url"]
        ))
    if not pages:
        return "No hay personajes con datos en esta vista", 404
    combined = "\n".join(pages)
    pdf_bytes = WeasyprintHTML(string=combined, base_url=str(TEMPLATES_DIR)).write_pdf()
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="personajes.pdf"
    )


# ── GESTIÓN DE PERSONAJES ─────────────────────────────────────────────────

@app.route("/characters")
def characters_list():
    """Lista todos los personajes."""
    try:
        chars = get_characters()
    except Exception as e:
        chars = []
    return render_template("ui/characters.html", characters=chars)


@app.route("/characters/new")
def character_new():
    """Formulario de nuevo personaje."""
    return render_template("ui/character_form.html", record_id=None, character=None, image_url=None)


@app.route("/characters/<int:record_id>/edit")
def character_edit(record_id: int):
    """Formulario de edición de personaje existente."""
    try:
        result = get_character(record_id)
    except Exception as e:
        return f"Error al cargar personaje: {e}", 500
    return render_template("ui/character_form.html",
                           record_id=record_id,
                           character=result["character"],
                           image_url=result["image_url"])


@app.route("/characters/save", methods=["POST"])
def character_save():
    """Guarda o actualiza un personaje en NocoDB."""
    import base64
    record_id = request.form.get("record_id") or None
    character_json = request.form.get("character_json", "{}")
    image_file = request.files.get("image")

    cfg = TABLE_CONFIG["character"]
    headers = {"xc-token": API_TOKEN}

    # Preparar datos del registro
    record_data = {
        "name": json.loads(character_json).get("name", "Sin nombre"),
        "data": character_json
    }

    try:
        if record_id:
            # Actualizar registro existente
            url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
            record_data["Id"] = int(record_id)
            r = req.patch(url, headers=headers, json=record_data)
        else:
            # Crear registro nuevo
            url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
            r = req.post(url, headers=headers, json=record_data)
        r.raise_for_status()
        saved_id = int(record_id) if record_id else r.json().get("Id", r.json()[0].get("Id") if isinstance(r.json(), list) else None)

        # Subir imagen si se proporcionó
        if image_file and image_file.filename:
            img_headers = {"xc-token": API_TOKEN}
            # 1. Subir fichero al storage de NocoDB
            upload_url = f"{NOCODB_URL}/api/v2/storage/upload"
            files = {"file": (image_file.filename, image_file.stream, image_file.mimetype)}
            upload_r = req.post(upload_url, headers=img_headers, files=files)
            upload_r.raise_for_status()
            attachment = upload_r.json()
            if isinstance(attachment, list):
                attachment = attachment[0]
            # 2. Asociar el attachment al campo image del registro
            patch_url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
            patch_data = {"Id": saved_id, "image": [attachment]}
            req.patch(patch_url, headers={**img_headers, "Content-Type": "application/json"}, json=patch_data)

    except Exception as e:
        return f"Error al guardar: {e}", 500

    return redirect(url_for("characters_list"))


@app.route("/characters/<int:record_id>/delete", methods=["POST"])
def character_delete(record_id: int):
    """Elimina un personaje."""
    cfg = TABLE_CONFIG["character"]
    headers = {"xc-token": API_TOKEN}
    try:
        url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
        r = req.delete(url, headers=headers, json={"Id": record_id})
        r.raise_for_status()
    except Exception as e:
        return f"Error al eliminar: {e}", 500
    return redirect(url_for("characters_list"))


@app.route("/api/form-data")
def form_data():
    """Devuelve todos los datos necesarios para el formulario de personaje."""
    try:
        skills     = get_table("skill")
        edges      = get_table("edge")
        hindrances = get_table("hindrance")
        powers     = get_table("power")
        ancestries = get_table("ancestry")
        return jsonify({
            "skills":     skills,
            "edges":      edges,
            "hindrances": hindrances,
            "powers":     powers,
            "ancestries": ancestries,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🎲 Savage Worlds Generator")
    print("   http://localhost:5000")
    app.run(debug=True, port=5000)