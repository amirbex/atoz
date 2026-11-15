#!/usr/bin/env python3
"""
AtoZfnb.info — Logo lockup generator (Phase 1).

Reads brand/tokens.json and writes pure-vector SVG lockups (all text outlined
to paths, Persian shaped with HarfBuzz) into logo/{fa,en,shared}/svg/.

Outputs (x3 variants: color / mono / white):
  symbol, wordmark-latin, wordmark-fa,
  horizontal-latin, horizontal-fa, vertical-latin, vertical-fa,
  full-latin, full-fa

Usage:
    pip install -r tools/requirements.txt
    python3 tools/build_logo.py
    cd tools && npm install && npm run render-png   # PNG exports via sharp
"""

import json
import os

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
import uharfbuzz as hb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS_PATH = os.path.join(ROOT, "brand", "tokens.json")
FONTS_DIR = os.path.join(ROOT, "tools", "fonts")
OUT_ROOT = os.path.join(ROOT, "logo")

with open(TOKENS_PATH, encoding="utf-8") as f:
    TOKENS = json.load(f)

BRAND_NAME = TOKENS["brand"]["name_latin_display"]
GOLD = TOKENS["color"]["innovation_gold"]["hex"]

VARIANTS = {
    name: {
        "mark": value["mark"],
        "dot": value["dot"],
        "main": value["wordmark_main"],
        "accent": value["wordmark_accent"],
    }
    for name, value in TOKENS["logo"]["variants"].items()
}

# ---------------------------------------------------------------------------
# Reference-faithful vector mark geometry. All values live in brand tokens.
# ---------------------------------------------------------------------------
GEOMETRY = TOKENS["logo"]["geometry"]
SYM_X0, SYM_Y0, SYM_W, SYM_H = GEOMETRY["symbol_bbox"]
CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H = GEOMETRY["symbol_canvas"]
SYMBOL_VIEWBOX = f"{SYM_X0 - 20} {SYM_Y0 - 20} {SYM_W + 40} {SYM_H + 40}"
MARK_PATH = GEOMETRY["mark_path"]
MARK_TRANSFORM = GEOMETRY["mark_transform"]
DOT = tuple(GEOMETRY["gold_dot"])


def symbol_group(variant, dot_override=None):
    """SVG fragment for the vector-traced AZ emblem with a token-colored dot."""
    v = VARIANTS[variant]
    cx, cy, r = DOT
    dot = dot_override or v["dot"]
    return (
        f'<path d="{MARK_PATH}" transform="{MARK_TRANSFORM}" fill="{v["mark"]}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{dot}"/>'
    )


# ---------------------------------------------------------------------------
# Text outlining (HarfBuzz shaping + fontTools outlines -> SVG paths)
# ---------------------------------------------------------------------------
_font_cache = {}


def _load_font(font_file):
    if font_file not in _font_cache:
        path = os.path.join(FONTS_DIR, font_file)
        ttfont = TTFont(path)
        blob = hb.Blob.from_file_path(path)
        face = hb.Face(blob)
        font = hb.Font(face)
        font.scale = (face.upem, face.upem)
        _font_cache[font_file] = (ttfont, font, face.upem)
    return _font_cache[font_file]


def shape_run(font_file, text, size, direction="ltr", script=None, language=None):
    """
    Shape text and return (glyphs, width, bbox).
    glyphs: list of (path_d, x, y, scale) with baseline at y=0, x from 0.
    bbox: (x0, y0, x1, y1) in the same local coords (y grows downward).
    """
    ttfont, font, upem = _load_font(font_file)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.direction = direction
    if script:
        buf.script = script
    if language:
        buf.language = language
    hb.shape(font, buf)

    order = ttfont.getGlyphOrder()
    glyph_set = ttfont.getGlyphSet()
    glyf = ttfont["glyf"]
    s = size / upem
    glyphs = []
    cursor = 0.0
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        gx = cursor + pos.x_offset * s
        gy = -pos.y_offset * s
        pen = SVGPathPen(glyph_set)
        glyph_set[name].draw(pen)
        d = pen.getCommands()
        if d:
            glyphs.append((d, gx, gy, s))
            g = glyf[name]
            if hasattr(g, "xMin"):
                x0 = min(x0, gx + g.xMin * s)
                x1 = max(x1, gx + g.xMax * s)
                y0 = min(y0, gy - g.yMax * s)
                y1 = max(y1, gy - g.yMin * s)
        cursor += pos.x_advance * s
    if x0 == float("inf"):
        x0 = y0 = x1 = y1 = 0.0
    return glyphs, cursor, (x0, y0, x1, y1)


def space_width(font_file, size):
    ttfont, _, upem = _load_font(font_file)
    return ttfont["hmtx"]["space"][0] * size / upem


def line_svg(runs, rtl=False):
    """
    Build one text line from runs placed left->right (or right->left if rtl).
    Each run: dict(font, text, size, direction, script, language, fill, gap_after)
    Returns (svg_fragment, width, height). The fragment is pre-translated so
    its content occupies y in [0, height]; baseline sits at y = top.
    """
    shaped = []
    for run in runs:
        glyphs, w, bbox = shape_run(
            run["font"], run["text"], run["size"],
            run.get("direction", "ltr"), run.get("script"), run.get("language"))
        shaped.append((run, glyphs, w, bbox))

    # Assign x offsets.
    offsets = []
    if rtl:
        # First run is rightmost.
        total = sum(w for _, _, w, _ in shaped) + \
            sum(r.get("gap_after", 0) for r, _, _, _ in shaped[:-1])
        x = total
        for run, glyphs, w, bbox in shaped:
            x -= w
            offsets.append(x)
            x -= run.get("gap_after", 0)
        total_w = total
    else:
        x = 0.0
        for run, glyphs, w, bbox in shaped:
            offsets.append(x)
            x += w + run.get("gap_after", 0)
        total_w = x - (shaped[-1][0].get("gap_after", 0) if shaped else 0)

    parts = []
    y0 = float("inf")
    y1 = float("-inf")
    for (run, glyphs, w, bbox), ox in zip(shaped, offsets):
        for d, gx, gy, s in glyphs:
            parts.append(
                f'<path d="{d}" fill="{run["fill"]}" '
                f'transform="translate({ox + gx:.2f} {gy:.2f}) scale({s:.5f} {-s:.5f})"/>')
        y0 = min(y0, bbox[1])
        y1 = max(y1, bbox[3])
    if y0 == float("inf"):
        y0 = y1 = 0.0
    body = "".join(parts)
    if y0 != 0.0:
        body = f'<g transform="translate(0 {-y0:.2f})">{body}</g>'
    return body, total_w, y1 - y0


def scale_to_width(runs, target_width, rtl=False):
    """Scale all run sizes so the line width equals target_width."""
    # Measure at size 100 for the first run's font as reference is not enough
    # (mixed fonts) — measure each run at its own size then compute factor.
    _, w, _ = line_svg(runs, rtl=rtl)
    factor = target_width / w if w else 1.0
    scaled = []
    for run in runs:
        r2 = dict(run)
        r2["size"] = run["size"] * factor
        if "gap_after" in r2:
            r2["gap_after"] = r2["gap_after"] * factor
        scaled.append(r2)
    return scaled


def latin_wordmark_runs(variant, size=100):
    v = VARIANTS[variant]
    wordmark = TOKENS["brand"]["name_latin_display"]
    accent_chars = set(TOKENS["logo"]["wordmark_latin_accent_chars"])
    runs = []
    current, current_accent = "", None
    for char in wordmark:
        accent = char in accent_chars
        if current and accent != current_accent:
            runs.append({"font": "Montserrat-ExtraBold.ttf", "text": current,
                         "size": size, "fill": v["accent"] if current_accent else v["main"]})
            current = ""
        current += char
        current_accent = accent
    if current:
        runs.append({"font": "Montserrat-ExtraBold.ttf", "text": current,
                     "size": size, "fill": v["accent"] if current_accent else v["main"]})
    return runs


def fa_wordmark_runs(variant, size=100):
    v = VARIANTS[variant]
    words = TOKENS["brand"]["name_fa_parts"]
    if len(words) != 2:
        raise ValueError("brand.name_fa_parts must contain exactly two wordmark segments")
    gap = space_width("Vazirmatn-ExtraBold.ttf", size)
    return [
        {"font": "Vazirmatn-ExtraBold.ttf", "text": words[0], "size": size,
         "direction": "rtl", "script": "arab", "language": "fa",
         "fill": v["accent"], "gap_after": gap},
        {"font": "Vazirmatn-ExtraBold.ttf", "text": words[1], "size": size,
         "direction": "rtl", "script": "arab", "language": "fa", "fill": v["main"]},
    ]


def fa_domain_run(variant, size=100):
    v = VARIANTS[variant]
    return [{"font": "Montserrat-SemiBold.ttf", "text": TOKENS["brand"]["domain"],
             "size": size, "fill": v["main"]}]


def fa_name_run(variant, size=100):
    v = VARIANTS[variant]
    return [{"font": "Vazirmatn-Bold.ttf", "text": TOKENS["brand"]["founder_fa"], "size": size,
             "direction": "rtl", "script": "arab", "language": "fa", "fill": v["main"]}]


def fa_title_runs(variant, size=100):
    v = VARIANTS[variant]
    title_fa = TOKENS["brand"]["title_fa"]
    fa_part, latin_part = title_fa.rsplit(" ", 1)
    gap = space_width("Vazirmatn-Medium.ttf", size)
    return [
        {"font": "Vazirmatn-Medium.ttf", "text": fa_part, "size": size,
         "direction": "rtl", "script": "arab", "language": "fa",
         "fill": v["main"], "gap_after": gap},
        {"font": "Montserrat-SemiBold.ttf", "text": latin_part, "size": size, "fill": v["main"]},
    ]


def latin_name_run(variant, size=100):
    v = VARIANTS[variant]
    return [{"font": "Montserrat-Bold.ttf", "text": TOKENS["brand"]["founder_latin"],
             "size": size, "fill": v["main"]}]


def latin_title_run(variant, size=100):
    v = VARIANTS[variant]
    return [{"font": "Montserrat-SemiBold.ttf", "text": TOKENS["brand"]["title_latin"],
             "size": size, "fill": v["main"]}]


# ---------------------------------------------------------------------------
# Lockup builders. Each returns (svg_inner, viewBox) with content placed so
# that the lockup bbox starts at (0, 0).
# ---------------------------------------------------------------------------
PAD = 20


def _svg_doc(inner, viewbox, title, desc):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" '
        f'role="img" aria-label="{title}">\n'
        f'<title>{title}</title>\n<desc>{desc}</desc>\n{inner}\n</svg>\n'
    )


def _place_symbol(dx, dy, scale=1.0):
    # Symbol native coords -> lockup coords, using the token-defined bbox origin.
    return f'<g transform="translate({dx - SYM_X0 * scale:.2f} {dy - SYM_Y0 * scale:.2f}) ' \
           f'scale({scale:.4f})">'


def build_symbol(variant):
    inner = symbol_group(variant)
    return _svg_doc(inner, SYMBOL_VIEWBOX,
                    f"{BRAND_NAME} symbol ({variant})",
                    "AZ monogram with growth arrow — symbol only.")


def build_wordmark_latin(variant):
    runs = scale_to_width(latin_wordmark_runs(variant), 1200)
    frag, w, h = line_svg(runs)
    vb = f"{-PAD} {-PAD} {w + 2 * PAD:.1f} {h + 2 * PAD:.1f}"
    inner = frag
    return _svg_doc(inner, vb, f"{BRAND_NAME} wordmark ({variant})",
                    "Latin wordmark only.")


def build_wordmark_fa(variant):
    runs = scale_to_width(fa_wordmark_runs(variant), 1200, rtl=True)
    frag1, w1, h1 = line_svg(runs, rtl=True)
    dom = scale_to_width(fa_domain_run(variant), 640)
    frag2, w2, h2 = line_svg(dom)
    gap = 28
    total_h = h1 + gap + h2
    x1 = (max(w1, w2) - w1) / 2
    x2 = (max(w1, w2) - w2) / 2
    inner = (f'<g transform="translate({x1:.1f} 0)">{frag1}</g>'
             f'<g transform="translate({x2:.1f} {h1 + gap:.1f})">{frag2}</g>')
    vb = f"{-PAD} {-PAD} {max(w1, w2) + 2 * PAD:.1f} {total_h + 2 * PAD:.1f}"
    return _svg_doc(inner, vb, f"{BRAND_NAME} wordmark FA ({variant})",
                    "Persian wordmark only.")


def build_vertical_latin(variant):
    runs = scale_to_width(latin_wordmark_runs(variant), 1294)
    frag, w, h = line_svg(runs)
    gap = 110
    total_w = max(SYM_W, w)
    sym_dx = (total_w - SYM_W) / 2
    wm_dx = (total_w - w) / 2
    inner = (_place_symbol(sym_dx, 0) + symbol_group(variant) + "</g>" +
             f'<g transform="translate({wm_dx:.1f} {SYM_H + gap:.1f})">{frag}</g>')
    vb = f"{-PAD} {-PAD} {total_w + 2 * PAD:.1f} {SYM_H + gap + h + 2 * PAD:.1f}"
    return _svg_doc(inner, vb, f"{BRAND_NAME} vertical lockup ({variant})",
                    "Symbol above Latin wordmark.")


def build_horizontal_latin(variant):
    runs = scale_to_width(latin_wordmark_runs(variant), 1688)
    frag, w, h = line_svg(runs)
    gap = 95
    total_w = SYM_W + gap + w
    wm_dy = (SYM_H - h) / 2
    inner = (_place_symbol(0, 0) + symbol_group(variant) + "</g>" +
             f'<g transform="translate({SYM_W + gap:.1f} {wm_dy:.1f})">{frag}</g>')
    vb = f"{-PAD} {-PAD} {total_w + 2 * PAD:.1f} {SYM_H + 2 * PAD:.1f}"
    return _svg_doc(inner, vb, f"{BRAND_NAME} horizontal lockup ({variant})",
                    "Symbol left, Latin wordmark right.")


def build_vertical_fa(variant):
    runs = scale_to_width(fa_wordmark_runs(variant), 1294, rtl=True)
    frag1, w1, h1 = line_svg(runs, rtl=True)
    dom = scale_to_width(fa_domain_run(variant), 700)
    frag2, w2, h2 = line_svg(dom)
    gap_sym = 110
    gap_lines = 28
    block_w = max(w1, w2)
    total_w = max(SYM_W, block_w)
    sym_dx = (total_w - SYM_W) / 2
    blk_dx = (total_w - block_w) / 2
    y = SYM_H + gap_sym
    inner = (_place_symbol(sym_dx, 0) + symbol_group(variant) + "</g>" +
             f'<g transform="translate({blk_dx + (block_w - w1) / 2:.1f} {y:.1f})">{frag1}</g>' +
             f'<g transform="translate({blk_dx + (block_w - w2) / 2:.1f} {y + h1 + gap_lines:.1f})">{frag2}</g>')
    total_h = SYM_H + gap_sym + h1 + gap_lines + h2
    vb = f"{-PAD} {-PAD} {total_w + 2 * PAD:.1f} {total_h + 2 * PAD:.1f}"
    return _svg_doc(inner, vb, f"{BRAND_NAME} vertical lockup FA ({variant})",
                    "Symbol above Persian wordmark.")


def build_horizontal_fa(variant):
    runs = scale_to_width(fa_wordmark_runs(variant), 1688, rtl=True)
    frag1, w1, h1 = line_svg(runs, rtl=True)
    dom = scale_to_width(fa_domain_run(variant), 900)
    frag2, w2, h2 = line_svg(dom)
    gap_sym = 95
    gap_lines = 28
    block_w = max(w1, w2)
    block_h = h1 + gap_lines + h2
    total_w = block_w + gap_sym + SYM_W
    blk_dy = (SYM_H - block_h) / 2
    # RTL: wordmark block on the left, symbol on the right.
    inner = (_place_symbol(block_w + gap_sym, 0) + symbol_group(variant) + "</g>" +
             f'<g transform="translate({(block_w - w1) / 2:.1f} {blk_dy:.1f})">{frag1}</g>' +
             f'<g transform="translate({(block_w - w2) / 2:.1f} {blk_dy + h1 + gap_lines:.1f})">{frag2}</g>')
    vb = f"{-PAD} {-PAD} {total_w + 2 * PAD:.1f} {SYM_H + 2 * PAD:.1f}"
    return _svg_doc(inner, vb, f"{BRAND_NAME} horizontal lockup FA ({variant})",
                    "Symbol right, Persian wordmark left (RTL).")


def _stacked_full(variant, wordmark_builder, name_builder, title_builder,
                  rtl_wordmark=False, rtl_name=False, rtl_title=False,
                  title=""):
    wm_runs = wordmark_builder(variant)
    wm_runs = scale_to_width(wm_runs, 1294, rtl=rtl_wordmark)
    frag_w, w_w, h_w = line_svg(wm_runs, rtl=rtl_wordmark)

    name_runs = scale_to_width(name_builder(variant), 800, rtl=rtl_name)
    frag_n, w_n, h_n = line_svg(name_runs, rtl=rtl_name)

    title_runs = scale_to_width(title_builder(variant), 750, rtl=rtl_title)
    frag_t, w_t, h_t = line_svg(title_runs, rtl=rtl_title)

    gap_sym, gap1, gap2 = 110, 55, 40
    total_w = max(SYM_W, w_w, w_n, w_t)
    sym_dx = (total_w - SYM_W) / 2
    y = SYM_H + gap_sym
    inner = _place_symbol(sym_dx, 0) + symbol_group(variant) + "</g>"
    inner += f'<g transform="translate({(total_w - w_w) / 2:.1f} {y:.1f})">{frag_w}</g>'
    y += h_w + gap1
    inner += f'<g transform="translate({(total_w - w_n) / 2:.1f} {y:.1f})">{frag_n}</g>'
    y += h_n + gap2
    inner += f'<g transform="translate({(total_w - w_t) / 2:.1f} {y:.1f})">{frag_t}</g>'
    total_h = y + h_t
    vb = f"{-PAD} {-PAD} {total_w + 2 * PAD:.1f} {total_h + 2 * PAD:.1f}"
    return _svg_doc(inner, vb, title, "Full three-line lockup.")


def build_full_latin(variant):
    return _stacked_full(
        variant, latin_wordmark_runs, latin_name_run, latin_title_run,
        title=f"{BRAND_NAME} full lockup ({variant})")


def build_full_fa(variant):
    return _stacked_full(
        variant, fa_wordmark_runs, fa_name_run, fa_title_runs,
        rtl_wordmark=True, rtl_name=True, rtl_title=True,
        title=f"{BRAND_NAME} full lockup FA ({variant})")


BUILDERS = {
    "symbol": build_symbol,
    "wordmark-latin": build_wordmark_latin,
    "wordmark-fa": build_wordmark_fa,
    "vertical-latin": build_vertical_latin,
    "horizontal-latin": build_horizontal_latin,
    "vertical-fa": build_vertical_fa,
    "horizontal-fa": build_horizontal_fa,
    "full-latin": build_full_latin,
    "full-fa": build_full_fa,
}


def build_app_icon():
    size = TOKENS["logo"]["app_icon_size_px"]
    scale = min((size - 96) / SYM_W, (size - 96) / SYM_H)
    dx = (size - SYM_W * scale) / 2
    dy = (size - SYM_H * scale) / 2
    inner = (f'<rect width="{size}" height="{size}" rx="{size * 0.22:.1f}" '
             f'fill="{TOKENS["color"]["strategic_navy"]["hex"]}"/>' +
             _place_symbol(dx, dy, scale) + symbol_group("white", TOKENS["color"]["innovation_gold"]["hex"]) + "</g>")
    return _svg_doc(inner, f"0 0 {size} {size}", "AtoZfnb.info app icon",
                    "White AZ emblem with gold dot on strategic navy.")


def _page_html():
    cards = []
    labels = {
        "symbol": ("نماد مستقل", "Standalone symbol"),
        "wordmark-latin": ("نوشتار لاتین", "Latin wordmark"),
        "wordmark-fa": ("نوشتار فارسی", "Persian wordmark"),
        "horizontal-latin": ("لاک‌آپ افقی لاتین", "Latin horizontal lockup"),
        "horizontal-fa": ("لاک‌آپ افقی فارسی", "Persian horizontal lockup"),
        "vertical-latin": ("لاک‌آپ عمودی لاتین", "Latin vertical lockup"),
        "vertical-fa": ("لاک‌آپ عمودی فارسی", "Persian vertical lockup"),
        "full-latin": ("لاک‌آپ کامل لاتین", "Full Latin lockup"),
        "full-fa": ("لاک‌آپ کامل فارسی", "Full Persian lockup"),
    }
    layout_map = {"symbol": "shared", **{k: "fa" for k in BUILDERS if k.endswith("-fa")},
                  **{k: "en" for k in BUILDERS if k.endswith("-latin")}}
    for layout in BUILDERS:
        folder = layout_map[layout]
        for variant in VARIANTS:
            stem = f"{layout}-{variant}"
            fa_label, en_label = labels[layout]
            lang = "shared" if layout == "symbol" else ("fa" if layout.endswith("-fa") else "en")
            cards.append(
                f'<article class="asset-card" data-layout="{layout}" data-variant="{variant}" '
                f'data-lang="{lang}"><div class="preview {"dark" if variant == "white" else "light"}">'
                f'<img loading="lazy" src="{folder}/png/{stem}.png" alt="{fa_label} — {variant}"/></div>'
                f'<div class="card-meta"><div><strong dir="rtl">{fa_label}</strong><small>{en_label} · {variant}</small></div>'
                f'<div class="downloads"><a href="{folder}/svg/{stem}.svg" download>SVG</a>'
                f'<a href="{folder}/png/{stem}.png" download>PNG</a></div></div></article>')
    icons = '''<article class="asset-card icon-card"><div class="preview dark"><img src="icons/png/app-icon.png" alt="آیکون برنامه"/></div>
      <div class="card-meta"><div><strong dir="rtl">آیکون برنامه و فاوآیکن</strong><small>App icon & favicon</small></div>
      <div class="downloads"><a href="icons/svg/app-icon.svg" download>SVG</a><a href="icons/png/app-icon.png" download>PNG</a></div></div>
      <div class="sizes"><a href="icons/png/favicon-16.png">16</a><a href="icons/png/favicon-32.png">32</a><a href="icons/png/favicon-48.png">48</a><a href="icons/png/apple-touch-icon.png">180</a><a href="icons/png/favicon-192.png">192</a><a href="icons/png/favicon-512.png">512</a><a href="icons/svg/favicon.svg">SVG</a></div></article>'''
    return f'''<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>لوگو و دارایی‌های برند | AtoZ.FnB</title><meta name="description" content="مرکز دانلود لوگوهای فارسی و انگلیسی AtoZ.FnB با فرمت SVG و PNG">
<style>
:root{{--navy:#0A1931;--gold:#FFB400;--surface:#F4F7FA;--ink:#17263e;--muted:#64748b;--line:#dce3eb}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--surface);color:var(--ink);font-family:Vazirmatn,"Noto Sans Arabic",Tahoma,sans-serif}}
a{{color:inherit}}.hero{{background:var(--navy);color:white;padding:48px max(24px,calc((100vw - 1380px)/2)) 42px;border-bottom:5px solid var(--gold)}}
.eyebrow{{font:600 12px/1.5 Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:var(--gold)}}h1{{font-size:clamp(30px,4vw,52px);line-height:1.25;margin:8px 0 6px}}.subtitle{{margin:0;color:#cbd5e1;font-size:15px}}
.wrap{{max-width:1380px;margin:auto;padding:26px 24px 70px}}.toolbar{{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:18px}}.toolbar span{{font-weight:700;margin-inline-end:8px}}
button{{border:1px solid var(--line);background:#fff;border-radius:99px;padding:9px 15px;font:inherit;font-size:13px;font-weight:600;color:var(--ink);cursor:pointer}}button.active,button:hover{{background:var(--navy);color:white;border-color:var(--navy)}}
.group-title{{display:flex;align-items:end;justify-content:space-between;margin:28px 0 13px;border-bottom:1px solid var(--line);padding-bottom:10px}}h2{{font-size:22px;margin:0}}.hint{{font-size:12px;color:var(--muted)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr));gap:14px}}
.asset-card{{background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 4px 14px #10233d0a}}.preview{{height:170px;display:grid;place-items:center;padding:16px}}.preview.light{{background:#fff}}.preview.dark{{background:var(--navy)}}.preview img{{max-width:100%;max-height:100%;object-fit:contain}}
.card-meta{{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px 15px}}.card-meta strong,.card-meta small{{display:block}}.card-meta strong{{font-size:14px}}.card-meta small{{color:var(--muted);font:12px/1.5 Arial,sans-serif;margin-top:3px}}
.downloads{{display:flex;gap:6px;direction:ltr}}.downloads a,.sizes a{{font:700 11px Arial,sans-serif;text-decoration:none;border:1px solid var(--line);border-radius:7px;padding:7px 9px;background:white}}.downloads a:hover,.sizes a:hover{{background:var(--gold);border-color:var(--gold)}}.sizes{{display:flex;gap:5px;justify-content:flex-start;padding:0 14px 13px;direction:ltr}}.sizes a{{padding:5px 8px}}
.note{{margin-top:28px;padding:18px 20px;background:#fff;border:1px solid var(--line);border-right:4px solid var(--gold);border-radius:10px;color:#475569;font-size:13px;line-height:1.9}}footer{{text-align:center;color:var(--muted);font:12px Arial,sans-serif;margin-top:36px}}
[hidden]{{display:none!important}}@media(max-width:600px){{.hero{{padding-top:32px}}.wrap{{padding-inline:14px}}.card-meta{{align-items:flex-start}}.preview{{height:145px}}}}
</style></head><body>
<header class="hero"><div class="eyebrow">AtoZ.FnB · Brand assets</div><h1>کتابخانهٔ لوگو</h1><p class="subtitle">نسخه‌های رسمی فارسی و انگلیسی · فایل‌های برداری SVG و تصاویر شفاف PNG</p></header>
<main class="wrap"><nav class="toolbar" aria-label="فیلتر دارایی‌ها"><span>نمایش:</span>
<button class="active" data-filter="all">همه / All</button><button data-filter="fa">فارسی / FA</button><button data-filter="en">English / EN</button><button data-filter="shared">نماد و آیکون / Marks</button>
<button data-variant="color">رنگی</button><button data-variant="mono">تک‌رنگ</button><button data-variant="white">سفید</button></nav>
<div class="group-title"><h2>لاک‌آپ‌های برند</h2><span class="hint">هر دارایی در SVG و PNG شفاف · ۲۰۴۸ px</span></div>
<section class="grid" id="logos">{''.join(cards)}</section>
<div class="group-title"><h2>آیکون‌ها</h2><span class="hint">برای اپلیکیشن، وب و بوکمارک</span></div><section class="grid">{icons}</section>
<div class="group-title"><h2>راهنمای استفاده</h2><span class="hint">حریم امن، حداقل اندازه و نسخه‌های مجاز</span></div>
<section class="grid"><article class="asset-card"><div class="preview light"><img src="guidelines/png/logo-guidelines.png" alt="راهنمای لوگو"/></div>
<div class="card-meta"><div><strong dir="rtl">راهنمای دوزبانهٔ لوگو</strong><small>Logo usage guidelines · SVG / PNG</small></div>
<div class="downloads"><a href="guidelines/svg/logo-guidelines.svg" download>SVG</a><a href="guidelines/png/logo-guidelines.png" download>PNG</a></div></div></article></section>
<div class="note">نسخهٔ سفید را روی زمینهٔ تیره استفاده کنید. نماد مستقل و مجموعهٔ آیکون‌ها زبان‌خنثی هستند. متن‌های لوگو در SVG به مسیر تبدیل شده‌اند؛ فایل‌های زیرشاخهٔ «قالب‌های محتوا» و «وب‌سایت» در فازهای بعدی تکمیل می‌شوند.</div>
<footer>AtoZ.FnB · atozfnb.info · Phase 1 — Logo system</footer></main>
<script>
let lang='all',variant='all';function update(){{document.querySelectorAll('.asset-card:not(.icon-card)').forEach(c=>{{c.hidden=!(lang==='all'||c.dataset.lang===lang)||!(variant==='all'||c.dataset.variant===variant)}});document.querySelectorAll('[data-filter]').forEach(b=>b.classList.toggle('active',b.dataset.filter===lang));document.querySelectorAll('button[data-variant]').forEach(b=>b.classList.toggle('active',b.dataset.variant===variant))}}
document.querySelectorAll('button[data-filter]').forEach(b=>b.onclick=()=>{{lang=b.dataset.filter;update()}});document.querySelectorAll('button[data-variant]').forEach(b=>b.onclick=()=>{{variant=variant===b.dataset.variant?'all':b.dataset.variant;update()}});
</script></body></html>'''


def write_icon_assets():
    icon_dir = os.path.join(OUT_ROOT, "icons", "svg")
    os.makedirs(icon_dir, exist_ok=True)
    svg = build_app_icon()
    with open(os.path.join(icon_dir, "app-icon.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    with open(os.path.join(icon_dir, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(svg.replace("app icon", "favicon"))
    manifest = {
        "name": BRAND_NAME, "short_name": "AtoZ.FnB", "lang": "fa", "dir": "rtl",
        "theme_color": TOKENS["color"]["strategic_navy"]["hex"],
        "background_color": TOKENS["color"]["strategic_navy"]["hex"],
        "display": "standalone",
        "icons": [
            {"src": "png/favicon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "png/favicon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    with open(os.path.join(OUT_ROOT, "icons", "site.webmanifest"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(os.path.join(OUT_ROOT, "icons", "head-snippet.html"), "w", encoding="utf-8") as f:
        f.write('''<link rel="icon" href="logo/icons/png/favicon.ico" sizes="any">
<link rel="icon" href="logo/icons/svg/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="logo/icons/png/apple-touch-icon.png">
<link rel="manifest" href="logo/icons/site.webmanifest">
''')


def main():
    for layout, builder in BUILDERS.items():
        if layout == "symbol":
            locale = "shared"
        elif layout.endswith("-fa"):
            locale = "fa"
        else:
            locale = "en"
        out_dir = os.path.join(OUT_ROOT, locale, "svg")
        os.makedirs(out_dir, exist_ok=True)
        for variant in VARIANTS:
            svg = builder(variant)
            path = os.path.join(out_dir, f"{layout}-{variant}.svg")
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
            print(f"  {os.path.relpath(path, ROOT)}")
    write_icon_assets()
    with open(os.path.join(OUT_ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(_page_html())
    print(f"Generated logo library in {OUT_ROOT}")

if __name__ == "__main__":
    main()
