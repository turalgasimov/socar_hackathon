"""Build the deck as one self-contained HTML file, for uploading or emailing:

    python3 pitch/deck/build.py        ->  pitch/RizzML_pitch.html

Scripts, styles, fonts, the GL-04 data and any team photos in team/ are inlined, so the file opens
offline in any browser, from anywhere. Only the live demo needs the app running (http://localhost:8501).
"""
import base64
import json
import re
from pathlib import Path

DECK = Path(__file__).resolve().parent
OUT = DECK.parent / "RizzML_pitch.html"


def js(path: str) -> str:
    # "</script" inside a script would end the tag early; "<\/script" means the same to JavaScript.
    return (DECK / path).read_text(encoding="utf-8").replace("</script", "<\\/script")


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


html = (DECK / "index.html").read_text(encoding="utf-8")
css = (DECK / "deck.css").read_text(encoding="utf-8")
for font in ("archivo-latin.woff2", "archivo-latin-ext.woff2"):
    css = css.replace(f"url(vendor/{font})", f"url({data_uri(DECK / 'vendor' / font, 'font/woff2')})")
gl04 = json.dumps(json.loads((DECK / "data" / "gl04.json").read_text()), separators=(",", ":"))

swaps = {
    '<link rel="stylesheet" href="vendor/reveal.css">': f"<style>{(DECK / 'vendor/reveal.css').read_text()}</style>",
    '<link rel="stylesheet" href="deck.css">': f"<style>{css}</style>",
    '<script src="vendor/reveal.js"></script>': f"<script>{js('vendor/reveal.js')}</script>",
    '<script src="vendor/notes.js"></script>': f"<script>{js('vendor/notes.js')}</script>",
    '<script src="diagrams.js"></script>': f"<script>{js('diagrams.js')}</script>",
    '<script type="module" src="charts.js"></script>':
        f"<script>window.GL04 = {gl04};</script>\n<script type=\"module\">{js('charts.js')}</script>",
}
for old, new in swaps.items():
    assert html.count(old) == 1, f"index.html no longer has: {old}"
    html = html.replace(old, new)


def photo(m: re.Match) -> str:     # team/<name>.jpg if it exists; otherwise the slide shows initials
    path = DECK / m.group(1)
    return f'src="{data_uri(path, "image/jpeg")}"' if path.exists() else m.group(0)


html = re.sub(r'src="(team/[\w-]+\.jpe?g)"', photo, html)
left = [ref for ref in re.findall(r'(?:src|href)="([\w./-]+)"', html)   # real paths, not ${templates} in reveal.js
        if not ref.startswith("team/")]
assert not left, f"still points at local files: {left}"
OUT.write_text(html, encoding="utf-8")
print(f"OK: {OUT.relative_to(DECK.parents[1])}, {OUT.stat().st_size / 1e3:.0f} KB, self-contained")
