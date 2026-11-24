#!/usr/bin/env python3
"""Generate the cleaned AtoZ logo family, brand book, templates and responsive motion gallery."""
from __future__ import annotations
import html
import json
import math
import re
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build_logo as core

TOKENS_PATH=ROOT/"brand/tokens.json"
TOKENS=json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
LOGO=ROOT/"logo"
PRIMARY=LOGO/"primary"
SUBS=LOGO/"subbrands"
MOTION=LOGO/"motion"
BOOK=LOGO/"brand-book"
TEMPLATES=ROOT/"content-templates"
NAVY=TOKENS["color"]["strategic_navy"]["hex"]
GOLD=TOKENS["color"]["innovation_gold"]["hex"]
WHITE="#FFFFFF"
SURFACE=TOKENS["color"]["neutral_surface"]["hex"]
INK="#13233D"
MUTED="#64748B"
BORDER="#D9E0EA"
PALETTE={
 "blog":TOKENS["color"]["magazine"]["hex"],
 "tools":TOKENS["color"]["calculators"]["hex"],
 "book":TOKENS["color"]["library"]["hex"],
 "pb":TOKENS["color"]["ai_prompts"]["hex"],
 "solicitor":TOKENS["color"]["solutions"]["hex"],
}
SUBBRANDS=[
 {"id":"blog","name":"Blog","display":"AtoZ Blog","purpose_fa":"مقاله، رهبری و مطالعهٔ موردی","content_pillars":["case-studies","leadership"],"icon":"editorial"},
 {"id":"tools","name":"Tools","display":"AtoZ Tools","purpose_fa":"ابزارهای محاسبه و کاربرد عملیاتی","content_pillars":["finance-market"],"icon":"toolkit"},
 {"id":"book","name":"book","display":"AtoZ book","purpose_fa":"آموزش، مسیر یادگیری و SOP","content_pillars":["education-sops","community-roadmaps"],"icon":"book"},
 {"id":"pb","name":"PB","display":"AtoZ PB","descriptor":"PROMPT BANK","purpose_fa":"بانک پرامپت و استفادهٔ مسئولانه از AI","content_pillars":["innovation-ai"],"icon":"prompt-bank"},
 {"id":"solicitor","name":"Solicitor","display":"AtoZ Solicitor","purpose_fa":"حوزهٔ دقیق این نام نیازمند تعریف مالک است","content_pillars":[],"scope_status":"pending_owner_definition","icon":"structured-document"},
]
PILLARS=[
 {"id":"education-sops","title":"F&B education & operating systems","fa":"آموزش F&B و سیستم‌های عملیاتی","purpose_fa":"یادگیری مرحله‌ای، SOP و چک‌لیست‌های قابل اجرا برای تیم‌ها و مدیران عملیات.","destination":"AtoZ book","color_id":"book"},
 {"id":"leadership","title":"Leadership and owner growth","fa":"رهبری و رشد مالکان","purpose_fa":"تصمیم‌گیری، مدیریت تیم و رشد بنیان‌گذار؛ تجربه از ادعای عمومی تفکیک شود.","destination":"AtoZ Blog","color_id":"blog"},
 {"id":"innovation-ai","title":"AI, innovation and automation","fa":"هوش مصنوعی، نوآوری و اتوماسیون","purpose_fa":"کاربردهای عملی AI و اتوماسیون؛ حریم خصوصی و نیاز به بازبینی انسانی رعایت شود.","destination":"AtoZ PB","color_id":"pb"},
 {"id":"finance-market","title":"F&B finance and market analysis","fa":"مالی و تحلیل بازار F&B","purpose_fa":"هزینه، قیمت‌گذاری، اقتصاد واحد و بازار؛ عدد و ادعا فقط با منبع معتبر.","destination":"AtoZ Tools","color_id":"tools"},
 {"id":"case-studies","title":"Case studies and field analysis","fa":"مطالعهٔ موردی و تحلیل میدانی","purpose_fa":"زمینه، روش، نتیجه و محدودیت مطالعهٔ موردی به‌صورت شفاف روایت شود.","destination":"AtoZ Blog","color_id":"blog"},
 {"id":"community-roadmaps","title":"Learning paths and community","fa":"مسیر یادگیری و جامعه","purpose_fa":"نقشه‌راه‌های پیوسته، منابع و یادگیری همتا‌به‌همتا؛ بدون وعدهٔ نتیجهٔ قطعی.","destination":"AtoZ book","color_id":"book"},
]

FA_BOLD="Vazirmatn-Bold.ttf"
FA_XBOLD="Vazirmatn-ExtraBold.ttf"
FA_REG="Vazirmatn-Regular.ttf"
FA_MED="Vazirmatn-Medium.ttf"
LATIN_BOLD="Montserrat-Bold.ttf"
LATIN_XBOLD="Montserrat-ExtraBold.ttf"
LATIN_SEMI="Montserrat-SemiBold.ttf"
LATIN_BODY="Lato-Regular.ttf"


def esc(s): return html.escape(str(s),quote=True)

def rect(x,y,w,h,fill=WHITE,stroke="none",r=0,sw=1,extra=""):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'

def line(x1,y1,x2,y2,color=BORDER,sw=2,dash=""):
 d=f' stroke-dasharray="{dash}"' if dash else ""
 return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round"{d}/>'

def circle(cx,cy,r,fill,stroke="none",sw=0):
 return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

def outlined(text,x,y,size,color,font=FA_REG,direction="rtl",align="right"):
 run={"font":font,"text":text,"size":size,"direction":direction,"script":"Arab" if direction=="rtl" else "Latn","language":"fa" if direction=="rtl" else "en","fill":color}
 frag,w,h=core.line_svg([run],rtl=(direction=="rtl"))
 px=x-w if align=="right" else (x-w/2 if align=="center" else x)
 return f'<g transform="translate({px:.2f} {y:.2f})">{frag}</g>',w,h

def wrap_lines(text,font,size,max_width,direction="rtl"):
 output=[]
 for para in text.split("\n"):
  words=para.split(); cur=""
  if not words: output.append(""); continue
  for word in words:
   candidate=(cur+" "+word).strip()
   run={"font":font,"text":candidate,"size":size,"direction":direction,"script":"Arab" if direction=="rtl" else "Latn","language":"fa" if direction=="rtl" else "en","fill":INK}
   if cur and core.line_svg([run],rtl=(direction=="rtl"))[1]>max_width:
    output.append(cur); cur=word
   else:cur=candidate
  if cur:output.append(cur)
 return output

def text_block(text,right,y,size,color,font=FA_REG,width=700,direction="rtl",align="right",leading=1.4):
 result=[]; lines=wrap_lines(text,font,size,width,direction)
 for i,row in enumerate(lines):
  if not row:continue
  group,_,_=outlined(row,right,y+i*size*leading,size,color,font,direction,align)
  result.append(group)
 return "".join(result),max(1,len(lines))*size*leading

def fa(text,right,y,size,color=INK,font=FA_REG,width=1000,leading=1.4):
 return text_block(text,right,y,size,color,font,width,"rtl","right",leading)[0]

def en(text,x,y,size,color=INK,font=LATIN_BODY,width=1000,align="left",leading=1.3):
 return text_block(text,x,y,size,color,font,width,"ltr",align,leading)[0]

def svg_doc(w,h,body,title,desc=""):
 return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
         f'<title>{esc(title)}</title><desc>{esc(desc)}</desc>{rect(0,0,w,h,"none")}{body}</svg>')

def place_mark(x,y,width,variant="color",dot=None):
 s=width/core.SYM_W
 if variant=="white" and dot is None:dot=GOLD
 fragment=core.symbol_group(variant,dot_override=dot)
 return f'<g transform="translate({x-core.SYM_X0*s:.3f} {y-core.SYM_Y0*s:.3f}) scale({s:.7f})">{fragment}</g>',core.SYM_H*s

def name_run(text,size,color,font=LATIN_XBOLD):
 return {"font":font,"text":text,"size":size,"direction":"ltr","script":"Latn","language":"en","fill":color}

def fa_run(text,size,color,font=FA_REG):
 return {"font":font,"text":text,"size":size,"direction":"rtl","script":"Arab","language":"fa","fill":color}

def run_fragment(runs,x,y,align="left",rtl=False):
 frag,w,h=core.line_svg(runs,rtl=rtl)
 px=x-w/2 if align=="center" else (x-w if align=="right" else x)
 return f'<g transform="translate({px:.2f} {y:.2f})">{frag}</g>',w,h

def group_lines(lines): return "".join(lines)

def svg_inner(svg):
 return re.sub(r'^<svg[^>]*><title>.*?</title><desc>.*?</desc><rect[^>]*/>', '', svg, count=1, flags=re.S).rsplit('</svg>',1)[0]


def primary_lockup(layout,variant):
 color=core.VARIANTS[variant]["mark"]
 text_color=core.VARIANTS[variant]["main"]
 accent=core.VARIANTS[variant]["accent"]
 is_white=variant=="white"
 if layout=="symbol":
  mark,_=place_mark(28,165,544,variant,dot=None)
  return svg_doc(600,600,mark,f"AtoZ primary symbol — {variant}","Reference AZ emblem: the A flows into an ascending Z arrow, finished by the gold node")
 if layout=="wordmark":
  frag,w,h=run_fragment([name_run("AtoZ",260,text_color)],24,26)
  return svg_doc(max(640,int(w+48)),330,frag,f"AtoZ wordmark — {variant}","Latin AtoZ wordmark only")
 if layout=="square":
  mark,_=place_mark(240,100,544,variant,dot=None)
  word,ww,wh=run_fragment([name_run("AtoZ",156,text_color)],512,755,align="center")
  return svg_doc(1024,1024,mark+word,f"AtoZ square lockup — {variant}","Symbol centered above the AtoZ wordmark")
 if layout=="horizontal":
  mark,mh=place_mark(42,38,520,variant,dot=None)
  word,ww,wh=run_fragment([name_run("AtoZ",225,text_color)],635,122)
  return svg_doc(1170,335,mark+word,f"AtoZ horizontal lockup — {variant}","Symbol on the left, AtoZ on the right")
 if layout=="vertical":
  mark,_=place_mark(263,55,498,variant,dot=None)
  word,ww,wh=run_fragment([name_run("AtoZ",155,text_color)],512,660,align="center")
  return svg_doc(1024,850,mark+word,f"AtoZ vertical lockup — {variant}","Symbol above the AtoZ wordmark")
 if layout=="founder":
  mark,_=place_mark(36,57,395,variant,dot=None)
  top,_,_=run_fragment([name_run("AtoZfnb.info",91,text_color,LATIN_XBOLD)],492,61)
  founder,_,_=run_fragment([fa_run("امیر زمانی",47,text_color,FA_BOLD)],1075,174,"right",rtl=True)
  title,_,_=run_fragment([fa_run(TOKENS["brand"]["title_fa"],29,text_color,FA_REG)],1075,236,"right",rtl=True)
  return svg_doc(1120,340,mark+top+founder+title,f"AtoZfnb.info founder signature — {variant}","AtoZfnb.info with Persian founder name and provisional title awaiting owner confirmation")
 raise KeyError(layout)


def subbrand_lockup(sub,layout,variant):
 item=next(x for x in SUBBRANDS if x["id"]==sub)
 accent=PALETTE[sub]
 txt=core.VARIANTS[variant]["main"]
 desc_color=WHITE if variant=="white" else (NAVY if variant=="mono" else accent)
 dot=None
 if layout=="icon":
  return subbrand_icon_svg(sub,variant)
 mark,_=place_mark(34,30,335,variant,dot=dot)
 runs=[name_run("AtoZ",126,txt,LATIN_XBOLD),name_run(" "+item["name"],92,desc_color,LATIN_SEMI)]
 x,_,_=run_fragment(runs,425,97)
 if sub=="pb":
  descriptor,_,_=run_fragment([name_run("PROMPT BANK",29,desc_color,LATIN_SEMI)],425,220)
  x+=descriptor
 return svg_doc(1110,270,mark+x,f'{item["display"]} — {variant}',f'{item["display"]} sub-brand lockup with primary AtoZ mark')


def subbrand_icon_elements(sub,stroke,accent):
 # Original, matched 24-unit outline pictograms; no external marks or copied glyphs.
 common=f'fill="none" stroke="{stroke}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"'
 accent_style=f'fill="none" stroke="{accent}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"'
 a=accent
 if sub=="blog":
  return f'<path {common} d="M4 5.5h7a3 3 0 0 1 3 3v11a3 3 0 0 0-3-3H4zM20 5.5h-7a3 3 0 0 0-3 3v11a3 3 0 0 1 3-3h7z"/><path d="M6.5 9h3M6.5 12h3M14.5 9h3M14.5 12h3" {accent_style}/>'
 if sub=="tools":
  return f'<path {common} d="M5 5v14M12 5v14M19 5v14"/><path d="M3 9h4M10 15h4M17 8h4" {accent_style}/><circle cx="5" cy="9" r="2" fill="{stroke}"/><circle cx="12" cy="15" r="2" fill="{stroke}"/><circle cx="19" cy="8" r="2" fill="{stroke}"/>'
 if sub=="book":
  return f'<path {common} d="M3.5 5.5c3.6-.9 6.5-.2 8.5 1.8v12c-2-2-4.9-2.7-8.5-1.8zM20.5 5.5c-3.6-.9-6.5-.2-8.5 1.8v12c2-2 4.9-2.7 8.5-1.8z"/><path d="M6 9h3M15 9h3" {accent_style}/>'
 if sub=="pb":
  return f'<path {common} d="M4 5.5h16v11H11l-5 3v-3H4z"/><path d="m12 7 1.1 2.6L16 10.5l-2.5 1.3-.8 2.7-1.4-2.4-2.7-.5 2.2-1.7z" {accent_style}/>'
 return f'<path {common} d="M6 3.5h8l4 4V20H6zM14 3.5V8h4"/><path {accent_style} d="M9 12h6M9 15.5h6M9 19h4"/><circle cx="18" cy="18" r="1.7" fill="{a}" stroke="none"/>'

def subbrand_icon_svg(sub,variant="color"):
 accent=PALETTE[sub]
 stroke=WHITE if variant=="white" else NAVY
 highlight=WHITE if variant=="white" else (NAVY if variant=="mono" else accent)
 body=subbrand_icon_elements(sub,stroke,highlight)
 back=rect(0,0,128,128,NAVY,r=28) if variant=="white" else ""
 return svg_doc(128,128,back+f'<g transform="translate(16 16) scale(4)">{body}</g>',f'AtoZ {sub} icon — {variant}',f'Original {sub} pictogram in the AtoZ icon family')


def icon_board_svg():
 body=[rect(0,0,1600,900,SURFACE),en("AtoZ  /  ICON SYSTEM",72,58,20,MUTED,LATIN_SEMI,width=600),fa("آیکون‌های زیر‌برند",1515,118,44,NAVY,FA_XBOLD,width=1000)]
 for i,s in enumerate(SUBBRANDS):
  x=86+i*298; color=PALETTE[s["id"]]
  body += [rect(x,225,250,470,WHITE,BORDER,20,2),rect(x,225,250,9,color,r=4)]
  glyph=subbrand_icon_elements(s["id"],NAVY,color)
  body.append(f'<g transform="translate({x+61} 300) scale(5.2)">{glyph}</g>')
  body.append(en(s["display"],x+26,560,23,NAVY,LATIN_BOLD,width=205))
  body.append(rect(x+28,620,40,8,color,r=4))
 body += [fa("خانوادهٔ آیکون: خطوط یکدست، فضای خالی، بدون تزئین یا جزئیات ریز؛ آیکون مستقل از وردمارک استفاده می‌شود.",1510,780,22,INK,FA_REG,width=1380)]
 return svg_doc(1600,900,"".join(body),"AtoZ sub-brand icon family")


def color_variant_svg():
 body=[rect(0,0,1600,900,SURFACE),en("AtoZ  /  LOGO COLOR MODES",72,58,20,MUTED,LATIN_SEMI,width=800),fa("رنگ، زمینه و کنتراست لوگو",1510,118,42,NAVY,FA_XBOLD,width=1200)]
 for i,(variant,bg,label) in enumerate([("color",WHITE,"رنگی روی روشن"),("mono",WHITE,"تک‌رنگ"),("white",NAVY,"سفید روی تیره")]):
  x=76+i*510
  body.append(rect(x,225,460,355,bg,BORDER if bg==WHITE else NAVY,18,2))
  logo_svg=primary_lockup("horizontal",variant)
  # Use wordmarks at native vector scale; one SVG per variant is also in the asset tree.
  inner=core.symbol_group(variant,dot_override=GOLD if variant=="white" else None)
  body.append(f'<g transform="translate({x+45} 350) scale(.24)">{inner}</g>')
  body.append(en("AtoZ",x+185,370,95,WHITE if variant=="white" else NAVY,LATIN_XBOLD,width=210))
  body.append(fa(label,x+425,510,21,WHITE if variant=="white" else NAVY,FA_BOLD,width=310))
 body += [rect(76,635,1440,160,"#FFF4D5",r=16),fa("کنتراست تأییدشده",1480,665,23,NAVY,FA_BOLD,width=330),fa("سرمه‌ای روی سفید ۱۷٫۵۵:۱ · سرمه‌ای روی طلایی ۹٫۸۵:۱ · سفید روی سرمه‌ای ۱۷٫۵۵:۱",1480,710,20,NAVY,FA_REG,width=1340),fa("طلایی روی سفید ۱٫۷۸:۱ است؛ هرگز برای متن ریز، یا لوگوی زرد روی زمینهٔ سفید استفاده نشود.",1480,755,18,NAVY,FA_REG,width=1340)]
 return svg_doc(1600,900,"".join(body),"AtoZ logo contrast and color use")


def build_tokens_and_system():
 # Remove the Persian transliteration from the brand-name identity while retaining the approved Persian founder/title.
 TOKENS["meta"].update({"version":"3.0.0","phase":"AtoZ master and sub-brand identity"})
 TOKENS["brand"]["name_latin"]="AtoZ"
 TOKENS["brand"]["name_latin_display"]="AtoZ"
 TOKENS["brand"]["name_fa"]="AtoZ"
 TOKENS["brand"]["founder_latin"]="Amir Zamani"
 TOKENS["brand"]["founder_fa"]="امیر زمانی"
 TOKENS["brand"]["title_fa"]="استراتژیست رشد F&B"
 TOKENS["brand"]["title_fa_status"]="provisional — owner confirmation required before public release"
 TOKENS["brand"]["domain"]=None
 TOKENS.pop("contact_placeholder",None)
 TOKENS["brand"]["name_fa_parts"]=[]
 TOKENS["brand"]["site_name_variants"]=["AtoZ","AtoZfnb.info"]
 TOKENS["typography"]["logo_wordmark_latin"]="Montserrat ExtraBold"
 TOKENS["typography"]["logo_wordmark_fa"]="not_used — Persian AtoZ wordmark prohibited"
 TOKENS["typography"]["logo_full_name_fa"]="Vazirmatn Bold — founder only"
 TOKENS["typography"]["logo_full_title_fa"]="Vazirmatn Medium — founder subtitle only"
 TOKENS["typography"]["expressive_display_candidate"]={"status":"removed","reason":"Unused; reducing bundled font set."}
 TOKENS["typography"]["license_note_fa"]="فقط Vazirmatn، Montserrat و Lato (مجوز SIL OFL 1.1) در سیستم باقی مانده‌اند. در لوگوهای AtoZ هیچ وردمارک فارسی وجود ندارد؛ متن فارسی فقط برای امیر زمانی و زیرعنوان پیشنهادیِ نیازمند تأیید او به‌کار می‌رود."
 TOKENS["logo"]["layouts"]=["symbol","wordmark","square","horizontal","vertical","horizontal-founder"]
 TOKENS["logo"]["persian_wordmark_policy"]="No Persian transliteration or Persian wordmark for AtoZ. Founder lockup may use the Persian founder name and a provisional title pending owner confirmation."
 TOKENS["logo"]["variants"]["color"]["wordmark_main"]=NAVY
 TOKENS["logo"]["variants"]["color"]["wordmark_accent"]=GOLD
 TOKENS["identity_system"]={"version":"3.0.0","design_system":"brand/design-system.json","logo_root":"logo/","motion_gallery":"logo/motion/index.html","brand_book":"logo/brand-book/brand-book.pdf","scope":"AtoZ master + five sub-brands"}
 TOKENS_PATH.write_text(json.dumps(TOKENS,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 system={"version":"3.0.0","status":"owner_review","mark_concept":"Recovered AZ emblem from the supplied approved reference: the A joins an ascending Z-shaped route and arrow, finished by the gold node. The surrounding lockups and naming are updated for the current AtoZ system.","master":{"name":"AtoZ","alternate_founder_lockup":"AtoZfnb.info","persian_wordmark":False,"founder":"Amir Zamani","founder_fa":"امیر زمانی","founder_title_fa":TOKENS["brand"]["title_fa"],"founder_title_status":"provisional; confirm the wording with the owner before public release"},"subbrands":SUBBRANDS,"content_pillars":PILLARS,"colors":{"navy":NAVY,"gold":GOLD,"surface":SURFACE,"white":WHITE,"section_accents":PALETTE},"logo_variants":["color","mono","white"],"logo_layouts":["symbol","wordmark","square","horizontal","vertical","horizontal-founder"],"motion_states":["intro","loader","waiting","outro"],"motion_orientations":["horizontal","vertical"],"font_families":{"persian":"Vazirmatn","latin_logo":"Montserrat","latin_support":"Lato"},"logo_rules":{"a_to_z_script":"Latin AtoZ only","allowed_persian_in_logo":["امیر زمانی",TOKENS["brand"]["title_fa"]],"founder_title_status":"provisional; confirmation required before public release","clearspace":"1× gold-dot diameter minimum","minimum_symbol_px":24,"min_horizontal_lockup_px":120,"backgrounds":{"color":"white or light surface","mono":"white or light surface","white":"strategic navy or approved dark background"},"misuse":["Do not translate AtoZ into Persian script","Do not alter letter case or spacing in AtoZ","Do not stretch, rotate, skew, outline, shadow, or add gradient","Do not place the gold variant on a white background for small text","Do not use the white variant on a light background","Do not combine the master icon with an unapproved wordmark"]},"motion_system":{"duration":{"intro_ms":900,"loader_loop_ms":1400,"waiting_loop_ms":2400,"outro_ms":650},"easing":"cubic-bezier(0.22,1,0.36,1)","reduced_motion":"Static mark; disable continuous loops when prefers-reduced-motion is set.","policy":"Motion is a progressive enhancement; the logo remains visible without animation or JavaScript."}}
 (ROOT/"brand/design-system.json").write_text(json.dumps(system,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return system


def build_logo_files():
 # Remove only superseded generated logo exports; keep canonical token/config sources and build tools.
 for stale in (LOGO/"fa",LOGO/"en",LOGO/"shared",LOGO/"guidelines",LOGO/"icons"/"svg",LOGO/"icons"/"png"):
  if stale.exists(): shutil.rmtree(stale)
 for stale_file in (LOGO/"icons"/"head-snippet.html",LOGO/"icons"/"site.webmanifest"): 
  if stale_file.exists(): stale_file.unlink()
 layouts=["symbol","wordmark","square","horizontal","vertical","founder"]
 for variant in ("color","mono","white"):
  folder=PRIMARY/variant;folder.mkdir(parents=True,exist_ok=True)
  for layout in layouts:
   svg=primary_lockup(layout,variant)
   (folder/f"{layout}.svg").write_text(svg,encoding="utf-8")
 for sub in SUBBRANDS:
  key=sub["id"];folder=SUBS/key; (folder/"logos").mkdir(parents=True,exist_ok=True);(folder/"icons").mkdir(parents=True,exist_ok=True)
  for variant in ("color","mono","white"):
   path=folder/"logos"/f"horizontal-{variant}.svg"
   path.write_text(subbrand_lockup(key,"horizontal",variant),encoding="utf-8")
   (folder/"logos"/f"square-{variant}.svg").write_text(subbrand_square(key,variant),encoding="utf-8")
  for variant in ("color","mono","white"):
   (folder/"icons"/f"icon-{variant}.svg").write_text(subbrand_icon_svg(key,variant),encoding="utf-8")
 for v in ("color","mono","white"):
  (LOGO/"icons").mkdir(parents=True,exist_ok=True)
  (LOGO/"icons"/f"favicon-{v}.svg").write_text(primary_lockup("symbol",v),encoding="utf-8")
 (LOGO/"icons"/"app-icon.svg").write_text(app_icon_svg(),encoding="utf-8")
 (LOGO/"icons"/"site.webmanifest").write_text(json.dumps({"name":"AtoZ","short_name":"AtoZ","icons":[{"src":"app-icon.svg","sizes":"any","type":"image/svg+xml"}],"theme_color":NAVY,"background_color":NAVY,"display":"standalone"},indent=2)+"\n",encoding="utf-8")
 (LOGO/"logo-library.html").write_text(build_logo_gallery(),encoding="utf-8")


def subbrand_square(sub,variant):
 bg=rect(0,0,512,512,NAVY,r=72) if variant=="white" else ""
 dot=None
 mark,_=place_mark(156,70,200,variant,dot=dot)
 word,_,_=run_fragment([name_run("AtoZ",60,WHITE if variant=="white" else NAVY,LATIN_XBOLD),name_run(" "+next(s["name"] for s in SUBBRANDS if s["id"]==sub),45,WHITE if variant=="white" else (PALETTE[sub] if variant=="color" else NAVY),LATIN_SEMI)],256,333,align="center")
 descriptor=""
 if sub=="pb":descriptor=run_fragment([name_run("PROMPT BANK",18,WHITE if variant=="white" else (NAVY if variant=="mono" else PALETTE[sub]),LATIN_SEMI)],256,408,align="center")[0]
 return svg_doc(512,512,bg+mark+word+descriptor,f'AtoZ {sub} square lockup — {variant}')

def app_icon_svg():
 size=512
 bg=rect(0,0,size,size,NAVY,r=106)
 mark,_=place_mark(80,169,352,"white",dot=GOLD)
 return svg_doc(size,size,bg+mark,"AtoZ application icon","AZ emblem with a gold growth point on navy")

def build_logo_gallery():
 cards=[]
 for variant in ("color","mono","white"):
  for layout in ("symbol","wordmark","square","horizontal","vertical","founder"):
   background="dark" if variant=="white" else "light"
   cards.append(f'<article data-variant="{variant}" class="card {background}"><img src="primary/{variant}/{layout}.svg" alt="AtoZ {layout} {variant}"><div><b>{layout.replace("-"," ")}</b><a href="primary/{variant}/{layout}.svg" download>SVG</a></div></article>')
 for sub in SUBBRANDS:
  for variant in ("color","mono","white"):
   cards.append(f'<article data-variant="{variant}" class="card {"dark" if variant=="white" else "light"}"><img src="subbrands/{sub["id"]}/logos/horizontal-{variant}.svg" alt="{esc(sub["display"])} {variant}"><div><b>{esc(sub["display"])}</b><a href="subbrands/{sub["id"]}/logos/horizontal-{variant}.svg" download>SVG</a></div></article>')
 return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AtoZ logo library</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f4f7fa;color:#13233d;font:15px/1.5 system-ui,Arial,sans-serif}}header{{background:#0A1931;color:white;padding:28px clamp(18px,5vw,70px);border-bottom:5px solid #FFB400}}h1{{margin:0;font-size:clamp(28px,5vw,46px)}}main{{max-width:1500px;margin:auto;padding:24px}}.filters{{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}}button{{border:1px solid #d9e0ea;background:white;border-radius:999px;padding:9px 16px;cursor:pointer}}button[aria-pressed=true]{{background:#0A1931;color:white}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}}.card{{border:1px solid #d9e0ea;border-radius:14px;overflow:hidden;background:white}}.card.dark{{background:#0A1931;color:white}}.card img{{display:block;width:100%;height:170px;object-fit:contain;padding:18px}}.card div{{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-top:1px solid #d9e0ea}}a{{color:inherit}}h2{{margin:30px 0 12px}}[hidden]{{display:none!important}}</style><header><h1>AtoZ logo library</h1><p>Master identity · five sub-brands · SVG source files</p></header><main><div class="filters"><button aria-pressed="true" data-filter="all">All</button><button data-filter="color">Color</button><button data-filter="mono">Monochrome</button><button data-filter="white">Reverse white</button></div><h2>Master identity & sub-brands</h2><section class="grid">{''.join(cards)}</section><p>Persian writing appears only in the dedicated founder lockup.</p></main><script>document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{{document.querySelectorAll('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',x===b));document.querySelectorAll('.card').forEach(c=>c.hidden=b.dataset.filter!=='all'&&c.dataset.variant!==b.dataset.filter)}}));</script></html>'''


def svg_symbol_for_motion(variant):
 return core.symbol_group(variant,dot_override=GOLD if variant=="white" else None)

def brand_lockup_parts(brand_id,orientation,variant):
 if brand_id=="atoz":
  text1=[name_run("AtoZ",160 if orientation=="horizontal" else 180,core.VARIANTS[variant]["main"],LATIN_XBOLD)]
  return text1,None,None
 sub=next(s for s in SUBBRANDS if s["id"]==brand_id)
 col=core.VARIANTS[variant]["main"]
 accent=WHITE if variant=="white" else (NAVY if variant=="mono" else PALETTE[brand_id])
 text1=[name_run("AtoZ",124 if orientation=="horizontal" else 150,col,LATIN_XBOLD),name_run(" "+sub["name"],91 if orientation=="horizontal" else 108,accent,LATIN_SEMI)]
 descriptor=[name_run(sub.get("descriptor",""),32,accent,LATIN_SEMI)] if sub.get("descriptor") else None
 return text1,descriptor,None

def motion_svg(brand_id,state,orientation):
 vertical=orientation=="vertical"; W,H=(1080,1920) if vertical else (1920,1080)
 variant="white"; fg=WHITE
 symbol=svg_symbol_for_motion(variant).replace("<circle ","<circle class=\"gold-dot\" ")
 is_primary=brand_id=="atoz"
 descriptor=None
 if is_primary:
  name_runs=[name_run("AtoZ",170 if vertical else 146,WHITE,LATIN_XBOLD)]
 else:
  sub=next(s for s in SUBBRANDS if s["id"]==brand_id)
  name_runs=[name_run("AtoZ",140 if vertical else 122,WHITE,LATIN_XBOLD),name_run(" "+sub["name"],94 if vertical else 82,PALETTE[brand_id],LATIN_SEMI)]
  if sub.get("descriptor"): descriptor=[name_run(sub["descriptor"],29,PALETTE[brand_id],LATIN_SEMI)]
 if vertical:
  mark_x=(W-600)/2;mark_y=H*.22;mark_w=600
  logo_y=H*.54; logo_x=W/2
 else:
  mark_x=W*.29;mark_y=(H-350)/2;mark_w=350
  logo_y=H*.47;logo_x=W*.51
 mark_h=core.SYM_H*(mark_w/core.SYM_W)
 symbol_group_html=f'<g class="symbol" transform="translate({mark_x-core.SYM_X0*(mark_w/core.SYM_W):.2f} {mark_y-core.SYM_Y0*(mark_w/core.SYM_W):.2f}) scale({mark_w/core.SYM_W:.6f})">{symbol}</g>'
 word,w,h=run_fragment(name_runs,logo_x,logo_y,align="center")
 desc_html=""
 if descriptor:
  desc_html,_,_=run_fragment(descriptor,logo_x,logo_y+92,align="center")
 if state=="intro":
  anim_css="""@keyframes drawin{0%{opacity:0;transform:translateY(28px) scale(.94)}100%{opacity:1;transform:none}}@keyframes settle{0%{transform:scale(.76);opacity:0}70%{transform:scale(1.12);opacity:1}100%{transform:scale(1)}}.symbol{animation:drawin .85s cubic-bezier(.22,1,.36,1) both}.word,.desc{opacity:0;animation:drawin .75s .28s cubic-bezier(.22,1,.36,1) both}.gold-dot{transform-box:fill-box;transform-origin:center;animation:settle .72s .38s cubic-bezier(.22,1,.36,1) both}"""
 elif state=="loader":
  anim_css="""@keyframes spin{to{transform:rotate(360deg)}}.orbit{transform-box:fill-box;transform-origin:center}@keyframes appear{from{opacity:0}to{opacity:1}}.symbol,.word,.desc{animation:appear .55s ease-out both}.orbit{animation:spin 1.5s linear infinite}.gold-dot{transform-box:fill-box;transform-origin:center;animation:pulse 1.2s ease-in-out infinite}@keyframes pulse{50%{opacity:.48;transform:scale(.84)}}"""
 elif state=="waiting":
  anim_css="""@keyframes breathe{0%,100%{transform:translateY(0);opacity:1}50%{transform:translateY(-5px);opacity:.84}}.symbol{animation:breathe 2.4s ease-in-out infinite}.gold-dot{transform-box:fill-box;transform-origin:center;animation:pulse 1.6s ease-in-out infinite}@keyframes pulse{50%{opacity:.55;transform:scale(.88)}}"""
 else:
  anim_css="""@keyframes leave{to{opacity:0;transform:translateY(-20px) scale(.97)}}.symbol,.word,.desc{animation:leave .62s cubic-bezier(.55,0,1,.45) both}"""
 if state=="loader":
  ringcx=mark_x+mark_w*.91;ringcy=mark_y+mark_h*.06
  moving=f'<circle class="orbit" cx="{ringcx:.2f}" cy="{ringcy:.2f}" r="30" fill="none" stroke="{GOLD}" stroke-width="5" stroke-dasharray="86 103"/>'
 else:moving=""
 is_dark=rect(0,0,W,H,NAVY)
 html_body=(is_dark+f'<style>{anim_css}@media(prefers-reduced-motion:reduce){{*,*::before,*::after{{animation-duration:.001ms!important;animation-delay:0ms!important;animation-iteration-count:1!important}}}}</style>'
            +moving+symbol_group_html+f'<g class="word">{word}</g>'+f'<g class="desc">{desc_html}</g>')
 return svg_doc(W,H,html_body,f'AtoZ {brand_id} {state} {orientation}',f'Animated vector logo; {state}; {orientation}; reduced-motion safe')


def build_motion_files():
 for brand in ["atoz"]+[x["id"] for x in SUBBRANDS]:
  folder=MOTION/brand
  folder.mkdir(parents=True,exist_ok=True)
  for state in ("intro","loader","waiting","outro"):
   for orientation in ("horizontal","vertical"):
    (folder/f"{state}-{orientation}.svg").write_text(motion_svg(brand,state,orientation),encoding="utf-8")
 manifest={"version":"3.0.0","master":"AtoZ","brands":[{"id":"atoz","name":"AtoZ"}]+SUBBRANDS,"states":["intro","loader","waiting","outro"],"orientations":[{"id":"horizontal","viewBox":"1920 1080"},{"id":"vertical","viewBox":"1080 1920"}],"source_format":"SVG with CSS keyframes","gallery":"logo/motion/index.html","responsive_html":"logo/motion/index.html","reduced_motion":"prefers-reduced-motion disables animation","exports":"48 independent source SVGs; gallery adapts the selected lockup to the viewport."}
 (MOTION/"motion-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (MOTION/"index.html").write_text(motion_gallery(),encoding="utf-8")
 (MOTION/"motion.css").write_text(""":root{color-scheme:light dark}*{box-sizing:border-box}body{margin:0;background:#f4f7fa;color:#13233d;font:15px/1.55 system-ui,Arial,sans-serif}.top{padding:20px clamp(16px,4vw,56px);background:#0a1931;color:#fff;border-bottom:4px solid #ffb400}.top h1{margin:0;font-size:clamp(24px,4vw,38px)}.controls{display:flex;gap:10px;flex-wrap:wrap;padding:16px clamp(16px,4vw,56px);background:white;border-bottom:1px solid #d9e0ea}label{display:grid;gap:4px;font-weight:700;font-size:12px}select,button{font:inherit;border:1px solid #cbd5e1;border-radius:8px;padding:9px 12px;background:white;color:#13233d}.frame{margin:clamp(12px,3vw,36px) auto;width:min(100% - 24px,1280px);aspect-ratio:16/9;background:#0a1931;border-radius:18px;overflow:hidden;box-shadow:0 16px 50px #0a193122}.frame.vertical{width:min(68vw,480px);aspect-ratio:9/16}.frame img{width:100%;height:100%;display:block;object-fit:contain}.download{display:inline-flex;margin:0 clamp(16px,4vw,56px) 30px;padding:10px 16px;border-radius:8px;background:#ffb400;color:#0a1931;text-decoration:none;font-weight:800}.note{margin:0 clamp(16px,4vw,56px) 30px;color:#475569}@media(max-width:600px){.frame{aspect-ratio:4/3}.frame.vertical{width:min(90vw,390px);aspect-ratio:9/16}.controls{gap:8px}}
""",encoding="utf-8")

def motion_gallery():
 ids=[{"id":"atoz","name":"AtoZ"}]+SUBBRANDS
 options="".join(f'<option value="{x["id"]}">{esc(x["display"] if "display" in x else "AtoZ")}</option>' for x in ids)
 return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AtoZ responsive logo motion gallery</title><link rel="stylesheet" href="motion.css"><header class="top"><h1>AtoZ motion library</h1><p>48 responsive SVG logo motions · intro, loader, waiting & outro</p></header><section class="controls"><label>Brand<select id="brand">'''+options+'''</select></label><label>Motion<select id="state"><option value="intro">Intro</option><option value="loader">Loading</option><option value="waiting">Waiting</option><option value="outro">Outro</option></select></label><label>Orientation<select id="orientation"><option value="horizontal">Horizontal</option><option value="vertical">Vertical</option></select></label><button id="replay" type="button">Replay</button></section><main><div class="frame" id="frame"><img id="preview" src="atoz/intro-horizontal.svg" alt="AtoZ animated logo"></div><a class="download" id="download" href="atoz/intro-horizontal.svg" download>Download source SVG</a><p class="note">SVG sources respect reduced-motion settings. Use HTML gallery controls to review responsive horizontal and vertical compositions.</p></main><script>const $=id=>document.getElementById(id),frame=$('frame'),image=$('preview');function update(){const src=$('brand').value+'/'+$('state').value+'-'+$('orientation').value+'.svg';image.src=src+'?v='+Date.now();$('download').href=src;frame.classList.toggle('vertical',$('orientation').value==='vertical');image.alt=$('brand').selectedOptions[0].text+' '+$('state').value+' logo motion'}['brand','state','orientation'].forEach(id=>$(id).addEventListener('change',update));$('replay').addEventListener('click',update);update();</script></html>'''


def build_content_templates():
 # Reusable blank visual masters, retaining the existing 4:5 / 9:16 content formats and replacing the old Persian AtoZ lockup.
 specs=[
  ("social/post-editorial","editorial",1080,1350),("social/post-data","data",1080,1350),("social/post-case-study","case",1080,1350),("social/post-quote","quote",1080,1350),
  ("carousels/slide-01-cover","cover",1080,1350),("carousels/slide-02-body","body",1080,1350),("carousels/slide-03-comparison","compare",1080,1350),("carousels/slide-04-evidence","evidence",1080,1350),("carousels/slide-05-checklist","checklist",1080,1350),("carousels/slide-06-outro","outro",1080,1350),
  ("video-covers/reel-cover","reel-cover",1080,1920),("video-covers/reel-lower-third","lower-third",1080,1920),("video-covers/reel-end-card","reel-end",1080,1920)]
 records=[]
 for path,kind,w,h in specs:
  base=TEMPLATES/path; base=base.with_suffix(".svg");base.parent.mkdir(parents=True,exist_ok=True)
  accent=GOLD if kind in {"editorial","cover","body","outro"} else PALETTE["blog"]
  body=rect(0,0,w,h,WHITE)
  m,_=place_mark(w-160,80,64,"color")
  body+=m+en("AtoZ",64,110,34,NAVY,LATIN_XBOLD,width=270)
  body+=rect(64,180,w-128,6,accent,r=3)
  if kind in {"editorial","cover","case","data","reel-cover"}:
   title="[[HEADLINE]]"
   body+=en(title, w-64, 300, 54, NAVY,LATIN_XBOLD,width=w-128,align="right")
  if kind in {"editorial","case","cover","reel-cover","data","evidence"}:
   box_y=470 if h<1500 else 700; box_h=min(500,h-box_y-320)
   body+=rect(64,box_y,w-128,box_h,SURFACE,BORDER,24,2,'stroke-dasharray="12 9"')
   body+=en("[[VISUAL / DIAGRAM / VIDEO FRAME]]",w/2,box_y+box_h/2,22,MUTED,LATIN_SEMI,width=w-160,align="center")
  if kind in {"body","compare","checklist","outro","lower-third"}:
   body+=en("[[SECTION / STEP]]",w-64,290,20,accent,LATIN_SEMI,width=w-128,align="right")
   body+=en("[[ONE KEY IDEA]]",w-64,365,40,NAVY,LATIN_XBOLD,width=w-128,align="right")
   if kind=="checklist":
    for i in range(4):
     yy=500+i*120;body+=rect(92,yy,40,40,WHITE,accent,8,3)+en(f"[[CHECK {i+1}]]",w-64,yy,24,INK,LATIN_BODY,width=w-200,align="right")
   else:body+=en("[[SUPPORTING DETAIL / SOURCE]]",w-64,470,24,INK,LATIN_BODY,width=w-128,align="right")
  if kind=="lower-third":
   body+=rect(64,int(h*.68),w-128,190,NAVY,r=20,extra='opacity=".94"')+rect(64,int(h*.68),9,190,accent,r=4)
   body+=en("AtoZ  ·  [[SUB-BRAND]]",w-96,int(h*.68)+45,25,WHITE,LATIN_SEMI,width=w-190,align="right")
   body+=en("[[SUBTITLE]]",w-96,int(h*.68)+100,28,WHITE,LATIN_XBOLD,width=w-190,align="right")
  if kind=="reel-end":
   body+=en("AtoZ",w/2,int(h*.55),68,NAVY,LATIN_XBOLD,width=w-128,align="center")+en("[[CALL TO ACTION]]",w/2,int(h*.66),24,INK,LATIN_BODY,width=w-128,align="center")
  body+=line(64,h-132,w-64,h-132,BORDER,2)+en("AtoZ  ·  [[SOURCE / PAGE]]",64,h-92,17,MUTED,LATIN_SEMI,width=w-128)
  svg=svg_doc(w,h,body,f'AtoZ {kind} content template',"Blank reusable AtoZ template; no new editorial content")
  base.write_text(svg,encoding="utf-8")
  records.append({"id":path.replace("/","-"),"svg":str(base.relative_to(ROOT)),"png":str(base.with_suffix(".png").relative_to(ROOT)),"width":w,"height":h,"status":"blank master"})
 (TEMPLATES/"template-manifest.json").write_text(json.dumps({"version":"3.0.0","status":"blank visual masters, no editorial content","templates":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (TEMPLATES/"README.md").write_text("# AtoZ visual templates\n\nBlank, editable SVG masters with PNG previews. Branding uses the AtoZ Latin wordmark only. Social, carousel and vertical reel formats remain content slots; no new copy, data or claim has been inserted. See `template-manifest.json` for dimensions.\n",encoding="utf-8")


def write_brand_book_sources():
 pages=[]
 # Cover
 b=[rect(0,0,1920,1080,NAVY),en("AtoZ  /  BRAND BOOK  3.0",120,120,22,"#CBD5E1",LATIN_SEMI,width=700),rect(110,165,1700,5,GOLD,r=2)]
 mark,_=place_mark(1330,250,380,"white")
 b += [mark,en("AtoZ",1180,690,120,WHITE,LATIN_XBOLD,width=550,align="center"),fa("هویت مادر، زیر‌برندها، لوگو و حرکت",950,830,38,WHITE,FA_BOLD,width=780),en("A MASTER BRAND SYSTEM FOR F&B",120,960,20,GOLD,LATIN_SEMI,width=600)]
 pages.append(svg_doc(1920,1080,"".join(b),"AtoZ Brand Book cover"))

 def page(index,section,title,subtitle=""):
  p=[rect(0,0,1920,1080,WHITE),en(section.upper(),110,72,16,MUTED,LATIN_SEMI,width=600),en(f"{index:02d}  /  16",1665,72,15,MUTED,LATIN_SEMI,width=140),line(110,116,1810,116,GOLD,3),fa(title,1780,152,45,NAVY,FA_XBOLD,width=1500)]
  if subtitle:p.append(fa(subtitle,1780,216,21,MUTED,FA_REG,width=1500))
  p.extend([line(110,1018,1810,1018,BORDER,2),en("AtoZ  ·  BRAND BOOK 3.0",110,1040,13,MUTED,LATIN_SEMI,width=400)])
  return p
 # 2. brand system
 b=page(2,"Brand architecture","AtoZ یک برند مادر است؛ نام‌ها همیشه لاتین‌اند","نوشتار فارسی برای AtoZ ساخته یا استفاده نمی‌شود؛ فقط نام بنیان‌گذار و عنوان فارسی او مجاز است.")
 b += [rect(115,330,780,520,NAVY,r=24),en("MASTER WORDMARK",165,385,17,GOLD,LATIN_SEMI,width=360),en("AtoZ",170,520,132,WHITE,LATIN_XBOLD,width=550),en("AtoZfnb.info",170,680,50,WHITE,LATIN_SEMI,width=500),fa("امیر زمانی",825,735,30,WHITE,FA_BOLD,width=500),fa(TOKENS["brand"]["title_fa"],825,785,21,"#CBD5E1",FA_REG,width=500)]
 b += [fa("حروف لاتین A و Z و نسبت حروف ثابت می‌ماند.",1760,390,25,NAVY,FA_BOLD,width=780),fa("نام زیر‌برند بعد از AtoZ می‌آید و با وزن/رنگ ثانویه خوانده می‌شود.",1760,480,22,INK,FA_REG,width=780),fa("نسخهٔ امضای بنیان‌گذار: AtoZfnb.info کوچک‌تر؛ سپس «امیر زمانی» و زیرعنوان فارسی.",1760,595,22,INK,FA_REG,width=780),fa("هیچ متن یا ترجمهٔ فارسی برای خود نام AtoZ در لوگو وجود ندارد.",1760,735,22,NAVY,FA_BOLD,width=780)]
 pages.append(svg_doc(1920,1080,"".join(b),"AtoZ master identity"))
 # 3 logo family
 b=page(3,"Primary logo family","خانوادهٔ اصلی لوگو","هر ترکیب فقط برای جایگاه مشخص طراحی شده؛ هیچ‌کدام با تغییر دستی نسبت‌ها ساخته نمی‌شود.")
 variants=[("symbol","نشان مستقل"),("wordmark","ورد‌مارک AtoZ"),("square","لوگوی مربعی"),("horizontal","لوگوی افقی"),("vertical","لوگوی عمودی"),("founder","امضای بنیان‌گذار")]
 for i,(kind,label) in enumerate(variants):
  x=110+(i%3)*575;y=320+(i//3)*315
  b.append(rect(x,y,530,255,SURFACE,BORDER,18,2))
  body=primary_lockup(kind,"color")
  if kind=="symbol":scale=.32;tx=x+(530-600*scale)/2;ty=y+8
  elif kind=="wordmark":scale=.42;tx=x+(530-640*scale)/2;ty=y+48
  elif kind=="square":scale=.18;tx=x+(530-1024*scale)/2;ty=y+8
  elif kind=="horizontal":scale=.38;tx=x+18;ty=y+30
  elif kind=="vertical":scale=.21;tx=x+(530-1024*scale)/2;ty=y+10
  else:scale=.36;tx=x+(530-1120*scale)/2;ty=y+18
  b.append(f'<g transform="translate({tx:.1f} {ty:.1f}) scale({scale})">{svg_inner(body)}</g>')
  b.append(fa(label,x+495,y+230,19,NAVY,FA_BOLD,width=460))
 b.append(rect(110,915,1700,76,"#FFF4D5",r=14))
 b.append(fa("نشان مرجع، حرف A را به مسیر صعودیِ Z و پیکان متصل می‌کند؛ نقطهٔ طلایی پایان مسیر را مشخص می‌کند. سیلوئت نشان اصلی حفظ شده و نام‌گذاری و چیدمان‌ها برای AtoZ به‌روزرسانی شده‌اند.",1770,927,19,NAVY,FA_REG,width=1600,leading=1.3))
 pages.append(svg_doc(1920,1080,"".join(b),"Primary logo family and design idea"))
 # 4 orientation rules
 b=page(4,"Logo lockups","چیدمان‌ها و ترتیب خواندن","علامت در سمت چپ وردمارک می‌آید؛ در چیدمان عمودی، نشان بالای AtoZ قرار می‌گیرد.")
 b.append(rect(110,330,1050,260,WHITE,BORDER,18,2)); b.append(en("AtoZ  /  SYMBOL LEFT",150,355,15,MUTED,LATIN_SEMI,width=400)); b.append(f'<g transform="translate(180 405) scale(.31)">{svg_inner(primary_lockup("horizontal","color"))}</g>')
 b.append(rect(1210,330,590,500,WHITE,BORDER,18,2)); b.append(en("SQUARE / APP",1250,355,15,MUTED,LATIN_SEMI,width=300)); b.append(f'<g transform="translate(1320 430) scale(.42)">{svg_inner(primary_lockup("square","color"))}</g>')
 b += [fa("حریم امن: حداقل یک قطر نقطهٔ طلایی اطراف نشان/لاک‌آپ.",1750,725,22,INK,FA_REG,width=1490),fa("حداقل دیجیتال: نشان ۲۴px، وردمارک ۸۰px، افقی ۱۲۰px؛ حداقل چاپ: نشان ۸mm، عمودی ۲۵mm، افقی/کامل ۳۰mm.",1750,778,22,INK,FA_REG,width=1490),fa("تراز لوگو با گوشهٔ قاب یا UI ممنوع؛ حریم امن همیشه حفظ شود.",1750,830,21,NAVY,FA_BOLD,width=1490)]
 pages.append(svg_doc(1920,1080,"".join(b),"Logo lockups and clear space"))
 # 5 founder
 b=page(5,"Founder signature","امضای بنیان‌گذار","نسخهٔ تخصصی و تنها محل مجاز برای فارسیِ نام و عنوان در خود لوگو.")
 b.append(rect(140,330,1640,420,SURFACE,BORDER,22,2)); founder=primary_lockup("founder","color");b.append(f'<g transform="translate(330 385) scale(1.10)">{svg_inner(founder)}</g>')
 b += [fa("ترتیب ثابت",1740,820,23,NAVY,FA_BOLD,width=300),fa("نشان + AtoZfnb.info + امیر زمانی + زیرعنوان فارسی.",1740,865,22,INK,FA_REG,width=1450),fa("عنوان فعلی فقط پیش‌نویس برگرفته از توکن قبلی است؛ عبارت نهایی را مالک تأیید کند.",1740,918,19,MUTED,FA_REG,width=1450)]
 pages.append(svg_doc(1920,1080,"".join(b),"Founder logo signature"))
 # 6 colors
 b=page(6,"Logo color modes","رنگ و زمینهٔ لوگو","رنگی، تک‌رنگ و معکوس سفید؛ انتخاب زمینه باید کنتراست را حفظ کند.")
 for i,(var,bg,label) in enumerate([("color",WHITE,"رنگی"),("mono",WHITE,"تک‌رنگ"),("white",NAVY,"سفید روی تیره")]):
  x=120+i*565;b.append(rect(x,330,520,260,bg,BORDER if bg==WHITE else NAVY,16,2))
  mark,_=place_mark(x+40,380,170,var,dot=None);b.append(mark)
  b.append(en("AtoZ",x+250,422,62,WHITE if var=="white" else NAVY,LATIN_XBOLD,width=220))
  b.append(fa(label,x+480,545,21,WHITE if var=="white" else NAVY,FA_BOLD,width=220))
 b += [fa("سرمه‌ای روی سفید: ۱۷٫۵۵:۱ · سرمه‌ای روی طلایی: ۹٫۸۵:۱ · سفید روی سرمه‌ای: ۱۷٫۵۵:۱",1780,720,23,NAVY,FA_BOLD,width=1520),fa("طلایی روی سفید فقط تأکید گرافیکی است؛ نسبت ۱٫۷۸:۱ برای نوشتهٔ ریز و لوگوی کوچک کافی نیست.",1780,790,21,INK,FA_REG,width=1520)]
 pages.append(svg_doc(1920,1080,"".join(b),"Logo color and contrast"))
 # 7 misuse
 b=page(7,"Do & don't","بایدها و نبایدهای استفاده","در نمونه‌های نادرست، تغییر نسبت، چرخش، رنگ یا پس‌زمینهٔ کم‌کنتراست نشان داده شده است.")
 good=[("نسخهٔ مجاز","رنگ و چیدمان مصوب","✓",PALETTE["tools"]),("فشرده/کشیده","نسبت حروف تغییر کرده","×","#C2413A"),("رنگ غیرمجاز","طلایی روی سفید کم‌کنتراست","×","#C2413A"),("اثر/چرخش","سایه، گرادیان یا زاویه","×","#C2413A")]
 for i,(h,sub,sym,c) in enumerate(good):
  x=110+(i%2)*850;y=330+(i//2)*270
  b.append(rect(x,y,790,220,WHITE,BORDER,18,2))
  b.append(circle(x+85,y+95,30,c));b.append(en(sym,x+85,y+83,28,WHITE,LATIN_BOLD,width=60,align="center"))
  b.append(en(h.upper(),x+145,y+47,17,c,LATIN_SEMI,width=500));b.append(fa(sub,x+735,y+104,22,INK,FA_REG,width=550))
  if i==0:
   mark,_=place_mark(x+565,y+50,135,"color");b.append(mark);b.append(en("AtoZ",x+635,y+165,36,NAVY,LATIN_XBOLD,width=150))
  if i==1:b.append(f'<g transform="translate({x+500} {y+60}) scale(1.35 .72)">{core.symbol_group("color")}</g>')
  if i==2:b.append(en("AtoZ",x+650,y+120,55,GOLD,LATIN_XBOLD,width=180))
  if i==3:b.append(f'<g transform="rotate(-12 {x+650} {y+110})">{en("AtoZ",x+570,y+90,46,NAVY,LATIN_XBOLD,width=190)}</g>')
 pages.append(svg_doc(1920,1080,"".join(b),"Logo do and don't"))
 # 8 subbrand architecture
 b=page(8,"Sub-brand architecture","پنج زیر‌برند زیر نام مادر AtoZ","هر زیر‌برند نام، مأموریت و مقصد خودش را دارد؛ نشان اصلی و قرارداد تایپوگرافی ثابت می‌ماند.")
 for i,s in enumerate(SUBBRANDS):
  x=110+i*340;c=PALETTE[s["id"]]
  b += [rect(x,350,300,410,WHITE,BORDER,18,2),rect(x,350,300,9,c,r=4)]
  b.append(en(s["display"],x+28,430,30,NAVY,LATIN_XBOLD,width=244))
  b.append(en(s.get("descriptor",""),x+28,475,16,c,LATIN_SEMI,width=244))
  b.append(fa(s["purpose_fa"],x+270,523,16,INK,FA_REG,width=244,leading=1.25))
  b.append(circle(x+40,650,9,c));b.append(en(s["icon"].upper(),x+65,641,14,MUTED,LATIN_SEMI,width=200))
 b += [fa("AtoZ Blog",1740,830,22,NAVY,FA_BOLD,width=250),fa("AtoZ Tools · AtoZ book · AtoZ PB / PROMPT BANK · AtoZ Solicitor",1740,875,21,INK,FA_REG,width=1540)]
 pages.append(svg_doc(1920,1080,"".join(b),"AtoZ five subbrands"))
 # 9 subbrand lockups
 b=page(9,"Sub-brand lockups","یک قاعدهٔ لوگو، پنج امضای رنگی","در همهٔ چیدمان‌ها AtoZ به لاتین می‌ماند؛ رنگ فقط نشانگر دسته است و مکمل نام نوشتاری است.")
 for i,s in enumerate(SUBBRANDS):
  x=110+(i%2)*855;y=325+(i//2)*215;c=PALETTE[s["id"]]
  b.append(rect(x,y,795,175,SURFACE,BORDER,16,2))
  mark,_=place_mark(x+25,y+45,135,"color");b.append(mark)
  r=[name_run("AtoZ",70,NAVY,LATIN_XBOLD),name_run(" "+s["name"],58,c,LATIN_SEMI)]
  logo,w,h=run_fragment(r,x+210,y+65);b.append(logo)
  if s.get("descriptor"):b.append(en(s["descriptor"],x+210,y+118,16,c,LATIN_SEMI,width=360))
 pages.append(svg_doc(1920,1080,"".join(b),"AtoZ sub-brand lockups"))
 # 10 icons
 b=page(10,"Iconography","آیکون‌های اختصاصی و یکپارچه","پیکتوگرام‌های خطی با ضخامت و گوشه‌های یکسان؛ لوگوی AtoZ را جایگزین آیکون دسته نکنید.")
 for i,s in enumerate(SUBBRANDS):
  x=160+i*320;c=PALETTE[s["id"]];b.append(rect(x,350,230,260,SURFACE,BORDER,18,2));b.append(rect(x,350,230,7,c,r=3))
  icon=subbrand_icon_elements(s["id"],NAVY,c);b.append(f'<g transform="translate({x+47} 410) scale(5.6)">{icon}</g>')
  b.append(en(s["display"],x+20,560,17,NAVY,LATIN_SEMI,width=190,align="center"))
 pages.append(svg_doc(1920,1080,"".join(b),"AtoZ sub-brand icons"))
 # 11 palette
 b=page(11,"Color system","رنگ مادر و رنگ‌های کمکی","همهٔ برندها از سرمه‌ای و طلایی AtoZ شروع می‌شوند؛ زیر‌برند فقط یک رنگ تشخیصی دارد.")
 color_rows=[("AtoZ Navy",NAVY,"#0A1931"),("AtoZ Gold",GOLD,"#FFB400"),("Blog",PALETTE["blog"],"#C05746"),("Tools",PALETTE["tools"],"#0F766E"),("book",PALETTE["book"],"#3B5998"),("PB",PALETTE["pb"],"#5D5FEF"),("Solicitor",PALETTE["solicitor"],"#D97706")]
 for i,(name,color,hx) in enumerate(color_rows):
  col=i%4;row=i//4;x=110+col*430;y=340+row*245
  b.append(rect(x,y,390,150,color,r=14));b.append(en(name,x+24,y+35,23,WHITE if color!=GOLD else NAVY,LATIN_BOLD,width=320));b.append(en(hx,x+24,y+100,17,WHITE if color!=GOLD else NAVY,LATIN_SEMI,width=250))
 b += [fa("برای متن روی رنگ دسته، از سفید یا سرمه‌ای تنها پس از آزمون کنتراست استفاده کنید.",1770,900,21,NAVY,FA_BOLD,width=1400)]
 pages.append(svg_doc(1920,1080,"".join(b),"AtoZ color system"))
 # 12 type
 b=page(12,"Typography","تایپوگرافی کم‌تنوع، خوانا و مجاز","سه خانوادهٔ OFL کافی است؛ فایل‌های تزئینی، اختصاصی و تکراری حذف شدند.")
 b += [rect(110,335,800,300,WHITE,BORDER,18,2),en("LATIN / WORDMARK",150,370,15,MUTED,LATIN_SEMI,width=400),en("AtoZ  ·  AtoZ PB",860,485,58,NAVY,LATIN_XBOLD,width=650,align="right"),en("Montserrat ExtraBold / SemiBold",860,565,18,PALETTE["blog"],LATIN_SEMI,width=620,align="right")]
 b += [rect(990,335,800,300,WHITE,BORDER,18,2),en("FOUNDER SIGNATURE ONLY",1030,370,15,MUTED,LATIN_SEMI,width=450),fa("امیر زمانی",1740,480,45,NAVY,FA_BOLD,width=500),fa(TOKENS["brand"]["title_fa"],1740,550,25,INK,FA_MED,width=500)]
 b += [fa("فارسی در وردمارک AtoZ نیست؛ فقط نام و عنوان بنیان‌گذار در قفل‌آپ مخصوص او فارسی است.",1760,760,22,NAVY,FA_BOLD,width=1460),fa("بدنهٔ فارسی: Vazirmatn Regular · بدنهٔ لاتین: Lato Regular · تیتر لاتین: Montserrat Bold.",1760,820,20,INK,FA_REG,width=1460)]
 pages.append(svg_doc(1920,1080,"".join(b),"AtoZ typography"))
 # 13 pillars
 b=page(13,"Content pillars","شش ستون محتوایی","ستون‌ها موضوع‌اند، نه لوگو؛ هر مورد یک مقصد اصلی و یک رنگ راهنما دارد.")
 for i,item in enumerate(PILLARS):
  col=i%3;row=i//3;x=110+col*575;y=320+row*300;c=PALETTE[item["color_id"]]
  b += [rect(x,y,530,250,WHITE,BORDER,18,2),rect(x,y,8,250,c,r=4),en(item["id"].upper(),x+30,y+28,14,c,LATIN_SEMI,width=400),fa(item["fa"],x+480,y+83,23,NAVY,FA_BOLD,width=445),fa(item["purpose_fa"],x+480,y+127,16,INK,FA_REG,width=445,leading=1.3),en(item["destination"].upper(),x+30,y+220,13,MUTED,LATIN_SEMI,width=440)]
 pages.append(svg_doc(1920,1080,"".join(b),"Content pillar system"))
 # 14 site map
 b=page(14,"Sub-brands × content pillars","مسیریابی محتوا به زیر‌برند","مالک هر محتوا را از روی وظیفه‌اش انتخاب کنید؛ یک ستون می‌تواند با چند زیر‌برند هم‌پوشانی داشته باشد.")
 for i,s in enumerate(SUBBRANDS):
  x=110+(i%3)*575;y=330+(i//3)*260;c=PALETTE[s["id"]]
  b.append(rect(x,y,530,200,WHITE,BORDER,18,2));b.append(rect(x,y,530,7,c,r=4));b.append(en(s["display"],x+26,y+35,27,NAVY,LATIN_XBOLD,width=460))
  related=[p["fa"] for p in PILLARS if p["id"] in s["content_pillars"]]
  summary=(" · ".join(related) if related else s["purpose_fa"])
  b.append(fa(summary,x+485,y+98,18,INK,FA_REG,width=445,leading=1.65))
 pages.append(svg_doc(1920,1080,"".join(b),"Content pillars and subbrands"))
 # 15 motions
 b=page(15,"Logo motion","چهار حرکت، دو جهت، یک منطق","اینترو · لودینگ · ویتینگ · اوترو؛ SVGهای مستقل و گالری HTML واکنش‌گرا.")
 for i,state in enumerate([("intro","INTRO","ورود یک‌باره"),("loader","LOADING","بارگذاری"),("waiting","WAITING","انتظار آرام"),("outro","OUTRO","خروج")]):
  x=110+i*420;c=PALETTE["tools"] if i==1 else GOLD
  b.append(rect(x,360,365,320,SURFACE,BORDER,18,2));b.append(circle(x+182,480,52,NAVY));b.append(circle(x+182,480,9,GOLD))
  b.append(en(state[1],x+30,575,19,NAVY,LATIN_BOLD,width=300));b.append(fa(state[2],x+335,625,18,INK,FA_REG,width=290))
 b += [en("HORIZONTAL  1920×1080",115,785,17,MUTED,LATIN_SEMI,width=500),en("VERTICAL  1080×1920",690,785,17,MUTED,LATIN_SEMI,width=500),fa("کاهش حرکت: prefers-reduced-motion انیمیشن پیوسته را متوقف می‌کند؛ لوگو هیچ‌گاه در حالت غیرفعال محو نمی‌شود.",1780,870,19,NAVY,FA_BOLD,width=1500)]
 pages.append(svg_doc(1920,1080,"".join(b),"AtoZ motion principles"))
 # 16 production + tree
 b=page(16,"Production & governance","ساختار فایل و دروازهٔ تأیید","هر منبع کنار پیش‌نمایش است؛ قبل از انتشار لوگو، عنوان بنیان‌گذار و نسخهٔ رنگی را بازبینی کنید.")
 tree="logo/\n├─ primary/ color · mono · white\n├─ subbrands/ blog · tools · book · pb · solicitor\n├─ icons/\n├─ motion/ [6 brands × 4 states × 2 orientations]\n└─ brand-book/"
 b.append(rect(110,330,735,485,SURFACE,BORDER,18,2));b.append(en(tree,150,385,24,NAVY,LATIN_BODY,width=650,leading=1.8))
 gates=["نام لاتین AtoZ درست است","رنگ و زمینه تأیید شده","عنوان فارسی فقط در founder-lockup","SVG و HTML در موبایل بازبینی شده"]
 for i,g in enumerate(gates):
  y=370+i*104;b.append(rect(965,y,40,40,WHITE,GOLD,8,3));b.append(fa(g,1740,y+4,22,INK,FA_REG,width=690))
 b.append(en("No new content / no invented claims / no automatic publishing.",965,860,17,MUTED,LATIN_SEMI,width=780))
 pages.append(svg_doc(1920,1080,"".join(b),"AtoZ asset governance"))
 for i,svg in enumerate(pages,1):
  (BOOK/"slides").mkdir(parents=True,exist_ok=True)
  (BOOK/"slides"/f"slide-{i:02d}.svg").write_text(svg,encoding="utf-8")
 manifest={"version":"3.0.0","slide_count":len(pages),"slides":[{"number":i,"path":f"logo/brand-book/slides/slide-{i:02d}.svg"} for i in range(1,len(pages)+1)],"formats":["SVG source and PNG preview per slide","responsive HTML","PDF"]}
 (BOOK/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (BOOK/"index.html").write_text(book_html(len(pages)),encoding="utf-8")

def book_html(n):
 sections="".join(f'<section><img src="slides/slide-{i:02d}.svg" alt="AtoZ brand book slide {i}"><span>{i:02d} / {n:02d}</span></section>' for i in range(1,n+1))
 return f'''<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AtoZ Brand Book</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#0a1931;font-family:Vazirmatn,Tahoma,sans-serif}}section{{min-height:100svh;display:grid;place-items:center;position:relative;scroll-snap-align:start;background:white}}html{{scroll-snap-type:y mandatory}}img{{width:min(100vw,177.78vh);height:min(56.25vw,100svh);object-fit:contain}}span{{position:absolute;bottom:14px;left:20px;color:#64748b;font:12px Montserrat,Arial}}</style>{sections}</html>'''

def write_readmes():
 (ROOT/"brand/README-fa.md").write_text("""# سیستم هویت AtoZ

- منبع حقیقت: `brand/tokens.json` و `brand/design-system.json`
- لوگو و زیر‌برندها: `logo/primary/` و `logo/subbrands/`
- کتابچهٔ برند: `logo/brand-book/index.html` و `logo/brand-book/brand-book.pdf`
- گالری موشن واکنش‌گرا: `logo/motion/index.html`
- قالب‌های خالی پست/کاروسل/ریل: `content-templates/`
- ممیزی و مجوز فونت: `brand/fonts/` و `tools/fonts/LICENSES.txt`

AtoZ همیشه لاتین نوشته می‌شود؛ فارسی فقط برای امضای بنیان‌گذار و عنوان او مجاز است. عنوان فعلی از مقدار قدیمی توکن به ارث رسیده و برای انتشار عمومی نیاز به تأیید مالک دارد. فایل‌های هویت قدیمی و فونت‌های غیرضروری پس از بررسی وابستگی/مجوز پاک‌سازی شدند. نام «AtoZ Solicitor» در این مرحله به‌تنهایی ادعای ارائهٔ خدمات یا مجوز حقوقی نیست.
""",encoding="utf-8")
 (ROOT/"logo/README.md").write_text("""# AtoZ logo system

`logo/primary/` contains the master mark and lockups in color, monochrome and white modes. `logo/subbrands/` contains five aligned sub-brand lockups and original pictograms. `logo/motion/` contains standalone animated SVGs and the responsive gallery. `logo/brand-book/` contains the 16-page book in SVG, PNG, PDF and HTML formats. Quick use rules are in `guidelines-fa.md`.

The Latin AtoZ spelling is invariant. Persian is reserved for the dedicated founder name/title line only. Do not edit generated SVG/PNG exports manually; rebuild with `python3 tools/build_brand_assets.py` and `npm --prefix tools run render-brand`.
""",encoding="utf-8")
 (ROOT/"logo/guidelines-fa.md").write_text("""# راهنمای سریع لوگوی AtoZ

## چیدمان و نام‌گذاری
- شکل نام برند در همه‌جا `AtoZ` است؛ ترجمه یا نوشتار فارسیِ آن ممنوع است.
- نسخهٔ افقی: نشان در چپ، `AtoZ` در سمت راست. نسخه‌های مربع و عمودی در `primary/` موجودند.
- امضای بنیان‌گذار: `AtoZfnb.info` کوچک‌تر از نشان/نام مادر؛ سپس «امیر زمانی» و زیرعنوان فارسی در سطرهای جدا.
- متن فعلی زیرعنوان از توکن قدیمی آمده و تا تأیید مالک، موقت است.
- برای زمینهٔ روشن نسخهٔ color یا mono؛ برای زمینهٔ سرمه‌ای/تیره نسخهٔ white.
- در نسخهٔ white، حروف و مسیر سفید می‌مانند و نقطهٔ شاخصِ نشان طلایی است.

## حریم امن و حداقل اندازه
- حریم امن پیرامون نشان یا لاک‌آپ: دست‌کم یک قطر نقطهٔ طلایی (`x`) در هر طرف.
- نشان مستقل: حداقل ۲۴ px دیجیتال / ۸ mm چاپ.
- وردمارک مستقل: حداقل ۸۰ px دیجیتال / ۲۰ mm چاپ.
- افقی: حداقل ۱۲۰ px دیجیتال / ۳۰ mm چاپ.
- عمودی: حداقل ۱۰۰ px دیجیتال / ۲۵ mm چاپ.
- کوچک‌تر از حداقل؟ فقط از نشان مستقل استفاده کنید و در اندازهٔ عملیاتی دوباره بسنجید.

## بایدها
- فایل SVG/PNG متناظر با زمینه را بدون تغییر نسبت و رنگ بردارید.
- نشان مادر را برای معرفی خانواده و رنگ زیر‌برند را فقط به‌عنوان کد دسته نگه دارید.
- نسخهٔ white را روی سرمه‌ای/زمینهٔ تیره و color را روی سطح روشن استفاده کنید.
- کنتراست نوشتاری navy/white برابر 17.55:1 و navy/gold برابر 9.85:1 است.

## نبایدها
- نام AtoZ را فارسی‌نویسی یا حروف آن را جابه‌جا/تغییر نکنید.
- لوگو را نکشید، نفشارید، نچرخانید، کج نکنید و دورخط/سایه/گرادیان ندهید.
- نسخهٔ white را روی سفید یا طلایی روی سفید برای نوشتهٔ ریز نگذارید؛ طلایی/سفید 1.78:1 است.
- نشان مادر را با نام/آیکون تأییدنشده ترکیب نکنید یا حریم امن را نشکنید.
- نام زیر‌برند `AtoZ Solicitor` را به‌تنهایی ادعای مجوز یا خدمات حقوقی تلقی نکنید.

## فایل‌های اصلی
- لوگوی مادر: `primary/{color,mono,white}/`
- زیر‌برندها و آیکون‌ها: `subbrands/{blog,tools,book,pb,solicitor}/`
- قواعد کامل، ستون‌های محتوا و نمونه‌ها: `brand-book/brand-book.pdf` یا `brand-book/index.html`
""",encoding="utf-8")


def main():
 system=build_tokens_and_system()
 build_logo_files()
 build_motion_files()
 build_content_templates()
 write_brand_book_sources()
 write_readmes()
 print(f"Built AtoZ master identity, {len(SUBBRANDS)} sub-brands, {len(SUBBRANDS)+1} motion systems, {len(SUBBRANDS)+1} motion types × 2 orientations, {len(PILLARS)} content pillars and 16 brand-book slides.")

if __name__=="__main__":main()
