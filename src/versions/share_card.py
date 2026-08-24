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

# Evolis brand palette (apps/frontend/public/brand/, apps/frontend/lib/styles.ts).
DEEP_FOREST = "#0B2A1E"
EMERALD = "#168B62"
MID_GREEN = "#4AAE70"
MUTED_GREEN = "#5C7A6C"
BORDER_TINT = "#DCEDE3"

# Canonical (English) section keys drive color lookup; display titles are
# localized separately below so Turkish UI mode doesn't need its own color map.
_SECTION_COLORS = {
    "added": EMERALD,
    "improved": EMERALD,
    "declining": "#b26a00",  # kept warm/amber on purpose — a status color, not a brand color
    "deprecated": MUTED_GREEN,
    "emerging": MID_GREEN,
    "known_issues": "#c62828",  # kept red on purpose — an alert, not a brand color
}

_SECTION_TITLES = {
    "en": {"added": "Added", "improved": "Improved", "declining": "Declining Focus", "deprecated": "Deprecated", "emerging": "Emerging Interest", "known_issues": "Known Issues"},
    "tr": {"added": "Eklenen", "improved": "İyileşen", "declining": "Azalan Odak", "deprecated": "Bırakılan", "emerging": "Yükselen İlgi", "known_issues": "Dikkat Edilecekler"},
}


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


def _build_lines(notes: dict, lang: str = "en") -> list[tuple[str, str]]:
    """Returns (text, color) pairs for every line below the title, reusing
    the same sectioning render_release_notes() already computed."""
    lines: list[tuple[str, str]] = []
    titles = _SECTION_TITLES["tr" if lang == "tr" else "en"]

    def add_section(key: str, items: list[str]):
        if not items:
            return
        title = titles[key]
        lines.append((title, DEEP_FOREST))
        for item in items:
            lines.append((item, _SECTION_COLORS.get(key, DEEP_FOREST)))
        lines.append(("", "#000000"))  # spacer

    add_section("added", [f"+ {t}" for t in notes["added"]])
    add_section("improved", notes["improved"])
    add_section("declining", [f"- {t}" for t in notes["declining"]])
    add_section("deprecated", [f"- {t}" for t in notes["deprecated"]])
    add_section("emerging", [f"→ {t}" for t in notes["emerging"]])
    add_section("known_issues", notes["known_issues"])

    if lines and lines[-1] == ("", "#000000"):
        lines.pop()

    return lines


def render_release_notes_svg(notes: dict, lang: str = "en") -> str:
    """notes = the dict returned by src.versions.release_notes.render_release_notes()."""
    lines = _build_lines(notes, lang)
    height = HEADER_HEIGHT + PADDING + max(len(lines), 1) * LINE_HEIGHT + PADDING
    section_titles = set(_SECTION_TITLES["tr" if lang == "tr" else "en"].values())

    body_lines = []
    y = HEADER_HEIGHT + PADDING
    for text, color in lines:
        if text:
            weight = "600" if text in section_titles else "400"
            body_lines.append(
                f'<text x="{PADDING}" y="{y}" font-family="ui-monospace, Menlo, monospace" '
                f'font-size="16" font-weight="{weight}" fill="{color}">{_escape(text)}</text>'
            )
        y += LINE_HEIGHT

    # The icon mark, scaled/translated from apps/frontend/public/brand/evolis-icon.svg
    # (same three-ribbon paths, same gradient stops) so the card matches the
    # rest of the product instead of inventing its own mark.
    icon = f"""<g transform="translate({PADDING} 16) scale(.09)">
    <path d="M137 119C163 84 201 68 245 68H389C391 109 368 132 329 132H243C207 132 178 145 157 170L137 194V119Z" fill="url(#evolis-card-g1)"/>
    <path d="M137 213C163 178 201 162 245 162H389C391 203 368 226 329 226H243C207 226 178 239 157 264L137 288V213Z" fill="url(#evolis-card-g2)"/>
    <path d="M137 307C162 274 200 256 243 256H324C365 256 389 279 389 320H251C221 320 198 330 180 350C194 372 219 384 253 384H345C374 384 392 400 398 433H249C184 433 137 393 137 334V307Z" fill="url(#evolis-card-g3)"/>
  </g>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_WIDTH}" height="{height}" viewBox="0 0 {CARD_WIDTH} {height}">
  <defs>
    <linearGradient id="evolis-card-g1" x1="124" y1="84" x2="386" y2="162" gradientUnits="userSpaceOnUse">
      <stop stop-color="#C7F36A"/><stop offset="1" stop-color="{MID_GREEN}"/>
    </linearGradient>
    <linearGradient id="evolis-card-g2" x1="126" y1="196" x2="389" y2="258" gradientUnits="userSpaceOnUse">
      <stop stop-color="{EMERALD}"/><stop offset="1" stop-color="#5DBA7E"/>
    </linearGradient>
    <linearGradient id="evolis-card-g3" x1="128" y1="300" x2="390" y2="386" gradientUnits="userSpaceOnUse">
      <stop stop-color="{DEEP_FOREST}"/><stop offset="1" stop-color="#69B968"/>
    </linearGradient>
  </defs>
  <rect width="{CARD_WIDTH}" height="{height}" fill="#ffffff" stroke="{BORDER_TINT}" stroke-width="1" rx="16"/>
  {icon}
  <text x="{PADDING + 46}" y="44" font-family="ui-monospace, Menlo, monospace" font-size="22" font-weight="700" fill="{DEEP_FOREST}">EVOLIS</text>
  <text x="{PADDING}" y="70" font-family="ui-monospace, Menlo, monospace" font-size="16" fill="{MUTED_GREEN}">YOU v{_escape(notes['base'])} &#8594; YOU v{_escape(notes['target'])}</text>
  <line x1="{PADDING}" y1="{HEADER_HEIGHT}" x2="{CARD_WIDTH - PADDING}" y2="{HEADER_HEIGHT}" stroke="{BORDER_TINT}" stroke-width="1"/>
  {''.join(body_lines)}
</svg>"""
