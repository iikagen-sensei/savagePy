# generate.py
# Script central. Genera uno o varios documentos de un tirón.
#
# Uso:
#   python generate.py --all                     → genera todo
#   python generate.py --powers                  → manual de poderes
#   python generate.py --cards                   → cartas de poderes
#   python generate.py --edges                   → manual de ventajas
#   python generate.py --hindrances              → manual de desventajas
#   python generate.py --powers --cards --pdf    → varios + PDF

import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from nocodb_client import get_table

TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR    = Path(__file__).parent / "output"


def render(template_name: str, data: dict, output_name: str, to_pdf: bool = False):
    OUTPUT_DIR.mkdir(exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(template_name)
    html = template.render(**data)

    html_path = OUTPUT_DIR / output_name
    html_path.write_text(html, encoding="utf-8")
    print(f"  ✅ {html_path}")

    if to_pdf:
        try:
            from weasyprint import HTML
            pdf_path = html_path.with_suffix(".pdf")
            HTML(filename=str(html_path)).write_pdf(str(pdf_path))
            print(f"  ✅ {pdf_path}")
        except ImportError:
            print("  ⚠️  WeasyPrint no instalado: pip install weasyprint")


def main():
    parser = argparse.ArgumentParser(description="Generador de documentos Savage Worlds")
    parser.add_argument("--all",        action="store_true", help="Generar todos los documentos")
    parser.add_argument("--powers",     action="store_true", help="Manual de poderes")
    parser.add_argument("--cards",      action="store_true", help="Cartas de poderes")
    parser.add_argument("--edges",      action="store_true", help="Manual de ventajas")
    parser.add_argument("--hindrances", action="store_true", help="Manual de desventajas")
    parser.add_argument("--pdf",        action="store_true", help="Generar también PDF")
    args = parser.parse_args()

    # Si no se especifica nada, mostrar ayuda
    if not any([args.all, args.powers, args.cards, args.edges, args.hindrances]):
        parser.print_help()
        return

    do_powers     = args.all or args.powers
    do_cards      = args.all or args.cards
    do_edges      = args.all or args.edges
    do_hindrances = args.all or args.hindrances

    # Cargar datos solo si se necesitan
    powers_data = None
    if do_powers or do_cards:
        print("📡 Cargando poderes...")
        powers_data = get_table("power")
        print(f"   → {len(powers_data)} poderes")

    edges_data = None
    if do_edges:
        print("📡 Cargando ventajas...")
        edges_data = get_table("edge")
        print(f"   → {len(edges_data)} ventajas")

    hindrances_data = None
    if do_hindrances:
        print("📡 Cargando desventajas...")
        hindrances_data = get_table("hindrance")
        print(f"   → {len(hindrances_data)} desventajas")

    print("\n📄 Generando documentos...")

    if do_powers:
        render("powers_manual.html", {"powers": powers_data}, "powers_manual.html", args.pdf)

    if do_cards:
        render("power_cards.html", {"powers": powers_data}, "power_cards.html", args.pdf)

    if do_edges:
        render("edges_manual.html", {"edges": edges_data}, "edges_manual.html", args.pdf)

    if do_hindrances:
        render("hindrances_manual.html", {"hindrances": hindrances_data}, "hindrances_manual.html", args.pdf)

    print(f"\n✨ Listo. Archivos en: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
