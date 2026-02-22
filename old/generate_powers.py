# generate_powers.py
# Genera el manual de poderes en HTML (y opcionalmente PDF).
#
# Uso:
#   python generate_powers.py                    → powers_manual.html
#   python generate_powers.py --output mi.html   → nombre personalizado
#   python generate_powers.py --pdf              → también genera PDF
#   python generate_powers.py --json             → también guarda el JSON

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from nocodb_client import get_table


def render_html(data: dict, template_path: Path, output_path: Path):
    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    template = env.get_template(template_path.name)
    html = template.render(**data)
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
    parser.add_argument("--output", default="powers_manual.html")
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    print("📡 Consultando NocoDB...")
    powers = get_table("power")
    print(f"   → {len(powers)} poderes obtenidos")

    template_data = {"powers": powers}

    if args.json:
        json_path = Path(args.output).with_suffix(".json")
        json_path.write_text(json.dumps(powers, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ JSON guardado: {json_path}")

    template_path = Path(__file__).parent / "templates" / "powers_manual.html"
    output_path = Path(args.output)

    render_html(template_data, template_path, output_path)

    if args.pdf:
        pdf_path = output_path.with_suffix(".pdf")
        render_pdf(output_path, pdf_path)


if __name__ == "__main__":
    main()
