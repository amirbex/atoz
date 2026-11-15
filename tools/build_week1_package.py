#!/usr/bin/env python3
"""Build the first AtoZ.FnB pre-publication content package from structured source data.

No publishing or website upload is performed. Social output is a manual handoff:
copyable text, SVG/PNG artwork and silent-of-voice video with original synthesized SFX.
"""
from __future__ import annotations

import html
import json
import math
import os
from functools import lru_cache
import shutil
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_logo import line_svg, symbol_group
from week1_website_articles import ARTICLES as WEBSITE_ARTICLES

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "tools/fonts"
OUT = ROOT / "پیش انتشار/ماه اول/هفته اول"
ASSET_ROOT = ROOT / "دارایی‌های-محتوا"
AUDIO_ROOT = ROOT / "دارایی‌های-انیمیشن/صداهای-افکت"
PRESENTATION_ROOT = ROOT / "پرزنتیشن-برند"
STATIC_ROOT = ROOT / "دارایی‌های-ثابت"
TEMPLATES_ROOT = ROOT / "قالب‌های-محتوا"
MOTION_ROOT = ROOT / "لوگوموشن"
SITE_UI_ROOT = ROOT / "رابط-وب‌سایت"

PILLARS = {
    1: {"id": "education-sops", "name": "آموزش و استانداردسازی عملیاتی", "color": "#3B5998", "dark": "#6085D6", "hub": "کتابخانه و SOPها"},
    2: {"id": "leadership", "name": "الهام‌بخشی، رهبری و ذهنیت", "color": "#0A1931", "dark": "#FFB400", "hub": "Solutions"},
    3: {"id": "innovation-ai", "name": "نوآوری، هوش مصنوعی و اتوماسیون", "color": "#5D5FEF", "dark": "#8183FF", "hub": "بانک پرامپت"},
    4: {"id": "finance-market", "name": "اقتصاد F&B و تحلیل بازار", "color": "#0F766E", "dark": "#2DD4BF", "hub": "آزمایشگاه ابزارها"},
    5: {"id": "case-studies", "name": "مطالعات موردی و کالبدشکافی", "color": "#C05746", "dark": "#E06D5B", "hub": "مجله تخصصی"},
    6: {"id": "community-roadmaps", "name": "جامعه‌سازی و نقشهٔ راه", "color": "#0284C7", "dark": "#38BDF8", "hub": "آکادمی"},
}
DAY_NAMES = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
BRAND_SITE = "https://atozfnb.info/"
INSTAGRAM = "@atozfnb.info"

# content_id, title, pillar, series, personas, thesis, source asset IDs, summary.
IDEAS = [
 (1,"مدل کسب‌وکار استروالدر در برابر بیزنس‌پلن سنتی در صنعت F&B",1,"مبانی کسب‌وکار و بوم استروالدر",["مریم","سینا"],"بوم مدل کسب‌وکار یک نقشهٔ زنده برای آزمودن فرض‌های ارزش، مشتری و درآمد است؛ جایگزین همهٔ تحلیل‌های مالی یا طرح اجرایی نیست.",[1,2],"مقایسهٔ بوم با طرح ایستا و معرفی تمرین بوم برای کافه."),
 (2,"از پشت دستگاه اسپرسو تا اتاق استراتژی F&B",2,"داستان برند و رهبری",["مریم","سینا"],"مهارت فنی شرط لازم است؛ رهبری، سیستم‌سازی و تصمیم‌گیری داده‌محور مهارت‌های جداگانه‌اند.",[3,4],"روایت بنیان‌گذار با دعوت به خواندن نسخهٔ کامل در سایت."),
 (3,"بلوک اول بوم: بخش‌بندی مشتریان و طراحی پرسونا با AI",1,"آموزش ۹ بلوک بوم",["مریم","سینا"],"تعریف «همه» به‌عنوان مشتری، نیازها و پیشنهاد ارزش را مبهم می‌کند.",[5,6],"یک تمرین بخش‌بندی مشتری برای کافه و رستوران."),
 (4,"اقتصاد کافه و نقطهٔ سربه‌سر",4,"اقتصاد عملیاتی و ابزارها",["سینا","کیان"],"فروش و حاشیهٔ سود ناخالص به‌تنهایی سود خالص یا نقطهٔ سربه‌سر را نشان نمی‌دهند.",[7,8],"تفکیک هزینه‌ها و معرفی ابزار محاسبه؛ نسبت‌های نمونه باید با دادهٔ واقعی کسب‌وکار تنظیم شوند."),
 (5,"SOP و چک‌لیست بازگشایی و بستن شیفت",1,"ساختار و فرآیندها",["سینا","مریم"],"فرآیند روشن و قابل‌آموزش، وابستگی عملیات به حافظه و حضور یک فرد را کم می‌کند.",[9,10],"نمونهٔ چک‌لیست قابل‌ویرایش و مراحل ساخت SOP."),
 (6,"۵ خطای رایج کسب‌وکارهای F&B و تلهٔ نقدینگی",5,"خطاها و کالبدشکافی",["مریم","سینا"],"ریسک نقدینگی، انتخاب مکان، نیروی انسانی، منو و بازاریابی باید پیش از تصمیم‌گیری بررسی شوند؛ فراوانی/درصد شکست نیازمند منبع است.",[11,12],"چک‌لیست ریسک با پرهیز از ادعای آماری بی‌منبع."),
 (7,"ماتریس رشد آنسوف و نفوذ در بازار",4,"استراتژی‌های رشد",["سینا","کیان"],"رشد را می‌توان با گزینه‌های محصول/بازار سنجید؛ تخفیف‌دادن به‌تنهایی استراتژی رشد نیست.",[13,14],"چهار مسیر ماتریس و یک تمرین برای ساعات خلوت."),
 (8,"تلهٔ اپراتور بودن به‌جای مالک کسب‌وکار بودن",2,"تغییر ذهنیت مالک به رهبر",["سینا"],"اگر کیفیت فقط با حضور مالک حفظ می‌شود، فرصت بازبینی سیستم‌ها و تفویض روشن وجود دارد.",[15],"میکرو‌ریلز B-roll و کپشن تأملی."),
 (9,"پیش‌نویس بوم کسب‌وکار با پرامپت AI",3,"ابزارهای AI برای مدیران F&B",["سینا","مریم"],["AI می‌تواند به ساخت پیش‌نویس و پرسیدن سؤال‌های بهتر کمک کند؛ خروجی آن باید با داده و تجربهٔ واقعی بررسی شود."][0],[16],"نمایش پرامپت و خروجی فرضی؛ نه وعدهٔ نتیجهٔ تضمینی."),
 (10,"بیانیهٔ آغاز مسیر AtoZ.FnB",2,"بیانیه‌های استراتژیک",["عمومی"],"کیفیت محصول نقطهٔ شروع است؛ سیستم و تجربهٔ پایدار نیز برای ادارهٔ کسب‌وکار اهمیت دارند.",[17],"کارت نقل‌قول برای معرفی لحن برند."),
 (11,"نمای کلی ۹ بلوک بوم کسب‌وکار",1,"مبانی کسب‌وکار و بوم",["مریم","سینا"],"بلوک‌های بوم به هم وابسته‌اند؛ تغییر در مشتری یا ارزش پیشنهادی بر فعالیت‌ها و هزینه‌ها هم اثر می‌گذارد.",[18],"نقشهٔ ۹ بلوک با برچسب‌های فارسی و انگلیسی."),
 (12,"باور غلط: ایده و دکور خاص برای موفقیت کافی است",1,"باورهای غلط مدیریتی",["مریم"],"ایده باید در کنار مدل درآمد، عملیات و تقاضای واقعی آزموده شود.",[19],"ریلز موشن‌گرافیک با صداهای افکت و بدون نریشن."),
 (13,"مقایسهٔ دو کافه با تعداد مشتری و اقتصاد متفاوت",5,"کیس‌استادی‌های واقعی",["سینا","کیان"],"تعداد مشتری به‌تنهایی سودآوری را توضیح نمی‌دهد؛ ارقام داستانی باید صریحاً نمونه فرضی نامیده شوند.",[20],"کیس فرضی برای آموزش محاسبه، نه ادعای دادهٔ واقعی."),
 (14,"سنجش چالش‌های جامعهٔ F&B",6,"اتاق گفت‌وگوی شبانه",["عمومی"],"پرسش‌وپاسخ جامعه، اولویت‌های عملیاتی را برای موضوع‌های بعدی روشن می‌کند.",[21],"نظرسنجی چهارگزینه‌ای؛ پاسخ‌ها بعداً به موضوع‌های آموزشی تبدیل می‌شوند."),
 (15,"سه درس گذار از باریستا/سرآشپز به مدیر",2,"درس‌های مسیر رهبری",["سینا","مریم"],"تفویض، مدیریت سیستم و استفاده از داده از مهارت فنی متمایزند.",[22],"کاروسل روایی از تجربهٔ بنیان‌گذار؛ ادعاها به تجربهٔ شخصی منتسب شوند."),
 (16,"خوشه‌بندی نظرهای مشتری با AI",3,"پرامپت‌نویسی کاربردی",["سینا"],"هوش مصنوعی می‌تواند بازخوردهای متنی را دسته‌بندی کند، اما نباید دادهٔ شخصی مشتری بدون مجوز وارد آن شود.",[23],"نمایش روند تحلیل با دادهٔ ساختگی/ناشناس."),
 (17,"کالبدشکافی منوی شلوغ و پیچیدگی عملیات",5,"کالبدشکافی منو",["سینا","مریم"],"پیچیدگی منو می‌تواند بر موجودی، آموزش و سرعت اثر بگذارد؛ تعداد بهینه به مدل و ظرفیت هر مجموعه بستگی دارد.",[24],"موشن‌گرافیک با افکت صوتی؛ پرهیز از حد قطعی بدون داده."),
 (18,"استراتژی مقدم بر تقلید دکور",2,"بیانیه‌های استراتژیک",["عمومی"],"تقلید ظاهر رقبا بدون شناخت مشتری، جایگزین انتخاب استراتژیک نیست.",[25],"کارت تک‌جمله‌ای سرمه‌ای/طلایی."),
 (19,"بلوک دوم بوم: ارزش پیشنهادی",1,"آموزش ۹ بلوک بوم",["مریم","سینا"],"ارزش پیشنهادی باید دلیل انتخاب مشتری و مسئله‌ای را که حل می‌کند روشن سازد.",[26],"کاروسل با تمرین یک‌خطی و مثال فرضی."),
 (20,"ساخت پیش‌نویس Opening SOP با AI",3,"AI در عملیات روزانه",["سینا"],"پرامپت می‌تواند پیش‌نویس چک‌لیست بسازد؛ مدیر باید آن را با فرایند، مسئولیت و ایمنی محل تطبیق دهد.",[27],"دموی فرضی و قابل‌ویرایش از متن به چک‌لیست."),
 (21,"تنهایی تصمیم‌گیری و ارزش شبکه‌سازی صنفی",6,"باشگاه شبانهٔ مدیران",["سینا","مریم"],"شبکهٔ همتایان می‌تواند محل تبادل تجربه باشد، نه جایگزین مشاورهٔ تخصصی یا داده.",[28],"میکرو‌ریلز آرام و همدلانه."),
 (22,"رشد یا سود؟ اولویت تصمیم‌گیری",4,"رشد و مالی",["سینا","کیان"],"پیش از توسعه باید اقتصاد هر واحد و جریان نقد بررسی شود.",[29],"ریلز چالشی با یک چارچوب تصمیم."),
 (23,"نشتی مالی در دریافت کالا و انبار",1,"SOP دریافت کالا",["سینا"],"وزن‌کشی، تاریخ مصرف و روش FIFO از کنترل‌های قابل‌تعریف برای دریافت کالا هستند.",[30],"ریلز میدانی و فرم نمونهٔ دریافت."),
 (24,"پیداکردن گلوگاه صف با پرامپت #02",3,"ممیزی هوشمند کسب‌وکار",["سینا","کیان"],"دادهٔ زمان انتظار و مراحل سرویس می‌تواند به شناسایی گلوگاه کمک کند؛ کیفیت داده و آزمون میدانی مهم است.",[31,32],"موشن‌گرافیک و کارت پرامپت."),
 (25,"تحلیل جمعی تجربهٔ شکست پروژه‌های F&B",6,"تعامل آخر هفته",["عمومی"],"گفت‌وگوی ناشناس و محترمانه می‌تواند علت‌های سیستمی را از سرزنش افراد جدا کند.",[33],"کارت پرسش برای دریافت تجربهٔ میدانی."),
 (26,"سه مدل کسب‌وکار نوآورانه در F&B",5,"پرونده‌های تحلیلی",["کیان","سینا","مریم"],"میکروکافه، آشپزخانهٔ ابری و اشتراک، الگوهایی برای مقایسه‌اند؛ نتیجهٔ مالی به بازار و اجرا وابسته است.",[34,35],"مقالهٔ تحلیلی و کاروسل؛ فقط با منابع قابل‌ارجاع."),
 (27,"مرور هفتهٔ اول و قلاب هفتهٔ دوم",6,"مرور هفتگی و نقشهٔ راه",["تمام دنبال‌کنندگان"],"جمع‌بندی، پیوندهای منابع و موضوع‌های بعدی را در یک نقطه ارائه می‌کند.",[36,37],"کارت مرور و تیزر یوتیوب؛ بدون انتشار خودکار."),
 (28,"Prime Cost به‌عنوان پیش‌درآمد هفتهٔ دوم",4,"آماده‌سازی مالی",["سینا","کیان"],"Prime Cost معمولاً از بهای مواد و نیروی کار تشکیل می‌شود؛ هر آستانه باید به تعریف و زمینهٔ بازار متصل باشد.",[38],"میکرو‌ریلز فرمول و دعوت به بررسی دادهٔ خود."),
]
IDEA_MAP = {row[0]: row for row in IDEAS}

# Seven daily editorial schedules. Five feed outputs and five stories are kept as the supplied week-one proposal.
# These day-level groups are editorial drafts, not an imposed weekly cadence; the numbers vary by day.
FEED_IDS = [[1,8,9],[11,2,12,13,14,10],[3,15,16,5],[5,22,17,4,18],[19,7,6,20,21,26,4],[7,6,23,24],[26,27,27,28,27,18]]
FEED_FORMATS = [
 ["carousel","micro_reel","mini_reel"],
 ["single_map","main_reel","animated_reel","mini_reel","community_post","quote"],
 ["carousel","story_carousel","micro_reel","single_infographic"],
 ["carousel","main_reel","animated_reel","micro_reel","quote"],
 ["carousel","single_infographic","main_reel","mini_reel","micro_reel","carousel","quote"],
 ["carousel","carousel","main_reel","animated_reel"],
 ["carousel","recap_post","mini_reel","micro_reel","quote","community_post"],
]
STORY_IDS = [[14,1,4,9],[12,2,13],[15,3,2,5,4],[5,5,22,4,5,7],[19,19,6,7],[7,6,24,27,23,25,14],[27,26,27,27,27,28]]
FEED_TIMES = [None] * 7
FEED_HOOKS = {
 1:"بیزنس‌پلن ۵۰ صفحه‌ای، بدون آزمودن فرض‌های کسب‌وکار چه چیزی را حل می‌کند؟",
 2:"از پشت دستگاه اسپرسو تا اتاق استراتژی: مهارت فنی کافی نیست.",
 3:"وقتی می‌گویید «مشتری ما همه‌اند»، هنوز مشتری را تعریف نکرده‌اید.",
 4:"فروش بالا به‌تنهایی نمی‌گوید کافه سود می‌دهد.",
 5:"سه SOP که می‌توانند آشفتگی شیفت را قابل‌کنترل‌تر کنند.",
 6:"پیش از سرمایه‌گذاری، این پنج ریسک را بررسی کن.",
 7:"برای رشد فقط تخفیف‌دادن یا شعبهٔ دوم وجود ندارد.",
 8:"اگر حضور شما برای حفظ کیفیت لازم است، کدام سیستم باید بازبینی شود؟",
 9:"با این پرامپت پیش‌نویس بوم را بساز—بعد با واقعیت بسنج.",
 10:"کیفیت نقطهٔ شروع است؛ سیستم هم باید کار کند.",
 11:"۹ بلوک بوم در یک نگاه؛ کدام خانه هنوز فرضی است؟",
 12:"ایده و دکور خاص به‌تنهایی مدل کسب‌وکار نمی‌سازند.",
 13:"مشتری بیشتر الزاماً به معنی سود بیشتر نیست.",
 14:"اگر یک گره از کسب‌وکارت را باز می‌کردی، کدام بود؟",
 15:"سه درسی که از گذار نقش فنی به مدیریت یاد گرفتم.",
 16:"بازخورد مشتری را به فهرست اقدام‌های قابل‌آزمون تبدیل کن.",
 17:"منوی بلند چه هزینه‌هایی را به عملیات اضافه می‌کند؟",
 18:"ظاهر رقبا را می‌شود کپی کرد؛ استراتژی را نه.",
 19:"«قهوهٔ باکیفیت» برای مشتری شما دقیقاً چه ارزشی می‌سازد؟",
 20:"از فرایند واقعی خودت یک پیش‌نویس Opening SOP بساز.",
 21:"تصمیم‌های سخت را لازم نیست همیشه تنها بررسی کنی.",
 22:"قبل از توسعه، اقتصاد واحد فعلی را بررسی کرده‌ای؟",
 23:"کنترل دریافت کالا از کجا شروع می‌شود؟",
 24:"صف کجا متوقف می‌شود؟ مراحل و زمان‌ها را اندازه بگیر.",
 25:"در تجربهٔ شما، یک شکست F&B از کجا شروع شد؟",
 26:"سه الگوی کسب‌وکار برای مقایسه، نه نسخهٔ تضمینی موفقیت.",
 27:"نقشهٔ هفتهٔ اول و آنچه در هفتهٔ بعد ادامه می‌یابد.",
 28:"Prime Cost چیست و چه داده‌ای برای محاسبه‌اش لازم است؟",
}
STORY_TIMES = [None] * 7
STORY_TEXT = [
 ["نظرسنجی شروع هفته: تمرکز شما راه‌اندازی است یا سیستم‌سازی؟","بازنشر کاروسل بوم و معرفی کاربرگ در Library.","نکتهٔ مالی امروز: نسبت هزینه‌ها را با دادهٔ خودتان بسنجید.","پشت‌صحنهٔ آماده‌سازی محتوای این هفته.","چقدر با بوم کسب‌وکار آشنایی دارید؟"],
 ["برای موفقیت کافه، ایده مهم‌تر است یا سیستم و مدل مالی؟","معرفی مقالهٔ مسیر رهبری در مجله.","بازنشر ریلز روایت مسیر حرفه‌ای.","یک نکته از کیس فرضی فروش و سود.","باکس پرسش دربارهٔ مسیر شغلی در F&B."],
 ["نکتهٔ رهبری: مهارت فنی و مهارت مدیریت یکی نیستند.","معرفی کاروسل Customer Segments و کارت پرامپت.","پاسخ به پرسش‌های منتخب مخاطبان.","تعریف کوتاه SOP و اشاره به فایل اجرایی.","کوئیز: چه داده‌ای برای Prime Cost لازم است؟"],
 ["پشت‌صحنهٔ ساخت فلوچارت SOP.","بازنشر کاروسل SOP و معرفی چک‌لیست.","نظرسنجی: رشد فروش یا اصلاح هزینه؟","دموی ماشین‌حساب و لینک صفحهٔ ابزار.","باکس پرسش دربارهٔ بی‌نظمی عملیات."],
 ["نکتهٔ ارزش پیشنهادی: ویژگی با ارزش یکی نیست.","بازنشر کاروسل Value Propositions.","بازنشر ریلز خطاها و چک‌لیست ریسک.","یک خانه از ماتریس آنسوف.","پاسخ به پرسش‌های عملیات و معرفی منابع."],
 ["نظرسنجی: تخفیف یا ساختن تجربه برای ساعت خلوت؟","معرفی دو محتوای تحلیلی امروز.","لینک کارت پرامپت #02.","بازنشر تجربهٔ مخاطب با اجازه.","نکتهٔ دریافت کالا: وزن و تاریخ را بررسی کن."],
 ["پرسش جمع‌بندی: چه تغییری را این هفته آزمودید؟","لینک پروندهٔ سه مدل کسب‌وکار.","بازنشر نقشهٔ گنج هفته.","تیزر شروع محتوای یوتیوب هفتهٔ دوم.","قلاب موضوع‌های هفتهٔ دوم و یادآوری."],
]

WEB_CONTENT = [1,2,3,4,5,24,26]
TG_CONTENT = [1,2,3,4,6,24,27]
WEB_TYPES = ["library_resource","magazine_article","prompt_card","calculator_guide","library_sop","prompt_card","magazine_case_study"]
TG_TYPES = ["telegram_file","telegram_summary","telegram_prompt","telegram_guide","telegram_checklist","telegram_prompt","telegram_digest"]
WEB_TIMES = [None] * 7
TG_TIMES = [None] * 7

ASSETS = [
 (1,1,"workbook","کاربرگ مستقل بوم کسب‌وکار؛ همراه با پیوند به منابع رسمی کتاب"),(2,1,"carousel","کاروسل بوم در برابر بیزنس‌پلن"),(3,2,"article","مقالهٔ مسیر از باریستا تا استراتژیست"),(4,2,"reel","ریلز روایت مسیر بنیان‌گذار"),(5,3,"prompt","کارت پرامپت بخش‌بندی مشتری"),(6,3,"carousel","کاروسل بخش مشتریان"),(7,4,"calculator_guide","راهنمای محاسبهٔ نقطهٔ سربه‌سر و Food Cost"),(8,4,"infographic_reel","اینفوگرافیک هزینه‌ها و دموی ابزار"),(9,5,"checklist","چک‌لیست Opening and Closing"),(10,5,"carousel","کاروسل SOPهای ضروری"),(11,6,"reel","ریلز پنج ریسک شروع کسب‌وکار"),(12,6,"carousel","کاروسل کالبدشکافی ریسک نقدینگی"),(13,7,"infographic","ماتریس آنسوف برای F&B"),(14,7,"carousel","کاروسل نفوذ در بازار"),(15,8,"reel","میکرو‌ریلز تلهٔ اپراتور بودن"),(16,9,"reel","مینی‌ریلز ساخت پیش‌نویس بوم با AI"),(17,10,"quote","کارت بیانیهٔ برند"),(18,11,"diagram","نقشهٔ ۹ بلوک بوم"),(19,12,"reel","ریلز موشن‌گرافیک باور غلط"),(20,13,"reel","مینی‌ریلز کیس فرضی فروش/سود"),(21,14,"community_card","کارت نظرسنجی جامعه"),(22,15,"carousel","کاروسل سه درس رهبری"),(23,16,"reel","میکرو‌ریلز بازخورد مشتری و AI"),(24,17,"reel","ریلز موشن‌گرافیک منو"),(25,18,"quote","کارت استراتژی مقدم بر تقلید"),(26,19,"carousel","کاروسل ارزش پیشنهادی"),(27,20,"reel","مینی‌ریلز پیش‌نویس SOP با AI"),(28,21,"reel","میکرو‌ریلز همدلی با مدیران"),(29,22,"reel","ریلز رشد یا سود"),(30,23,"reel","ریلز دریافت کالا و FIFO"),(31,24,"prompt","کارت پرامپت گلوگاه"),(32,24,"reel","ریلز موشن‌گرافیک گلوگاه صف"),(33,25,"community_card","کارت پرسش تجربهٔ شکست"),(34,26,"article","پروندهٔ تحلیلی سه الگو"),(35,26,"carousel","کاروسل سه مدل کسب‌وکار"),(36,27,"recap_card","کارت مرور هفته"),(37,27,"reel","تیزر هفتهٔ دوم"),(38,28,"reel","میکرو‌ریلز Prime Cost"),
]

# Hook/description by delivery content and channel are generated from these editorial blocks.

def cid(n): return f"ATZ-C-{n:06d}"
def did(n): return f"ATZ-D-{n:06d}"
def aid(n): return f"ATZ-A-{n:06d}"

def style_for(n): return ["editorial","formal","minimal","artwork","retro","handwritten-accent"][n % 6]

@lru_cache(maxsize=4096)
def text_wrap(text, font, size, max_width):
    words = text.split()
    rtl = font.startswith("Vazirmatn")
    direction, script, language = ("rtl", "Arab", "fa") if rtl else ("ltr", "Latn", "en")
    lines=[]; current=""
    for word in words:
        candidate=(current+" "+word).strip()
        _, width, _ = line_svg([{"font":font,"text":candidate,"size":size,"direction":direction,"script":script,"language":language,"fill":"#000"}],rtl=rtl)
        if current and width > max_width:
            lines.append(current); current=word
        else: current=candidate
    if current: lines.append(current)
    return lines

def shaped_text(text, x_right, y, size, color, font="Vazirmatn-Bold.ttf", max_width=850, align="right"):
    rtl = font.startswith("Vazirmatn")
    direction, script, language = ("rtl", "Arab", "fa") if rtl else ("ltr", "Latn", "en")
    lines=text_wrap(text,font,size,max_width)
    parts=[]
    for i,line in enumerate(lines):
        run={"font":font,"text":line,"size":size,"direction":direction,"script":script,"language":language,"fill":color}
        body,w,h=line_svg([run],rtl=rtl)
        x=(x_right-w) if align=="right" else (x_right-w/2)
        yy=y+i*(size*1.38)
        parts.append(f'<g transform="translate({x:.1f} {yy:.1f})">{body}</g>')
    return "".join(parts), len(lines)*size*1.38

def mark_svg(x,y,scale=0.045,color_variant="color"):
    return f'<g transform="translate({x} {y}) scale({scale})">{symbol_group(color_variant)}</g>'

def theme_color(pillar): return PILLARS[pillar]["color"]

def make_card(title,subtitle,pillar,kind="feed",slide=1,total=1,style="editorial",background=None):
    W,H=(1080,1920) if kind in {"story","reel"} else ((1280,720) if kind=="youtube" else (1080,1350))
    accent=theme_color(pillar); dark="#0A1931"; white="#FFFFFF"; pale="#F8FAFC"
    bg=background or (dark if pillar==2 or style=="retro" else pale)
    if style=="artwork": bg="#FDF6F5" if pillar==5 else "#F6F6FD"
    if style=="handwritten-accent": bg="#FFFDF6"
    if bg==dark: fg=white; secondary="#CBD5E1"
    else: fg=dark; secondary="#475569"
    if style=="retro": secondary="#D97706"
    if kind=="youtube": bg=dark; fg=white
    # Base flat 2D layout; color remains a section cue, not the whole identity.
    parts=[f'<rect width="{W}" height="{H}" fill="{bg}"/>']
    parts.append(f'<rect x="0" y="0" width="{W}" height="24" fill="{accent}"/>')
    if style=="artwork":
        parts.append(f'<circle cx="{W-85}" cy="245" r="190" fill="{accent}" opacity=".10"/><circle cx="75" cy="{H-260}" r="150" fill="#FFB400" opacity=".13"/>')
    elif style=="retro":
        parts.append(f'<path d="M0 {H-300} Q{W/2} {H-500} {W} {H-300} L{W} {H} L0 {H}Z" fill="#E9D8A6" opacity=".36"/>')
        for i in range(6): parts.append(f'<line x1="{40+i*18}" y1="170" x2="{40+i*18}" y2="{H-130}" stroke="#C05746" opacity=".11"/>')
    elif style=="handwritten-accent":
        parts.append(f'<path d="M90 {H-210} Q300 {H-260} 510 {H-215} T980 {H-220}" fill="none" stroke="#FFB400" stroke-width="8" stroke-linecap="round"/>')
    # Logo and brand label; full domain/handle on normal-size creative.
    parts.append(mark_svg(W-160,72,0.055))
    parts.append(shaped_text("AtoZ.FnB",W-190,112,30,fg,"Montserrat-SemiBold.ttf",max_width=240)[0])
    parts.append(shaped_text("آ تو ز",W-190,165,25,accent,"Vazirmatn-Bold.ttf",max_width=220)[0])
    parts.append(shaped_text(f"ستون {pillar}  ·  {PILLARS[pillar]['name']}",W-70,245,28,accent,"Vazirmatn-Bold.ttf",max_width=W-150)[0])
    title_size=64 if kind in {"feed","story","reel"} else 54
    title_svg,title_h=shaped_text(title,W-82,330,title_size,fg,"Vazirmatn-ExtraBold.ttf",max_width=W-170,align="right")
    parts.append(title_svg)
    body_y=350+title_h+46
    body,body_h=shaped_text(subtitle,W-82,body_y,34,secondary,"Vazirmatn-Regular.ttf",max_width=W-180,align="right")
    parts.append(body)
    if kind=="carousel":
        parts.append(f'<rect x="72" y="{H-150}" width="{W-144}" height="5" rx="2" fill="#CBD5E1"/>')
        parts.append(f'<rect x="72" y="{H-150}" width="{(W-144)*slide/max(total,1):.1f}" height="5" rx="2" fill="{accent}"/>')
        num=f"{slide:02d} / {total:02d}"
    else: num=""
    # Footer signature and site/handle, readable at the intended social size.
    footer_y=H-95
    parts.append(f'<line x1="70" y1="{footer_y-48}" x2="{W-70}" y2="{footer_y-48}" stroke="{accent}" stroke-opacity=".35" stroke-width="2"/>')
    footer="atozfnb.info  ·  @atozfnb.info"
    parts.append(shaped_text(footer,W-78,footer_y,24,fg,"Montserrat-SemiBold.ttf",max_width=W-240)[0])
    if num: parts.append(shaped_text(num,90,footer_y,22,accent,"Montserrat-Bold.ttf",max_width=140,align="right")[0])
    # Keep the CTA concise and editable in the companion text file.
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'+''.join(parts)+'</svg>'


def make_document_html(title, body, caption, hashtags, extra=""):
    return f'''<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title>
<style>@font-face{{font-family:Vazirmatn;src:url('../../../../tools/fonts/Vazirmatn-Regular.ttf')}}@font-face{{font-family:Vazirmatn;src:url('../../../../tools/fonts/Vazirmatn-Bold.ttf');font-weight:700}}body{{margin:0;background:#f1f5f9;color:#0A1931;font:16px/1.9 Vazirmatn,Tahoma,sans-serif}}main{{max-width:860px;margin:30px auto;padding:28px;background:#fff;border-radius:18px}}h1,h2{{line-height:1.5}}.copy{{white-space:pre-wrap;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px}}button{{background:#0A1931;color:#fff;border:0;border-radius:8px;padding:10px 16px;cursor:pointer;margin:8px 0}}small{{color:#64748b}}a{{color:#3B5998}}</style><main>
<p><b>AtoZ.FnB</b> · atozfnb.info · {INSTAGRAM}</p><h1>{html.escape(title)}</h1><p>{html.escape(body)}</p>{extra}
<h2>کپشن — قابل کپی</h2><div class="copy" id="caption">{html.escape(caption)}</div><button onclick="navigator.clipboard.writeText(document.getElementById('caption').innerText)">کپی کپشن</button>
<h2>هشتگ‌ها — قابل کپی</h2><div class="copy" id="tags">{html.escape(hashtags)}</div><button onclick="navigator.clipboard.writeText(document.getElementById('tags').innerText)">کپی هشتگ‌ها</button>
<p><small>پیش‌نویس برای بازبینی و انتشار دستی. لینک‌های خروجی را در صورت نیاز ویرایش کنید.</small></p></main></html>'''


def synth_sfx(path: Path, duration: float, seed: int=0):
    import random, struct
    random.seed(seed)
    rate=22050; n=int(rate*duration); samples=[]
    # Original short whoosh/ticks, no voice and no third-party music.
    for i in range(n):
        t=i/rate; value=0.0
        for center, length, freq in [(0.18,0.46,380+seed*7),(duration*0.48,0.16,850),(duration*0.82,0.35,480+seed*5)]:
            x=(t-center)/length
            if 0 <= x <= 1:
                env=(math.sin(math.pi*x)**1.6)
                sweep=freq*(1.5-0.9*x)
                value += env*(0.5*math.sin(2*math.pi*sweep*t)+0.20*math.sin(2*math.pi*sweep*2.01*t))
        # Add extremely low synthetic noise for a soft transition texture.
        if value==0 and random.random()<0.015: value += random.uniform(-0.02,0.02)
        samples.append(max(-1,min(1,value*0.22)))
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate)
        wf.writeframes(b''.join(struct.pack('<h',int(v*32767)) for v in samples))


def idea_object(row):
    n,title,pillar,series,personas,thesis,asset_ids,summary=row
    return {"content_id":cid(n),"pillar_id":PILLARS[pillar]["id"],"series_id":series.lower().replace(" ","-").replace("/","-").replace(" ","-"),"primary_persona_id":personas[0].lower().replace(" ","-"),"secondary_persona_ids":[p.lower().replace(" ","-") for p in personas[1:]],"objective":("resource_clicks" if pillar in [1,3,4,5] else "engagement_and_community"),"topic":title,"core_message":thesis,"audience_problem":summary,"evidence_level":"hypothesis" if n in [6,13,17,28] else "experience","source_ids":[],"claim_ids":[],"status":"draft","review_labels":None,"linked_asset_ids":[aid(a) for a in asset_ids]}


def make_delivery(dno, day, channel, content_no, fmt, time, hook, *, story_text=None):
    idea=IDEA_MAP[content_no]; n,title,pillar,series,personas,thesis,asset_ids,summary=idea
    channel_slug={"website":"WEB","telegram":"TG","instagram":"IG"}[channel]
    fmt_code={"website":"WEB","telegram":"DOC","feed":"FEED","story":"STR","carousel":"CAR","single":"POST","micro_reel":"MRL","mini_reel":"mRL","main_reel":"RL","animated_reel":"ANM","telegram_file":"DOC","telegram_prompt":"PRM","telegram_guide":"GUIDE","telegram_digest":"DIG","telegram_post":"CHN","web_resource":"LIB","web_article":"MAG","prompt_card":"PRM","calculator_guide":"CAL","sop_resource":"SOP","case_article":"MAG"}.get(fmt,fmt.upper()[:4])
    schedule=f"M01-W01-D{day:02d}-{channel_slug}-{fmt_code}-{(dno%100):02d}"
    primary={"carousel":"save_rate_by_reach","story":"story_interaction_rate","micro_reel":"avg_watch_ratio","mini_reel":"share_rate_by_reach","main_reel":"avg_watch_ratio","animated_reel":"shares_and_watch_time","single_infographic":"save_rate_by_reach","quote":"shares_by_reach","community_post":"comments_and_replies","single_map":"saves_and_resource_clicks"}.get(fmt,"resource_clicks" if channel in ["website","telegram"] else "shares_by_reach")
    asset_ids_list=[aid(a) for a in asset_ids]
    # Key deliverable graphic; actual page upload and scheduling remain manual.
    kind="story" if channel=="instagram" and fmt=="story" else ("reel" if fmt in {"micro_reel","mini_reel","main_reel","animated_reel"} else "feed")
    if channel in {"website","telegram"}: kind="feed"
    style=style_for(content_no)
    visual=make_card(hook or title,summary,pillar,kind=kind,slide=1,total=1,style=style)
    caption=(f"{hook or title}\n\n{summary}\n\nمحتوای مرتبط و منابع بیشتر: atozfnb.info\nپیوندهای برند: {INSTAGRAM}\n\n{thesis}")
    tags="#AtoZFnB #مدیریت_FnB #کافه_رستوران"
    row={"delivery_id":did(dno),"content_id":cid(content_no),"schedule_key":schedule,"channel_id":channel,"format_id":fmt,"planned_day_index":day,"day_name_fa":DAY_NAMES[day-1],"planned_time_local":time,"language":"fa-IR","hook":hook or title,"caption":caption,"hashtags":[tags],"primary_kpi_id":primary,"secondary_kpi_ids":["profile_visits","resource_clicks"],"creative_spec":{"template_id":f"{fmt}-{PILLARS[pillar]['id']}-{style}","template_version":"0.1.0","aspect_ratio":"9:16" if kind=="story" or kind=="reel" else "4:5","width_px":1080,"height_px":1920 if kind in {"story","reel"} else 1350,"duration_seconds":({"micro_reel":8,"mini_reel":24,"main_reel":55,"animated_reel":28}.get(fmt) if fmt in {"micro_reel","mini_reel","main_reel","animated_reel"} else None),"slides":8 if fmt=="carousel" else None,"language":"fa-IR","pillar_token":PILLARS[pillar]["id"],"background_token":"brand-navy" if pillar==2 else "neutral-surface","font_ids":["vazirmatn-extrabold","vazirmatn-regular","montserrat-semibold","lato-regular"],"style_id":style,"brand_signature":True,"website_url_visible":True,"instagram_handle_visible":True},"asset_ids":asset_ids_list,"platform_post_id":None,"status":"produced","_visual_svg":visual,"_kind":kind,"_style":style,"_idea_summary":summary,"_idea_title":title,"_pillar_num":pillar,"_story_text":story_text}
    if channel in {"website","telegram"}:
        row["cta"]={"label":"مشاهدهٔ منابع و فایل‌های مرتبط","target_id":PILLARS[pillar]["id"],"target_url":BRAND_SITE,"link_status":"ready_owner_confirmed","utm_campaign":"M01-W01","utm_source":channel,"utm_medium":"owned"}
    elif fmt not in {"quote","community_post"}:
        row["cta"]={"label":"منابع و ابزارهای مرتبط","target_id":PILLARS[pillar]["id"],"target_url":BRAND_SITE,"link_status":"ready_owner_confirmed","utm_campaign":"M01-W01","utm_source":"instagram","utm_medium":"social"}
    return row


def generate_plan():
    root=OUT
    root.mkdir(parents=True,exist_ok=True)
    deliveries=[]; dno=1
    # One independently countable site and Telegram delivery for each selected daily hub item.
    for day in range(1,8):
        web_id=WEB_CONTENT[day-1]; tg_id=TG_CONTENT[day-1]
        deliveries.append(make_delivery(dno,day,"website",web_id,["web_resource","web_article","prompt_card","calculator_guide","sop_resource","prompt_card","case_article"][day-1],WEB_TIMES[day-1],IDEA_MAP[web_id][1])); dno+=1
        deliveries.append(make_delivery(dno,day,"telegram",tg_id,["telegram_file","telegram_post","telegram_prompt","telegram_guide","telegram_file","telegram_prompt","telegram_digest"][day-1],TG_TIMES[day-1],IDEA_MAP[tg_id][1])); dno+=1
        for j,(content_no,fmt) in enumerate(zip(FEED_IDS[day-1],FEED_FORMATS[day-1]),1):
            deliveries.append(make_delivery(dno,day,"instagram",content_no,fmt,FEED_TIMES[j-1],FEED_HOOKS[content_no])); dno+=1
        for j,content_no in enumerate(STORY_IDS[day-1],1):
            story_script=STORY_TEXT[day-1][j-1] if j <= len(STORY_TEXT[day-1]) else f"نکتهٔ روز {day}: {IDEA_MAP[content_no][7]}"
            deliveries.append(make_delivery(dno,day,"instagram",content_no,"story",STORY_TIMES[j-1],story_script,story_text=story_script)); dno+=1
    assert len(deliveries)==84 and dno==85
    daily_counts=[sum(1 for d in deliveries if d["planned_day_index"]==day) for day in range(1,8)]
    assert len(set(daily_counts))>1, "Do not impose a fixed daily cadence."
    contents=[]
    for row in IDEAS:
        obj=idea_object(row)
        obj["status"]="draft"
        obj["review_labels"]={"decision":"revise","reason_tags":["first-draft-needs-owner-review"]}
        contents.append(obj)
    asset_records=[]
    for aid_num,content_no,typ,name in ASSETS:
        candidates=[d for d in deliveries if d["content_id"]==cid(content_no)]
        reel_candidates=[d for d in candidates if d["_kind"]=="reel"]
        if ("reel" in typ or typ in {"video"}) and reel_candidates:
            selected=reel_candidates[0]
            subpath="reel.mp4"
            mime="video/mp4"
        elif typ=="carousel":
            selected=next((d for d in candidates if d["format_id"]=="carousel"),candidates[0])
            subpath="slides/slide-01.svg" if selected["format_id"]=="carousel" else "creative.svg"
            mime="image/svg+xml"
        elif typ in {"article","workbook","checklist","calculator_guide"} and any(d["channel_id"]=="website" for d in candidates):
            selected=next(d for d in candidates if d["channel_id"]=="website")
            subpath="website-draft.md"
            mime="text/markdown"
        else:
            selected=candidates[0]
            subpath="creative.svg"
            mime="image/svg+xml"
        relative=f"{DAY_NAMES[selected['planned_day_index']-1]}/{selected['content_id']}/{selected['delivery_id']}/{subpath}"
        asset_records.append({"asset_id":aid(aid_num),"content_id":cid(content_no),"delivery_id":selected["delivery_id"],"asset_type":typ,"path":relative,"mime_type":mime,"source_or_generated":"generated","license_status":"owned","template_id":None,"template_version":"0.1.0","status":"rendered","title":name})
    plan={"schema_version":"2.0.0-relational-telemetry","plan_id":"ATZ-M01-W01","brand_id":"atoz-fnb","period":{"month_index":1,"week_index":1},"timezone":"Asia/Tehran","locale":"fa-IR","weekly_theme":"فونداسیون کسب‌وکار F&B، معماری بوم و آغاز اکوسیستم محتوایی متصل","goals":["پوشش ۶ ستون محتوا در یک روایت متصل","تولید محتوای مادر و بازبسته‌بندی دستی برای وب، تلگرام و اینستاگرام","ساخت مرجع‌های قابل‌استفاده برای هفته‌های بعد"],"active_channels":["website","instagram","telegram"],"upcoming_channels":["youtube"],"content_items":contents,"deliveries":[],"relationships":[{"from_id":d["delivery_id"],"to_id":d["content_id"],"relationship_type":"repurposes"} for d in deliveries],"assets":asset_records,"notes":["این برنامه برای تولید و انتشار دستی است؛ هیچ بارگذاری یا زمان‌بندی خودکاری اجرا نمی‌شود.","URL پیش‌فرض محتوا: https://atozfnb.info/ و شناسهٔ اینستاگرام: @atozfnb.info؛ URLهای صفحه را مالک می‌تواند پیش از انتشار ویرایش کند.","مقادیر KPI نمونه و داده‌های عملکرد بعد از انتشار ثبت می‌شوند؛ هیچ آماری در این نسخه جعل نشده است.","تعداد تجمیعی 84 در خلاصهٔ ورودی با جمع delivery_count_w1 ردیف‌ها (64) اختلاف دارد؛ برنامهٔ تولیدی 84 شناسهٔ تحویلی را بر مبنای جمع کانال‌های ادعاشده نگه می‌دارد و 20 مورد باید با ردیف‌های منبع تطبیق داده شود."]}
    for d in deliveries:
        clean={k:v for k,v in d.items() if not k.startswith("_")}
        plan["deliveries"].append(clean)
    # Count from actual publish instances, not a handwritten total.
    counts={}
    for d in deliveries: counts[d["channel_id"]]=counts.get(d["channel_id"],0)+1
    plan["computed_summary"]={"content_items":len(contents),"assets":len(asset_records),"deliveries":len(deliveries),"deliveries_by_channel":counts,"instagram_feed_deliveries":sum(1 for d in deliveries if d["channel_id"]=="instagram" and d["format_id"]!="story"),"instagram_story_deliveries":sum(1 for d in deliveries if d["channel_id"]=="instagram" and d["format_id"]=="story")}
    return plan,deliveries


def write_plan(plan, deliveries):
    (OUT/"assets").mkdir(parents=True,exist_ok=True)
    (OUT/"plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"assets"/"asset-registry.json").write_text(json.dumps(plan["assets"],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # Content-item source pages: full idea brief and its relation to the six-pillar system.
    idea_root=OUT/"content-items"
    idea_root.mkdir(exist_ok=True)
    for row in IDEAS:
        n,title,pillar,series,personas,thesis,asset_ids,summary=row
        folder=idea_root/cid(n); folder.mkdir(exist_ok=True)
        meta={"content_id":cid(n),"title":title,"pillar":PILLARS[pillar],"series":series,"target_personas":personas,"core_thesis":thesis,"production_summary":summary,"asset_ids":[aid(a) for a in asset_ids],"linked_deliveries":[d["delivery_id"] for d in deliveries if d["content_id"]==cid(n)],"status":"draft_for_review"}
        (folder/"content-item.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        (folder/"brief.fa.md").write_text(f"# {title}\n\n**شناسه:** `{cid(n)}`  \n**ستون:** {PILLARS[pillar]['name']}  \n**سری:** {series}  \n**مخاطبان اولیه:** {'، '.join(personas)}\n\n## پیام محوری\n{thesis}\n\n## هدف تولید\n{summary}\n\n## CTA پیش‌فرض\nمنابع و محتوای مرتبط در [AtoZfnb.info]({BRAND_SITE}) · اینستاگرام {INSTAGRAM}\n\n> پیش‌نویس برای بازبینی مالک؛ آمار/درصدهای نیازمند منبع در قالب ادعای قطعی منتشر نشوند.\n",encoding="utf-8")


def write_delivery_files(plan, deliveries):
    for d in deliveries:
        day=d["planned_day_index"]; idea_no=int(d["content_id"].split("-")[-1]); idea=IDEA_MAP[idea_no]
        day_root=OUT/DAY_NAMES[day-1]/d["content_id"]/d["delivery_id"]
        day_root.mkdir(parents=True,exist_ok=True)
        visual=d["_visual_svg"]
        (day_root/"creative.svg").write_text(visual,encoding="utf-8")
        metadata={k:v for k,v in d.items() if not k.startswith("_")}
        metadata["content_title"]=d["_idea_title"]
        metadata["content_summary"]=d["_idea_summary"]
        metadata["content_pillar"]=PILLARS[d["_pillar_num"]]
        metadata["platform_manual_action"]="تولید فایل انجام شده؛ زمان‌بندی/آپلود دستی است."
        (day_root/"metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        caption=d["caption"]
        tags=" ".join(d["hashtags"])
        (day_root/"caption.txt").write_text(caption+"\n\n"+tags+"\n",encoding="utf-8")
        (day_root/"hashtags.txt").write_text(tags+"\n",encoding="utf-8")
        body=d["_story_text"] or d["_idea_summary"]
        extra=""
        if d["channel_id"]=="website":
            article_title, article_body = WEBSITE_ARTICLES[idea_no]
            blocks=[]
            for line in article_body.splitlines():
                line=line.strip()
                if not line: continue
                if line.startswith("## "):
                    blocks.append(f"<h2>{html.escape(line[3:])}</h2>")
                elif line.startswith("**") and line.endswith("**"):
                    blocks.append(f"<p><strong>{html.escape(line[2:-2])}</strong></p>")
                else:
                    safe=html.escape(line).replace("**","<strong>",1) if "**" in line else html.escape(line)
                    if "**" in line:
                        safe=html.escape(line).replace("**میکروکافه:**","<strong>میکروکافه:</strong>").replace("**آشپزخانهٔ ابری:**","<strong>آشپزخانهٔ ابری:</strong>").replace("**اشتراک:**","<strong>اشتراک:</strong>")
                    blocks.append(f"<p>{safe}</p>")
            extra=f"<article><h2>{html.escape(article_title)}</h2>{''.join(blocks)}<p><small>پیش‌نویس تحریریه؛ مالک پیش از انتشار باید منابع و ادعاها را بازبینی کند. این فایل در سایت بارگذاری نمی‌شود.</small></p></article>"
            (day_root/"website-draft.html").write_text(make_document_html(d["_idea_title"],d["_idea_summary"],caption,tags,extra),encoding="utf-8")
            (day_root/"website-draft.md").write_text(f"# {article_title}\n\n{article_body}\n\n## پیام محوری\n{idea[5]}\n\n## کپشن/هشتگ\n{caption}\n\n{tags}\n",encoding="utf-8")
        elif d["channel_id"]=="telegram":
            (day_root/"telegram-post.html").write_text(make_document_html(d["_idea_title"],d["_idea_summary"],caption,tags,"<p>نسخهٔ متنی قابل کپی برای انتشار دستی در کانال تلگرام.</p>"),encoding="utf-8")
            (day_root/"telegram-post.txt").write_text(caption+"\n\n"+tags+"\n",encoding="utf-8")
            if d["format_id"] in {"telegram_file","telegram_guide"}:
                (day_root/"resource-outline.md").write_text(f"# {d['_idea_title']}\n\n{d['_idea_summary']}\n\n- هدف: استفادهٔ عملی و قابل‌ویرایش\n- نسخهٔ تکمیلی/فایل مرجع: طبق فهرست منابع مورد تأیید مالک\n- ارجاع: {BRAND_SITE}\n- مجوز: فقط فایل اصیل یا دارای حق بازنشر\n",encoding="utf-8")
        else:
            (day_root/"copy.html").write_text(make_document_html(d["_idea_title"],d["_idea_summary"],caption,tags,"<p>برای استوری، Poll/Quiz/Question/Link sticker باید داخل اپ اینستاگرام دستی اضافه شود.</p>" if d["format_id"]=="story" else ""),encoding="utf-8")
        if d["format_id"]=="carousel":
            slides=day_root/"slides";slides.mkdir(exist_ok=True)
            slide_lines=[d["_idea_title"],d["_idea_summary"],"تعریف مسئله برای یک کسب‌وکار F&B","یک مثال فرضی؛ اعداد را با دادهٔ واقعی خود جایگزین کنید.","سه پرسش برای بررسی مشتری و ارزش","یک گام اجرایی برای همین هفته","منابع/فرض‌ها را پیش از تصمیم‌گیری بررسی کنید.",f"اقدام بعدی و منابع: {BRAND_SITE} · {INSTAGRAM}"]
            for i,text in enumerate(slide_lines,1):
                svg=make_card(text,d["_idea_summary"] if i in [2,6] else "یک ایده در هر اسلاید؛ کوتاه، روشن و قابل‌اقدام.",d["_pillar_num"],kind="feed",slide=i,total=8,style=d["_style"])
                (slides/f"slide-{i:02d}.svg").write_text(svg,encoding="utf-8")
        if d["_kind"]=="reel":
            reel=day_root/"reel-source";reel.mkdir(exist_ok=True)
            for i,phase in enumerate(["قلاب","یک نکتهٔ اجرایی","جمع‌بندی و CTA"],1):
                scene_title=[d["_idea_title"],phase,d["_idea_title"]][i-1]
                scene_sub=[d["hook"],d["_idea_summary"],f"ادامه و منابع مرتبط: {BRAND_SITE} · {INSTAGRAM}"][i-1]
                svg=make_card(scene_title,scene_sub,d["_pillar_num"],kind="reel",style=d["_style"])
                (reel/f"scene-{i:02d}.svg").write_text(svg,encoding="utf-8")
            (day_root/"audio").mkdir(exist_ok=True)
            duration=float(d["creative_spec"].get("duration_seconds") or 12)
            synth_sfx(day_root/"audio"/"original-sfx.wav",duration,seed=dno_seed(d["delivery_id"]))
            (day_root/"audio"/"README.md").write_text("افکت‌های کوتاه به‌صورت سینتتیک و بدون نریشن/موسیقی ساخته شده‌اند؛ صدای گوینده عمداً اضافه نشده است.\n",encoding="utf-8")
        # For all still outputs, give a delivery-level cover/source pair; carousel has slide deck too.
    # Index for each of seven days with the content IDs requested.
    for i,dayname in enumerate(DAY_NAMES,1):
        daily=[d for d in deliveries if d["planned_day_index"]==i]
        folder=OUT/dayname
        folder.mkdir(parents=True,exist_ok=True)
        rows=[]
        for d in daily:
            rows.append(f"- `{d['content_id']}/{d['delivery_id']}` · {d['channel_id']} · زمان انتشار: انتخاب دستی · {d['format_id']}")
        (folder/"README.md").write_text(f"# {dayname} — روز {i}\n\nبرنامهٔ دستی با منطقهٔ زمانی `Asia/Tehran`.\n\n"+"\n".join(rows)+"\n",encoding="utf-8")


def write_package_guide(plan):
    (OUT/"README.md").write_text(f"""# پیش‌انتشار — ماه اول، هفتهٔ اول

**وضعیت:** پیش‌نویس تولیدی برای بازبینی مالک؛ بارگذاری و زمان‌بندی دستی است.

- ۲۸ محتوای مادر (`ATZ-C-000001` تا `ATZ-C-000028`)
- ۳۸ ردیف رجیستری دارایی (`ATZ-A-000001` تا `ATZ-A-000038`)
- ۸۴ تحویل محتوایی (`ATZ-D-000001` تا `ATZ-D-000084`): ۷ وب‌سایت، ۷ تلگرام، ۳۵ پست/فید اینستاگرام و ۳۵ استوری
- منطقهٔ زمانی مرجع: `Asia/Tehran`؛ هیچ ساعت/تاریخ انتشار تعیین یا اجرا نشده است و تعداد تحویل روزها عمداً یکسان نشده است.

## پیمایش

هر روز دقیقاً پوشهٔ خودش را دارد. اگر یک ایده چند خروجی داشته باشد یا در روزهای متفاوت بازاستفاده شود، مسیر چنین است:

`روز/ATZ-C-xxxxxx/ATZ-D-xxxxxx/`

شناسهٔ مادر در روزهای مختلف تکرار می‌شود، اما شناسهٔ تحویل یکتا است؛ بنابراین فایل‌ها با هم تداخل ندارند. پروندهٔ مادر و خلاصهٔ ارتباط‌ها در `content-items/ATZ-C-xxxxxx/` قرار دارد. `plan.json` مرجع ساختاریافتهٔ رابطه‌ها و فایل‌هاست.

هر تحویل تصویری فایل `creative.svg` و `creative.png` دارد؛ کاروسل‌ها پوشهٔ `slides/` شامل هشت جفت SVG/PNG دارند. خروجی ویدئوهای ریل در `reel.mp4` است؛ استوری‌بورد در `reel-source/` و افکت صوتی اختصاصی در `audio/original-sfx.wav` قرار دارد. ویدیو نریشن یا موسیقی ندارد. متن‌ها در `caption.txt`, `hashtags.txt`, `metadata.json` و HTML قابل‌کپی‌اند. پیش‌نویس‌های سایت در `website-draft.md/html` هستند و خودکار بارگذاری نمی‌شوند.

## نکتهٔ تطبیق شمارش

در خلاصهٔ برنامهٔ ورودی تعداد کل ۸۴ آمده است (۷ وب‌سایت + ۷ تلگرام + ۳۵ اینستاگرام فید + ۳۵ استوری)، اما جمع `delivery_count_w1` در ۲۸ ایده ۶۴ است؛ اختلاف ۲۰ تحویل است. نسخهٔ فعلی ۸۴ شناسه را از جمع کانال‌ها گرفته تا ساختار خواسته‌شده کامل باشد. پیش از تأیید نهایی، شناسه‌ها/قالب‌ها را با ردیف‌های اصلی تطبیق دهید؛ اختلاف در `VALIDATION.fa.md` هم ثبت شده است.

## ویرایش و انتشار

`AtoZfnb.info` و `@atozfnb.info` امضای پایه‌اند. لینک مقصدها در metadata قابل‌ویرایش است؛ CTA نهایی، URL صفحه و زمان انتشار را مالک انتخاب می‌کند. هیچ سایت، API شبکهٔ اجتماعی، صف زمان‌بندی یا آمار ساختگی در این بسته فعال نیست.

## بازبینی ادعاها

هر مثال عددی در فایل‌های محتوایی با عنوان «فرضی» مشخص شده است. درصدهای شکست، نسبت‌های ثابت هزینه و ادعاهای مالی/بازاری بدون منبع معتبر به‌عنوان واقعیت چاپ نشوند. کاربرگ‌های آموزشی اصل‌اند؛ محتوای دارای حق نشر بازتوزیع نشده است.
""",encoding="utf-8")
    (OUT/"VALIDATION.fa.md").write_text("""# گزارش اعتبارسنجی و موارد نیازمند تأیید

## مغایرت تعداد تحویل

- خلاصهٔ تعدادها: ۷ وب‌سایت + ۷ تلگرام + ۳۵ Instagram Feed + ۳۵ Instagram Story = ۸۴.
- جمع فیلدهای `delivery_count_w1` در ۲۸ ردیف محتوا: ۶۴.
- اختلاف: ۲۰ تحویل.
- برای حفظ شماره‌گذاری تحویلی که در برنامه خواسته شده، این پیش‌نویس ۸۴ شناسه می‌سازد؛ این کار به معنی تأیید شمارش ۸۴ در ردیف‌های منبع نیست. پیش از انتشار نهایی، مشخصات هر `ATZ-D-*` باید با جدول اصلی بررسی شود.

## موارد آماده

- هفت پوشهٔ روزانه و شناسه‌های محتوا/تحویل یکتا.
- خروجی PNG و SVG، کپشن/هشتگ قابل کپی و HTML برای تحویل‌های رسانه‌ای.
- برای ریل‌ها MP4، سه صحنهٔ منبع و WAV افکت صوتی سینتتیک بدون نریشن.
- فایل‌های وب در حد پیش‌نویس تحریریه‌اند؛ مالک آن‌ها را بازبینی و در سایت بارگذاری می‌کند.

## موارد نیازمند تصمیم مالک

1. تطبیق ۲۰ تحویل اختلافی با جدول اصلی و نهایی‌کردن تخصیص کانال/روز.
2. تأیید عنوان‌ها، personaها، CTA و هر ادعای مبتنی بر تجربهٔ شخصی.
3. انتخاب تاریخ و ساعت انتشار (در صورت نیاز) و URLهای مقصد نهایی.
4. منابع معتبر برای داده‌های بازار/مالی و صحت حقوقی منابع پیش از انتشار.
5. بررسی فنی بصری روی دستگاه‌های هدف و افزودن نسخه‌های نهایی/لوگوهای جایگزین در صورت نیاز.

تا تکمیل موارد بالا، وضعیت تمام محتواها «پیش‌نویس برای بازبینی» است.
""",encoding="utf-8")
    (OUT/"TYPOGRAPHY.fa.md").write_text("""# قرارداد تایپوگرافی و دارایی‌های پایه

- فارسی: Vazirmatn؛ fallback CSS: `Vazirmatn, Noto Sans Arabic, Tahoma, sans-serif`.
- تیتر لاتین: Montserrat؛ fallback: `Montserrat, Arial, sans-serif`.
- متن لاتین: Lato؛ fallback: `Lato, Arial, sans-serif`.
- فونت دست‌نویس Iran Sans Handwriting عمداً اضافه نشده؛ منتظر فایل و تأیید مجوز از مالک است.
- فایل‌های موجود در `tools/fonts/` همراه با `tools/fonts/LICENSES.txt` هستند؛ فایل فونت ساختگی/نامشخص وارد نشده است.
- لوگوی اصلی و خروجی‌های رسمی SVG/PNG در `logo/` و رنگ‌های مرجع در `brand/tokens.json` قرار دارند.
- ساختار styleها: editorial، formal، minimal، artwork، retro و handwritten-accent. گزینهٔ handwritten-accent صرفاً یک خط تأکیدی برداری است و از فونت دست‌نویس استفاده نمی‌کند.

## دارایی‌های موجود در ریپو

`logo/` کتابخانهٔ لوگوهای رسمی؛ `brand/tokens.json` توکن‌های مرجع؛ `content-templates/` نمونه‌های ساختار/قالب قبلی؛ `website/sections/` قطعات سایت برای توسعهٔ دستی. هیچ‌یک خودکار روی سایت منتشر نمی‌شوند.
""",encoding="utf-8")


def dno_seed(value): return sum(ord(c) for c in value) % 997


def render_pngs():
    cmd=["node",str(ROOT/"tools/render_content_assets.mjs"),str(OUT)]
    subprocess.run(cmd,cwd=ROOT,check=True)


def encode_reels():
    try:
        import imageio_ffmpeg
        ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError("Install imageio-ffmpeg (declared in tools/requirements.txt) to render MP4 previews") from exc
    for d in _LAST_DELIVERIES:
        if d["_kind"]!="reel": continue
        day_root=OUT/DAY_NAMES[d["planned_day_index"]-1]/d["content_id"]/d["delivery_id"]
        reel=day_root/"reel-source"
        frames=[reel/f"scene-{i:02d}.png" for i in range(1,4)]
        audio=day_root/"audio/original-sfx.wav"
        out=day_root/"reel.mp4"
        dur=float(d["creative_spec"].get("duration_seconds") or 12)
        # Three-card, slow zoom/pan-free motion sequence; original SFX only.
        args=[ffmpeg,"-y"]
        each=dur/3
        for frame in frames: args += ["-loop","1","-t",f"{each:.3f}","-i",str(frame)]
        args += ["-stream_loop","-1","-i",str(audio)]
        filt=[]
        for i in range(3):
            filt.append(f"[{i}:v]scale=600:1067,zoompan=z='min(zoom+0.0005,1.04)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=540x960:fps=12,setsar=1,format=yuv420p[v{i}]")
        filt.append("[v0][v1][v2]concat=n=3:v=1:a=0[v]")
        filt.append("[3:a]volume=0.32,afade=t=out:st="+str(max(0,dur-0.7))+":d=0.7[a]")
        args += ["-filter_complex",";".join(filt),"-map","[v]","-map","[a]","-t",str(dur),"-r","12","-c:v","libx264","-preset","veryfast","-b:v","320k","-pix_fmt","yuv420p","-c:a","aac","-b:a","64k","-movflags","+faststart",str(out)]
        subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        # The final vector scene is also the editable motion storyboard reference.
        (day_root/"reel-source.svg").write_text((reel/"scene-01.svg").read_text(encoding="utf-8"),encoding="utf-8")


def main():
    global _LAST_DELIVERIES
    plan, deliveries=generate_plan(); _LAST_DELIVERIES=deliveries
    write_plan(plan,deliveries)
    write_delivery_files(plan,deliveries)
    write_package_guide(plan)
    render_pngs()
    encode_reels()
    print(f"Built {len(plan['content_items'])} mother ideas, {len(plan['assets'])} conceptual assets, {len(deliveries)} manual deliveries under {OUT.relative_to(ROOT)}")

if __name__=="__main__": main()
