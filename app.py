# app.py
# Interfaz web Flask. Solo rutas — la lógica de generación está en generate.py.

from flask import Flask, render_template, jsonify, send_file, Response, request, redirect, url_for
from pathlib import Path
import io
import json
import requests as req
from config import NOCODB_URL, API_TOKEN, TABLE_CONFIG, DOCUMENTS
from nocodb_client import get_table, get_characters, get_character, get_bestiary_entries, get_bestiary_entry, _get_record
from generate import find_doc, doc_type, render_html, render_pdf, render_docx, resolve_view_name, output_filename
from utils import check_environment

check_environment()

app = Flask(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


# ── DOCUMENTOS ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("ui/index.html", documents=DOCUMENTS)


@app.route("/api/status")
def status():
    headers = {"xc-token": API_TOKEN}
    counts = {}
    for key, cfg in TABLE_CONFIG.items():
        try:
            r = req.get(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records?limit=1",
                        headers=headers, timeout=5)
            r.raise_for_status()
            counts[key] = r.json()["pageInfo"]["totalRows"]
        except Exception:
            counts[key] = None
    return jsonify(counts)


@app.route("/api/views/<table_key>")
def get_views(table_key: str):
    if table_key not in TABLE_CONFIG:
        return jsonify({"error": "Tabla no encontrada"}), 404
    try:
        r = req.get(f"{NOCODB_URL}/api/v2/meta/tables/{TABLE_CONFIG[table_key]['table_id']}/views",
                    headers={"xc-token": API_TOKEN}, timeout=5)
        r.raise_for_status()
        PREFIX = "pub:"
        views = [
            {"id": v["id"], "title": v["title"].removeprefix(PREFIX).strip()}
            for v in r.json().get("list", [])
            if v["title"].startswith(PREFIX)
        ]
        return jsonify(views)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/preview/<path:doc_id>")
def preview(doc_id: str):
    view_id = request.args.get("view_id") or None
    try:
        return Response(render_html(doc_id, view_id=view_id), mimetype="text/html")
    except ValueError:
        return "Documento no encontrado", 404


@app.route("/download/<path:doc_id>/html")
def download_html(doc_id: str):
    view_id = request.args.get("view_id") or None
    try:
        html = render_html(doc_id, view_id=view_id)
    except ValueError:
        return "Documento no encontrado", 404
    return Response(html, mimetype="text/html",
                    headers={"Content-Disposition": f"attachment; filename={doc_id}.html"})


@app.route("/download/<path:doc_id>/pdf")
def download_pdf(doc_id: str):
    view_id = request.args.get("view_id") or None
    doc, table_key = find_doc(doc_id)
    if not doc:
        return "Documento no encontrado", 404
    if doc_type(doc) != "html":
        return "Este documento no tiene formato PDF", 400
    try:
        pdf_bytes = render_pdf(doc_id, view_id=view_id)
    except Exception as e:
        return f"Error al generar PDF: {e}", 500
    view_name = resolve_view_name(table_key, view_id)
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=True, download_name=output_filename(doc_id, "pdf", view_name))


@app.route("/download/<path:doc_id>/docx")
def download_docx(doc_id: str):
    view_id = request.args.get("view_id") or None
    doc, table_key = find_doc(doc_id)
    if not doc:
        return "Documento no encontrado", 404
    if doc_type(doc) not in ("docx", "md"):
        return "Este documento no tiene formato Word", 400
    try:
        docx_bytes = render_docx(doc_id, view_id=view_id)
    except Exception as e:
        return f"Error al generar Word: {e}", 500
    view_name = resolve_view_name(table_key, view_id)
    return send_file(io.BytesIO(docx_bytes),
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     as_attachment=True, download_name=output_filename(doc_id, "docx", view_name))


# ── PERSONAJES ────────────────────────────────────────────────────────────

@app.route("/preview/characters")
def preview_characters():
    view_id = request.args.get("view_id") or None
    try:
        return Response(render_html("character.character_sheet", view_id=view_id), mimetype="text/html")
    except ValueError as e:
        return str(e), 404
    except Exception as e:
        return f"Error al cargar personajes: {e}", 500


@app.route("/download/characters/pdf")
def download_characters_pdf():
    view_id = request.args.get("view_id") or None
    doc, table_key = find_doc("character.character_sheet")
    try:
        pdf_bytes = render_pdf("character.character_sheet", view_id=view_id)
    except ValueError as e:
        return str(e), 404
    except Exception as e:
        return f"Error al generar PDF: {e}", 500
    view_name = resolve_view_name(table_key, view_id)
    return send_file(io.BytesIO(pdf_bytes), mimetype="application/pdf",
                     as_attachment=True, download_name=output_filename("character.character_sheet", "pdf", view_name))


# ── GESTIÓN DE PERSONAJES ─────────────────────────────────────────────────

@app.route("/characters")
def characters_list():
    try:
        chars = get_characters(full=True, view_id=TABLE_CONFIG["character"]["view_id"])
    except Exception:
        chars = []
    return render_template("ui/characters.html", characters=chars)


@app.route("/characters/new")
def character_new():
    return render_template("ui/character_form.html", record_id=None, character=None, image_url=None)


@app.route("/characters/<int:record_id>/edit")
def character_edit(record_id: int):
    try:
        result = get_character(record_id)
    except Exception as e:
        return f"Error al cargar personaje: {e}", 500
    return render_template("ui/character_form.html", record_id=record_id,
                           character=result["character"], image_url=result["image_url"])


@app.route("/characters/save", methods=["POST"])
def character_save():
    record_id = request.form.get("record_id") or None
    character_json = request.form.get("character_json", "{}")
    image_file = request.files.get("image")
    cfg = TABLE_CONFIG["character"]
    headers = {"xc-token": API_TOKEN}
    record_data = {"name": json.loads(character_json).get("name", "Sin nombre"), "data": character_json}
    try:
        if record_id:
            record_data["Id"] = int(record_id)
            r = req.patch(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=headers, json=record_data)
        else:
            r = req.post(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=headers, json=record_data)
        r.raise_for_status()
        saved_id = int(record_id) if record_id else (r.json()[0].get("Id") if isinstance(r.json(), list) else r.json().get("Id"))
        if image_file and image_file.filename:
            upload_r = req.post(f"{NOCODB_URL}/api/v2/storage/upload", headers={"xc-token": API_TOKEN},
                                files={"file": (image_file.filename, image_file.stream, image_file.mimetype)})
            upload_r.raise_for_status()
            attachment = upload_r.json()
            if isinstance(attachment, list):
                attachment = attachment[0]
            req.patch(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                      headers=headers, json={"Id": saved_id, "image": [attachment]})
    except Exception as e:
        return f"Error al guardar: {e}", 500
    return redirect(url_for("characters_list"))


@app.route("/characters/<int:record_id>/delete", methods=["POST"])
def character_delete(record_id: int):
    cfg = TABLE_CONFIG["character"]
    try:
        r = req.delete(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                       headers={"xc-token": API_TOKEN}, json={"Id": record_id})
        r.raise_for_status()
    except Exception as e:
        return f"Error al eliminar: {e}", 500
    return redirect(url_for("characters_list"))


@app.route("/api/form-data")
def form_data():
    try:
        return jsonify({
            "skills":     get_table("skill"),
            "edges":      get_table("edge"),
            "hindrances": get_table("hindrance"),
            "powers":     get_table("power"),
            "ancestries": get_table("ancestry"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GESTIÓN DE BESTIARIO ──────────────────────────────────────────────────

@app.route("/bestiary")
def bestiary_list():
    try:
        creatures = get_bestiary_entries(full=True, view_id=TABLE_CONFIG["bestiary"]["view_id"])
    except Exception:
        creatures = []
    return render_template("ui/bestiary.html", creatures=creatures)


@app.route("/bestiary/new")
def bestiary_new():
    return render_template("ui/bestiary_form.html", record_id=None, creature=None, image_url=None)


@app.route("/bestiary/<int:record_id>/edit")
def bestiary_edit(record_id: int):
    try:
        result = get_bestiary_entry(record_id)
    except Exception as e:
        return f"Error al cargar criatura: {e}", 500
    return render_template("ui/bestiary_form.html", record_id=record_id,
                           creature=result["creature"], image_url=result["image_url"])


@app.route("/bestiary/save", methods=["POST"])
def bestiary_save():
    record_id = request.form.get("record_id") or None
    creature_json = request.form.get("creature_json", "{}")
    image_file = request.files.get("image")
    cfg = TABLE_CONFIG["bestiary"]
    headers = {"xc-token": API_TOKEN}
    parsed = json.loads(creature_json)
    record_data = {"name": parsed.get("name", "Sin nombre"), "type": parsed.get("type", ""),
                   "concept": parsed.get("concept", ""), "data": creature_json}
    try:
        if record_id:
            record_data["Id"] = int(record_id)
            r = req.patch(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=headers, json=record_data)
        else:
            r = req.post(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records", headers=headers, json=record_data)
        r.raise_for_status()
        saved_id = int(record_id) if record_id else (r.json()[0].get("Id") if isinstance(r.json(), list) else r.json().get("Id"))
        if image_file and image_file.filename:
            upload_r = req.post(f"{NOCODB_URL}/api/v2/storage/upload", headers={"xc-token": API_TOKEN},
                                files={"file": (image_file.filename, image_file.stream, image_file.mimetype)})
            upload_r.raise_for_status()
            attachment = upload_r.json()
            if isinstance(attachment, list):
                attachment = attachment[0]
            req.patch(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                      headers=headers, json={"Id": saved_id, "image": [attachment]})
    except Exception as e:
        return f"Error al guardar: {e}", 500
    return redirect(url_for("bestiary_list"))


@app.route("/bestiary/<int:record_id>/delete", methods=["POST"])
def bestiary_delete(record_id: int):
    cfg = TABLE_CONFIG["bestiary"]
    try:
        r = req.delete(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                       headers={"xc-token": API_TOKEN}, json={"Id": record_id})
        r.raise_for_status()
    except Exception as e:
        return f"Error al eliminar: {e}", 500
    return redirect(url_for("bestiary_list"))


@app.route("/api/form-data/bestiary")
def form_data_bestiary():
    try:
        return jsonify({
            "skills":     get_table("skill",     view_id=TABLE_CONFIG["skill"]["view_id"]),
            "edges":      get_table("edge",      view_id=TABLE_CONFIG["edge"]["view_id"]),
            "hindrances": get_table("hindrance", view_id=TABLE_CONFIG["hindrance"]["view_id"]),
            "powers":     get_table("power",     view_id=TABLE_CONFIG["power"]["view_id"]),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GESTIÓN DE REGLAS ─────────────────────────────────────────────────────

@app.route("/api/form-data/rules")
def form_data_rules():
    try:
        return jsonify({"books": get_table("reference_book")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/rules")
def rules_list():
    try:
        rules = get_table("rule")
    except Exception:
        rules = []
    return render_template("ui/rules.html", rules=rules)


@app.route("/rules/new")
def rule_new():
    return render_template("ui/rule_form.html", record_id=None, rule=None)


@app.route("/rules/<int:record_id>/edit")
def rule_edit(record_id: int):
    try:
        rule = _get_record("rule", record_id)
    except Exception as e:
        return f"Error al cargar regla: {e}", 500
    return render_template("ui/rule_form.html", record_id=record_id, rule=rule)


@app.route("/rules/save", methods=["POST"])
def rule_save():
    record_id = request.form.get("record_id") or None
    cfg = TABLE_CONFIG["rule"]
    headers = {"xc-token": API_TOKEN}
    ref_book_id = request.form.get("reference_book_id", "").strip()
    record_data = {
        "name":          request.form.get("name", ""),
        "name_original": request.form.get("name_original", ""),
        "description":   request.form.get("description", ""),
        "content":       request.form.get("content", ""),
        "source":        request.form.get("source", "Propio"),
        "icon":          request.form.get("icon", ""),
        "page_no":       int(request.form.get("page_no")) if request.form.get("page_no", "").strip() else None,
    }
    if ref_book_id:
        record_data["nc_a70b___reference_book_id"] = int(ref_book_id)
    try:
        url = f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records"
        if record_id:
            record_data["Id"] = int(record_id)
            r = req.patch(url, headers=headers, json=record_data)
        else:
            r = req.post(url, headers=headers, json=record_data)
        if not r.ok:
            return f"Error al guardar: {r.text}", 500
    except Exception as e:
        return f"Error al guardar: {e}", 500
    return redirect(url_for("rules_list"))


@app.route("/rules/<int:record_id>/delete", methods=["POST"])
def rule_delete(record_id: int):
    cfg = TABLE_CONFIG["rule"]
    try:
        r = req.delete(f"{NOCODB_URL}/api/v2/tables/{cfg['table_id']}/records",
                       headers={"xc-token": API_TOKEN}, json={"Id": record_id})
        r.raise_for_status()
    except Exception as e:
        return f"Error al eliminar: {e}", 500
    return redirect(url_for("rules_list"))


# ── GLOSARIO ───────────────────────────────────────────────────────────────

@app.route("/glossary")
def glossary():
    tabs = [(key, config['label']) for key, config in TABLE_CONFIG.items() if config.get("glossary") is True
            ]
    # tabs = [("power", "Poderes"), ("edge", "Ventajas"), ("hindrance", "Desventajas"), ("skill", "Habilidades")]
    data = {
        key: [{"name": r.get("name") or "", "name_original": r.get("name_original")}
              for r in get_table(key) if r.get("name") and r.get("name_original")]
        for key, _ in tabs
    }
    return render_template("ui/glossary.html", tabs=tabs, data=data)


if __name__ == "__main__":
    print("🎲 Savage Worlds Generator")
    print("   http://localhost:5000")
    app.run(debug=True, port=5000)
