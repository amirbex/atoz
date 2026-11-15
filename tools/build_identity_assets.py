#!/usr/bin/env python3
"""Build AtoZ.FnB identity book, design sheets, template masters, and logo motions.

This is an asset-only build: it creates no editorial package and performs no upload,
scheduling, website edit, or social publication.
"""
from __future__ import annotations

import html
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_logo as logo

TOKENS_PATH = ROOT / "brand/tokens.json"
SYSTEM_PATH = ROOT / "brand/design-system.json"
TOKENS = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
SYSTEM = json.loads(SYSTEM_PATH.read_text(encoding="utf-8"))

NAVY = TOKENS["color"]["strategic_navy"]["hex"]
GOLD = TOKENS["color"]["innovation_gold"]["hex"]
SURFACE = TOKENS["color"]["neutral_surface"]["hex"]
WHITE = TOKENS["color"]["pure_white"]["hex"]
INK = "#0A1931"
BODY = "#334155"
MUTED = "#64748B"
BORDER = "#D9E0EA"
PALE_GOLD = "#FFF4D5"
FA_BOLD = "Vazirmatn-Bold.ttf"
FA_XBOLD = "Vazirmatn-ExtraBold.ttf"
FA_REG = "Vazirmatn-Regular.ttf"
LATIN_BOLD = "Montserrat-Bold.ttf"
LATIN_SEMI = "Montserrat-SemiBold.ttf"
LATIN_BODY = "Lato-Regular.ttf"
DONGOL = "534316143Dongol.ttf"

BOOK = ROOT / "brand/brand-book"
SLIDES = BOOK / "slides"
SHEETS = ROOT / "brand/sheets"
PRESETS = ROOT / "brand/presets"
TEMPLATES = ROOT / "content-templates"
MOTION = ROOT / "logo-motion"
BUILD_TEMP = ROOT / ".brand-build"

PILLARS = SYSTEM["architecture"]["content_pillars"]
DESTINATIONS = SYSTEM["architecture"]["site_destinations"]
SECTION_COLORS = SYSTEM["visual_system"]["section_palette"]


def esc(value):
    return html.escape(str(value), quote=True)


def _measure(text_value, font, size, rtl):
    direction, script, language = ("rtl", "Arab", "fa") if rtl else ("ltr", "Latn", "en")
    return logo.shape_run(font, text_value, size, direction=direction, script=script, language=language)[1]


def wrap_text(text_value, font, size, max_width, rtl=True):
    lines = []
    for paragraph in str(text_value).split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = (current + " " + word).strip()
            if current and _measure(candidate, font, size, rtl) > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines or [""]


def shaped(text_value, x, y, size, color, font=FA_REG, rtl=True, max_width=None, align="right", line_height=None):
    """Return SVG paths for shaped, outlined Persian or Latin text.

    x is the right edge for right-aligned text, left edge for left-aligned text,
    or center point for centered text. y is the top of the first line's glyph box.
    """
    if max_width is None:
        max_width = 1500
    direction, script, language = ("rtl", "Arab", "fa") if rtl else ("ltr", "Latn", "en")
    step = line_height or size * 1.42
    chunks = []
    for i, line in enumerate(wrap_text(text_value, font, size, max_width, rtl)):
        if not line:
            continue
        run = {"font": font, "text": line, "size": size, "direction": direction,
               "script": script, "language": language, "fill": color}
        body, width, _ = logo.line_svg([run], rtl=rtl)
        if align == "center":
            px = x - width / 2
        elif align == "left":
            px = x
        else:
            px = x - width
        py = y + i * step
        chunks.append(f'<g transform="translate({px:.2f} {py:.2f})">{body}</g>')
    return "".join(chunks), len(wrap_text(text_value, font, size, max_width, rtl)) * step


def fa(text_value, right, y, size, color=INK, font=FA_REG, width=700, align="right", line_height=None):
    return shaped(text_value, right, y, size, color, font, True, width, align, line_height)[0]


def en(text_value, left, y, size, color=INK, font=LATIN_BODY, width=900, align="left"):
    return shaped(text_value, left if align != "center" else left, y, size, color, font, False, width, align)[0]


def rect(x, y, w, h, fill=WHITE, stroke="none", radius=0, sw=1, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def rule(x1, y1, x2, y2, color=BORDER, sw=2, dash=None):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round"{dash_attr}/>'


def circle(cx, cy, r, fill, stroke="none", sw=0):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def brand_mark(x, y, width, variant="color", opacity=1):
    scale = width / logo.SYM_W
    return (f'<g transform="translate({x - logo.SYM_X0*scale:.2f} {y - logo.SYM_Y0*scale:.2f}) scale({scale:.5f})" opacity="{opacity}">'
            + logo.symbol_group(variant) + '</g>')


def logo_lockup(x, y, width=300, variant="color", fa_first=False):
    scale = width / logo.SYM_W
    mark_h = logo.SYM_H * scale
    group = [brand_mark(x, y, width, variant)]
    fg = WHITE if variant == "white" else NAVY
    tx = x + width + 28
    latin_font = "Montserrat-SemiBold.ttf"
    persian_name = fa("آ تو ز", tx + 190, y + mark_h * .42, max(22, width * .10), fg, FA_BOLD, width=220)
    latin_name = en("AtoZfnb.info", tx, y + mark_h * .44, max(23, width * .1), fg, latin_font, width=300)
    if fa_first:
        group.append(persian_name)
        group.append(en("F&B STRATEGY", tx, y + mark_h * .76, 15, fg, "Montserrat-SemiBold.ttf", width=240))
    else:
        group.append(latin_name)
        group.append(fa("آ تو ز اف‌ان‌بی", tx + 265, y + mark_h * .76, max(16, width * .065), fg, FA_REG, width=280))
    return "".join(group)


def svg_doc(width, height, body, background=WHITE, title="AtoZ.FnB identity asset", desc=""):
    bg = f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}"/>' if background else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title><desc>{esc(desc)}</desc>{bg}{body}</svg>')


def card(x, y, w, h, title, body, accent=GOLD, label=None, fill=WHITE, title_color=INK, body_color=BODY):
    out = [rect(x, y, w, h, fill, BORDER, 20, 2), rect(x, y, 9, h, accent, radius=4)]
    if label:
        out.append(en(label, x + 28, y + 20, 15, accent, "Montserrat-SemiBold.ttf", width=w - 56))
        ty = y + 55
    else:
        ty = y + 30
    out.append(fa(title, x + w - 28, ty, 30, title_color, FA_BOLD, width=w - 60))
    out.append(fa(body, x + w - 28, ty + 57, 21, body_color, FA_REG, width=w - 62, line_height=30))
    return "".join(out)


def title_block(index, en_label, title, subtitle="", accent=GOLD, background=WHITE):
    out = [rect(0, 0, 1920, 1080, background)]
    out.append(en(en_label.upper(), 120, 74, 17, MUTED, LATIN_SEMI, width=840))
    out.append(fa(f"{index:02d}", 1800, 68, 24, accent, FA_BOLD, width=70))
    out.append(rule(120, 116, 1800, 116, accent, 3))
    out.append(fa(title, 1780, 152, 52, NAVY, FA_XBOLD, width=1500))
    if subtitle:
        out.append(fa(subtitle, 1780, 226, 24, MUTED, FA_REG, width=1500))
    return out


def page_footer(index, total=12, dark=False):
    fg = "#B8C2D1" if dark else MUTED
    out = [rule(120, 1018, 1800, 1018, "#334155" if dark else BORDER, 2)]
    out.append(en("AtoZfnb.info  ·  BRAND FOUNDATION", 120, 1038, 14, fg, "Montserrat-SemiBold.ttf", width=620))
    out.append(fa("آ تو ز", 1800, 1034, 17, GOLD if dark else NAVY, FA_BOLD, width=110))
    out.append(en(f"{index:02d} / {total:02d}", 880, 1038, 14, fg, "Montserrat-SemiBold.ttf", width=180, align="center"))
    return "".join(out)


def build_book_slides():
    slides = []
    # 01 — cover
    b = [rect(0, 0, 1920, 1080, NAVY)]
    # Quiet coordinate field and A→Z rising trajectory.
    for x in range(1240, 1860, 80):
        b.append(rule(x, 130, x, 890, "#1B2A43", 1))
    for y in range(150, 940, 80):
        b.append(rule(1180, y, 1860, y, "#1B2A43", 1))
    b.append(f'<path d="M1260 800 C1420 760 1470 600 1580 540 S1740 400 1820 230" fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round" opacity=".78"/>')
    for i,(cx,cy) in enumerate([(1260,800),(1460,610),(1630,500),(1820,230)]):
        b.append(circle(cx, cy, 11 if i < 3 else 22, GOLD, NAVY, 5))
    b.append(brand_mark(1325, 265, 360, "white"))
    b.append(en("AtoZfnb.info  /  BRAND SYSTEM 2.0", 140, 130, 18, "#B8C2D1", LATIN_SEMI, width=800))
    b.append(fa("هویت بصری", 990, 300, 86, WHITE, FA_XBOLD, width=870))
    b.append(fa("و نظام طراحی", 990, 410, 78, GOLD, FA_XBOLD, width=870))
    b.append(fa("از دانش تا سیستم؛ از سیستم تا رشد پایدار", 990, 565, 33, "#D8E0EB", FA_REG, width=810))
    b.append(rule(140, 700, 760, 700, "#334155", 2))
    b.append(fa("برندبوک پایه، شیت‌ها، قالب‌ها و موشن‌لوگو", 990, 735, 27, "#B8C2D1", FA_REG, width=810))
    b.append(en("FOUNDATION ASSETS · REVIEW EDITION", 140, 930, 17, GOLD, LATIN_SEMI, width=600))
    b.append(page_footer(1, dark=True))
    slides.append(svg_doc(1920,1080,"".join(b),None,"AtoZ.FnB — Brand Foundation", "Brand system review edition"))

    # 02 — brand core
    b = title_block(2,"BRAND CORE","ما از «اطلاعات» چه می‌سازیم؟","وعدهٔ برند باید از محتوای آموزشی تا ابزار و تجربهٔ دیجیتال یکدست بماند.")
    b.append(rect(120,315,790,560,NAVY,radius=26))
    b.append(en("BRAND PROMISE",165,355,17,GOLD,LATIN_SEMI,width=350))
    b.append(fa("رشد کسب‌وکار خود را با",840,455,40,WHITE,FA_BOLD,width=620))
    b.append(fa("هوش مصنوعی سیستم‌سازی کنید",840,525,42,GOLD,FA_XBOLD,width=620))
    b.append(fa("دانش کاربردی، استراتژی داده‌محور و ابزار هوشمند؛ برای تصمیم‌های روشن‌تر در F&B.",840,650,23,"#D8E0EB",FA_REG,width=625,line_height=36))
    stages=[("۱","شناخت","مسئله و زمینه"),("۲","طراحی","چارچوب و فرض"),("۳","اقدام","ابزار و فرایند"),("۴","یادگیری","اندازه‌گیری و اصلاح")]
    x0=1000; y=365; gap=24; cw=185
    for i,(num,head,sub) in enumerate(stages):
        x=x0+i*(cw+gap)
        b.append(rect(x,y,cw,220,WHITE,BORDER,18,2))
        b.append(circle(x+cw/2,y+48,22,GOLD))
        b.append(en(num,x+cw/2,y+40,18,NAVY,LATIN_BOLD,width=44,align="center"))
        b.append(fa(head,x+cw-15,y+96,25,NAVY,FA_BOLD,width=cw-30))
        b.append(fa(sub,x+cw-15,y+146,18,MUTED,FA_REG,width=cw-30))
        if i<3:b.append(rule(x+cw+4,y+110,x+cw+gap-4,y+110,GOLD,4))
    b.append(fa("وعده: دانش را به تصمیم و تصمیم را به سیستم قابل‌اجرا نزدیک کنیم.",1780,700,26,NAVY,FA_BOLD,width=790))
    b.append(page_footer(2)); slides.append(svg_doc(1920,1080,"".join(b),None,"هستهٔ برند"))

    # 03 — voice and character
    b=title_block(3,"PERSONALITY & VOICE","صدای برند؛ متخصص، روشن، همراه","اعتماد از قطعیت‌نمایی نمی‌آید؛ از شفافیت، زمینه و اقدام قابل‌سنجش ساخته می‌شود.")
    traits=[
      ("متخصص و دلسوز","دقیق توضیح می‌دهد؛ مخاطب را بابت ندانستن سرزنش نمی‌کند.","حس مطلوب: فهمیده‌شدن"),
      ("داده‌محور و شفاف","منبع، فرض، تجربه و مثال فرضی را از هم جدا می‌کند.","حس مطلوب: اعتماد آگاهانه"),
      ("صریح و اجرایی","نکته را کوتاه می‌گوید و قدم بعدی را پیشنهاد می‌کند.","حس مطلوب: توان اقدام")]
    for i,(head,copy,tag) in enumerate(traits):
        x=120+i*575
        accent=[SECTION_COLORS["library"],SECTION_COLORS["calculators"],GOLD][i]
        b.append(rect(x,330,520,480,WHITE,BORDER,24,2))
        b.append(rect(x,330,520,13,accent,radius=6))
        b.append(circle(x+78,410,32,accent))
        b.append(en(f"0{i+1}",x+78,400,20,NAVY if accent==GOLD else WHITE,LATIN_BOLD,width=54,align="center"))
        b.append(fa(head,x+470,500,34,NAVY,FA_XBOLD,width=440))
        b.append(fa(copy,x+470,580,23,BODY,FA_REG,width=440,line_height=36))
        b.append(rule(x+50,720,x+470,720,BORDER,2))
        b.append(fa(tag,x+470,750,19,accent if accent!=GOLD else NAVY,FA_BOLD,width=430))
    b.append(rect(120,858,1680,100,SURFACE,radius=16))
    b.append(fa("هر ادعای عددی: منبع + تاریخ + زمینه؛ هر مثال: برچسب «فرضی».",1765,890,22,NAVY,FA_BOLD,width=1550))
    b.append(page_footer(3)); slides.append(svg_doc(1920,1080,"".join(b),None,"شخصیت و لحن"))

    # 04 — content pillars
    b=title_block(4,"CONTENT PILLARS","شش ستون محتوایی، شش وعدهٔ روشن","رنگ فقط نشانهٔ کمکی است؛ نام ستون و مقصد همواره باید همراه آن دیده شوند.")
    for i,item in enumerate(PILLARS):
        col=i%3; row=i//3; x=120+col*570; y=330+row*295
        accent=SECTION_COLORS[item["color_token"]]
        b.append(rect(x,y,530,250,WHITE,BORDER,20,2))
        b.append(rect(x,y,10,250,accent,radius=5))
        b.append(en(f"PILLAR 0{i+1}",x+36,y+24,15,accent,LATIN_SEMI,width=200))
        b.append(fa(item["name_fa"],x+490,y+68,29,NAVY,FA_XBOLD,width=445))
        b.append(fa(item["purpose_fa"],x+490,y+118,20,BODY,FA_REG,width=445,line_height=30))
        b.append(en(item["destination"].upper(),x+36,y+208,13,MUTED,LATIN_SEMI,width=430))
    b.append(page_footer(4)); slides.append(svg_doc(1920,1080,"".join(b),None,"شش ستون محتوایی"))

    # 05 — site information architecture
    b=title_block(5,"DIGITAL DESTINATIONS","خانه و شش مقصد تخصصی","یک مسیر اصلی برای هر محتوا؛ ارتباط‌های ثانویه فقط وقتی برای مخاطب مفیدند.")
    b.append(rect(745,315,430,112,NAVY,radius=20))
    b.append(en("HOME  /  ENTRY POINT",800,338,15,GOLD,LATIN_SEMI,width=330))
    b.append(fa("خانه و مسیریابی برند",1135,370,27,WHITE,FA_BOLD,width=340))
    b.append(rule(960,427,960,480,GOLD,4))
    b.append(rule(260,480,1660,480,GOLD,3))
    for i,dest in enumerate(DESTINATIONS[1:]):
        col=i%3; row=i//3; x=120+col*570; y=505+row*195
        cx=x+255
        b.append(rule(cx,480,cx,y,GOLD,3))
        b.append(circle(cx,480,7,GOLD))
        color=SECTION_COLORS.get(dest["id"].replace("-","_"),SECTION_COLORS.get(dest["id"],GOLD))
        if dest["id"]=="ai-prompts":color=SECTION_COLORS["ai_prompts"]
        if dest["id"]=="calculators":color=SECTION_COLORS["calculators"]
        if dest["id"]=="library":color=SECTION_COLORS["library"]
        if dest["id"]=="magazine":color=SECTION_COLORS["magazine"]
        if dest["id"]=="academy":color=SECTION_COLORS["academy"]
        if dest["id"]=="solutions":color=SECTION_COLORS["solutions"]
        b.append(rect(x,y,510,145,WHITE,BORDER,18,2))
        b.append(rect(x,y,510,8,color,radius=4))
        b.append(en(dest["name"].upper(),x+26,y+24,14,color,LATIN_SEMI,width=460))
        b.append(fa(dest["role_fa"],x+475,y+68,19,BODY,FA_REG,width=455,line_height=29))
    b.append(fa("Home مقصد هفتم محتوایی نیست؛ ورودی و راهبری سایت است.",1770,930,20,MUTED,FA_BOLD,width=1000))
    b.append(page_footer(5)); slides.append(svg_doc(1920,1080,"".join(b),None,"معماری مقصدهای دیجیتال"))

    # 06 — palette and accessibility
    b=title_block(6,"COLOR SYSTEM","پالت؛ پایهٔ برند و رنگ‌های موضوعی","سرمه‌ای و سفید می‌سازند؛ طلایی تأکید می‌کند؛ رنگ موضوعی فقط راهنمای مسیر است.")
    core=[("آبی استراتژیک",NAVY,"متن، لوگو، زمینهٔ تیره"),("طلایی نوآوری",GOLD,"تأکید، نقطهٔ رشد، CTA"),("سطح خنثی",SURFACE,"پس‌زمینهٔ بخش و کارت"),("سفید",WHITE,"فضای تنفس و سطح محتوا")]
    for i,(name,color,role) in enumerate(core):
        x=120+i*420
        b.append(rect(x,325,380,190,color,BORDER if color in [WHITE,SURFACE] else color,18,2))
        fg=WHITE if color==NAVY else NAVY
        b.append(fa(name,x+345,395,24,fg,FA_BOLD,width=315))
        b.append(en(color,x+25,467,18,fg,LATIN_SEMI,width=280))
        b.append(fa(role,x+345,545,18,MUTED,FA_REG,width=315))
    b.append(en("SECTION ACCENTS",120,620,15,MUTED,LATIN_SEMI,width=260))
    for i,item in enumerate(PILLARS):
        x=120+i*280
        color=SECTION_COLORS[item["color_token"]]
        b.append(rect(x,660,235,72,color,radius=14))
        b.append(fa(item["name_fa"],x+212,681,17,NAVY if color==GOLD else WHITE,FA_BOLD,width=195))
        b.append(en(color,x,747,14,MUTED,LATIN_SEMI,width=230))
    b.append(rect(120,805,1680,145,PALE_GOLD,radius=18))
    b.append(fa("دسترسی‌پذیری",1765,828,22,NAVY,FA_BOLD,width=300))
    b.append(fa("متن اصلی سرمه‌ای روی سفید: ۱۷٫۵۵:۱ · سرمه‌ای روی طلایی: ۹٫۸۵:۱ · طلایی روی سفید: ۱٫۷۸:۱",1765,867,20,NAVY,FA_REG,width=1570))
    b.append(fa("طلایی و بعضی رنگ‌های موضوعی روی سفید برای متن ریز مجاز نیستند؛ از رنگ تیرهٔ متن یا کنتراست کنترل‌شده استفاده کنید.",1765,906,17,NAVY,FA_REG,width=1570))
    b.append(page_footer(6)); slides.append(svg_doc(1920,1080,"".join(b),None,"پالت و دسترسی‌پذیری رنگ"))

    # 07 — typography
    b=title_block(7,"TYPOGRAPHY","تایپوگرافی؛ خوانایی اول، امضا بعد","فایل‌های دارای مجوز روشن در سیستم اصلی‌اند؛ فونت‌های تزئینی فقط پس از بررسی مجوز و نمونه.")
    font_cards=[
      (120,"فارسی · تیتر", "Vazirmatn ExtraBold","رشد کسب‌وکار F&B",FA_XBOLD,NAVY,"تیتر اصلی، جلد و قلاب"),
      (690,"فارسی · متن", "Vazirmatn Regular","یک ایدهٔ روشن، یک اقدام قابل‌آزمون.",FA_REG,BODY,"پاراگراف، زیرتیتر و راهنما"),
      (1260,"لاتین · عنوان", "Montserrat / Lato","AtoZfnb.info",LATIN_BOLD,NAVY,"Montserrat تیتر · Lato بدنه")]
    for x,label,name,sample,font,color,role in font_cards:
        b.append(rect(x,335,520,365,WHITE,BORDER,22,2))
        b.append(fa(label,x+470,365,16,MUTED,FA_BOLD,width=450))
        b.append(en(name,x+28,413,18,SECTION_COLORS["library"],LATIN_SEMI,width=440))
        if font.startswith("Vazirmatn"):
            b.append(fa(sample,x+470,510,37,color,font,width=450))
        else:
            b.append(en(sample,x+28,510,38,color,font,width=450))
        b.append(rule(x+28,580,x+480,580,BORDER,2))
        b.append(fa(role,x+470,615,19,MUTED,FA_REG,width=450))
    # Dongol as a candidate, not used by default.
    b.append(rect(120,745,1660,205,"#F7F4EE",BORDER,20,2))
    b.append(en("OPTIONAL DISPLAY STUDY · DONGOL",155,773,15,"#7B5C45",LATIN_SEMI,width=480))
    b.append(fa("آ تو ز",1660,797,42,NAVY,DONGOL,width=440))
    b.append(fa("نمونهٔ نمایشی کوتاه؛ متادیتا OFL را اعلام می‌کند، اما نویسهٔ نیم‌فاصله ندارد و تا تأیید منبع مجوز، فونت اصلی سیستم نیست.",1660,858,18,BODY,FA_REG,width=1450))
    b.append(page_footer(7)); slides.append(svg_doc(1920,1080,"".join(b),None,"نظام تایپوگرافی"))

    # 08 — logo system
    b=title_block(8,"LOGO SYSTEM","لوگو؛ هندسهٔ ثابت، رنگ و زمینهٔ کنترل‌شده","نشان رشد A تا Z و نقطهٔ طلایی؛ نام فارسی در کاربردهای دوزبانه دقیقاً «آ تو ز» نوشته می‌شود.")
    # main mark hero
    b.append(rect(120,320,680,560,SURFACE,BORDER,24,2))
    b.append(brand_mark(270,405,390,"color"))
    b.append(en("PRIMARY SYMBOL",165,810,15,MUTED,LATIN_SEMI,width=300))
    # variant swatches
    for i,(label,variant,bg) in enumerate([("رنگی روی روشن","color",WHITE),("تک‌رنگ","mono",WHITE),("سفید روی تیره","white",NAVY)]):
        x=865+i*300
        b.append(rect(x,330,270,190,bg,BORDER if bg!=NAVY else NAVY,18,2))
        b.append(brand_mark(x+75,360,125,variant))
        b.append(fa(label,x+245,550,19,NAVY,FA_BOLD,width=230))
    b.append(rect(865,610,870,260,WHITE,BORDER,18,2))
    b.append(fa("قواعد ثابت",1695,640,25,NAVY,FA_XBOLD,width=300))
    rules=["حریم امن: قطر نقطهٔ طلایی حول کل ترکیب.","حداقل لاک‌آپ افقی: ۱۲۰ px؛ عمودی: ۱۰۰ px.","نماد تنها: حداقل ۲۴ px؛ در ابعاد کمتر جزئیات حذف می‌شوند.","نکشید، نچرخانید، رنگ برند را تغییر ندهید، افکت اضافه نکنید."]
    for i,line in enumerate(rules):
        b.append(circle(900,700+i*40,5,GOLD))
        b.append(fa(line,1690,688+i*40,17,BODY,FA_REG,width=745))
    b.append(page_footer(8)); slides.append(svg_doc(1920,1080,"".join(b),None,"سیستم لوگو"))

    # 09 — grids and safe areas
    b=title_block(9,"LAYOUT & SAFE AREAS","شبکه و حریم؛ هر قالب یک ریتم، یک امضا","ابعاد پلتفرم ثابت است؛ جای متن و CTA با رابط کاربری و سوژهٔ تصویر سنجیده می‌شود.")
    # 12-column presentation grid
    gx,gy,gw,gh=120,350,930,470; colw=gw/12
    b.append(rect(gx,gy,gw,gh,WHITE,BORDER,18,2))
    for i in range(12):
        b.append(rect(gx+i*colw+6,gy+18,colw-12,gh-36,"#EDF2F7",radius=5))
        b.append(en(f"{i+1:02d}",gx+i*colw+8,gy+34,12,MUTED,LATIN_BODY,width=32,align="center"))
    b.append(en("12-COLUMN GRID · 6% SAFE MARGIN",gx+24,gy+gh+30,15,MUTED,LATIN_SEMI,width=560))
    # Social mock frames
    for x,w,h,label in [(1160,225,280,"FEED 4:5"),(1460,200,355,"STORY / REEL 9:16")]:
        y=350
        b.append(rect(x,y,w,h,WHITE,NAVY,14,3))
        safe=w*.08
        b.append(rect(x+safe,y+safe,w-2*safe,h-2*safe,"#F8FAFC",GOLD,8,2,'stroke-dasharray="8 6"'))
        b.append(rect(x+safe+10,y+safe+30,w-2*safe-20,24,NAVY,radius=6))
        b.append(rect(x+safe+10,y+safe+74,w-2*safe-20,40,"#E2E8F0",radius=8))
        b.append(rect(x+safe+10,y+h-safe-45,w-2*safe-20,24,GOLD,radius=6))
        b.append(en(label,x,y+h+24,14,MUTED,LATIN_SEMI,width=w,align="center"))
    b.append(fa("عنوان  ·  سوژه/نمودار  ·  نکته  ·  نشان ستون  ·  فوتر",1770,845,21,NAVY,FA_BOLD,width=1500))
    b.append(fa("حریم امن عمودی ریل: ۸٪ پایه؛ بخش‌های تعاملی اپ را در ۱۲٪ بالا و ۱۶٪ پایین خالی بگذارید.",1770,895,18,MUTED,FA_REG,width=1500))
    b.append(page_footer(9)); slides.append(svg_doc(1920,1080,"".join(b),None,"شبکه و حریم امن"))

    # 10 — visual language and sample references
    b=title_block(10,"VISUAL LANGUAGE","از مرجع‌ها چه می‌گیریم؟","کنتراست و سلسله‌مراتب را ترجمه می‌کنیم؛ متن، تصویر و نشان متعلق به برندهای دیگر را کپی نمی‌کنیم.")
    visual=[
      ("سردبیرانه","تیتر کوتاه و بزرگ؛ فضای خالی؛ یک لحن اصلی.","تیتر / مکث / پیام",SECTION_COLORS["magazine"]),
      ("شاهد و منبع","نشان دسته، یک نمودار ساده، منبع و تاریخ خوانا.","ادعا / داده / منبع",SECTION_COLORS["calculators"]),
      ("روایت میدانی","یک سوژهٔ واقعی، زمینهٔ عملیاتی و اقدام بعدی.","زمینه / مشاهده / اقدام",SECTION_COLORS["library"])]
    for i,(head,copy,recipe,accent) in enumerate(visual):
        x=120+i*570
        b.append(rect(x,335,520,470,WHITE,BORDER,22,2))
        # Different original visual blocks, not copied photographs.
        if i==0:
            b.append(rect(x+28,370,464,180,NAVY,radius=14))
            b.append(fa("تیتر اصلی",x+458,413,30,WHITE,FA_XBOLD,width=390))
            b.append(rect(x+40,502,220,7,accent,radius=3))
        elif i==1:
            b.append(rect(x+28,370,464,180,"#F1F5F9",radius=14))
            for j,h in enumerate([42,80,60,105,132]):
                b.append(rect(x+86+j*58,520-h,25,h,accent if j==3 else "#AAB6C6",radius=5))
            b.append(rule(x+65,520,x+455,520,NAVY,2))
        else:
            b.append(rect(x+28,370,464,180,"#E9EEF2",radius=14))
            b.append(circle(x+382,430,45,"#CAD7C8"))
            b.append(rect(x+55,442,185,80,"#C8BDAE",radius=10))
            b.append(path if False else "")
            b.append(f'<path d="M{x+80} 520 L{x+168} 412 L{x+257} 520" fill="none" stroke="{NAVY}" stroke-width="8" stroke-linejoin="round"/>')
        b.append(en(recipe.upper(),x+28,585,13,accent,LATIN_SEMI,width=460))
        b.append(fa(head,x+470,630,28,NAVY,FA_XBOLD,width=430))
        b.append(fa(copy,x+470,687,20,BODY,FA_REG,width=435,line_height=31))
    b.append(page_footer(10)); slides.append(svg_doc(1920,1080,"".join(b),None,"زبان بصری"))

    # 11 — motion principles
    b=title_block(11,"MOTION IDENTITY","حرکت لوگو؛ پیشروی، مکث، تثبیت","حرکت از مسیر رشد الهام می‌گیرد؛ بی‌صدا، کوتاه، آرام و با نسخهٔ reduced-motion.")
    # timeline
    b.append(rule(230,530,1690,530,"#C7D0DC",6))
    beats=[("۰٫۰ ثانیه","مسیر ظاهر می‌شود",230), ("۰٫۶ ثانیه","نشان شکل می‌گیرد",620), ("۱٫۱ ثانیه","نقطهٔ طلایی می‌نشیند",1010), ("۱٫۷ ثانیه","نام برند خوانا می‌شود",1400), ("۲٫۷ ثانیه","مکث و خروج",1690)]
    for i,(time,label,x) in enumerate(beats):
        b.append(circle(x,530,20,GOLD if i==2 else NAVY))
        b.append(en(time,x-72,460,15,MUTED,LATIN_SEMI,width=145,align="center"))
        b.append(fa(label,x+120,600,18,NAVY,FA_BOLD,width=270,align="center"))
    # motion principles cards
    principles=[("دامنه","ورود ۹۰۰ ms · تثبیت ۱۲۰۰ ms · خروج نرم"),("منحنی","روان و کنترل‌شده؛ بدون جهش کارتونی"),("دسترسی","بدون چشمک؛ reduced-motion با فید ثابت")]
    for i,(head,copy) in enumerate(principles):
        x=120+i*570
        b.append(rect(x,730,520,165,SURFACE,BORDER,18,2))
        b.append(fa(head,x+480,760,22,NAVY,FA_BOLD,width=450))
        b.append(fa(copy,x+480,807,18,MUTED,FA_REG,width=450))
    b.append(page_footer(11)); slides.append(svg_doc(1920,1080,"".join(b),None,"هویت حرکتی"))

    # 12 — toolkit and gates
    b=title_block(12,"ASSET TOOLKIT","دارایی‌ها پیش از محتوا؛ دروازهٔ تأیید قبل از بازنویسی","این تحویل، سیستم پایه و قالب خالی است؛ پکیج محتوایی وارد این فاز نشده است.")
    inventory=[("01","Brand book","تعریف‌ها، بخش‌ها، رنگ و لحن"),("02","Foundation sheets","توکن، فونت، لوگو، شبکه، موشن"),("03","Template masters","پست، کاروسل، کاور و لایهٔ ریل"),("04","Logo motion","سورس SVG، تایم‌لاین و MP4")]
    for i,(num,title,desc) in enumerate(inventory):
        x=120+i*420
        b.append(rect(x,335,385,250,WHITE,BORDER,20,2))
        b.append(en(num,x+28,365,17,GOLD,LATIN_BOLD,width=80))
        b.append(en(title.upper(),x+28,415,17,NAVY,LATIN_SEMI,width=325))
        b.append(fa(desc,x+340,475,20,BODY,FA_REG,width=315,line_height=30))
    b.append(rect(120,650,1680,255,NAVY,radius=22))
    b.append(en("REVIEW GATES",160,684,16,GOLD,LATIN_SEMI,width=280))
    gates=[("۱","هویت و پیام"),("۲","فونت و مجوز"),("۳","قالب‌های پست و کاروسل"),("۴","موشن و خروجی‌ها")]
    for i,(num,label) in enumerate(gates):
        x=190+i*405
        b.append(circle(x,790,26,GOLD))
        b.append(en(num,x,780,17,NAVY,LATIN_BOLD,width=45,align="center"))
        b.append(fa(label,x+300,775,21,WHITE,FA_BOLD,width=260,align="center"))
        if i<3:b.append(rule(x+55,790,x+340,790,"#6C7B92",3))
    b.append(fa("پس از دریافت نمونه‌های مرجع شما، فقط قالب‌ها و صفحات هویت بصری اصلاح می‌شوند؛ تولید محتوا بعد از تأیید دارایی‌ها.",1780,945,20,NAVY,FA_BOLD,width=1600))
    b.append(page_footer(12)); slides.append(svg_doc(1920,1080,"".join(b),None,"پکیج دارایی‌های پایه"))

    return slides


def template_svg(template_id, mode, width, height, accent=GOLD):
    """Blank, editable visual template master with literal Persian replacement tokens."""
    is_vertical=height>width
    dark=mode in {"quote","case-dark","reel-end"}
    bg=NAVY if dark else WHITE
    fg=WHITE if dark else NAVY
    secondary="#CBD5E1" if dark else BODY
    out=[rect(0,0,width,height,bg)]
    margin=70 if width<=1080 else 100
    out.append(rect(margin,margin,width-2*margin,12,accent,radius=6))
    # Brand signature at top; always separate from variable content.
    mark_size=90 if is_vertical else 72
    out.append(brand_mark(width-margin-mark_size,margin+38,mark_size,"white" if dark else "color"))
    out.append(en("AtoZfnb.info",margin,margin+45,18,fg,LATIN_SEMI,width=360))
    out.append(fa("آ تو ز",margin+215,margin+77,17,fg,FA_BOLD,width=155))
    gutter=50 if is_vertical else 34
    label_y=margin+142
    section=template_id.upper().replace("-","  ·  ")
    out.append(en(section[:54],margin,label_y,14,accent if not dark else GOLD,LATIN_SEMI,width=width-2*margin))
    if mode=="editorial":
        out.append(fa("[[عنوان اصلی]]",width-margin,label_y+86,62,fg,FA_XBOLD,width=width-2*margin,line_height=78))
        out.append(rect(margin,label_y+255,width*.46,290,"#EEF2F7",BORDER,20,2,'stroke-dasharray="10 8"'))
        out.append(fa("[[جای تصویر / نمودار]]",margin+width*.46-30,label_y+385,24,MUTED,FA_BOLD,width=width*.42))
        out.append(fa("[[پیام کلیدی]]",width-margin,label_y+600,30,secondary,FA_REG,width=width-2*margin))
    elif mode=="data":
        out.append(fa("[[شاخص / پرسش]]",width-margin,label_y+70,38,fg,FA_BOLD,width=width-2*margin))
        out.append(rect(margin,label_y+160,width-2*margin,380,accent,radius=22))
        out.append(fa("[[عدد]]",width/2,label_y+255,86,NAVY,FA_XBOLD,width=width-2*margin,align="center"))
        out.append(fa("[[توضیح و زمینهٔ عدد]]",width/2,label_y+390,25,NAVY,FA_BOLD,width=width-2*margin,align="center"))
        out.append(fa("منبع: [[نام منبع · تاریخ]]",width-margin,label_y+605,17,secondary,FA_REG,width=width-2*margin))
    elif mode=="case":
        out.append(fa("[[عنوان مطالعهٔ موردی]]",width-margin,label_y+72,48,fg,FA_XBOLD,width=width-2*margin))
        half=(width-2*margin-25)/2
        out.append(rect(margin,label_y+180,half,310,"#F1F5F9",BORDER,18,2))
        out.append(rect(margin+half+25,label_y+180,half,310,"#F1F5F9",BORDER,18,2))
        out.append(fa("[[زمینه]]",margin+half-20,label_y+220,24,accent if not dark else GOLD,FA_BOLD,width=half-35))
        out.append(fa("[[تصویر/نمودار]]",margin+half-20,label_y+320,19,MUTED,FA_REG,width=half-35))
        out.append(fa("[[بینش یا گام بعدی]]",width-margin,label_y+570,27,secondary,FA_REG,width=width-2*margin))
    elif mode=="quote":
        out.append(en("FIELD NOTE  /  QUOTE",margin,label_y+80,16,GOLD,LATIN_SEMI,width=500))
        out.append(fa("«",width-margin,label_y+200,112,GOLD,FA_XBOLD,width=150))
        out.append(fa("[[نقل‌قول کوتاه]]",width-margin,label_y+355,57,fg,FA_XBOLD,width=width-2*margin,line_height=76))
        out.append(rule(margin,label_y+540,width-margin,label_y+540,"#334155",2))
        out.append(fa("[[نام / منبع / زمینه]]",width-margin,label_y+600,22,secondary,FA_REG,width=width-2*margin))
    elif mode=="carousel-cover":
        out.append(fa("[[قلاب کوتاه]]",width-margin,label_y+116,64,fg,FA_XBOLD,width=width-2*margin,line_height=83))
        out.append(rect(margin,label_y+370,width-2*margin,410,"#EEF2F7",BORDER,22,2,'stroke-dasharray="12 9"'))
        out.append(fa("[[تصویر / نمودار اصلی]]",width/2,label_y+555,25,MUTED,FA_BOLD,width=width-2*margin,align="center"))
        out.append(fa("اسلاید ۱  /  [[تعداد]]",width-margin,height-margin-35,17,MUTED,FA_REG,width=width-2*margin))
    elif mode=="carousel-body":
        out.append(fa("[[شمارهٔ گام]]",width-margin,label_y+70,27,accent if not dark else GOLD,FA_BOLD,width=width-2*margin))
        out.append(fa("[[عنوان یک نکته]]",width-margin,label_y+155,48,fg,FA_XBOLD,width=width-2*margin))
        out.append(fa("[[شرح کوتاه؛ یک ایده در هر اسلاید]]",width-margin,label_y+270,27,secondary,FA_REG,width=width-2*margin,line_height=42))
        out.append(rect(margin,label_y+475,width-2*margin,290,"#F1F5F9",BORDER,18,2,'stroke-dasharray="9 7"'))
        out.append(fa("[[مثال / نمودار / تصویر]]",width/2,label_y+590,23,MUTED,FA_BOLD,width=width-2*margin,align="center"))
        out.append(rule(margin,height-margin-65,width-margin,height-margin-65,BORDER,3))
        out.append(rect(margin,height-margin-65,(width-2*margin)*.28,6,accent,radius=3))
    elif mode=="carousel-compare":
        out.append(fa("[[عنوان مقایسه]]",width-margin,label_y+95,46,fg,FA_XBOLD,width=width-2*margin))
        half=(width-2*margin-24)/2
        for i,(label,x) in enumerate([("[[گزینهٔ یک]]",margin),("[[گزینهٔ دو]]",margin+half+24)]):
            out.append(rect(x,label_y+210,half,440,"#F8FAFC",BORDER,20,2))
            out.append(rect(x,label_y+210,half,16,SECTION_COLORS["library"] if i==0 else SECTION_COLORS["magazine"],radius=8))
            out.append(fa(label,x+half-24,label_y+260,26,fg,FA_BOLD,width=half-48))
            out.append(fa("[[معیار / نکته]]",x+half-24,label_y+340,22,secondary,FA_REG,width=half-48))
            out.append(rule(x+24,label_y+420,x+half-24,label_y+420,BORDER,2))
            out.append(fa("[[شرط / محدودیت]]",x+half-24,label_y+465,20,secondary,FA_REG,width=half-48))
    elif mode=="carousel-checklist":
        out.append(fa("[[عنوان چک‌لیست]]",width-margin,label_y+95,48,fg,FA_XBOLD,width=width-2*margin))
        for i in range(4):
            y=label_y+210+i*116
            out.append(rect(margin,y,46,46,WHITE,accent,10,3))
            out.append(fa(f"[[مورد {i+1}]]",width-margin,y+4,25,secondary,FA_REG,width=width-2*margin-80))
            if i<3:out.append(rule(margin,y+80,width-margin,y+80,BORDER,2))
    elif mode=="carousel-evidence":
        out.append(fa("[[ادعا یا پرسش]]",width-margin,label_y+90,42,fg,FA_XBOLD,width=width-2*margin))
        out.append(rect(margin,label_y+205,width-2*margin,370,"#F8FAFC",BORDER,18,2))
        for i,h in enumerate([110,180,138,240,205]):
            out.append(rect(margin+70+i*122,label_y+525-h,56,h,accent if i==3 else "#AEB9C8",radius=8))
        out.append(rule(margin+45,label_y+525,width-margin-40,label_y+525,NAVY,3))
        out.append(fa("منبع · بازه · محدودیت داده: [[مشخصات]]",width-margin,label_y+635,20,MUTED,FA_REG,width=width-2*margin))
    elif mode=="carousel-outro":
        out.append(fa("[[جمع‌بندی در یک جمله]]",width-margin,label_y+140,55,fg,FA_XBOLD,width=width-2*margin,line_height=72))
        out.append(rect(margin,label_y+400,width-2*margin,175,GOLD,radius=18))
        out.append(fa("[[اقدام بعدی]]",width/2,label_y+455,28,NAVY,FA_BOLD,width=width-2*margin,align="center"))
        out.append(fa("منابع و مسیر ادامه: [[نشانی قابل‌ویرایش]]",width-margin,label_y+650,19,secondary,FA_REG,width=width-2*margin))
    elif mode=="reel-cover":
        out.append(fa("[[قلاب ریل]]",width-margin,label_y+160,68,fg,FA_XBOLD,width=width-2*margin,line_height=90))
        out.append(rect(margin,label_y+500,width-2*margin,590,"#F1F5F9",BORDER,24,2,'stroke-dasharray="12 10"'))
        out.append(circle(width/2,label_y+795,60,WHITE,accent,4))
        out.append(f'<path d="M{width/2-16} {label_y+760} L{width/2+24} {label_y+795} L{width/2-16} {label_y+830}Z" fill="{accent}"/>')
        out.append(fa("[[فریم ویدئو / B-roll]]",width/2,label_y+965,21,MUTED,FA_BOLD,width=width-2*margin,align="center"))
        out.append(fa("زیرنویس امن · یک پیام در هر صحنه",width-margin,height-margin-70,17,MUTED,FA_REG,width=width-2*margin))
    elif mode=="reel-lower-third":
        out.append(rect(margin,height*.66,width-2*margin,210,"#0A1931",radius=22,extra='opacity=".94"'))
        out.append(rect(margin,height*.66,10,210,accent,radius=5))
        out.append(en("TOPIC  /  [[SECTION]]",margin+30,height*.66+28,14,GOLD,LATIN_SEMI,width=500))
        out.append(fa("[[زیرنویس کوتاه و پرکنتراست]]",width-margin-32,height*.66+78,30,WHITE,FA_BOLD,width=width-2*margin-64))
        out.append(fa("AtoZfnb.info",width-margin-24,height*.66+150,17,"#CBD5E1",FA_REG,width=width-2*margin-50))
    elif mode=="reel-end":
        out.append(circle(width/2,height*.40,width*.26,"#132747"))
        out.append(brand_mark(width*.35,height*.23,width*.30,"white"))
        out.append(en("AtoZfnb.info",width/2,height*.64,40,GOLD,LATIN_BOLD,width=width*.8,align="center"))
        out.append(fa("آ تو ز اف‌ان‌بی",width*.78,height*.70,28,WHITE,FA_BOLD,width=width*.7,align="center"))
        out.append(fa("[[دعوت به اقدام / URL قابل‌ویرایش]]",width*.78,height*.80,21,"#CBD5E1",FA_REG,width=width*.7,align="center"))
    # Shared footer; URL and handle are editable and never burned into a destination link.
    if mode not in {"reel-end","reel-cover","carousel-cover"}:
        fy=height-margin-35
        out.append(rule(margin,fy-42,width-margin,fy-42,"#334155" if dark else BORDER,2))
        out.append(en("atozfnb.info  ·  @atozfnb.info",margin,fy,15,secondary,LATIN_SEMI,width=620))
        if mode.startswith("carousel"):
            out.append(en("[[01 / 06]]",width-margin-140,fy,14,accent,LATIN_SEMI,width=140))
    return svg_doc(width,height,"".join(out),None,f"AtoZ template {template_id}","Editable template master with replaceable text and visual slots")


def build_templates():
    specs = [
        ("social/post-editorial","editorial",1080,1350,"single_post","Single editorial post"),
        ("social/post-data","data",1080,1350,"single_post","Evidence / data post"),
        ("social/post-case-study","case",1080,1350,"single_post","Case study / comparison post"),
        ("social/post-quote","quote",1080,1350,"single_post","Quote / field note post"),
        ("carousels/slide-01-cover","carousel-cover",1080,1350,"carousel_cover","Carousel cover"),
        ("carousels/slide-02-body","carousel-body",1080,1350,"carousel_body","Carousel body / one key idea"),
        ("carousels/slide-03-comparison","carousel-compare",1080,1350,"carousel_comparison","Carousel comparison"),
        ("carousels/slide-04-evidence","carousel-evidence",1080,1350,"carousel_evidence","Carousel evidence / source"),
        ("carousels/slide-05-checklist","carousel-checklist",1080,1350,"carousel_checklist","Carousel checklist"),
        ("carousels/slide-06-outro","carousel-outro",1080,1350,"carousel_outro","Carousel closing / CTA"),
        ("video-covers/reel-cover","reel-cover",1080,1920,"reel_cover","Reel cover / safe zones"),
        ("video-covers/reel-lower-third","reel-lower-third",1080,1920,"reel_overlay","Reel lower-third overlay"),
        ("video-covers/reel-end-card","reel-end",1080,1920,"reel_outro","Reel end card"),
    ]
    manifest=[]
    for path,mode,w,h,fmt,label in specs:
        dest=TEMPLATES/path
        dest=dest.with_suffix(".svg")
        dest.parent.mkdir(parents=True,exist_ok=True)
        accent=GOLD if "post" in path or "carousels" in path else SECTION_COLORS["library"]
        svg=template_svg(path.replace("/"," · "),mode,w,h,accent)
        dest.write_text(svg,encoding="utf-8")
        manifest.append({"template_id":path.replace("/","-"),"label":label,"format":fmt,"source_svg":str(dest.relative_to(ROOT)),"width":w,"height":h,"aspect_ratio":f"{w}:{h}","status":"template_for_owner_review","slots":["headline","body_or_visual","section","source_if_claim","editable_cta","brand_signature"],"fonts":{"fa":"Vazirmatn","latin":"Montserrat + Lato"}})
    (TEMPLATES/"template-manifest.json").write_text(json.dumps({"version":"1.0.0-draft","description":"Blank brand templates only; no week-one editorial text.","templates":manifest},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (TEMPLATES/"README.md").write_text("""# قالب‌های هویت بصری AtoZ.FnB

این‌ها masterهای خالی و قابل‌ویرایش‌اند؛ محتوا، عنوان‌های هفته و آمار واقعی در آن‌ها درج نشده است.

- `social/`: پست ادیتوریال، داده/منبع، کیس‌استادی، نقل‌قول
- `carousels/`: جلد، بدنه، مقایسه، شواهد، چک‌لیست، پایان/CTA
- `video-covers/`: کاور عمودی، lower-third، end-card
- `template-manifest.json`: ابعاد، نوع خروجی و slotهای قابل‌جایگزینی

هر master در SVG نگهداری و در PNG پیش‌نمایش می‌شود. قبل از پرکردن با محتوا، نمونه‌های قالب را با مرجع‌های مالک تطبیق دهید. لینک CTA قابل‌ویرایش می‌ماند و خودکار به مقصدی هدایت نمی‌شود.
""",encoding="utf-8")
    return manifest


def contrast_ratio(hex_a,hex_b):
    def channel(value):
        c=int(value,16)/255
        return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
    def lum(h):
        return .2126*channel(h[1:3])+.7152*channel(h[3:5])+.0722*channel(h[5:7])
    light,dark=sorted([lum(hex_a),lum(hex_b)],reverse=True)
    return round((light+.05)/(dark+.05),2)


def write_contrast_report():
    pairs={
      "body_navy_on_white":(NAVY,WHITE),"body_secondary_on_surface":("#475569",SURFACE),
      "navy_on_gold":(NAVY,GOLD),"white_on_navy":(WHITE,NAVY),
      "gold_on_white":(GOLD,WHITE)
    }
    report={"standard":"WCAG 2.2 contrast ratio calculation (sRGB)","thresholds":{"normal_text":4.5,"large_text":3.0},"pairs":{k:{"foreground":a,"background":b,"ratio":contrast_ratio(a,b),"normal_text_pass":contrast_ratio(a,b)>=4.5,"large_text_pass":contrast_ratio(a,b)>=3.0} for k,(a,b) in pairs.items()},"section_accents":{"policy":"Use accent for stripes, borders, icons, or large labels; do not assume small accent-colored text passes on white.","results":{}}
    }
    for key,color in SECTION_COLORS.items():
        report["section_accents"]["results"][key]={"accent":color,"on_white":contrast_ratio(color,WHITE),"large_text_on_white_pass":contrast_ratio(color,WHITE)>=3.0,"body_text_on_white_pass":contrast_ratio(color,WHITE)>=4.5,"navy_on_accent":contrast_ratio(NAVY,color),"white_on_accent":contrast_ratio(WHITE,color)}
    out=PRESETS/"contrast-report.json";out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# گزارش کنتراست رنگ", "", "محاسبه بر اساس sRGB و آستانهٔ متن معمولی ۴٫۵:۱ / متن بزرگ ۳:۱. این گزارش جایگزین آزمون تصویر نهایی، وزن فونت و اندازهٔ واقعی نیست.", "", "| جفت رنگ | نسبت | متن معمولی |", "|---|---:|---|"]
    for key,row in report["pairs"].items():
        lines.append(f"| {key} | {row['ratio']}:1 | {'قبول' if row['normal_text_pass'] else 'فقط تزئینی/تیتر بزرگ'} |")
    lines += ["", "رنگ طلایی روی سفید فقط تأکید بصری است، نه متن ریز. رنگ‌های ستون‌ها روی سفید برای خطوط، نشان و نوار به‌کار روند؛ متن بدنه با سرمه‌ای/خاکستری تیره نوشته شود."]
    (PRESETS/"contrast-report-fa.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return report


def build_design_sheets():
    SHEETS.mkdir(parents=True, exist_ok=True)
    outputs = {}

    # Color sheet: tokens, practical use, and accessible pairings.
    b = [rect(0, 0, 1600, 1000, SURFACE), en("AtoZ.FnB  /  COLOR TOKENS", 80, 78, 19, MUTED, LATIN_SEMI, width=600), fa("رنگ، برای معنا نه تزئین", 1510, 135, 42, NAVY, FA_XBOLD, width=1200)]
    swatches = [("سرمه‌ای پایه", NAVY), ("طلایی تأکیدی", GOLD), ("سطح خنثی", SURFACE), ("سفید", WHITE)]
    for i, (label, color) in enumerate(swatches):
        x = 80 + i * 365
        fg = WHITE if color == NAVY else NAVY
        b += [rect(x, 200, 320, 190, color, BORDER if color in (WHITE, SURFACE) else color, 18, 2), fa(label, x + 295, 270, 22, fg, FA_BOLD, width=280), en(color, x + 24, 345, 17, fg, LATIN_SEMI, width=240)]
    b.append(en("SECTION ACCENTS · LABEL + COLOR ALWAYS", 80, 465, 15, MUTED, LATIN_SEMI, width=600))
    for i, item in enumerate(PILLARS):
        x = 80 + i * 245; color = SECTION_COLORS[item["color_token"]]
        b += [rect(x, 500, 205, 80, color, radius=14), fa(item["name_fa"], x + 185, 520, 16, NAVY if color == GOLD else WHITE, FA_BOLD, width=170), en(color, x, 603, 13, MUTED, LATIN_SEMI, width=185)]
    b += [rect(80, 690, 1440, 190, PALE_GOLD, radius=18), fa("قاعدهٔ کنتراست", 1480, 725, 24, NAVY, FA_BOLD, width=400), fa("سرمه‌ای روی سفید: ۱۷٫۵۵:۱  ·  سرمه‌ای روی طلایی: ۹٫۸۵:۱  ·  طلایی روی سفید: ۱٫۷۸:۱", 1480, 775, 21, NAVY, FA_REG, width=1320), fa("طلایی و بعضی رنگ‌های ستون روی سفید برای متن ریز نیستند؛ ستون را با نام/نشانه هم مشخص کنید.", 1480, 825, 18, NAVY, FA_REG, width=1320)]
    outputs["color-system"] = svg_doc(1600, 1000, "".join(b), None, "AtoZ color system")

    # Content architecture sheet.
    b = [rect(0,0,1600,1000,WHITE), en("AtoZ.FnB  /  CONTENT ARCHITECTURE",80,78,19,MUTED,LATIN_SEMI,width=700), fa("شش ستون، مقصدهای روشن",1510,138,42,NAVY,FA_XBOLD,width=1300)]
    for i,item in enumerate(PILLARS):
        col=i%3; row=i//3; x=80+col*490; y=215+row*310; color=SECTION_COLORS[item["color_token"]]
        b += [rect(x,y,440,255,WHITE,BORDER,18,2), rect(x,y,9,255,color,radius=4), en(f"PILLAR 0{i+1}",x+30,y+26,14,color,LATIN_SEMI,width=200), fa(item["name_fa"],x+405,y+72,25,NAVY,FA_BOLD,width=365), fa(item["purpose_fa"],x+405,y+125,17,BODY,FA_REG,width=365,line_height=26), en(item["destination"].upper(),x+30,y+215,12,MUTED,LATIN_SEMI,width=360)]
    outputs["section-map"] = svg_doc(1600,1000,"".join(b),None,"Content pillar and destination map")

    # Logo use sheet with original vector mark, legal clearspace and min-size tests.
    b=[rect(0,0,1600,1000,SURFACE),en("AtoZ.FnB  /  LOGO USAGE",80,78,19,MUTED,LATIN_SEMI,width=500),fa("نشان را تغییر ندهید؛ زمینه را انتخاب کنید",1510,138,39,NAVY,FA_XBOLD,width=1350)]
    b += [rect(80,210,690,450,WHITE,BORDER,20,2), brand_mark(250,300,300,"color"), en("PRIMARY SYMBOL · COLOR",115,605,14,MUTED,LATIN_SEMI,width=400)]
    b += [rect(810,210,690,205,NAVY,radius=20),brand_mark(905,253,120,"white"),logo_lockup(1060,260,100,"white"),en("WHITE REVERSE · DARK BACKGROUND",845,375,14,"#CBD5E1",LATIN_SEMI,width=600)]
    b += [rect(810,455,690,205,WHITE,BORDER,20,2),brand_mark(905,495,120,"mono"),logo_lockup(1060,500,100,"mono"),en("MONOCHROME · SINGLE INK",845,620,14,MUTED,LATIN_SEMI,width=600)]
    b += [rect(80,705,1420,195,WHITE,BORDER,18,2),fa("حریم امن",1455,740,22,NAVY,FA_BOLD,width=250),fa("حداقل ۱× قطر نقطهٔ طلایی پیرامون کل ترکیب.",1455,785,19,BODY,FA_REG,width=1250),fa("حداقل اندازه: لاک‌آپ افقی ۱۲۰ px؛ عمودی ۱۰۰ px؛ نماد تنها ۲۴ px.",1455,830,19,BODY,FA_REG,width=1250),fa("تغییر رنگ، کشیدن، چرخاندن، سایه/درخشش و جداسازی بی‌قاعدهٔ نشان ممنوع.",1455,870,17,MUTED,FA_REG,width=1250)]
    outputs["logo-use"] = svg_doc(1600,1000,"".join(b),None,"Logo use and clearspace")

    # Grid sheet for the three production aspect ratios.
    b=[rect(0,0,1600,1000,WHITE),en("AtoZ.FnB  /  LAYOUT GRID",80,78,19,MUTED,LATIN_SEMI,width=500),fa("شبکه، نسبت تصویر و ناحیهٔ امن",1510,138,40,NAVY,FA_XBOLD,width=1350)]
    for x,y,w,h,label,cols in [(100,240,580,330,"PRESENTATION · 16:9 · 12 COL",12),(785,240,230,320,"FEED · 4:5",6),(1110,205,185,400,"STORY / REEL · 9:16",4)]:
        b += [rect(x,y,w,h,SURFACE,NAVY,12,2)]
        m=int(min(w,h)*.07)
        b.append(rect(x+m,y+m,w-2*m,h-2*m,"#F8FAFC",GOLD,6,2,'stroke-dasharray="8 6"'))
        cw=(w-2*m)/cols
        for i in range(cols): b.append(rect(x+m+i*cw+3,y+m+4,cw-6,h-2*m-8,"#E6EBF1",radius=3))
        b.append(en(label,x,y+h+30,13,MUTED,LATIN_SEMI,width=w))
    b += [fa("فید ۱۰۸۰×۱۳۵۰",1010,650,19,NAVY,FA_BOLD,width=380),fa("استوری/ریل ۱۰۸۰×۱۹۲۰؛ بالا ۱۲٪ و پایین ۱۶٪ خالی برای UI",1510,710,19,NAVY,FA_BOLD,width=900),fa("نمایش موبایل را در اندازهٔ واقعی هم بازبینی کنید.",1510,780,19,MUTED,FA_REG,width=850)]
    outputs["layout-grid"] = svg_doc(1600,1000,"".join(b),None,"Layout grids and safe zones")

    # Motion storyboard sheet; no animation or editorial copy.
    b=[rect(0,0,1600,800,NAVY),en("AtoZ.FnB  /  MOTION SYSTEM",80,75,19,"#CBD5E1",LATIN_SEMI,width=650),fa("لوگوموشن؛ رشد، مکث، تثبیت",1510,140,40,WHITE,FA_XBOLD,width=1300)]
    xs=[155,490,825,1160,1450]
    for i,x in enumerate(xs):
        if i==0: b.append(circle(x,340,14,GOLD))
        elif i==1: b.append(f'<path d="M{x-105} 385 Q{x-20} 320 {x+80} 285" fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>')
        elif i==2: b.append(brand_mark(x-75,275,125,"white"))
        elif i==3: b.append(brand_mark(x-85,270,145,"white")); b.append(en("AtoZ",x+2,385,23,WHITE,LATIN_BOLD,width=100))
        else: b.append(logo_lockup(x-130,285,90,"white"))
        if i<len(xs)-1:b.append(rule(x+90,340,xs[i+1]-115,340,"#52627B",3))
        b.append(en(["0.0 s","0.6 s","1.1 s","1.7 s","2.7 s"][i],x-40,460,14,GOLD,LATIN_SEMI,width=100,align="center"))
        b.append(fa(["مسیر","نشان","نقطه","نام برند","مکث"][i],x+60,510,18,WHITE,FA_BOLD,width=150,align="center"))
    b += [fa("ورود حدود ۹۰۰ ms · تثبیت ۱۲۰۰ ms · خروج نرم · ۳۰ fps · بدون صدا · reduced-motion",1510,655,18,"#CBD5E1",FA_REG,width=1340)]
    outputs["motion-principles"] = svg_doc(1600,800,"".join(b),None,"Motion identity storyboard")

    for key, data in outputs.items():
        (SHEETS/f"{key}.svg").write_text(data,encoding="utf-8")
    return outputs


def write_presets():
    PRESETS.mkdir(parents=True,exist_ok=True)
    (PRESETS/"layout-presets.json").write_text(json.dumps(SYSTEM["layout_presets"],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (PRESETS/"motion-presets.json").write_text(json.dumps(SYSTEM["motion_identity"],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    components={"version":"1.0.0-draft","components":[
      {"id":"section-tag","height_px":44,"uses":["section_name","section_color","icon_or_number"]},
      {"id":"headline","max_lines":3,"font":"Vazirmatn ExtraBold","keep_one_primary_message":True},
      {"id":"evidence-source","fields":["source_name","publication_date","method_or_scope"],"required_for_numeric_claims":True},
      {"id":"brand-footer","fields":["domain","instagram_handle"],"cta_target_editable":True},
      {"id":"carousel-progress","role":"position only","max_contrast":True},
      {"id":"reel-caption-safe-zone","top_ui_clear_pct":12,"bottom_ui_clear_pct":16}
    ]}
    (PRESETS/"component-presets.json").write_text(json.dumps(components,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return write_contrast_report()


def update_tokens():
    # Keep the existing logo geometry and variants untouched; extend only brand-system metadata.
    colors={
      "calculators":("#0F766E","آزمایشگاه ابزارها","نوار و نشان Calculators"),
      "academy":("#0284C7","آکادمی","نوار و نشان Academy"),
      "solutions":("#D97706","راهکارها","نوار و نشان Solutions"),
      "leadership":("#0A1931","رهبری","سرمه‌ای پایه برای محتوای رهبری"),
      "text_secondary":("#475569","متن ثانویه","متن بدنهٔ ثانویه روی سطح روشن"),
      "border":("#D9E0EA","مرز","خطوط و جداکننده‌های کم‌کنتراست")
    }
    for key,(hex_value,name,usage) in colors.items():
        if key in TOKENS["color"]:continue
        rgb=[int(hex_value[i:i+2],16) for i in (1,3,5)]
        TOKENS["color"][key]={"name_fa":name,"hex":hex_value,"rgb":rgb,"usage":usage}
    TOKENS["meta"]["version"]="2.0.0-draft"
    TOKENS["meta"]["phase"]="Phase 2: complete brand identity and reusable asset system"
    TOKENS["meta"]["notes_fa"]="منبع حقیقت رنگ، هویت لوگو و تایپوگرافی است؛ جزئیات معماری و قالب‌ها در brand/design-system.json آمده است. فایل‌های خروجی صرفاً دارایی پایه‌اند و محتوای هفته‌ای تولید نمی‌کنند."
    TOKENS["typography"]["expressive_display_candidate"]={"fa":"Dongol","status":"candidate_only","usage":"نمونهٔ کوتاه ادیتوریال؛ فایل فاقد U+200C است و مجوز منبع باید بازبینی شود.","not_for":"متن بدنه، کپشن، لوگوتایپ، عبارت دارای نیم‌فاصله"}
    TOKENS["typography"]["fallbacks"]={"fa":"Vazirmatn, Noto Sans Arabic, Tahoma, sans-serif","latin_heading":"Montserrat, Arial, sans-serif","latin_body":"Lato, Arial, sans-serif"}
    TOKENS["typography"]["license_note_fa"]="Vazirmatn، Montserrat و Lato در LICENSES.txt با مجوز OFL 1.1 ثبت شده‌اند. Dongol فقط مجوز OFL را در متادیتای فایل اعلام می‌کند و هنوز نامزد آزمایشی است. سایر فونت‌های ارسالی با All Rights Reserved یا مجوز نامشخص تا تأیید مالک در خروجی عمومی استفاده نمی‌شوند. ایران‌سنس دست‌نویس نصب نشده است."
    TOKENS["identity_system"]={"version":"2.0.0-draft","design_system":"brand/design-system.json","font_audit":"brand/fonts/font-inventory.json","font_policy":"Use only licensed families; preserve owner-supplied restricted fonts without embedding them in public exports."}
    TOKENS_PATH.write_text(json.dumps(TOKENS,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def write_font_documents():
    SHEETS.mkdir(parents=True, exist_ok=True)
    inventory=json.loads((ROOT/"brand/fonts/font-inventory.json").read_text(encoding="utf-8"))
    specimen=[]
    specimen.append(rect(0,0,1600,900,SURFACE))
    specimen.append(en("TYPE SYSTEM  /  LICENSE REVIEW",80,90,20,MUTED,LATIN_SEMI,width=800))
    specimen.append(fa("تایپوگرافی؛ خوانایی اول",1500,155,52,NAVY,FA_XBOLD,width=1000))
    specimens=[
      ("فارسی · تیتر",FA_XBOLD,"رشد کسب‌وکار F&B",NAVY),
      ("فارسی · بدنه",FA_REG,"یک ایدهٔ روشن، یک اقدام قابل‌آزمون.",BODY),
      ("نامزد ادیتوریال · Dongol (بدون تعبیهٔ فونت)",FA_REG,"آ تو ز",SECTION_COLORS["magazine"]),
    ]
    for i,(label,font,copy,color) in enumerate(specimens):
        y=245+i*190
        specimen.append(rect(80,y,1440,150,WHITE,BORDER,18,2))
        specimen.append(fa(label,1470,y+28,16,MUTED,FA_BOLD,width=440))
        specimen.append(fa(copy,1470,y+72,38,color,font,width=1280))
        if "Dongol" in label:
            specimen.append(en("CANDIDATE ONLY · NOT EMBEDDED · MISSING ZWNJ · LICENSE SOURCE CHECK REQUIRED",115,y+118,12,"#7B5C45",LATIN_SEMI,width=1000))
    specimen.append(fa("لاتین · عنوان و متن",1470,855,22,NAVY,FA_BOLD,width=420))
    specimen.append(en("Montserrat Bold  /  Lato Regular  ·  AtoZfnb.info",115,830,27,NAVY,LATIN_SEMI,width=950))
    sheet=svg_doc(1600,900,"".join(specimen),None,"Typography specimen sheet","Approved stack and a clearly marked candidate; proprietary fonts excluded")
    (SHEETS/"typography-specimen.svg").write_text(sheet,encoding="utf-8")
    # The audit report intentionally lists every filename and flags restricted use.
    (SHEETS/"README-fa.md").write_text("""# شیت‌های هویت

شیت‌ها از همان منبع رنگ، فونت و ابعاد ساخته می‌شوند:

- `color-system.svg/png`: رنگ پایه، رنگ ستون‌ها و قاعدهٔ کنتراست
- `section-map.svg/png`: تعریف ستون‌های محتوایی و مقصدهای سایت
- `typography-specimen.svg/png`: خانواده‌های پایه و نامزد ادیتوریال با برچسب وضعیت
- `logo-use.svg/png`: نسخه‌ها، اندازهٔ حداقلی و حریم امن
- `layout-grid.svg/png`: شبکه و safe-zoneهای قالب‌ها
- `motion-principles.svg/png`: تایم‌لاین موشن

برای ممیزی فایل‌های فونت، به `brand/fonts/font-inventory-fa.md` مراجعه کنید.
""",encoding="utf-8")


def build_html(slides):
    slide_tags=[]
    for i in range(1,len(slides)+1):
        slide_tags.append(f'<section class="slide" id="s{i}"><img src="slides/slide-{i:02d}.svg" alt="AtoZ.FnB brand guide slide {i}"><span>{i:02d} / {len(slides):02d}</span></section>')
    html_doc=f'''<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AtoZ.FnB — Brand Book 2.0</title><style>
*{{box-sizing:border-box}}html{{scroll-snap-type:y mandatory;background:#0A1931}}body{{margin:0;color:#0A1931;font-family:Vazirmatn,Tahoma,sans-serif}}.slide{{height:100vh;min-height:540px;display:grid;place-items:center;scroll-snap-align:start;position:relative;background:#fff}}.slide img{{width:min(100vw,177.78vh);height:min(56.25vw,100vh);object-fit:contain}}.slide span{{position:absolute;bottom:20px;left:24px;color:#64748B;font:600 13px Montserrat,Arial,sans-serif}}@media print{{html{{scroll-snap-type:none;background:#fff}}.slide{{height:auto;min-height:0;page-break-after:always}}.slide img{{width:100%;height:auto}}.slide span{{display:none}}}}
</style>{''.join(slide_tags)}<script>document.addEventListener('keydown',e=>{{if(e.key==='ArrowDown'||e.key==='PageDown')window.scrollBy({{top:innerHeight,behavior:'smooth'}});if(e.key==='ArrowUp'||e.key==='PageUp')window.scrollBy({{top:-innerHeight,behavior:'smooth'}})}})</script></html>'''
    (BOOK/"brand-book.html").write_text(html_doc,encoding="utf-8")


def main():
    update_tokens()
    # Re-run the inventory after updating the license notice; the audit itself is standalone.
    subprocess.run([sys.executable,str(ROOT/"tools/audit_brand_fonts.py")],check=True,cwd=ROOT)
    build_design_sheets()
    write_font_documents()
    PRESETS.mkdir(parents=True,exist_ok=True)
    write_presets()
    slides=build_book_slides()
    SLIDES.mkdir(parents=True,exist_ok=True)
    for i,svg in enumerate(slides,1):
        (SLIDES/f"slide-{i:02d}.svg").write_text(svg,encoding="utf-8")
    manifest={"version":"2.0.0-draft","format":"16:9 presentation","slides":[{"slide":i,"file":f"slides/slide-{i:02d}.svg","title":"AtoZ.FnB identity"} for i in range(1,len(slides)+1)],"note":"Review edition; owner approval is required before applying to full content packages."}
    (BOOK/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    build_html(slides)
    build_templates()
    MOTION.mkdir(parents=True, exist_ok=True)
    (MOTION/"README-fa.md").write_text("""# لوگوموشن AtoZ.FnB — نسخهٔ پایه

سه خروجی بی‌صدا به همراه SVG منبع و مشخصات تایم‌لاین:

- `growth-reveal`: نمایان‌شدن مسیر رشد و نشان
- `brand-lockup`: تثبیت نماد، نام لاتین و نام فارسی «آ تو ز»
- `vertical-outro`: کارت پایانی عمودی برای ویدئو

مدت‌ها کوتاه و بدون افکت چشمک‌زن‌اند. در همهٔ منابع، نسخهٔ ثابت و `prefers-reduced-motion` در نظر گرفته شده است. MP4ها پیش‌نمایش نهایی برای استفادهٔ عمومی نیستند و تا بازبینی مالک، وضعیت آن‌ها draft است.
""",encoding="utf-8")
    (ROOT/"brand/README-fa.md").write_text("""# هویت پایهٔ AtoZ.FnB — دارایی‌ها، نه محتوا

- کتاب برند: `brand/brand-book/brand-book.pdf` و HTML قابل پیمایش
- شیت‌ها و ممیزی فونت: `brand/sheets/` و `brand/fonts/`
- توکن‌ها و presetها: `brand/tokens.json`, `brand/design-system.json`, `brand/presets/`
- قالب‌های خالی: `content-templates/`
- لوگوموشن: `logo-motion/`

این بسته در وضعیت draft برای مرور مالک است. هیچ محتوای هفته‌ای، CTA نهایی، زمان‌بندی یا انتشار خودکار ساخته نمی‌شود. فونت‌های دارای حق نامشخص حفظ شده‌اند اما وارد خروجی‌های عمومی نشده‌اند.

جعبه‌ابزار آپلودشدهٔ `CaReMa` بررسی شد، اما به این ریپو منتقل نشد: پیکربندی و ماژول‌های HR/CRM/ERP/منو برای هویت و محصول دیگری‌اند و نشانش با AtoZ فرق می‌کند. مرجع‌های تصویری فقط برای سطح کیفیت و سلسله‌مراتب بصری در نظر گرفته شدند؛ دارایی یا محتوای برند دیگر کپی نشده است. ارزیابی فنی وابستگی‌ها در `tools/ENGINE-REVIEW-fa.md` قرار دارد.
""",encoding="utf-8")
    print(f"Prepared {len(slides)} book slides and reusable identity templates. Run tools/render_identity_assets.mjs, then tools/finalize_identity_assets.py.")


if __name__=="__main__":
    main()
