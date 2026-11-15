#!/usr/bin/env python3
"""Inventory local fonts, extract metadata and flag unverified usage rights."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "tools/fonts"
OUT = ROOT / "brand/fonts"
PERSIAN_CODEPOINTS = {
    "peh": 0x067E, "tcheh": 0x0686, "jeh": 0x0698,
    "keheh": 0x06A9, "gaf": 0x06AF, "farsi_yeh": 0x06CC,
    "zwnj": 0x200C, "arabic_comma": 0x060C,
}


def name_values(font, name_ids):
    values = []
    if "name" not in font:
        return values
    for record in font["name"].names:
        if record.nameID in name_ids:
            try:
                text = record.toUnicode().strip()
            except Exception:
                continue
            if text and text not in values:
                values.append(text)
    return values


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify(license_text, filename):
    text = license_text.casefold()
    if filename.startswith(("Vazirmatn-", "Montserrat-", "Lato-")):
        return "OFL-1.1 (confirmed by tools/fonts/LICENSES.txt; retain attribution/license notice)"
    if "this font software is licensed under the sil open font license, version 1.1" in text:
        return "OFL-1.1 (font metadata declares; original license text/source still required for redistribution)"
    if "all rights reserved" in text or "license agreement" in text or "may not copy or distribute" in text:
        return "restricted/proprietary metadata — do not embed or redistribute without owner license"
    if license_text:
        return "license metadata present but not verified — owner confirmation required"
    return "no license metadata — owner confirmation required"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    hashes = defaultdict(list)
    for path in sorted(FONT_DIR.iterdir(), key=lambda p: p.name.casefold()):
        if path.suffix.lower() not in {".ttf", ".otf", ".woff", ".woff2"}:
            continue
        sha = sha256(path)
        hashes[sha].append(path.name)
        font = TTFont(path, lazy=True)
        names = name_values(font, {0, 1, 2, 4, 6, 8, 9, 10, 11, 12, 13, 14})
        all_names = "\n".join(names)
        license_bits = name_values(font, {13, 14})
        copyright_bits = name_values(font, {0})
        family_bits = name_values(font, {1})
        subfamily_bits = name_values(font, {2})
        full_bits = name_values(font, {4})
        cmap = set().union(*(set(table.cmap) for table in font["cmap"].tables)) if "cmap" in font else set()
        license_text = "\n".join(license_bits + copyright_bits)
        records.append({
            "file": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha,
            "family": family_bits[0] if family_bits else path.stem,
            "subfamily": subfamily_bits[0] if subfamily_bits else "",
            "full_name": full_bits[0] if full_bits else path.stem,
            "license_metadata": license_bits,
            "copyright_metadata": copyright_bits,
            "license_status": classify(license_text, path.name),
            "persian_required_glyphs": {key: code in cmap for key, code in PERSIAN_CODEPOINTS.items()},
            "persian_coverage_complete": all(PERSIAN_CODEPOINTS[key] in cmap for key in ("peh", "tcheh", "jeh", "keheh", "gaf", "farsi_yeh", "zwnj")),
            "latin_basic_coverage": all(code in cmap for code in range(0x20, 0x7F)),
            "glyph_count": len(cmap),
            "source_note": "In-repository font metadata only; this audit is not a substitute for the original purchase/license document.",
        })
        font.close()

    result = {
        "schema_version": "1.0.0",
        "inventory_date": "2026-11-14",
        "font_directory": "tools/fonts/",
        "font_count": len(records),
        "records": records,
        "identical_file_groups": [sorted(names) for names in hashes.values() if len(names) > 1],
        "policy": {
            "approved_open_families": ["Vazirmatn", "Montserrat", "Lato"],
            "expressive_candidate": "Dongol (metadata states SIL OFL 1.1; missing ZWNJ glyph; keep limited to short display treatments until visual review)",
            "restricted_or_unverified": "All other user-supplied families remain in the source font folder, but are not embedded, outlined into production exports, or copied to deliverables until a valid license is confirmed.",
        },
    }
    (OUT / "font-inventory.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# ممیزی فونت‌های هویت AtoZ.FnB",
        "",
        f"تاریخ ثبت: {result['inventory_date']} · تعداد فایل فونت: {len(records)}",
        "",
        "> این گزارش از متادیتای داخل فایل‌ها ساخته شده است؛ مجوز استفادهٔ مالک را اثبات نمی‌کند.",
        "",
        "## فونت‌های مناسب برای خروجی عمومی بر اساس مجوز موجود در ریپو",
        "",
        "| خانواده | کاربرد پایه | وضعیت |",
        "|---|---|---|",
        "| Vazirmatn | فارسی: متن و تیتر | SIL Open Font License 1.1؛ فایل‌های OFL در `tools/fonts/` |",
        "| Montserrat | تیتر و برچسب لاتین | SIL Open Font License 1.1؛ فایل‌های OFL در `tools/fonts/` |",
        "| Lato | متن لاتین | SIL Open Font License 1.1؛ فایل‌های OFL در `tools/fonts/` |",
        "| Dongol | نامزد نمایشی/ادیتوریال کوتاه | متادیتا OFL 1.1 را اعلام می‌کند؛ نویسهٔ نیم‌فاصله را ندارد، بنابراین فقط نمونهٔ کوتاه و نیازمند بازبینی |",
        "",
        "## فونت‌های ارسالی با حق استفادهٔ نیازمند تأیید",
        "",
        "در خانواده‌های DigiFonts، Shoko/Shokoh، DG Jory، Mj و Massir، متادیتا شامل `All rights reserved`، توافق‌نامهٔ محدود، یا فاقد متن مجوز قابل‌اتکا است. فایل‌ها حذف نشده‌اند؛ اما تا دریافت مجوز/فاکتور/اجازهٔ کتبی، از آن‌ها در SVG نهایی، PDF برندبوک، قالب‌های عمومی یا موشن استفاده نمی‌شود. وجود فایل در پوشه به‌تنهایی مجوز بازتوزیع یا outline کردن را ثابت نمی‌کند.",
        "",
        "فایل‌های TTF/OTF تکراری با هش یکسان در `font-inventory.json` ثبت شده‌اند؛ برای استفاده، نسخهٔ تکراری لازم نیست کپی شود.",
        "",
        "## قرارداد تایپوگرافی",
        "",
        "- فارسی: `Vazirmatn ExtraBold/Bold` تیتر، `Vazirmatn Regular` متن؛ fallback: `Noto Sans Arabic, Tahoma, sans-serif`.",
        "- لاتین: `Montserrat Bold/SemiBold` تیتر، `Lato Regular` بدنه؛ fallback: `Arial, sans-serif`.",
        "- `Dongol` تنها در نمونه‌های نمایشی کوتاه و جدا از متن بدنه؛ به علت نبود U+200C برای متن دارای نیم‌فاصله مناسب نیست.",
        "- ایران‌سنس دست‌نویس در این وابستگی نیست؛ تا دریافت فایل و مجوز، استفاده نمی‌شود.",
        "",
    ]
    for row in records:
        if row["license_status"].startswith("OFL") and row["family"].casefold() not in {"vazirmatn", "montserrat", "lato", "dongol"}:
            lines.append(f"- **{row['file']}** — {row['family']} {row['subfamily']}: OFL metadata found; confirm license text/source before use.")
    (OUT / "font-inventory-fa.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Audited {len(records)} font files; wrote {OUT.relative_to(ROOT)}/font-inventory.json")


if __name__ == "__main__":
    main()
