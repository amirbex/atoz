#!/usr/bin/env python3
"""Build a new, review-only package from the existing week-one plan."""
from __future__ import annotations
import argparse, copy, hashlib, html, json, os, re, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import build_week1_package as renderer
from content_copy_engine import build_copy_outline, build_carousel, build_reel_scenes
from validate_content_plan import PLAN_SCHEMA, schema_errors, validate_plan_integrity

SOURCE_DEFAULT=ROOT/"پیش انتشار/ماه اول/هفته اول/plan.json"
OUTPUT_DEFAULT=ROOT/"content-output/week-01"
ENGINE_VERSION="1.0.0"
ENGINE_FILES=(Path(__file__),ROOT/"tools/build_week1_package.py",ROOT/"tools/build_logo.py",ROOT/"tools/content_copy_engine.py",ROOT/"tools/week1_website_articles.py",ROOT/"tools/build_motion_lab.py",ROOT/"tools/render_motion_lab.mjs",ROOT/"tools/render_content_assets.mjs")
OWNER_SITE="https://OWNER-APPROVAL-REQUIRED.invalid/"
OWNER_HANDLE="[[OWNER_APPROVED_SOCIAL_HANDLE]]"


def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def preserve_local_workspace(previous:Path,stage:Path)->None:
    """Carry dashboard decisions and intake drafts across safe engine rebuilds."""
    for name in ("review-state.json","intake-drafts.json"):
        source=previous/name
        if source.is_file():shutil.copy2(source,stage/name)
    intake=previous/"intake"
    if intake.is_dir():shutil.copytree(intake,stage/"intake",dirs_exist_ok=True)

def engine_fingerprint()->str:
    digest=hashlib.sha256()
    for path in ENGINE_FILES:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()

def sanitize(value):
    if isinstance(value,str):
        value=value.replace("https://atozfnb.info/",OWNER_SITE).replace("http://atozfnb.info/",OWNER_SITE)
        value=value.replace("@atozfnb.info",OWNER_HANDLE).replace("atozfnb.info",OWNER_SITE)
        return value
    if isinstance(value,list):return [sanitize(x) for x in value]
    if isinstance(value,dict):return {k:sanitize(v) for k,v in value.items()}
    return value

def count_reference_mismatch(notes:list[str])->dict:
    text=" ".join(notes)
    reference=re.search(r"جمع[^.]{0,180}?\((\d+)\)\s*اختلاف",text)
    difference=re.search(r"اختلاف[^.]{0,100}?\b(\d+)\s*مورد",text)
    if reference and difference:
        return {"reference_count":int(reference.group(1)),"difference":int(difference.group(1))}
    return {}

def validate_source(plan:dict)->dict:
    errors=schema_errors(plan,PLAN_SCHEMA,"week-one source plan")
    integrity,summary=validate_plan_integrity(plan);errors.extend(integrity)
    if errors:raise ValueError("Source plan failed validation:\n- "+"\n- ".join(errors[:30]))
    if len(plan.get("content_items",[]))!=28 or len(plan.get("deliveries",[]))!=84:
        raise ValueError("This first engine run expects the existing 28-item / 84-delivery week-one plan; the plan was not changed.")
    return summary

def recipe_for(item:dict, delivery:dict)->str|None:
    fmt=delivery.get("format_id")
    if fmt not in {"micro_reel","mini_reel","main_reel","animated_reel"}:return None
    pillar=item.get("pillar_id")
    if pillar=="finance-market":return "anatomy-explode" if item.get("content_id")=="ATZ-C-000004" else "bar-chart-build"
    if pillar=="case-studies":return "before-after-wipe"
    if pillar=="innovation-ai":return "flow-map"
    if fmt=="main_reel":return "kinetic-headline"
    return "staggered-chapters"

def enrich(plan:dict)->tuple[dict,list[dict]]:
    safe=sanitize(copy.deepcopy(plan))
    content={x["content_id"]:x for x in safe["content_items"]}
    pillar_number={p["id"]:n for n,p in renderer.PILLARS.items()}
    deliveries=[]
    for source in safe["deliveries"]:
        d=copy.deepcopy(source);item=content[d["content_id"]]
        n=int(d["content_id"].rsplit("-",1)[1]);pillar=pillar_number[item["pillar_id"]]
        fmt=d.get("format_id","");is_story=d.get("channel_id")=="instagram" and fmt=="story"
        is_reel=fmt in {"micro_reel","mini_reel","main_reel","animated_reel"}
        style=renderer.style_for(n);summary=item.get("audience_problem") or item.get("core_message","")
        kind="story" if is_story else "reel" if is_reel else "feed"
        outline=build_copy_outline(item,d)
        d["creative_spec"]["style_id"]=style
        recipe=recipe_for(item,d)
        if recipe:outline.update({"motion_recipe_id":recipe})
        if isinstance(d.get("cta"),dict):
            d["cta"]["target_url"]=OWNER_SITE
            d["cta"]["link_status"]="owner_approval_required"
        d.update({"_visual_svg":renderer.make_card(d.get("hook") or item["topic"],summary,pillar,kind=kind,style=style),"_kind":kind,"_style":style,"_idea_summary":summary,"_idea_title":item["topic"],"_pillar_num":pillar,"_story_text":d.get("hook") if is_story else None,"_copy_outline":outline})
        if fmt=="carousel":
            slides=build_carousel(item,d);d["_slide_copy"]=[{"title":x["title"],"body":x["body"]} for x in slides]
        if is_reel:
            d["_scene_copy"]=build_reel_scenes(item,d)
        deliveries.append(d)
    safe["deliveries"]=[{k:v for k,v in d.items() if not k.startswith("_")} for d in deliveries]
    safe["notes"]=[sanitize(x) for x in safe.get("notes",[])]
    # Keep the unresolved mismatch visible; neither count is silently rewritten.
    safe["notes"].append("موتور تولید، فهرست تحویل‌های منبع را همان‌طور که هست نگه می‌دارد؛ اختلاف شمارندهٔ ۶۴ با ۸۴ تحویل باید پیش از تأیید مالک تطبیق داده شود.")
    return safe,deliveries

CATEGORY_INFO={
    "01-reels":{"label":"ریلز","description":"ویدیو، استوری‌بورد سه‌صحنه‌ای و افکت صوتی"},
    "02-carousels":{"label":"کاروسل‌ها","description":"اسلایدهای شماره‌گذاری‌شده و متن هر اسلاید"},
    "03-posts":{"label":"پست‌های تکی","description":"پست، نقل‌قول، نقشه، اینفوگرافیک و محتوای تصویری"},
    "04-stories":{"label":"استوری‌ها","description":"استوری و محتوای تعاملی برای آماده‌سازی دستی"},
    "05-web-telegram":{"label":"وب‌سایت و تلگرام","description":"پیش‌نویس مقاله و متن‌های قابل‌کپی"},
}

def category_for(delivery:dict)->str:
    if delivery.get("channel_id")=="instagram":
        if delivery.get("_kind")=="reel":return "01-reels"
        if delivery.get("format_id")=="carousel":return "02-carousels"
        if delivery.get("format_id") in {"story","story_carousel"}:return "04-stories"
        return "03-posts"
    return "05-web-telegram"

def write_daily_catalog(out:Path,plan:dict,deliveries:list[dict])->None:
    """Add a day-first, type-grouped navigation layer without duplicating large media files."""
    by_day={day:[] for day in renderer.DAY_NAMES}
    for delivery in deliveries:by_day[delivery["day_name_fa"]].append(delivery)
    content={item["content_id"]:item for item in plan["content_items"]}
    day_summaries=[]
    for day_index,day in enumerate(renderer.DAY_NAMES,1):
        folder=out/day;folder.mkdir(parents=True,exist_ok=True);rows=by_day[day]
        groups={name:[] for name in CATEGORY_INFO}
        for delivery in rows:groups[category_for(delivery)].append(delivery)
        counts={name:len(items) for name,items in groups.items()}
        day_summaries.append({"day_index":day_index,"day_name_fa":day,"delivery_count":len(rows),"categories":counts})
        page_cards=[]
        for category,info in CATEGORY_INFO.items():
            category_dir=folder/category;category_dir.mkdir(parents=True,exist_ok=True)
            items=groups[category]
            catalog=[]
            for delivery in items:
                item=content[delivery["content_id"]]
                relative=f"../{delivery['content_id']}/{delivery['delivery_id']}"
                entry={"delivery_id":delivery["delivery_id"],"content_id":delivery["content_id"],"title":item["topic"],"channel_id":delivery["channel_id"],"format_id":delivery["format_id"],"asset_folder":relative,"review_status":"owner_review_required","publishing_enabled":False}
                catalog.append(entry)
                media=""
                if delivery["_kind"]=="reel":
                    media=f'<video controls playsinline preload="metadata" poster="{html.escape(relative)}/reel-source/scene-01.png"><source src="{html.escape(relative)}/reel.mp4" type="video/mp4"></video>'
                elif delivery["format_id"]=="carousel":
                    slides=[]
                    for n,slide in enumerate(delivery.get("_slide_copy",[]),1):
                        src=f"{relative}/slides/slide-{n:02d}.png"
                        slides.append(f'<a href="{html.escape(src)}"><img loading="lazy" src="{html.escape(src)}" alt="اسلاید {n}: {html.escape(slide["title"])}"><span>{n:02d} · {html.escape(slide["title"])}</span></a>')
                    media=f'<div class="gallery">{"".join(slides)}</div>'
                else:
                    media=f'<a class="still" href="{html.escape(relative)}/creative.png"><img loading="lazy" src="{html.escape(relative)}/creative.png" alt="پیش‌نمایش {html.escape(item["topic"])}"></a>'
                caption=html.escape(delivery.get("caption", ""))
                hashtags=html.escape(" ".join(delivery.get("hashtags",[])))
                action_links=[f'<a href="{html.escape(relative)}/metadata.json">مشخصات JSON</a>',f'<a href="{html.escape(relative)}/copy-outline.json">طرح کپی</a>',f'<a href="{html.escape(relative)}/caption.txt">متن کپشن</a>']
                if delivery["_kind"]=="reel":action_links.append(f'<a href="{html.escape(relative)}/reel.mp4" download>دریافت MP4</a>')
                if delivery["format_id"]=="carousel":action_links.append(f'<a href="{html.escape(relative)}/slides/">فایل‌های اسلاید</a>')
                card=f'''<article class="delivery" id="{html.escape(delivery['delivery_id'])}"><div class="media">{media}</div><div class="copy"><div class="meta"><span>{html.escape(delivery['delivery_id'])}</span><span>{html.escape(delivery['channel_id'])} · {html.escape(delivery['format_id'])}</span></div><h2>{html.escape(item['topic'])}</h2><p class="hook">{html.escape(delivery.get('hook',''))}</p><details><summary>کپشن و متن آماده</summary><div class="caption">{caption}</div><small>{hashtags}</small></details><nav>{' · '.join(action_links)}</nav><small class="review">پیش‌نویس · بازبینی مالک لازم است · انتشار خودکار خاموش</small></div></article>'''
                (category_dir/f"{delivery['delivery_id']}.html").write_text(f'''<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(item['topic'])} · {day}</title><link rel="stylesheet" href="../day-board.css"><body><header><a href="../index.html">← {day} · بازگشت به روز</a><span>AtoZ CONTENT STUDIO · {CATEGORY_INFO[category]['label']}</span></header>{card}</body></html>''',encoding="utf-8")
            index_rows=[]
            for delivery,entry in zip(items,catalog):
                item=content[delivery["content_id"]]
                index_rows.append(f'<li><a href="{delivery["delivery_id"]}.html"><b>{html.escape(item["topic"])}</b><small>{delivery["delivery_id"]} · {html.escape(delivery["format_id"])}</small></a></li>')
            category_html=f'''<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{CATEGORY_INFO[category]['label']} · {day}</title><link rel="stylesheet" href="../day-board.css"><body><header><a href="../index.html">← {day} · بازگشت به روز</a><span>{day_index:02d} / 07</span></header><main class="catalog"><p class="eyebrow">ATOZ · {day.upper()}</p><h1>{CATEGORY_INFO[category]['label']}</h1><p>{CATEGORY_INFO[category]['description']}</p><ul>{''.join(index_rows) if index_rows else '<li class="empty">برای این روز تحویلی در این دسته ثبت نشده است.</li>'}</ul></main></body></html>'''
            (category_dir/"index.html").write_text(category_html,encoding="utf-8")
            (category_dir/"index.json").write_text(json.dumps({"day":day,"category":category,"label_fa":info["label"],"count":len(items),"items":catalog},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            (category_dir/"README.fa.md").write_text(f"# {day} · {info['label']}\n\n**تعداد:** {len(items)}\n\n{info['description']}\n\n"+"\n".join(f"- [{content[d['content_id']]['topic']}]({d['delivery_id']}.html) · `{d['delivery_id']}`" for d in items)+("\n" if items else "\nاین دسته در برنامهٔ این روز تحویل ندارد.\n"),encoding="utf-8")
            page_cards.append(f'<a class="category" href="{category}/index.html"><span>{html.escape(info["label"])}</span><b>{len(items):02d}</b><small>{html.escape(info["description"])}</small></a>')
        css='''@font-face{font-family:V;src:url(../../../tools/fonts/Vazirmatn-Regular.ttf)}@font-face{font-family:V;src:url(../../../tools/fonts/Vazirmatn-Bold.ttf);font-weight:700}*{box-sizing:border-box}body{margin:0;background:#F3F6FA;color:#0A1931;font:16px/1.85 V,Tahoma,sans-serif}header{display:flex;justify-content:space-between;align-items:center;padding:18px max(22px,calc((100vw - 1180px)/2));background:#0A1931;color:#fff}header a{color:#FFB400;text-decoration:none}main{max-width:1180px;margin:40px auto;padding:0 24px}.eyebrow{color:#A56E00;font:700 12px Arial,sans-serif;letter-spacing:1px}h1{font-size:clamp(30px,5vw,54px);margin:4px 0}.intro{color:#52627A}.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:25px 0}.category{display:flex;flex-direction:column;gap:2px;padding:18px;border:1px solid #DDE4ED;border-radius:16px;background:#fff;color:inherit;text-decoration:none;box-shadow:0 8px 24px #0A19310A}.category b{font:700 30px Arial;color:#A56E00}.category small{color:#66758A}.delivery-link{display:flex;flex-direction:column;gap:4px;padding:14px;border:1px solid #DDE4ED;border-radius:12px;background:#fff;color:#203B60;text-decoration:none}.delivery-link small{color:#738097}.section-title{margin:35px 0 12px}.delivery{display:grid;grid-template-columns:minmax(240px,42%) 1fr;gap:24px;padding:22px;margin:14px 0;background:#fff;border:1px solid #DFE6EF;border-radius:18px}.media img,.media video{width:100%;max-height:620px;object-fit:contain;border-radius:12px;background:#0A1931}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.gallery a{position:relative}.gallery img{display:block}.gallery span{font-size:12px;color:#51627A}.meta{display:flex;justify-content:space-between;color:#6B7890;font-size:12px}.copy h2{font-size:22px;line-height:1.5}.hook{color:#475569;font-weight:700}.caption{white-space:pre-wrap;background:#F5F7FA;padding:16px;border-radius:12px;margin:10px 0}.copy nav{display:flex;flex-wrap:wrap;gap:12px;margin:14px 0}.copy nav a,.catalog a{color:#294E82}.review{color:#8A5A00}.catalog{max-width:900px}.catalog ul{list-style:none;padding:0}.catalog li{margin:10px 0;padding:14px;background:#fff;border:1px solid #DFE6EF;border-radius:12px}.catalog li a{display:flex;justify-content:space-between;gap:16px;text-decoration:none}.catalog li small{color:#65748A}.empty{color:#6B7890}@media(max-width:760px){header{padding:14px 18px}.delivery{grid-template-columns:1fr;gap:12px}main{margin:24px auto}.catalog li a{flex-direction:column}}'''
        (folder/"day-board.css").write_text(css,encoding="utf-8")
        summary_cards=''.join(page_cards)
        board_items=[]
        for category,items in groups.items():
            for delivery in items:
                item=content[delivery["content_id"]];link=f"{category}/{delivery['delivery_id']}.html"
                board_items.append(f'<a class="delivery-link" href="{link}"><span>{html.escape(item["topic"])}</span><small>{html.escape(CATEGORY_INFO[category]["label"])} · {delivery["delivery_id"]}</small></a>')
        board=f'''<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>برنامهٔ تولید {day} · هفتهٔ اول AtoZ</title><link rel="stylesheet" href="day-board.css"><body><header><a href="../README.md">AtoZ CONTENT ENGINE</a><span>ماه ۱ · هفتهٔ ۱</span></header><main><p class="eyebrow">WEEK 01 · DAY {day_index:02d}</p><h1>{day}</h1><p class="intro">تابلوی تولید روزانه · {len(rows)} تحویل برای آماده‌سازی، کنترل و بازبینی دستی</p><section class="summary">{summary_cards}</section><h2 class="section-title">فهرست تحویل‌های امروز</h2><section class="summary">{''.join(board_items)}</section><p class="review">همهٔ خروجی‌ها پیش‌نویس‌اند. منبع‌ها، اعداد، مقصدها و مجوزها را پیش از استفاده بررسی کنید؛ هیچ زمان‌بندی یا انتشار خودکار انجام نمی‌شود.</p></main></body></html>'''
        (folder/"index.html").write_text(board,encoding="utf-8")
        (folder/"daily-manifest.json").write_text(json.dumps({"day_index":day_index,"day_name_fa":day,"delivery_count":len(rows),"categories":counts,"deliveries":[{"delivery_id":d["delivery_id"],"content_id":d["content_id"],"category":category_for(d),"format_id":d["format_id"]} for d in rows],"review_required":True,"publishing_enabled":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        (folder/"README.md").write_text(f"# {day} · روز {day_index:02d}\n\n**{len(rows)} تحویل** · [بازکردن تابلوی روزانه](index.html)\n\n## دسته‌بندی سریع\n\n"+"\n".join(f"- [{CATEGORY_INFO[name]['label']} — {counts[name]}](./{name}/index.html)" for name in CATEGORY_INFO)+"\n\n## جزئیات منبع\n\n"+"\n".join(f"- `{d['content_id']}/{d['delivery_id']}` · {d['channel_id']} · {d['format_id']}" for d in rows)+"\n\n> پیش‌نویس برای بازبینی مالک؛ انتشار و زمان‌بندی خودکار وجود ندارد.\n",encoding="utf-8")
    mismatch=count_reference_mismatch(plan.get("notes",[]))
    daily_index={"week_index":1,"day_count":7,"content_items":len(plan["content_items"]),"delivery_count":len(deliveries),"reported_reference_count":mismatch.get("reference_count"),"delivery_count_discrepancy":mismatch.get("difference"),"days":day_summaries,"publishing_enabled":False}
    (out/"daily-index.json").write_text(json.dumps(daily_index,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    cards=[]
    for summary in day_summaries:
        day=summary["day_name_fa"];counts=summary["categories"]
        cats=" · ".join(f"{html.escape(CATEGORY_INFO[key]['label'])} {counts[key]}" for key in CATEGORY_INFO if counts[key])
        cards.append(f'<a class="day" href="{html.escape(day)}/index.html"><span>روز {summary["day_index"]:02d}</span><h2>{html.escape(day)}</h2><b>{summary["delivery_count"]} تحویل</b><small>{cats}</small></a>')
    alert=f'<aside>نیازمند تطبیق مالک: ۸۴ تحویل در برنامه در برابر {mismatch.get("reference_count",64)} در جمع ردیف‌ها؛ اختلاف {mismatch.get("difference",20)} مورد.</aside>'
    week_html=f'''<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AtoZ · بستهٔ تولید هفتهٔ اول</title><style>@font-face{{font-family:V;src:url(../../tools/fonts/Vazirmatn-Regular.ttf)}}@font-face{{font-family:V;src:url(../../tools/fonts/Vazirmatn-Bold.ttf);font-weight:700}}*{{box-sizing:border-box}}body{{margin:0;background:#F3F6FA;color:#0A1931;font:16px/1.9 V,Tahoma,sans-serif}}header{{background:#0A1931;color:#fff;padding:24px max(22px,calc((100vw - 1180px)/2))}}header img{{width:155px;height:42px;object-fit:contain}}main{{max-width:1180px;margin:38px auto;padding:0 24px}}.eyebrow{{color:#B88400;font:700 12px Arial,sans-serif;letter-spacing:1.4px}}h1{{font-size:clamp(32px,5vw,58px);margin:5px 0}}.lead{{color:#52627A}}.days{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:15px;margin:28px 0}}.day{{display:flex;flex-direction:column;gap:4px;padding:22px;border:1px solid #DCE4ED;background:#fff;border-radius:18px;color:inherit;text-decoration:none;box-shadow:0 12px 28px #0A19310A}}.day span{{color:#8A6500;font-size:12px}}.day h2{{margin:0;font-size:24px}}.day b{{font-size:20px;color:#0F766E}}.day small{{color:#5B6A7F;line-height:1.7}}aside{{padding:16px 18px;border-right:4px solid #D99A00;background:#FFF6D9;border-radius:10px;color:#665018}}footer{{margin:30px 0;color:#6A778A;font-size:13px}}@media(max-width:640px){{main{{margin:24px auto}}}}</style><body><header><img src="../../logo/primary/white/horizontal.svg" alt="AtoZ"><div>CONTENT ENGINE · OWNER REVIEW ONLY</div></header><main><p class="eyebrow">WEEK 01 · PRODUCTION PACKAGE</p><h1>برنامهٔ تولید هفتهٔ اول</h1><p class="lead">{len(plan['content_items'])} محتوای مادر · {len(deliveries)} تحویل · مرتب‌شده بر اساس روز و نوع خروجی</p>{alert}<section class="days">{''.join(cards)}</section><footer>همهٔ فایل‌ها پیش‌نویس بازبینی‌اند. انتشار و زمان‌بندی خودکار خاموش است؛ نشانی‌ها و شواهد را مالک تأیید کند.</footer></main></body></html>'''
    (out/"index.html").write_text(week_html,encoding="utf-8")

def build(source:Path,out:Path,skip_video:bool=False,allow_replace:bool=False)->dict:
    raw=source.read_bytes();original=json.loads(raw.decode("utf-8"));summary=validate_source(original)
    plan,deliveries=enrich(original)
    final_errors=schema_errors(plan,PLAN_SCHEMA,"generated week-one plan")
    if final_errors:raise ValueError("Generated plan failed schema validation:\n- "+"\n- ".join(final_errors[:30]))
    tokens=ROOT/"brand/tokens.json";system=ROOT/"brand/design-system.json"
    discrepancy=count_reference_mismatch(original.get("notes",[]))
    manifest={"engine":"AtoZ Content Engine","engine_version":ENGINE_VERSION,"status":"owner_review","plan_id":plan.get("plan_id"),"source_plan":str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),"source_sha256":hashlib.sha256(raw).hexdigest(),"engine_source_sha256":engine_fingerprint(),"brand_tokens_sha256":sha(tokens),"design_system_sha256":sha(system),"generated_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),"generation_mode":"deterministic-local","approval_required":True,"publishing_enabled":False,"source_summary":summary,"reported_reference_count":discrepancy.get("reference_count"),"delivery_count_discrepancy":discrepancy.get("difference"),"renderers":{"svg":"AtoZ SVG templates + brand-token mark","png":"sharp (SVG rasterization)","mp4":"imageio-ffmpeg / ffmpeg","motion_demo":"HTML/SVG seekable anatomy"},"remotion":"optional source adapter; not invoked","hyperframes":"portable HTML/timeline handoff; CLI not invoked"}
    # All new files are created in an isolated staging folder. Existing exports are never cleaned or overwritten.
    stage=Path(tempfile.mkdtemp(prefix=f".{out.name}.build-",dir=out.parent))
    try:
        renderer.OUT=stage
        renderer.BRAND_SITE=OWNER_SITE
        renderer.INSTAGRAM=OWNER_HANDLE
        renderer.write_plan(plan,deliveries)
        renderer.write_delivery_files(plan,deliveries)
        renderer.write_package_guide(plan)
        write_daily_catalog(stage,plan,deliveries)
        (stage/"README.md").write_text("""# AtoZ Content Engine · هفتهٔ اول

**وضعیت بسته: پیش‌نویس برای بازبینی مالک.** این خروجی نسخه‌ای مستقل است و فایل‌های منبع یا بستهٔ قدیمی را تغییر نمی‌دهد.

## پیمایش

- `plan.json` و `assets/`: برنامه و رجیستری منبع؛ شناسه‌ها همان شناسه‌های ورودی‌اند.
- `content-items/`: brief هر یک از ۲۸ ایدهٔ مادر.
- `index.html`: نمای هفته؛ هر روز تابلو و پوشه‌های نوع‌محور `01-reels/`, `02-carousels/`, `03-posts/`, `04-stories/`, `05-web-telegram/` دارد.\n- منبع هر تحویل در `روز/شناسهٔ محتوا/شناسهٔ تحویل/` نگه‌داری می‌شود؛ صفحه‌های دسته‌بندی به فایل‌های اصلی پیوند می‌دهند و رسانه را بی‌دلیل کپی نمی‌کنند.
- هر تحویل شامل متن، `copy-outline.json`، `metadata.json` و SVG/PNG است؛ کاروسل‌ها پوشهٔ `slides/` و ریل‌ها `reel-source/` و `reel.mp4` دارند.
- `motion-lab/`: دمو HTML داده‌محور، storyboard، فریم‌ها، poster و MP4 فرضی.
- `review-state.json` و `intake-drafts.json`: داده‌های محلی داشبورد؛ هیچ درخواست بیرونی یا انتشاری انجام نمی‌شود.
- `content-engine-manifest.json` و `generated-file-index.json`: منشأ، نسخه و فهرست فایل‌ها.

## بازبینی

هیچ انتشار یا زمان‌بندی خودکاری وجود ندارد. مقصد URL با دامنهٔ رزروشدهٔ `.invalid` و هندل اجتماعی به‌صورت placeholder نشان داده شده‌اند؛ فقط مالک می‌تواند پس از تأیید جایگزین کند. زیرعنوان بنیان‌گذار موقت است. مثال‌های عددی آزمایشگاه موشن فرضی‌اند.

**تطبیق لازم:** برنامه ۸۴ تحویل دارد، اما جمع شمارنده‌های ردیف‌های منبع ۶۴ است؛ اختلاف ۲۰ مورد در plan، manifest و داشبورد آشکار می‌ماند و با تولید حل یا بازنویسی نشده است.

داشبورد: `python3 tools/serve_content_studio.py` را اجرا کنید. بازتولید در مسیر تازه: `python3 tools/run_content_engine.py --out content-output/week-01-copy`.
""",encoding="utf-8")
        (stage/"review-state.json").write_text("{}\n",encoding="utf-8")
        (stage/"intake-drafts.json").write_text("[]\n",encoding="utf-8")
        (stage/"content-engine-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        motion_cmd=[sys.executable,str(ROOT/"tools/build_motion_lab.py"),"--out",str(stage/"motion-lab")]
        subprocess.run(motion_cmd,cwd=ROOT,check=True)
        renderer.render_pngs()
        if not skip_video:
            renderer._LAST_DELIVERIES=deliveries
            renderer.encode_reels()
        else:
            manifest["renderers"]["week_reels"]="skipped by --skip-video; SVG storyboard sources remain"
            (stage/"content-engine-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        # Attach render status to each delivery metadata without mutating the source plan.
        video_count=sum(1 for d in deliveries if d["_kind"]=="reel") if not skip_video else 0
        manifest["rendered_video_count"]=video_count
        manifest["motion_demo_video"]=(stage/"motion-lab/break-even-anatomy.mp4").exists()
        if allow_replace:preserve_local_workspace(out,stage)
        indexed=[]
        for asset_path in sorted(p for p in stage.rglob("*") if p.is_file() and p.name not in {"generated-file-index.json","content-engine-manifest.json"}):
            indexed.append({"path":asset_path.relative_to(stage).as_posix(),"bytes":asset_path.stat().st_size,"sha256":sha(asset_path)})
        (stage/"generated-file-index.json").write_text(json.dumps({"files":indexed},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        manifest["asset_file_count"]=len(indexed)
        (stage/"content-engine-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        # Swap only a prior package created by this engine from the same source plan.
        if out.exists() and any(out.iterdir()):
            try:prior=json.loads((out/"content-engine-manifest.json").read_text(encoding="utf-8"))
            except Exception:prior={}
            if not allow_replace or prior.get("engine")!="AtoZ Content Engine" or prior.get("source_sha256")!=sha(source):
                raise FileExistsError(f"Output path is not an owned package for this source: {out}. Existing files were not changed.")
            backup=Path(tempfile.mkdtemp(prefix=f".{out.name}.previous-",dir=out.parent));backup.rmdir()
            out.rename(backup)
            try:stage.rename(out)
            except Exception:
                backup.rename(out)
                raise
            shutil.rmtree(backup)
        else:
            if out.exists():out.rmdir()
            stage.rename(out)
    except Exception:
        if stage.exists():shutil.rmtree(stage)
        raise
    return manifest

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=SOURCE_DEFAULT,help="Existing week-one plan.json (read-only)")
    parser.add_argument("--out",type=Path,default=OUTPUT_DEFAULT,help="New output package path")
    parser.add_argument("--skip-video",action="store_true",help="Keep SVG storyboards but omit the 16 social MP4 renders")
    args=parser.parse_args();source=args.source.expanduser().resolve();out=args.out.expanduser().resolve()
    if not source.is_file():parser.error(f"source plan not found: {source}")
    allow_replace=False
    if out.exists() and any(out.iterdir()):
        marker=out/"content-engine-manifest.json"
        try:existing=json.loads(marker.read_text(encoding="utf-8"))
        except Exception:existing={}
        same_owned_source=(existing.get("engine")=="AtoZ Content Engine" and existing.get("engine_version")==ENGINE_VERSION and existing.get("source_sha256")==sha(source))
        if same_owned_source and existing.get("engine_source_sha256")==engine_fingerprint():
            print(f"This exact source and engine build already exists at {out}; no files changed.");return 0
        if same_owned_source:allow_replace=True
        else:parser.error(f"output path already contains files not owned by this engine/source: {out}. Pick a new --out path; nothing was overwritten.")
    out.parent.mkdir(parents=True,exist_ok=True)
    try:
        manifest=build(source,out,args.skip_video,allow_replace=allow_replace)
    except Exception as exc:
        print(f"Build failed safely: {exc}",file=sys.stderr);return 1
    print(f"Built {manifest['source_summary']['content_items']} content items, {manifest['source_summary']['deliveries']} manual deliveries, {manifest['rendered_video_count']} reel videos and anatomy demo at {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")
    print("Status: owner review required; publication and scheduling are disabled.")
    return 0

if __name__=="__main__":raise SystemExit(main())
