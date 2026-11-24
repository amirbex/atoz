#!/usr/bin/env python3
"""Build a new, review-only package from the existing week-one plan."""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re, shutil, subprocess, sys, tempfile
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
        (stage/"README.md").write_text("""# AtoZ Content Engine · هفتهٔ اول

**وضعیت بسته: پیش‌نویس برای بازبینی مالک.** این خروجی نسخه‌ای مستقل است و فایل‌های منبع یا بستهٔ قدیمی را تغییر نمی‌دهد.

## پیمایش

- `plan.json` و `assets/`: برنامه و رجیستری منبع؛ شناسه‌ها همان شناسه‌های ورودی‌اند.
- `content-items/`: brief هر یک از ۲۸ ایدهٔ مادر.
- پوشه‌های روزهای هفته: تحویل‌ها به‌شکل `روز/شناسهٔ محتوا/شناسهٔ تحویل/`.
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
