#!/usr/bin/env python3
"""Build a concise 10-slide AtoZ identity presentation from the same brand tokens."""
from pathlib import Path
import json
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pptx import Presentation
from pptx.util import Inches

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build_brand_assets as A

OUT=ROOT/"brand/presentation"
SLIDES=OUT/"slides"
W,H=1920,1080
NAVY=A.NAVY; GOLD=A.GOLD; WHITE=A.WHITE; SURFACE=A.SURFACE; INK=A.INK; MUTED=A.MUTED; BORDER=A.BORDER


def frame(number,section,title,subtitle=""):
 body=[A.rect(0,0,W,H,WHITE),A.en("AtoZ  /  IDENTITY PRESENTATION",105,64,15,MUTED,A.LATIN_SEMI,width=550),A.en(f"{number:02d}  /  10",1690,64,15,MUTED,A.LATIN_SEMI,width=120),A.line(105,105,1815,105,GOLD,3),A.en(section.upper(),105,145,15,GOLD,A.LATIN_SEMI,width=500),A.fa(title,1780,145,40,NAVY,A.FA_XBOLD,width=1500)]
 if subtitle:body.append(A.fa(subtitle,1780,202,20,MUTED,A.FA_REG,width=1500))
 body += [A.line(105,1018,1815,1018,BORDER,2),A.en("AtoZ  ·  OWNER REVIEW EDITION  ·  v3.1",105,1042,12,MUTED,A.LATIN_SEMI,width=500)]
 return body

def master_logo(layout,variant="color",x=0,y=0,scale=1):
 svg=A.primary_lockup(layout,variant)
 return f'<g transform="translate({x} {y}) scale({scale})">{A.svg_inner(svg)}</g>'

def sub_logo(sub,layout="horizontal",variant="color",x=0,y=0,scale=1):
 svg=A.subbrand_lockup(sub,layout,variant)
 return f'<g transform="translate({x} {y}) scale({scale})">{A.svg_inner(svg)}</g>'


def build_slides():
 pages=[]
 # 1: Cover / visual entry
 body=[A.rect(0,0,W,H,NAVY),A.rect(105,145,1710,4,GOLD,r=2),A.en("AtoZ  /  BRAND SYSTEM",115,95,18,"#D5DEEA",A.LATIN_SEMI,width=650),master_logo("horizontal","white",275,295,1.12),A.fa("هویت مادر، خانوادهٔ لوگو، زیر‌برندها و دارایی‌ها",1780,800,36,WHITE,A.FA_BOLD,width=1380),A.en("IDENTITY PRESENTATION  ·  REVIEW EDITION",115,958,17,GOLD,A.LATIN_SEMI,width=800),A.en("v3.1  /  NOVEMBER 2026",1680,958,14,"#D5DEEA",A.LATIN_SEMI,width=300,align="right")]
 pages.append(A.svg_doc(W,H,"".join(body),"AtoZ identity presentation cover"))
 # 2: recovered brand mark and concept
 b=frame(2,"Identity idea","نشان مرجع و منطق آن","سیلوئت نشان اصلی حفظ شده؛ نام، تایپوگرافی و چیدمان‌ها با قواعد فعلی AtoZ هماهنگ شده‌اند.")
 b += [A.rect(105,305,750,570,SURFACE,BORDER,22,2),A.rect(915,305,900,570,NAVY,r=22)]
 mark,_=A.place_mark(220,420,520,"color");b.append(mark)
 b += [A.fa("حرف A به مسیر Z متصل می‌شود؛ مسیر صعودی و پیکان حرکت تا نقطهٔ پایان را نشان می‌دهد.",1745,395,25,WHITE,A.FA_BOLD,width=720),A.fa("نقطهٔ طلایی، انتهای مسیر و کانون توجه است. این نشان از فایل مرجع اصلی بازیابی شده؛ AZ جداگانه جایگزین آن نیست.",1745,535,22,"#D9E2EF",A.FA_REG,width=720),A.en("NAVY  #0A1931",970,760,17,"#D9E2EF",A.LATIN_SEMI,width=350),A.en("GOLD  #FFB400",1390,760,17,GOLD,A.LATIN_SEMI,width=330)]
 pages.append(A.svg_doc(W,H,"".join(b),"AtoZ emblem concept"))
 # 3: Primary lockups and signature
 b=frame(3,"Primary logo family","خانوادهٔ لوگوی مادر","نام مادر در همهٔ قفل‌آپ‌ها با حروف لاتین ثابت می‌ماند.")
 cards=[("horizontal","افقی؛ نشان چپ، نام راست",.52),("square","مربع / آواتار",.22),("founder","امضای بنیان‌گذار",.48)]
 positions=[(105,330),(705,330),(1305,330)]
 for (layout,label,scale),(x,y) in zip(cards,positions):
  b.append(A.rect(x,y,510,455,SURFACE,BORDER,20,2))
  if layout=="horizontal": tx=x+45;ty=y+165;scale=.30
  elif layout=="square": tx=x+145;ty=y+40
  else: tx=x+30;ty=y+145;scale=.40
  b.append(master_logo(layout,"color",tx,ty,scale))
  b.append(A.fa(label,x+475,y+415,18,NAVY,A.FA_BOLD,width=430))
 b.append(A.fa("نسخه‌های رنگی، تک‌رنگ و سفید؛ هرکدام فقط روی زمینهٔ هم‌کنتراست استفاده شوند.",1780,875,20,INK,A.FA_REG,width=1500))
 pages.append(A.svg_doc(W,H,"".join(b),"AtoZ primary logo family"))
 # 4: Sub-brand family and scope
 b=frame(4,"Sub-brand architecture","پنج زیر‌برند زیر نام AtoZ","رنگ دسته مکملِ نام است؛ نشان مادر در خانواده ثابت می‌ماند.")
 for i,s in enumerate(A.SUBBRANDS):
  col=i%3;row=i//3;x=105+col*575;y=305+row*310;c=A.PALETTE[s["id"]]
  b += [A.rect(x,y,535,255,WHITE,BORDER,18,2),A.rect(x,y,535,7,c,r=4),sub_logo(s["id"],"horizontal","color",x+18,y+40,.43),A.fa(s["purpose_fa"],x+495,y+170,17,INK,A.FA_REG,width=465,leading=1.3)]
 pages.append(A.svg_doc(W,H,"".join(b),"AtoZ sub-brand family"))
 # 5: Color and typography
 b=frame(5,"Visual language","رنگ و تایپوگرافی","سرمه‌ای و طلایی رنگ مادرند؛ رنگ زیر‌برند تنها برای تمایز دسته به‌کار می‌رود.")
 rows=[("AtoZ NAVY",NAVY,"#0A1931"),("AtoZ GOLD",GOLD,"#FFB400")]+[(s["display"].upper(),A.PALETTE[s["id"]],A.PALETTE[s["id"]]) for s in A.SUBBRANDS]
 for i,(label,color,hx) in enumerate(rows):
  col=i%4;row=i//4;x=105+col*435;y=315+row*230
  b += [A.rect(x,y,390,126,color,r=14),A.en(label,x+24,y+35,18,NAVY if color==GOLD else WHITE,A.LATIN_BOLD,width=330),A.en(hx,x+24,y+86,15,NAVY if color==GOLD else WHITE,A.LATIN_SEMI,width=300)]
 b += [A.rect(105,790,825,142,SURFACE,BORDER,16,2),A.en("LATIN LOGO  /  MONTSERRAT EXTRA BOLD",140,830,16,NAVY,A.LATIN_SEMI,width=710),A.en("AtoZ  ·  AtoZ PB",140,885,36,NAVY,A.LATIN_XBOLD,width=700),A.rect(985,790,830,142,SURFACE,BORDER,16,2),A.fa("فارسی فقط برای نام بنیان‌گذار و زیرعنوان او",1780,835,19,NAVY,A.FA_BOLD,width=730),A.fa("بدنه: Vazirmatn · لاتین بدنه: Lato",1780,885,17,INK,A.FA_REG,width=730)]
 pages.append(A.svg_doc(W,H,"".join(b),"AtoZ color and typography"))
 # 6: Sub-brand pictograms
 b=frame(6,"Icon family","آیکون‌های اختصاصی و هم‌وزن","آیکون مستقل از وردمارک استفاده می‌شود و جزئیات ریز/تزئینی ندارد.")
 for i,s in enumerate(A.SUBBRANDS):
  x=105+i*350;c=A.PALETTE[s["id"]]
  b += [A.rect(x,350,310,405,SURFACE,BORDER,18,2),A.rect(x,350,310,7,c,r=4)]
  glyph=A.subbrand_icon_elements(s["id"],NAVY,c)
  b.append(f'<g transform="translate({x+75} 430) scale(6.7)">{glyph}</g>')
  b.append(A.en(s["display"],x+285,680,17,NAVY,A.LATIN_SEMI,width=260,align="center"))
 if True:
  b.append(A.fa("نشان مربوط به AtoZ Solicitor در این نسخه خنثی است؛ حوزهٔ دقیق زیر‌برند تا تعریف مالک تعیین‌نشده باقی می‌ماند.",1780,850,18,INK,A.FA_REG,width=1500))
 pages.append(A.svg_doc(W,H,"".join(b),"AtoZ sub-brand icon family"))
 # 7: six content pillars
 b=frame(7,"Content architecture","شش ستون محتوایی","ستون موضوع را مشخص می‌کند؛ زیر‌برند مقصد/قالب را تعیین می‌کند.")
 for i,item in enumerate(A.PILLARS):
  col=i%3;row=i//3;x=105+col*575;y=300+row*310;c=A.PALETTE[item["color_id"]]
  b += [A.rect(x,y,535,255,WHITE,BORDER,18,2),A.rect(x,y,8,255,c,r=4),A.en(item["id"].upper(),x+28,y+28,13,c,A.LATIN_SEMI,width=420),A.fa(item["fa"],x+480,y+78,23,NAVY,A.FA_BOLD,width=455),A.fa(item["purpose_fa"],x+480,y+127,16,INK,A.FA_REG,width=455,leading=1.3),A.en(item["destination"].upper(),x+28,y+225,12,MUTED,A.LATIN_SEMI,width=430)]
 pages.append(A.svg_doc(W,H,"".join(b),"AtoZ content pillars"))
 # 8: motion set
 b=frame(8,"Motion toolkit","سامانهٔ موشن","چهار وضعیت، دو نسبت تصویر و گالری واکنش‌گرا.")
 states=[("INTRO","ورود یک‌باره"),("LOADING","بارگذاری"),("WAITING","انتظار آرام"),("OUTRO","خروج")]
 for i,(en_title,fa_title) in enumerate(states):
  x=105+i*430;c=GOLD if i!=1 else A.PALETTE["tools"]
  b += [A.rect(x,360,380,330,SURFACE,BORDER,18,2),A.circle(x+190,485,56,NAVY),A.circle(x+190,485,12,GOLD),A.en(en_title,x+28,580,19,NAVY,A.LATIN_BOLD,width=320),A.fa(fa_title,x+350,635,17,INK,A.FA_REG,width=290)]
 b += [A.en("HORIZONTAL  1920 × 1080",115,785,16,MUTED,A.LATIN_SEMI,width=500),A.en("VERTICAL  1080 × 1920",700,785,16,MUTED,A.LATIN_SEMI,width=500),A.fa("برای برند مادر و پنج زیر‌برند؛ فایل برداری متحرک و تنظیم کاهش حرکت سیستم‌عامل پشتیبانی می‌شود.",1780,865,19,NAVY,A.FA_BOLD,width=1450)]
 pages.append(A.svg_doc(W,H,"".join(b),"AtoZ motion system"))
 # 9: logo rules
 b=frame(9,"Usage rules","قواعد استفادهٔ لوگو","از فایل آماده استفاده کنید؛ نسبت، فاصله و رنگ را دستی تغییر ندهید.")
 rules=[("حریم امن","حداقل یک قطر نقطهٔ طلایی در هر طرف."),("حداقل دیجیتال","نشان ۲۴px · وردمارک ۸۰px · افقی ۱۲۰px."),("حداقل چاپ","نشان ۸mm · عمودی ۲۵mm · افقی/کامل ۳۰mm."),("رنگ/زمینه","رنگی و تک‌رنگ روی روشن؛ سفید روی زمینهٔ تیره."),("نام","AtoZ فقط لاتین؛ فارسی برای بنیان‌گذار و زیرعنوان."),("ممنوع","کشیدگی، چرخش، سایه، گرادیان یا ادغام غیرمصوب.")]
 for i,(heading,detail) in enumerate(rules):
  col=i%2;row=i//2;x=105+col*870;y=315+row*205
  b += [A.rect(x,y,810,160,WHITE,BORDER,16,2),A.rect(x,y,7,160,GOLD if i<3 else A.PALETTE["tools"],r=4),A.fa(heading,x+760,y+35,22,NAVY,A.FA_BOLD,width=700),A.fa(detail,x+760,y+90,18,INK,A.FA_REG,width=700)]
 pages.append(A.svg_doc(W,H,"".join(b),"AtoZ logo usage rules"))
 # 10: review gates and files
 b=frame(10,"Delivery & approval","تحویل و دروازهٔ تأیید","فایل‌های برداری منبع و خروجی‌های پیش‌نمایش کنار هم نگهداری می‌شوند.")
 b += [A.rect(105,310,790,500,NAVY,r=20),A.en("ASSETS",150,355,18,GOLD,A.LATIN_SEMI,width=300),A.en("logo/primary/",150,420,24,WHITE,A.LATIN_SEMI,width=550),A.en("logo/subbrands/",150,480,24,WHITE,A.LATIN_SEMI,width=550),A.en("logo/motion/",150,540,24,WHITE,A.LATIN_SEMI,width=550),A.en("brand/presentation/",150,600,24,WHITE,A.LATIN_SEMI,width=550),A.en("logo/brand-book/",150,660,24,WHITE,A.LATIN_SEMI,width=550),A.rect(975,310,840,500,SURFACE,BORDER,20,2)]
 checklist=["نام و نوشتار زیر‌برندها تأیید شود","عنوان فارسی بنیان‌گذار هنوز موقت است","حوزهٔ AtoZ Solicitor نیازمند تعریف مالک است","دامنه/هندل در هیچ خروجی فرض نشده است"]
 for i,text in enumerate(checklist):
  y=375+i*92;b += [A.rect(1020,y,32,32,WHITE,GOLD,7,3),A.fa(text,1770,y+2,19,INK,A.FA_REG,width=690)]
 b.append(A.en("Owner review required before public use.",1020,760,15,MUTED,A.LATIN_SEMI,width=680))
 pages.append(A.svg_doc(W,H,"".join(b),"AtoZ presentation delivery and approval"))
 return pages


def main():
 OUT.mkdir(parents=True,exist_ok=True);SLIDES.mkdir(parents=True,exist_ok=True)
 pages=build_slides()
 for i,svg in enumerate(pages,1):
  (SLIDES/f"slide-{i:02d}.svg").write_text(svg,encoding="utf-8")
 (OUT/"manifest.json").write_text(json.dumps({"version":"3.1.0","slide_count":len(pages),"status":"owner_review","pptx":"brand/presentation/AtoZ-brand-presentation.pptx","pdf":"brand/presentation/AtoZ-brand-presentation.pdf","source_slides":"brand/presentation/slides/","format":"16:9 executive overview; the PowerPoint deck uses high-resolution slide artwork and paired editable SVG sources."},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(f"Built {len(pages)} presentation source slides; render then run build_brand_presentation.py again to package PPTX/PDF.")

def package():
 pngs=sorted(SLIDES.glob("slide-*.png"))
 if len(pngs)!=10: raise SystemExit("Render brand/presentation/slides/slide-*.svg to PNG first; expected 10 slides.")
 pdf=canvas.Canvas(str(OUT/"AtoZ-brand-presentation.pdf"),pagesize=(W,H),pageCompression=1,invariant=1)
 pdf.setTitle("AtoZ Brand Presentation 3.1");pdf.setAuthor("AtoZ");pdf.setSubject("AtoZ identity family and brand architecture");pdf.setCreator("AtoZ reproducible build")
 for image in pngs:
  pdf.drawImage(ImageReader(str(image)),0,0,width=W,height=H,mask="auto");pdf.showPage()
 pdf.save()
 pres=Presentation();pres.slide_width=Inches(13.333333);pres.slide_height=Inches(7.5)
 blank=pres.slide_layouts[6]
 for i,image in enumerate(pngs,1):
  slide=pres.slides.add_slide(blank);picture=slide.shapes.add_picture(str(image),0,0,width=pres.slide_width,height=pres.slide_height)
  picture._element._nvXxPr.cNvPr.set("descr",f"AtoZ identity presentation, slide {i} of 10; editable SVG source beside the deck")
 pres.core_properties.title="AtoZ Brand System Presentation"
 pres.core_properties.author="AtoZ"
 pres.core_properties.subject="Identity family, sub-brands, content pillars and usage rules"
 pres.core_properties.keywords="AtoZ, brand system, identity, sub-brands"
 pres.save(OUT/"AtoZ-brand-presentation.pptx")
 print(f"Packaged PPTX/PDF with {len(pngs)} slides in {OUT.relative_to(ROOT)}")

if __name__=="__main__":
 if "--package" in sys.argv:package()
 else:main()
