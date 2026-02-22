"""
generate_powers.py
Genera el manual de poderes en HTML a partir de NocoDB.

Uso:
    python generate_powers.py                    # genera powers_manual.html
    python generate_powers.py --output mi.html   # nombre personalizado
    python generate_powers.py --pdf              # también genera PDF (requiere weasyprint)
"""

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from nocodb_client import build_powers_json


def render_html(powers: list[dict], template_path: Path, output_path: Path):
    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    template = env.get_template(template_path.name)
    html = template.render(powers=powers)
    output_path.write_text(html, encoding="utf-8")
    print(f"✅ HTML generado: {output_path}")


def render_pdf(html_path: Path, pdf_path: Path):
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        print(f"✅ PDF generado: {pdf_path}")
    except ImportError:
        print("⚠️  WeasyPrint no instalado. Instálalo con: pip install weasyprint")


def main():
    parser = argparse.ArgumentParser(description="Genera el manual de poderes")
    parser.add_argument("--output", default="powers_manual.html", help="Nombre del archivo HTML de salida")
    parser.add_argument("--pdf", action="store_true", help="Generar también PDF con WeasyPrint")
    parser.add_argument("--json", action="store_true", help="Guardar también el JSON combinado")
    args = parser.parse_args()

    print("📡 Consultando NocoDB...")
    powers = build_powers_json()
    print(f"   → {len(powers)} poderes obtenidos")

    if args.json:
        json_path = Path(args.output).with_suffix(".json")
        json_path.write_text(json.dumps(powers, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ JSON guardado: {json_path}")

    template_path = Path(__file__).parent / "powers_template.html"
    output_path = Path(args.output)

    render_html(powers, template_path, output_path)

    if args.pdf:
        pdf_path = output_path.with_suffix(".pdf")
        render_pdf(output_path, pdf_path)


if __name__ == "__main__":
    main()