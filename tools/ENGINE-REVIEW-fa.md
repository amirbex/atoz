# بازبینی موتورهای ساخت هویت AtoZ.FnB

## تصمیم کوتاه

معماری مفید موتور CaReMa برای تولید طراحی را به‌عنوان مرجع فنی بررسی کردیم، ولی خود پروژه/ماژول‌های CaReMa را به AtoZ وارد نکردیم: تنظیمات و کد آن یک خانوادهٔ محصول جداگانه با رنگ سرمه‌ای `#0F2142`، نشان متفاوت و ماژول‌های HR/CRM/ERP/منو است. منبع حقیقت AtoZ همین `brand/tokens.json`، هندسهٔ نشان موجود و `tools/build_logo.py` باقی می‌ماند. از موتور AtoZ فقط اجزای عمومی و واقعاً لازم انتخاب شده‌اند.

## نتیجهٔ بررسی سورس CaReMa آپلودشده

نسخه‌های داخل یادداشت کاربر ادعای نسخهٔ زمان ساخت‌اند، نه lockfile قابل‌نصب. `setup_env.sh` بیشتر dependencyها را بدون نسخه pin می‌کند. در فایل‌های آپلودشده `pack.py` و مسیر `src/emblem.json` و فولدر `fonts/` مطابق manifest موجود نیستند؛ پس بستهٔ ارائه‌شده را نمی‌توان از روی این کپی به‌صورت clean-room بازسازی کرد.

| بخش | ارزیابی برای AtoZ |
|---|---|
| `uharfbuzz` + `fontTools` | مناسب شکل‌دهی و تبدیل نویسهٔ فارسی به path؛ در `build_logo.py` و سازنده‌های AtoZ استفاده شده و به نسخه‌های آزموده‌شده pin شده است. |
| `sharp` / رندر SVG | مناسب خروجی preview سریع؛ renderer همهٔ پیش‌نمایش‌های SVG این بسته را ساخته است. از نسخهٔ 0.34.5 به 0.35.5 ارتقا یافت، چون `npm audit` برای نسخهٔ قبلی آسیب‌پذیری High در وابستگی libvips گزارش می‌کرد؛ پس از ارتقا `npm audit --omit=dev` صفر آسیب‌پذیری گزارش کرد. |
| `imageio-ffmpeg` | مناسب باینری FFmpeg قابل‌حمل؛ سه MP4 بی‌صدای لوگوموشن را ساخته است. در این محیط FFmpeg سیستمی یافت نشد، اما باینری bundled پکیج کار کرد. |
| `reportlab` | برای ترکیب PNGهای برداری‌شده در PDF چندصفحه‌ای برندبوک استفاده شده؛ ساده‌تر از افزودن PyMuPDF به این پروژه. |
| `jsonschema` | برای اعتبارسنجی برنامه‌ها و ساختارهای JSON فعلی در ریپو لازم است؛ در قرارداد محیط pin شده است. |
| `Pillow` | وابستگی مستقیم برخی ابزارهای تصویری/موشن است و در موتور CaReMa هم برای این کارها استفاده می‌شد؛ نسخه در lock ثبت شده است. |
| Playwright + Chromium | در CaReMa برای HTML زنده، PDF، فریم‌برداری و screenshot مناسب است، اما این محیط Chromium/Playwright نصب‌شده ندارد و مسیر دانلود browser در زمان build تضمین‌شده نیست. خروجی‌های این مرحله به آن نیاز ندارند؛ افزودن browser بزرگ، شکننده و بلااستفاده می‌بود. |
| `shapely`, `resvg-py`, `CairoSVG`, `PyMuPDF` | در AtoZ فعلی مسیر ضروری ندارند؛ متن از HarfBuzz/fontTools مستقیماً outline شده، SVG با Sharp raster می‌شود و PDF با ReportLab ساخته شده است. نصبشان هزینه و سطح وابستگی می‌افزود بی‌آنکه خروجی این مرحله را بهتر کند. |
| `numpy`, `opencv-python`, `scipy` | در موتور CaReMa طبق manifest صرفاً برای استخراج نشان از تصویر مصرف می‌شوند؛ AtoZ نشان هندسی و مسیر برداری از قبل دارد، پس این وابستگی‌ها استفاده نشدند. |
| React / Vite | برای assetهای ایستا (SVG/PNG/PDF و HTML پیمایشی برندبوک) لازم نیست. اپ جداگانه‌ای به درخواست این فاز نبود؛ React اضافه نشده تا scope و حجم نصب بی‌دلیل زیاد نشود. اگر بعداً پنل تعاملی توکن‌ها/قالب‌ها خواسته شود، آن زمان کاربرد واقعی دارد. |

### اشکال‌های بسته‌بندی در setup موتور مرجع

- در manifest، `Pillow`, `numpy`, `opencv-python`, `scipy` مستقیماً import می‌شوند اما `setup_env.sh` آن‌ها را نصب نمی‌کند؛ نصب تازه برای برخی مسیرها شکست می‌خورد.
- `pypdf` و `skia-pathops` طبق همان manifest مصرف مستقیم ندارند.
- دستور setup از `pip install` بدون نسخه استفاده می‌کند؛ بنابراین فهرست نسخه‌های ذکرشده به‌تنهایی بازتولیدپذیر نیست.
- منبع font، نشان و `pack.py` در کپی فعلی کامل نیست؛ پکیج مرجع را نباید به‌عنوان وابستگی production پروژهٔ AtoZ تلقی کرد.

## موتور AtoZ که اکنون قابل‌بازسازی است

### Python — `tools/requirements.txt` و `tools/requirements.lock`

نسخه‌های direct/runtime که با آن‌ها build و test شده‌اند:

- fontTools 4.68.0
- uharfbuzz 0.57.0
- Brotli 1.2.1
- Pillow 13.0.0
- imageio-ffmpeg 0.8.1
- ReportLab 5.1.0
- jsonschema 4.26.0

`requirements.lock` نسخهٔ dependencyهای transitive را نیز ثبت می‌کند. Python اجرایی این sandbox، 3.11.2 است؛ نسخهٔ 3.13.18 در یادداشت CaReMa را معادل محیط آزموده‌شده فرض نمی‌کنیم.

### JavaScript

- Node.js 22.22.3 و npm 10.9.8
- `sharp` 0.35.5 با pin دقیق در `tools/package.json` و `tools/package-lock.json`
- `npm --prefix tools audit --omit=dev`: صفر آسیب‌پذیری در dependencyهای production پس از ارتقای sharp.
- `npm --prefix tools run render-identity`: بازسازی previewهای SVG به PNG.

## آزمون

`python3 tools/validate_identity_assets.py` تعداد اسلایدها، قالب‌ها، شیت‌ها، فونت‌ها، SVGها و ویدئوها را کنترل می‌کند. `python3 -m pytest -q` روی مجموعهٔ فعلی ریپو: ۱۱ تست و ۴۵۸ subtest موفق. نصب‌های موقت بررسی/آزمون در `/tmp` انجام شده‌اند و وابستگی به `node_modules` یا virtualenv خارج‌شده از مخزن نیستند.

سیستم‌عامل این build: Linux x86_64، glibc 2.36؛ با مشخصات CaReMa یعنی glibc 2.41 یکسان نیست. Windows و macOS برای هر دو موتور هنوز آزموده نشده‌اند.
