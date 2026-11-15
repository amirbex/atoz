#!/usr/bin/env python3
"""Generate the bilingual, outlined logo-use sheet from brand tokens."""
import json
import os
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(__file__))
import build_logo as logo  # reuses HarfBuzz/fontTools outlined text + mark geometry

TOKENS = json.load(open(os.path.join(ROOT, "brand", "tokens.json"), encoding="utf-8"))
NAVY = TOKENS["color"]["strategic_navy"]["hex"]
GOLD = TOKENS["color"]["innovation_gold"]["hex"]
SURFACE = TOKENS["color"]["neutral_surface"]["hex"]
WHITE = TOKENS["color"]["pure_white"]["hex"]
OUT = os.path.join(ROOT, "logo", "guidelines", "svg", "logo-guidelines.svg")
parts = []


def rect(x, y, w, h, fill=WHITE, stroke="none", rx=18, extra=""):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" {extra}/>')


def line(x1, y1, x2, y2, color="#D5DCE6", width=2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    parts.append(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="{width}"{d}/>')


def text(text_value, x, y, width, size, font, fill=NAVY, rtl=False):
    run = {"font": font, "text": text_value, "size": size, "fill": fill}
    if rtl:
        run.update(direction="rtl", script="arab", language="fa")
    runs = logo.scale_to_width([run], width, rtl=rtl)
    frag, _, _ = logo.line_svg(runs, rtl=rtl)
    parts.append(f'<g transform="translate({x},{y})">{frag}</g>')


def fa(value, x, y, width, size=28, fill=NAVY):
    text(value, x, y, width, size, "Vazirmatn-Bold.ttf", fill, rtl=True)


def en(value, x, y, width, size=28, fill=NAVY, font="Montserrat-Bold.ttf"):
    text(value, x, y, width, size, font, fill)

# Page background and title band.
parts.append(f'<rect width="1600" height="1200" fill="{SURFACE}"/>')
en("Logo use guide", 70, 48, 590, 72)
fa("راهنمای استفاده از لوگو", 860, 57, 670, 53)
line(70, 145, 1530, 145, GOLD, 5)
en("AtoZfnb.info  /  Phase 1", 72, 165, 390, 24, NAVY, "Montserrat-SemiBold.ttf")
fa("نسخه‌های رسمی، حریم امن و حداقل اندازه", 1000, 166, 530, 24, NAVY)

# Clear-space card with scaled symbol and a dotted exclusion zone.
rect(70, 215, 710, 455)
en("Clearspace", 100, 238, 260, 38)
fa("حریم امن", 550, 242, 190, 31)
# x = scaled gold-dot diameter (104 native units * 0.40 scale).
scale = 0.27
unit = 2 * logo.DOT[2] * scale
mark_w = logo.SYM_W * scale
mark_h = logo.SYM_H * scale
mark_x, mark_y = 270, 360
zone_x, zone_y = mark_x - unit, mark_y - unit
zone_w, zone_h = mark_w + 2 * unit, mark_h + 2 * unit
parts.append(f'<rect x="{zone_x:.1f}" y="{zone_y:.1f}" width="{zone_w:.1f}" height="{zone_h:.1f}" rx="8" fill="none" stroke="{GOLD}" stroke-width="3" stroke-dasharray="10 8"/>')
parts.append(f'<g transform="translate({mark_x - logo.SYM_X0*scale:.2f} {mark_y - logo.SYM_Y0*scale:.2f}) scale({scale})">{logo.symbol_group("color")}</g>')
# Dimension key and explanation.
line(106, 605, 147, 605, GOLD, 3)
line(106, 596, 106, 614, GOLD, 3); line(147, 596, 147, 614, GOLD, 3)
en("x", 111, 622, 30, 19, GOLD)
en("x = dot diameter", 165, 620, 220, 19, NAVY, "Montserrat-SemiBold.ttf")
fa("x = قطر نقطه طلایی", 435, 620, 270, 18, NAVY)

# Minimum size card, sourced directly from the tokens.
rect(805, 215, 725, 455)
en("Minimum reproduction size", 835, 238, 380, 34)
fa("حداقل اندازه بازتولید", 1230, 243, 260, 25)
line(835, 292, 1500, 292, "#E3E8EF", 2)
rows = [
    ("Horizontal lockup", "لاک‌آپ افقی", "30 mm  /  120 px", "horizontal_lockup"),
    ("Vertical lockup", "لاک‌آپ عمودی", "25 mm  /  100 px", "vertical_lockup"),
    ("Full lockup", "لاک‌آپ کامل", "30 mm  /  120 px", "full_lockup"),
    ("Symbol only", "نماد تنها", "8 mm  /  24 px", "symbol_only"),
    ("Wordmark only", "نوشتار تنها", "20 mm  /  80 px", "wordmark_only"),
]
for i, (label_en, label_fa, _display, key) in enumerate(rows):
    y = 307 + i * 67
    minv = TOKENS["logo"]["min_size"][key]
    en(label_en, 840, y, 245, 24, NAVY, "Montserrat-SemiBold.ttf")
    fa(label_fa, 1115, y + 1, 185, 22)
    en(f'{minv["print_mm"]} mm  /  {minv["digital_px"]} px', 1335, y, 165, 19, NAVY, "Montserrat-SemiBold.ttf")
    if i < len(rows)-1:
        line(840, y + 49, 1500, y + 49, "#EEF1F5", 1)
fa(TOKENS["logo"]["min_size"]["note_fa"], 840, 635, 660, 17, NAVY)

# Approved usage and misuse rules.
rect(70, 700, 1460, 430)
en("Approved variants", 100, 724, 430, 36)
fa("نسخه‌های مجاز", 1260, 728, 230, 27)
# Three compact approved variant swatches.
for x, title, variant, background in [
    (105, "Color on light", "color", WHITE),
    (590, "Mono on light", "mono", WHITE),
    (1075, "White on dark", "white", NAVY),
]:
    rect(x, 780, 420, 150, background, "#E3E8EF" if background == WHITE else "none", 12)
    # centered mark display; label below
    en(title, x + 105, 790, 210, 18, WHITE if background == NAVY else NAVY, "Montserrat-SemiBold.ttf")
    sm = 0.14
    dx = x + 132
    dy = 820
    parts.append(f'<g transform="translate({dx - logo.SYM_X0*sm:.2f} {dy - logo.SYM_Y0*sm:.2f}) scale({sm})">{logo.symbol_group(variant)}</g>')
# Rules in two columns, token-driven list.
line(100, 952, 1500, 952, "#E3E8EF", 2)
en("Never", 105, 973, 120, 22, GOLD)
fa("انجام ندهید", 270, 976, 150, 21, GOLD)
misuse_en = [
    "Do not stretch, squash, rotate or skew the artwork.",
    "Do not recolor, add effects, outlines or gradients.",
    "Do not place the logo on a low-contrast background.",
]
misuse_fa = [
    "لوگو را نکشید، فشرده، چرخان یا کج نکنید.",
    "رنگ را تغییر ندهید و افکت، دورخط یا گرادیان ندهید.",
    "لوگو را روی پس‌زمینه کم‌کنتراست قرار ندهید.",
]
for i, (a, b) in enumerate(zip(misuse_en, misuse_fa)):
    y = 1005 + i * 37
    parts.append(f'<circle cx="118" cy="{y+9}" r="5" fill="{GOLD}"/>')
    en(a, 137, y, 620, 18, NAVY, "Montserrat-SemiBold.ttf")
    fa(b, 820, y + 1, 670, 18, NAVY)

svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" '
       'role="img" aria-label="AtoZfnb.info bilingual logo use guide">\n'
       '<title>AtoZfnb.info — Logo use guide / راهنمای استفاده از لوگو</title>\n'
       '<desc>Clearspace, minimum size, approved variants and misuse rules generated from brand tokens.</desc>\n'
       + "\n".join(parts) + "\n</svg>\n")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Generated {os.path.relpath(OUT, ROOT)}")
