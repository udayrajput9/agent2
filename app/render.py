from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

TEMPLATES_DIR = Path("app/templates")
STATIC_CSS = Path("app/static/css/style.css")

_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def _render_map_html(plan: dict) -> str:
    partial = _env.get_template("partials/treasure_map.html")
    map_html = partial.render(plan=plan)
    css = STATIC_CSS.read_text(encoding="utf-8")
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
{css}
body {{ margin: 0; background: #1a1a2e; }}
.render-wrap {{ width: 900px; }}
</style></head>
<body><div class="render-wrap">{map_html}</div></body></html>"""


def map_to_png(plan: dict) -> bytes:
    html = _render_map_html(plan)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 650})
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(300)
        element = page.query_selector("#treasure-map")
        png_bytes = element.screenshot() if element else page.screenshot()
        browser.close()
    return png_bytes
