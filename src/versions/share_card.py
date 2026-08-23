"""Social Share Cards — sections 28 & 41.

Renders a release-notes dict (src/versions/release_notes.py) as a
self-contained SVG image: no image library dependency (Pillow, etc.), no
font-rendering environment to get right server-side, and it scales cleanly
wherever it's displayed (an <img>, downloaded, or converted to PNG
client-side). This is the "shareable visual card" the product spec
describes for Release Notes For You.
"""
from __future__ import annotations

import html

CARD_WIDTH = 640
LINE_HEIGHT = 26
PADDING = 32
HEADER_HEIGHT = 90

_SECTION_COLORS = {
    "Added": "#2e7d32",
    "Improved": "#2e7d32",
    "Declining Focus": "#b26a00",
    "Deprecated": "#757575",
    "Emerging Interest": "#1565c0",
    "Known Issues": "#c62828",
}


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


def _build_lines(notes: dict) -> list[tuple[str, str]]:
    """Returns (text, color) pairs for every line below the title, reusing
    the same sectioning render_release_notes() already computed."""
    lines: list[tuple[str, str]] = []

    def add_section(title: str, items: list[str]):
        if not items:
            return
        lines.append((title, "#111111"))
        for item in items:
            lines.append((item, _SECTION_COLORS.get(title, "#333333")))
        lines.append(("", "#000000"))  # spacer

    add_section("Added", [f"+ {t}" for t in notes["added"]])
    add_section("Improved", notes["improved"])
    add_section("Declining Focus", [f"- {t}" for t in notes["declining"]])
    add_section("Deprecated", [f"- {t}" for t in notes["deprecated"]])
    add_section("Emerging Interest", [f"→ {t}" for t in notes["emerging"]])
    add_section("Known Issues", notes["known_issues"])

    if lines and lines[-1] == ("", "#000000"):
        lines.pop()

    return lines


def render_release_notes_svg(notes: dict) -> str:
    """notes = the dict returned by src.versions.release_notes.render_release_notes()."""
    lines = _build_lines(notes)
    height = HEADER_HEIGHT + PADDING + max(len(lines), 1) * LINE_HEIGHT + PADDING

    body_lines = []
    y = HEADER_HEIGHT + PADDING
    for text, color in lines:
        if text:
            weight = "600" if text in {"Added", "Improved", "Declining Focus", "Deprecated", "Emerging Interest", "Known Issues"} else "400"
            body_lines.append(
                f'<text x="{PADDING}" y="{y}" font-family="ui-monospace, Menlo, monospace" '
                f'font-size="16" font-weight="{weight}" fill="{color}">{_escape(text)}</text>'
            )
        y += LINE_HEIGHT

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_WIDTH}" height="{height}" viewBox="0 0 {CARD_WIDTH} {height}">
  <rect width="{CARD_WIDTH}" height="{height}" fill="#ffffff" stroke="#e5e5e5" stroke-width="1" rx="16"/>
  <text x="{PADDING}" y="44" font-family="ui-monospace, Menlo, monospace" font-size="22" font-weight="700" fill="#111111">LifeDiff</text>
  <text x="{PADDING}" y="70" font-family="ui-monospace, Menlo, monospace" font-size="16" fill="#666666">YOU v{_escape(notes['base'])} &#8594; YOU v{_escape(notes['target'])}</text>
  <line x1="{PADDING}" y1="{HEADER_HEIGHT}" x2="{CARD_WIDTH - PADDING}" y2="{HEADER_HEIGHT}" stroke="#eeeeee" stroke-width="1"/>
  {''.join(body_lines)}
</svg>"""
