# موتور تولید محتوای هفتهٔ اول

## محدوده

`build_week1_package.py` دادهٔ محتوایی، متن/HTML، SVG/PNG، استوری‌بورد ویدئو، افکت صوتی WAV و MP4 تولید می‌کند. این ابزار **هیچ فایل/محتوایی را در سایت یا شبکهٔ اجتماعی آپلود نمی‌کند، ساعت انتشار تنظیم نمی‌کند و پستی منتشر نمی‌کند**.

## پیش‌نیازها

- Python 3.10+
- Node.js 18+
- فایل‌های فونت مجاز موجود در `tools/fonts/`

در ریشهٔ repository:

```bash
python3 -m pip install -r tools/requirements.txt
npm install --prefix tools
python3 tools/build_week1_package.py
```

خروجی در `پیش انتشار/ماه اول/هفته اول/` ساخته می‌شود. PNG با Sharp رندر می‌شود و MP4 با ffmpeg بستهٔ `imageio-ffmpeg` ساخته می‌شود. SFX از سینتسایزر محلی همین موتور است؛ نریشن و موسیقی استفاده نمی‌شود.

برای آزمون‌ها:

```bash
python3 -m unittest discover -s tests -v
python3 tools/validate_content_plan.py --plan-only --plan 'پیش انتشار/ماه اول/هفته اول/plan.json'
```

## محل تغییر ورودی‌ها

- ردیف‌های ۲۸ ایده، ۳۸ asset و تخصیص هفت‌روزه: `tools/build_week1_package.py`
- متن هفت پیش‌نویس سایت: `tools/week1_website_articles.py`
- قرارداد داده: `content-pilot/schemas/week-plan.schema.json`
- fonts / logo / palette: `tools/fonts/`, `logo/`, `brand/tokens.json`

پیش از بازسازی، خروجی قبلی را در جای امن نگه دارید اگر مالک روی آن یادداشت/ویرایش دستی انجام داده است؛ موتور فایل‌های هم‌نام را بازنویسی می‌کند. پس از تولید، اختلاف `84` با مجموع `delivery_count_w1` یعنی `64` را از `پیش انتشار/ماه اول/هفته اول/VALIDATION.fa.md` بررسی کنید.
