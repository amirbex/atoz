"""Deterministic Persian copy scaffolding; never invents facts or citations."""
from __future__ import annotations


def evidence_note(level: str) -> str:
    return {
        "verified": "ادعای قابل انتشار فقط همراه منبع، تاریخ دسترسی و دامنهٔ کاربرد ثبت شود.",
        "experience": "این نکته فقط تجربهٔ منتسب است؛ نام، زمینه و اجازهٔ صاحب تجربه بازبینی شود.",
        "fictional_example": "مثال فرضی است؛ به فرد، کسب‌وکار یا بازار واقعی نسبت داده نشود.",
        "hypothesis": "فرض اولیه است؛ پیش از بیان به‌عنوان واقعیت باید آزمون یا منبع معتبر داشته باشد.",
    }.get(level, "سطح شواهد روشن نیست؛ تا بررسی منبع، ادعای قطعی منتشر نشود.")


def build_carousel(item: dict, delivery: dict) -> list[dict]:
    topic = item.get("topic", "موضوع")
    problem = item.get("audience_problem") or "مسئله و مخاطب را پیش از پیشنهاد راه‌حل دقیق کنید."
    thesis = item.get("core_message") or "پیام محوری باید با شواهد بررسی شود."
    cta = (delivery.get("cta") or {}).get("label") or "این نکته را ذخیره و در فرایند خود بررسی کنید."
    caution = evidence_note(item.get("evidence_level", "unknown"))
    return [
        {"role":"cover","title":delivery.get("hook") or topic,"body":"یک مسئلهٔ روشن؛ یک نکتهٔ قابل‌آزمایش."},
        {"role":"context","title":"مسئله چیست؟","body":problem},
        {"role":"principle","title":"اصل کلیدی","body":thesis},
        {"role":"diagnostic","title":"چه چیزی را بررسی کنیم؟","body":"مخاطب، زمان، هزینه و معیار نتیجه را پیش از مقایسه ثبت کنید."},
        {"role":"action","title":"یک اقدام کوچک","body":"یک نمونهٔ واقعی از فرایند خود انتخاب کنید و فقط یک فرض را روشن بنویسید."},
        {"role":"measure","title":"از فرض تا مشاهده","body":"ورودی، مسئول، بازهٔ زمانی و نتیجه را ثبت کنید؛ بدون داده، علت قطعی نسازید."},
        {"role":"evidence","title":"حد شواهد","body":caution},
        {"role":"cta","title":"گام بعدی","body":cta},
    ]


def build_reel_scenes(item: dict, delivery: dict) -> list[dict]:
    return [
        {"role":"hook","title":delivery.get("hook") or item.get("topic", "موضوع"),"body":item.get("audience_problem", "")},
        {"role":"insight","title":"یک نکتهٔ اجرایی","body":item.get("core_message", "")},
        {"role":"handoff","title":"حالا چه کنیم؟","body":evidence_note(item.get("evidence_level", "unknown"))},
    ]


def build_copy_outline(item: dict, delivery: dict) -> dict:
    format_id=delivery.get("format_id", "")
    result={"content_id":item.get("content_id"),"delivery_id":delivery.get("delivery_id"),"format_id":format_id,"language":"fa-IR","evidence_level":item.get("evidence_level","unknown"),"claim_policy":"no-new-claims; owner-review-required"}
    if format_id=="carousel": result["slides"]=build_carousel(item,delivery)
    elif format_id in {"micro_reel","mini_reel","main_reel","animated_reel"}: result["scenes"]=build_reel_scenes(item,delivery)
    else: result["hook"]=delivery.get("hook", "")
    result["caption"]=delivery.get("caption", "")
    result["cta"]=(delivery.get("cta") or {}).get("label", "")
    return result
