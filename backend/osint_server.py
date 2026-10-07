#!/usr/bin/env python3
import http.server
import json
import os
import re
import socketserver
import threading
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

PORT = 8890
DATA_FILE = os.environ.get("OSINT_DATA_FILE", os.path.join(os.path.dirname(__file__), "..", "data", "events.json"))

DEFAULT_EVENTS = [
    {
        "id": "evt-01",
        "title": "آماده‌باش حداکثری سامانه‌های باور-۳۷۳ و سامانه سوم خرداد در مرکز کشور",
        "category": "airdefense",
        "severity": "ops",
        "region": "iran",
        "location": "اصفهان، پایگاه هشتم شکاری و تاسیسات هسته‌ای",
        "lat": 32.7500,
        "lng": 51.8600,
        "time": "۱۸ دقیقه پیش",
        "hoursAgo": 0.3,
        "summary": "افزایش سطح هوشیاری یگان‌های پدافندی ارتش و سپاه در شعاع ۲۰۰ کیلومتری اصفهان و رصد مستمر کریدورهای غرب کشور با رادارهای کشف افق.",
        "weapon": "باور-۳۷۳ / سوم خرداد",
        "source": "دیده‌بان‌های راداری و منابع محلی",
        "isHot": True
    },
    {
        "id": "evt-02",
        "title": "فعال‌سازی آژیرهای هشدار در منطقه دان و پایگاه اطلاعاتی گالیلوت",
        "category": "alert",
        "severity": "crit",
        "region": "israel",
        "location": "تل‌آویو، مقر گالیلوت و تل‌آویو بزرگ",
        "lat": 32.1450,
        "lng": 34.8050,
        "time": "۲۸ دقیقه پیش",
        "hoursAgo": 0.5,
        "summary": "به صدا درآمدن آژیر خطر در شمال تل‌آویو پس از رصد ورود پرتابه‌های ناشناس از سمت شمال؛ سامانه‌های فلاخن داوود و پیکان فعال شدند.",
        "weapon": "پیکان ۳ / فلاخن داوود",
        "source": "سامانه رسمی پیک جبهه داخلی",
        "isHot": True
    },
    {
        "id": "evt-03",
        "title": "پرواز گشت‌های شناسایی پهپادهای هرمس ۹۰۰ بر فراز آسمان بیروت",
        "category": "aviation",
        "severity": "warn",
        "region": "lebanon",
        "location": "بیروت، حریم هوایی ضاحیه جنوبی",
        "lat": 33.8500,
        "lng": 35.5000,
        "time": "۴۲ دقیقه پیش",
        "hoursAgo": 0.7,
        "summary": "پرواز مداوم پرنده‌های بدون سرنشین شناسایی ارتش اسرائیل در ارتفاع متوسط و تصویربرداری الکترواپتیکال از مناطق جنوبی پایتخت لبنان.",
        "weapon": "Hermes 900 UAV",
        "source": "گزارش‌های ناوبری هوایی بیروت",
        "isHot": False
    },
    {
        "id": "evt-04",
        "title": "گزارش حادثه امنیتی دریایی UKMTO در ۶۵ مایلی بندر الحدیده",
        "category": "naval",
        "severity": "crit",
        "region": "yemen",
        "location": "دریای سرخ، جنوب غرب بندر الحدیده",
        "lat": 14.7900,
        "lng": 42.9500,
        "time": "۱ ساعت پیش",
        "hoursAgo": 1.0,
        "summary": "سازمان عملیات تجارت دریایی بریتانیا از حمله دو فروند شناور تندرو انتحاری و شلیک پرتابه ضدکشتی به یک تانکر عبوری در تنگه باب‌المندب خبر داد.",
        "weapon": "موشک ضدکشتی صیاد / قایق بدون سرنشین",
        "source": "UKMTO Maritime Advisory",
        "isHot": True
    },
    {
        "id": "evt-05",
        "title": "رهگیری پهپاد انتحاری بر فراز بندر و خلیج حیفا توسط گنبد آهنین",
        "category": "missile",
        "severity": "crit",
        "region": "israel",
        "location": "حیفا، بندرگاه و حریم دریایی",
        "lat": 32.8190,
        "lng": 34.9980,
        "time": "۱ ساعت و ۱۵ دقیقه پیش",
        "hoursAgo": 1.25,
        "summary": "شلیک دو تیر موشک تمیر از سامانه گنبد آهنین به سمت یک ریزپرنده انتحاری نفوذی که از خاک لبنان به سمت لنگرگاه و پالایشگاه حیفا پرواز کرده بود.",
        "weapon": "گنبد آهنین (Tamir)",
        "source": "رسانه‌های محلی و تصاویر شاهدان",
        "isHot": False
    },
    {
        "id": "evt-06",
        "title": "رصد پروازهای فشرده سوخت‌رسان KC-135 و جنگنده‌های ائتلاف در التنف",
        "category": "aviation",
        "severity": "ops",
        "region": "syria_iraq",
        "location": "مرز سوریه-اردن-عراق، پایگاه التنف",
        "lat": 33.4300,
        "lng": 38.8300,
        "time": "۲ ساعت پیش",
        "hoursAgo": 2.0,
        "summary": "فعالیت سنگین راداری و پشتیبانی هوایی سوخت‌رسان‌های آمریکایی در کریدور بیابانی بادیه الشام و مرز غربی استان الانبار عراق.",
        "weapon": "Boeing KC-135 Stratotanker",
        "source": "داده‌های فلایت رادار ADS-B Exchange",
        "isHot": False
    },
    {
        "id": "evt-07",
        "title": "رزمایش پدافند ساحلی و موشک‌های کروز قدیر در تنگه هرمز",
        "category": "naval",
        "severity": "ops",
        "region": "iran",
        "location": "بندرعباس، جزیره قشم و تنگه هرمز",
        "lat": 27.1500,
        "lng": 56.2800,
        "time": "۲ ساعت و ۴۰ دقیقه پیش",
        "hoursAgo": 2.6,
        "summary": "استقرار پرتابگرهای متحرک موشک‌های کروز ساحل به دریای قدیر و پایش الکترونیکی خروج ناوگروه رزمی خارجی توسط پهپادهای ابابیل ۵.",
        "weapon": "کروز دریایی قدیر / پهپاد ابابیل",
        "source": "قرارگاه نیروی دریایی",
        "isHot": False
    },
    {
        "id": "evt-08",
        "title": "استقرار اسکادران جدید جنگنده‌های F-35I آدور در پایگاه نواتیم",
        "category": "aviation",
        "severity": "diplo",
        "region": "israel",
        "location": "صحرای نقب، پایگاه هوایی نواتیم",
        "lat": 31.2080,
        "lng": 35.0120,
        "time": "۳ ساعت پیش",
        "hoursAgo": 3.0,
        "summary": "تصاویر ماهواره‌ای نشان‌دهنده افزایش حضور و آماده‌باش جنگنده‌های نسل پنجم F-35 در آشیانه‌های مستحکم پایگاه نواتیم در جنوب اراضی اشغالی است.",
        "weapon": "F-35I Adir Stealth Fighter",
        "source": "تصاویر ماهواره‌ای Planet Labs",
        "isHot": False
    },
    {
        "id": "evt-09",
        "title": "فعالیت پدافند موشکی پانتسیر در جنوب غربی دمشق",
        "category": "airdefense",
        "severity": "warn",
        "region": "syria_iraq",
        "location": "دمشق، منطقه الکسوه و جبل المانع",
        "lat": 33.3600,
        "lng": 36.2400,
        "time": "۳ ساعت و ۳۰ دقیقه پیش",
        "hoursAgo": 3.5,
        "summary": "مقابله پدافند ارتش سوریه با اهداف متخاصم هوایی در آسمان ریف جنوبی دمشق و شنیده شدن صدای چند انفجار پیاپی.",
        "weapon": "سامانه پانتسیر-اس۱ (Pantsir-S1)",
        "source": "خبرگزاری رسمی سانا",
        "isHot": False
    },
    {
        "id": "evt-10",
        "title": "پایش پایداری درگاه‌های اینترنت و رصد ترانزیت داده (رادار Cloudflare / IODA)",
        "category": "cyber",
        "severity": "ops",
        "region": "iran",
        "location": "تهران، هاب مخابراتی LCT و دیتاسنترهای ملی",
        "lat": 35.7150,
        "lng": 51.4050,
        "time": "۱۵ دقیقه پیش",
        "hoursAgo": 0.25,
        "summary": "داده‌های زنده Cloudflare Radar و مرکز پایش IODA نشان‌دهنده پایداری ۹۸.۴ درصدی ترافیک، جریان بدون اختلال ترانزیت درگاه‌های جنوب و غرب و آماده‌باش تیم‌های دفاع سایبری است.",
        "weapon": "سپر دفاع سایبری دژفا / مانیتورینگ BGP",
        "source": "رادار Iran Monitor / IODA NetBlocks",
        "isHot": True
    },
    {
        "id": "evt-11",
        "title": "پایش هوایی-دریایی نفتکش‌های انرژی و کریدورهای صادراتی تنگه هرمز",
        "category": "naval",
        "severity": "ops",
        "region": "iran",
        "location": "تنگه هرمز، آبراه ورودی به دریای عمان",
        "lat": 26.5500,
        "lng": 56.4500,
        "time": "۴۵ دقیقه پیش",
        "hoursAgo": 0.75,
        "summary": "گشت‌های مستمر شناورهای کلاس شهید سلیمانی و پهپادهای شناسایی در طول خطوط کشتیرانی بین‌المللی؛ شاخص پرمیوم ریسک بیمه نفتکش‌ها در وضعیت پایدار رصد می‌شود.",
        "weapon": "شناور گشتی رزمی / رادارهای سطحی ساحلی",
        "source": "داده‌های AIS MarineTraffic و دیده‌بان هرمز",
        "isHot": False
    },
    {
        "id": "evt-12",
        "title": "ثبت امواج تداخل جنگ الکترونیک و اسپوفینگ GPS در کریدورهای هوایی منطقه",
        "category": "airdefense",
        "severity": "warn",
        "region": "israel",
        "location": "مدیترانه شرقی، حریم هوایی حیفا و قبرس",
        "lat": 33.1500,
        "lng": 34.2000,
        "time": "۱ ساعت و ۴۰ دقیقه پیش",
        "hoursAgo": 1.6,
        "summary": "هشدار ناوبری سازمان ایمنی هوانوردی در خصوص ثبت نوسانات شدید سیگنال‌های موقعیت‌یاب ماهواره‌ای GPS در لایه‌های پروازی ۳۰ تا ۴۰ هزار پا بر فراز شرق مدیترانه.",
        "weapon": "سامانه‌های اخلالگر رادیویی و جنگال",
        "source": "اطلاعیه هوانوردی NOTAM بین‌المللی",
        "isHot": False
    }
]

def load_events():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception as e:
            print("Error loading events.json:", e)
    return DEFAULT_EVENTS

def save_events(events):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving events.json:", e)

# REAL-TIME WIRE FEED FETCHER
LIVE_WIRE = [
    {"source": "Al Jazeera War Wire", "title": "هشدار پدافند هوایی در مرزهای شمالی پس از رصد تحرکات پهپادی", "time": "چند لحظه پیش", "tag": "فوری"},
    {"source": "Reuters Defense", "title": "افزایش پروازهای شناسایی نیروهای ائتلاف در شرق فرات و حریم هوایی عراق", "time": "۵ دقیقه پیش", "tag": "هوایی"},
    {"source": "UKMTO Maritime", "title": "توصیه امنیتی به کشتی‌های تجاری در خلیج عدن و تنگه باب‌المندب", "time": "۱۴ دقیقه پیش", "tag": "دریایی"},
    {"source": "OSINT Telegram Digest", "title": "فعالیت سامانه‌های راداری دوربرد قدیر در مناطق جنوب غربی کشور", "time": "۲۲ دقیقه پیش", "tag": "پدافند"}
]


# IRAN MONITOR OSINT PULSE DATA ENGINE
IRAN_MONITOR_DATA = {
    "daily_briefing": {
        "title": "بولتن راهبردی و ارزیابی ریسک بحران (AI Daily Crisis Briefing)",
        "threat_level": "DEFCON 2 / سطح هوشیاری بالا",
        "threat_score": 82,
        "summary": "تشدید آمادگی عملیاتی یگان‌های پدافندی ارتش و سپاه در مرکز و غرب کشور در واکنش به پروازهای فشرده شناسایی و سوخت‌رسانی ائتلاف در مرزهای شرقی سوریه و عراق. تردد تانکرهای انرژی در تنگه هرمز تحت اسکورت هوایی-دریایی جریان دارد و نشانه‌هایی از تحرکات دیپلماتیک غیرمستقیم در مسقط برای مدیریت تنش مخابره شده است.",
        "key_takeaways": [
            "آماده‌باش سامانه‌های پدافندی باور-۳۷۳ و سوم خرداد در شعاع پایگاه‌های مرکزی و هسته‌ای",
            "افزایش گشت‌های هوایی سوخت‌رسان KC-135 و پرنده‌های بدون سرنشین در پایگاه التنف و شرق فرات",
            "پایداری و عبور امن خطوط دریانوردی تجاری در تنگه هرمز با حضور گشت‌های ناوبری سپاه",
            "پایش و رصد مداوم درگاه‌های اینترنت بین‌الملل و زیرساخت‌های مخابراتی جهت پیشگیری از حملات سایبری"
        ],
        "updated_at": "به‌روزرسانی خودکار زنده"
    },
    "activity_markets": {
        "news_volume": {
            "articles_24h": 4180,
            "change_pct": "+19.4%",
            "tracked_sources": 54,
            "sentiment_crisis": "76%",
            "label": "حجم انتشار اخبار جنگ"
        },
        "twitter_activity": {
            "mentions_24h": "188.4K",
            "change_pct": "+31.2%",
            "top_hashtags": ["#Iran", "#Israel", "#IRGC", "#Hormuz", "#MiddleEastCrisis"],
            "label": "فعالیت توییتر / X"
        },
        "net_connectivity": {
            "overall_status": "پایدار و عادی",
            "score": "98.4%",
            "nin_traffic": "99.8%",
            "global_transit": "94.5%",
            "provider": "Cloudflare Radar / IODA",
            "label": "رصد پایداری اینترنت ایران"
        },
        "crude_oil_energy": {
            "brent": 77.65,
            "brent_change": "+2.24%",
            "wti": 73.90,
            "wti_change": "+1.95%",
            "natural_gas_ttf": 39.85,
            "risk_premium": "بالا (تنش ژئوپلیتیک)",
            "label": "شاخص نفت و انرژی"
        }
    },
    "live_tv_channels": [
        {
            "id": "aljazeera_en",
            "name": "Al Jazeera English Live",
            "badge": "بین‌المللی",
            "desc": "پوشش زنده و ۲۴ ساعته بحران خاورمیانه و تحولات نظامی",
            "embed_url": "https://www.youtube-nocookie.com/embed/gCNeDWCI0vo?autoplay=1"
        },
        {
            "id": "reuters_wire",
            "name": "Reuters / Sky News Live",
            "badge": "سرخط لحظه‌ای",
            "desc": "تصاویر ماهواره‌ای و فیدهای زنده رسانه‌های غربی",
            "embed_url": "https://www.youtube-nocookie.com/embed/9Auq9mYxFEE?autoplay=1"
        },
        {
            "id": "france24_en",
            "name": "France 24 English Live",
            "badge": "دیپلماسی",
            "desc": "تحلیل مانورهای دیپلماتیک و نشست‌های شورای امنیت",
            "embed_url": "https://www.youtube-nocookie.com/embed/h3MuIUNCCzI?autoplay=1"
        }
    ]
}


# ==============================================================================
# IRAN MONITOR OSINT INTELLIGENCE ENGINE & LIVE SYNC
# ==============================================================================
IRAN_MONITOR_TRANSLATIONS = {
  "Saudi Arabia fires missile at Al-Zahir border area in Yemen's Saada province": {
    "title": "حمله موشکی ارتش عربستان به نوار مرزی الظاهر در استان صعده یمن",
    "summary": "خبرنگار المسیره گزارش داد که یگان‌های موشکی عربستان منطقه مرزی الظاهر در استان صعده را هدف آتش سنگین قرار دادند. ارزیابی خسارات ادامه دارد.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "صعده، نوار مرزی الظاهر در شمال یمن",
    "lat": 16.9402,
    "lng": 43.7639,
    "weapon": "موشک‌های هدایت‌شونده زمین‌به‌زمین و توپخانه سنگین"
  },
  "Iran Deputy FM Gharibabadi meets ambassadors of India, Japan, and Spain in Tehran": {
    "title": "رایزنی معاون وزیر امور خارجه با سفرای هند، ژاپن و اسپانیا در تهران",
    "summary": "کاظم غریب‌آبادی در سلسله دیدارهای دیپلماتیک در محل وزارت خارجه، تحولات منطقه‌ای، تنش‌های جاری در خلیج فارس و مواضع ایران در شورای امنیت را تبیین کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، ساختمان وزارت امور خارجه",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "میز مذاکرات و مجاری دیپلماتیک"
  },
  "New footage reveals extent of Houthi missile damage to Saudi Aramco Rabigh refinery": {
    "title": "انتشار تصاویر جدید از خسارات حمله موشکی به پالایشگاه آرامکو در رابغ",
    "summary": "ویدیوهای ماهواره‌ای و محلی تایید می‌کنند که حمله ترکیبی موشکی و پهپادی نیروهای مسلح یمن به پالایشگاه آرامکو در بندر رابغ ساحل دریای سرخ خسارات جدی به تأسیسات تقطیر وارد کرده است.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "عربستان، بندر رابغ و پالایشگاه آرامکو در ساحل دریای سرخ",
    "lat": 22.7986,
    "lng": 39.0347,
    "weapon": "موشک بالستیک قدس-۴ و پهپاد صماد-۳"
  },
  "Houthis claim missile strike on King Khalid International Airport in Riyadh and Aden Airport area": {
    "title": "شلیک موشک‌های دوربرد به فرودگاه بین‌المللی ملک خالد ریاض و عدن",
    "summary": "نیروهای مسلح یمن از اجرای عملیات موشکی هم‌زمان علیه اهداف راهبردی در فرودگاه بین‌المللی ملک خالد ریاض و تأسیسات فرودگاه عدن خبر دادند.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "عربستان، فرودگاه بین‌المللی ملک خالد ریاض",
    "lat": 24.9576,
    "lng": 46.6988,
    "weapon": "موشک‌های بالستیک دوربرد فلسطین-۲"
  },
  "Houthis launch missile and drone strikes on three Saudi military bases in border regions": {
    "title": "حمله هم‌زمان موشکی و پهپادی انصارالله به ۳ پایگاه نظامی عربستان در نوار مرزی",
    "summary": "یگان موشکی و پهپادی ارتش یمن در عملیاتی ترکیبی، پایگاه‌ها و مقرهای فرماندهی ارتش عربستان در مناطق مرزی نجران، جیزان و عسیر را هدف قرار دادند.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "نوار مرزی عسیر، جیزان و نجران در جنوب عربستان",
    "lat": 17.5656,
    "lng": 44.2289,
    "weapon": "موشک‌های نقطه‌زن بدر و پهپادهای تهاجمی قاصف-۲K"
  },
  "Houthis strike Aden International Airport with missiles; flight diverted to Jeddah": {
    "title": "اصابت موشک به فرودگاه بین‌المللی عدن و تغییر مسیر پروازها به جده",
    "summary": "در پی شلیک چندین فروند موشک بالستیک به محوطه فرودگاه عدن، فعالیت پروازی متوقف شد و پروازهای ورودی به سمت فرودگاه بین‌المللی جده هدایت شدند.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "یمن، فرودگاه بین‌المللی و پایگاه هوایی عدن",
    "lat": 12.8295,
    "lng": 45.0287,
    "weapon": "موشک‌های بالستیک تاکتیکی قدس"
  },
  "Houthis launch missile and drone strikes on Khamis Mushait base and Abha Airport in Saudi Arabia": {
    "title": "حملات موشکی و پهپادی به پایگاه ملک خالد در خمیس مشیط و فرودگاه ابها",
    "summary": "آژیرهای خطر در جنوب عربستان به صدا درآمدند؛ گزارش‌های میدانی از فعال شدن پدافند پاتریوت و اصابت پرتابه‌ها به مجاورت آشیانه‌های پایگاه هوایی خمیس مشیط حکایت دارند.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "عربستان، پایگاه هوایی ملک خالد در خمیس مشیط",
    "lat": 18.3,
    "lng": 42.7333,
    "weapon": "موشک بالستیک ذوالفقار و پهپادهای صماد"
  },
  "Israel tightens security at southern bases after US bombers evacuated from UK over Iran threat": {
    "title": "آماده‌باش فوق‌العاده در پایگاه‌های جنوب اسرائیل پس از تخلیه بمب‌افکن‌های آمریکایی",
    "summary": "به دنبال تصمیم پنتاگون مبنی بر تخلیه بمب‌افکن‌های استراتژیک از پایگاه فیرفورد انگلیس در پی تهدیدات موشکی و پهپادی، ارتش اسرائیل سطح هشدار در پایگاه نواتیم را به بالاترین حد رساند.",
    "category": "alert",
    "severity": "ops",
    "region": "israel",
    "location": "اراضی اشغالی، صحرای نقب، پایگاه هوایی نواتیم",
    "lat": 31.2081,
    "lng": 35.0125,
    "weapon": "سامانه‌های پدافندی پیکان ۳ و فلاخن داوود"
  },
  "Houthis shoot down Saudi CH-4 reconnaissance drone over al-Jawf province": {
    "title": "رهگیری و انهدام پهپاد شناسایی-تهاجمی CH-4 عربستان بر فراز استان الجوف",
    "summary": "پدافند هوایی انصارالله با شلیک موشک زمین‌به‌هوا، یک فروند پهپاد پیشرفته مسلح مدل CH-4 متعلق به ائتلاف را در حین مأموریت جاسوسی بر فراز آسمان الجوف ساقط کرد.",
    "category": "airdefense",
    "severity": "ops",
    "region": "yemen",
    "location": "یمن، استان الجوف و نوار مرزی شمال",
    "lat": 16.7833,
    "lng": 45.25,
    "weapon": "موشک پدافندی بومی مدل ۳۵۸"
  },
  "Houthis launch missile attack on Aden International Airport; unofficial reports of Saudi officer casualties": {
    "title": "موج دوم حمله موشکی به فرودگاه عدن و گزارش تلفات افسران ائتلاف",
    "summary": "منابع محلی از تلفات جانی در پی شلیک موشک‌های نقطه‌زن به بخش نظامی فرودگاه بین‌المللی عدن خبر دادند؛ گزارش‌های غیررسمی از آسیب دیدن کادر هدایت پرواز ائتلاف حکایت دارد.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "یمن، بخش نظامی فرودگاه بین‌المللی عدن",
    "lat": 12.8295,
    "lng": 45.0287,
    "weapon": "موشک‌های بالستیک نقطه‌زن قدس"
  },
  "Strong explosions reported in Aden, Yemen": {
    "title": "وقوع انفجارهای پیاپی و مهیب در شهر بندری عدن یمن",
    "summary": "ساکنان شهر عدن از شنیده شدن صدای چند رشته انفجار مهیب در نزدیکی مراکز فرماندهی و ساحل خبر دادند؛ ستون‌های دود بر فراز منطقه خورمکسر دیده شده است.",
    "category": "alert",
    "severity": "ops",
    "region": "yemen",
    "location": "یمن، منطقه خورمکسر و بندر عدن",
    "lat": 12.8,
    "lng": 45.03,
    "weapon": "پرتابه‌های تهاجمی و راکت‌های سنگین"
  },
  "US Congressional Research Service: 81 American aircraft damaged or lost in war with Iran": {
    "title": "گزارش کنگره آمریکا: آسیب یا انهدام ۸۱ فروند پرنده نظامی در نبرد با ایران",
    "summary": "مرکز تحقیقات کنگره آمریکا (CRS) در ارزیابی جامع خسارات عملیاتی تایید کرد ۸۱ فروند جنگنده، پهپاد و هواپیمای ائتلاف در جریان تنش‌ها و درگیری‌های منطقه‌ای با ایران سرنگون یا دچار آسیب سنگین شده‌اند.",
    "category": "combat",
    "severity": "crit",
    "region": "iran",
    "location": "حریم هوایی خلیج فارس و پایگاه‌های سنتکام در منطقه",
    "lat": 26.0,
    "lng": 52.0,
    "weapon": "سامانه‌های پدافندی سوم خرداد و صیاد"
  },
  "US VP Vance says Iran must reduce nuclear enrichment to end war": {
    "title": "معاون ترامپ: هرگونه پایان جنگ منوط به توقف غنی‌سازی هسته‌ای ایران است",
    "summary": "جی‌دی ونس، معاون رئیس‌جمهور آمریکا در اظهاراتی تند اعلام کرد توافق دیپلماتیک یا پایان تنش‌های نظامی در منطقه تنها در صورت عقب‌نشینی کامل ایران از ذخایر غنی‌سازی امکان‌پذیر خواهد بود.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "میز مذاکرات و مواضع رسمی کاخ سفید، واشنگتن",
    "lat": 38.8951,
    "lng": -77.0364,
    "weapon": "بیانیه‌های راهبردی و پرونده دیپلماسی هسته‌ای"
  },
  "US Embassy warns Americans to leave Russia amid pneumonic plague outbreak reports": {
    "title": "هشدار امنیتی سفارت آمریکا در مسکو برای خروج فوری شهروندان",
    "summary": "سفارت ایالات متحده در روسیه در پی انتشار گزارش‌های بهداشتی و تنش‌های امنیتی ناشی از جنگ، از اتباع خود خواست فوراً خاک این کشور را ترک کنند.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "روسیه، مسکو، سفارت ایالات متحده",
    "lat": 55.7558,
    "lng": 37.6173,
    "weapon": "هشدارهای کنسولی و امنیتی"
  },
  "Foreign Affairs warns military victory is a 'myth,' cites Iran, Gaza, Ukraine wars": {
    "title": "تحلیل فارن افرز: پیروزی نظامی قطعی در جنگ‌های ایران، غزه و اوکراین یک توهم است",
    "summary": "نشریه معتبر فارن افرز در تحلیلی راهبردی تاکید کرد ساختار قدرت منطقه‌ای ایران و بازدارندگی موشکی آن امکان تحمیل شکست قطعی از طریق حملات هوایی را ناممکن ساخته است.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "اندیشکده‌های راهبردی واشنگتن و نیویورک",
    "lat": 40.7128,
    "lng": -74.006,
    "weapon": "تحلیل‌های اندیشکده‌ای و ژئوپلیتیک"
  },
  "Trump claims Strait of Hormuz belongs to United States": {
    "title": "ادعای جنجالی ترامپ درباره حاکمیت آمریکا بر آبراهه تنگه هرمز",
    "summary": "دونالد ترامپ در سخنرانی انتخاباتی خود ادعا کرد تنگه هرمز عملاً متعلق به آمریکا و تحت اراده نیروی دریایی آن است؛ ادعایی که با واکنش تند تهران همراه شد.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "تنگه هرمز و واشنگتن",
    "lat": 26.5667,
    "lng": 56.25,
    "weapon": "مواضع سیاسی و تهدیدات ژئوپلیتیک"
  },
  "Trump says 'nobody knows who is running Iran,' calls it possibly a good thing": {
    "title": "اظهارات مبهم ترامپ پیرامون ساختار تصمیم‌گیری سیاسی و دفاعی ایران",
    "summary": "رئیس‌جمهور سابق آمریکا مدعی شد در ساختار حاکمیتی ایران تصمیم‌گیرنده نهایی مشخص نیست و این وضعیت می‌تواند برای هرگونه مذاکره دارای پیچیدگی باشد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "واشنگتن / تهران",
    "lat": 38.8951,
    "lng": -77.0364,
    "weapon": "جنگ روانی و رسانه‌ای"
  },
  "Trump vows to 'finish the job' on Iran, says 'good way or not-so-good way'": {
    "title": "تهدید ترامپ به «تمام کردن کار» ایران با ابزارهای نظامی یا تحریمی",
    "summary": "ترامپ مدعی شد چه از مسیر توافق سخت‌گیرانه و چه از مسیر تهاجم سنگین نظامی، پرونده هسته‌ای و نفوذ منطقه‌ای ایران را یکسره خواهد کرد.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "واشنگتن / خاورمیانه",
    "lat": 38.8951,
    "lng": -77.0364,
    "weapon": "فشار حداکثری و تهدید نظامی"
  },
  "Iran FM Araghchi meets Armenian counterpart in Tehran, emphasizes regional dialogue": {
    "title": "دیدار سید عباس عراقچی با وزیر خارجه ارمنستان و تاکید بر امنیت قفقاز",
    "summary": "وزیر امور خارجه ایران در دیدار با همتای ارمنی خود در تهران بر عدم تغییر مرزهای ژئوپلیتیک شمال غرب و رد دخالت نیروهای فرامنطقه‌ای در قفقاز تاکید کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، وزارت امور خارجه",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "مذاکرات دیپلماتیک دوجانبه"
  },
  "Iran rep at OPCW: US strikes damaged 111 petrochemical and pharmaceutical facilities": {
    "title": "گزارش ایران در سازمان منع سلاح‌های شیمیایی: خسارت به ۱۱۱ تأسیسات دارویی و پتروشیمی",
    "summary": "نماینده دائم ایران در OPCW اعلام کرد تجاوزات نظامی آمریکا منجر به آسیب جدی به ۱۱۱ واحد صنعتی، پتروشیمی و تولید دارو در کشور شده است.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "لاهه، هلند و تأسیسات صنعتی ایران",
    "lat": 52.0705,
    "lng": 4.3007,
    "weapon": "حقوق بین‌الملل و اسناد نقض حاکمیت"
  },
  "Trump remarks suggest Iran could strike Los Angeles or San Diego, sparking California backlash": {
    "title": "جنجال ادعای ترامپ درباره توانایی موشکی ایران برای هدف قرار دادن لس‌آنجلس",
    "summary": "اظهارات انتخاباتی دونالد ترامپ مبنی بر اینکه ایران در صورت تشدید جنگ می‌تواند خاک آمریکا را هدف قرار دهد، با واکنش تند رسانه‌ها و مقامات کالیفرنیا روبرو شد.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "واشنگتن / کالیفرنیا، بازتاب‌های سیاسی",
    "lat": 34.0522,
    "lng": -118.2437,
    "weapon": "جنگ روانی رسانه‌ای و بیانیه‌های انتخاباتی"
  },
  "Islamic Republic linked to alleged plot to attack RAF Fairford air base in UK": {
    "title": "گزارش‌های اطلاعاتی غرب درباره رصد پایگاه بمب‌افکن‌های فیرفورد در بریتانیا",
    "summary": "رسانه‌های غربی از شناسایی فعالیت‌های مشکوک اطلاعاتی پیرامون پایگاه هوایی استراتژیک RAF Fairford انگلیس که محل استقرار بمب‌افکن‌های B-52 آمریکاست خبر دادند.",
    "category": "combat",
    "severity": "crit",
    "region": "iran",
    "location": "اروپا، بریتانیا، پایگاه استراتژیک هوایی فیرفورد",
    "lat": 51.6842,
    "lng": -1.7911,
    "weapon": "اشراف اطلاعاتی و رصد سایبری/انسانی"
  },
  "Two US warships leave Middle East; USS George Washington sole carrier remaining": {
    "title": "خروج ۲ ناو جنگی آمریکا از خاورمیانه و کاهش تراکم ناوگان پنجم",
    "summary": "فرماندهی مرکزی آمریکا اعلام کرد دو ناوشکن رزمی از آب‌های خلیج فارس و دریای عمان خارج شده‌اند و ناو هواپیمابر جورج واشنگتن تنها گروه ضربت دریایی در منطقه است.",
    "category": "naval",
    "severity": "ops",
    "region": "iran",
    "location": "دریای عمان و شمال اقیانوس هند",
    "lat": 24.5,
    "lng": 58.0,
    "weapon": "ناو هواپیمابر هسته‌ای جورج واشنگتن"
  },
  "Explosion reported in Sulaymaniyah, northern Iraq; cause under investigation": {
    "title": "وقوع انفجار مشکوک در حومه سلیمانیه در اقلیم کردستان عراق",
    "summary": "صدای انفجاری شدید در مناطق حاشیه‌ای شهر سلیمانیه شنیده شد؛ نیروهای امنیتی اقلیم در حال ارزیابی حمله احتمالی پهپادی یا انفجار انبار مهمات هستند.",
    "category": "alert",
    "severity": "ops",
    "region": "syria_iraq",
    "location": "عراق، حومه سلیمانیه در اقلیم کردستان",
    "lat": 35.5612,
    "lng": 45.4371,
    "weapon": "پرتابه انفجاری ناشناس / ریزپرنده"
  },
  "Satellite imagery shows Iran rebuilding nuclear weapons site at Minzadayi after Israeli strikes": {
    "title": "تصاویر ماهواره‌ای: بازسازی پرشتاب سازه‌های مستحکم کوهستانی پس از حملات",
    "summary": "تصاویر ماهواره‌های تجاری نشان می‌دهند عملیات بتن‌ریزی مسلحانه و حفر تونل‌های دسترسی در سایت کوهستانی آسیب‌دیده با سرعت بالا در حال انجام است.",
    "category": "alert",
    "severity": "crit",
    "region": "iran",
    "location": "ایران، سایت تأسیسات تقویت‌شده زیرزمینی",
    "lat": 33.72,
    "lng": 51.72,
    "weapon": "استحکامات پدافندی و بتن مصلح ضدبمب"
  },
  "Houthis confirm killing Saudi-backed 35th Armored Brigade commander, seize strategic heights in Yemen": {
    "title": "هلاکت فرمانده تیپ ۳۵ زرهی ائتلاف و پیشروی رزمندگان یمنی در ارتفاعات کلیدی",
    "summary": "نیروهای مسلح یمن با تایید هلاکت فرمانده تیپ ۳۵ زرهی وابسته به ائتلاف، از تسلط کامل بر ارتفاعات استراتژیک مشرف به خطوط امداد نیروهای تحت حمایت عربستان خبر دادند.",
    "category": "combat",
    "severity": "ops",
    "region": "yemen",
    "location": "یمن، استان تعز و بلندی‌های راهبردی جنوب غربی",
    "lat": 13.5795,
    "lng": 44.0209,
    "weapon": "یگان‌های تکاوری و موشک‌های ضدزره هدایت‌شونده"
  },
  "Oman Defense Ministry: ship attacked in Musandam": {
    "title": "گزارش وزارت دفاع عمان از حمله به کشتی تجاری در تنگه هرمز و شبه‌جزیره مسندم",
    "summary": "وزارت دفاع عمان تایید کرد که یک فروند شناور تجاری در آب‌های ساحلی استان مسندم در مدخل تنگه هرمز مورد اصابت قرار گرفته و یگان‌های امداد ساحلی عازم محل حادثه شدند.",
    "category": "naval",
    "severity": "crit",
    "region": "iran",
    "location": "عمان، شبه‌جزیره مسندم در مدخل جنوبی تنگه هرمز",
    "lat": 26.15,
    "lng": 56.25,
    "weapon": "پرتابه موشکی دریایی / شهپاد انتحاری"
  },
  "Turkey plans to deploy military forces, jets, and special troops to Saudi Arabia": {
    "title": "طرح ترکیه برای اعزام اسکادران‌های F-16 و کماندوهای ویژه به عربستان",
    "summary": "گزارش‌ها حاکی از توافق امنیتی جدید آنکارا و ریاض برای استقرار جنگنده‌های ارتش ترکیه و نیروهای نخبه هوابرد در پایگاه‌های هوایی عربستان جهت پر کردن خلاء دفاعی است.",
    "category": "combat",
    "severity": "ops",
    "region": "yemen",
    "location": "ریاض و پایگاه‌های هوایی مرکزی عربستان سعودی",
    "lat": 24.7136,
    "lng": 46.6753,
    "weapon": "جنگنده‌های F-16 و سامانه‌های پدافند هوایی مشترک"
  },
  "Oil tanker MT On Peace struck by unknown projectile in Strait of Hormuz, 12 crew injured": {
    "title": "اصابت پرتابه ناشناس به نفتکش بین‌المللی MT On Peace در آب‌های تنگه هرمز",
    "summary": "سازمان تجارت دریایی بریتانیا تایید کرد که نفتکش حامل محموله انرژی در حین ترانزیت از تنگه هرمز هدف اصابت مستقیم قرار گرفته و ۱۲ نفر از خدمه آن زخمی شدند.",
    "category": "naval",
    "severity": "crit",
    "region": "iran",
    "location": "آبراهه بین‌المللی تنگه هرمز",
    "lat": 26.5667,
    "lng": 56.25,
    "weapon": "موشک ضدکشتی / قایق تندرو انتحاری"
  },
  "Iranian state media questions whether Pakistani forces are entering Yemen war": {
    "title": "بررسی احتمال ورود نیروهای ارتش پاکستان به کارزار نظامی یمن و ائتلاف سعودی",
    "summary": "رسانه‌های رسمی در ایران گزارش‌های مربوط به احتمال اعزام یگان‌های کماندویی و متخصصان نظامی پاکستان به جبهه‌های درگیری در جنوب شبه‌جزیره عربستان را بررسی کردند.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "yemen",
    "location": "اسلام‌آباد / ریاض / صنعا",
    "lat": 33.6844,
    "lng": 73.0479,
    "weapon": "توافقات امنیتی دوجانبه"
  },
  "Houthi official threatens to close all Saudi airports and ports": {
    "title": "هشدار مقام ارشد انصارالله: در صورت تداوم تجاوز، تمام فرودگاه‌ها و بنادر سعودی بسته خواهد شد",
    "summary": "عضو دفتر سیاسی انصارالله هشدار داد در صورت عدم توقف حملات هوایی و محاصره، تمامی زیرساخت‌های هوانوردی و بنادر نفتی عربستان هدف حملات فلج‌کننده قرار خواهند گرفت.",
    "category": "alert",
    "severity": "crit",
    "region": "yemen",
    "location": "یمن، صنعا / نوار مرزی عربستان",
    "lat": 15.3694,
    "lng": 44.191,
    "weapon": "تهدیدات موشکی دوربرد و پهپادی"
  },
  "Putin and Pezeshkian to hold bilateral meeting in Turkmenistan on Friday": {
    "title": "دیدار دوجانبه مسعود پزشکیان و ولادیمیر پوتین در ترکمنستان در بحبوحه بحران منطقه‌ای",
    "summary": "رؤسای جمهور ایران و روسیه در حاشیه نشست بین‌المللی در عشق‌آباد پیرامون تقویت همکاری‌های راهبردی دفاعی، مسیرهای ترانزیت شمال-جنوب و تحولات جنگ خاورمیانه گفتگو می‌کنند.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ترکمنستان، عشق‌آباد و تهران/مسکو",
    "lat": 37.9601,
    "lng": 58.3261,
    "weapon": "مذاکرات سران و پیمان جامع راهبردی"
  },
  "US grants visas to Iran wrestling team for Under-23 World Championships": {
    "title": "صدور روادید آمریکا برای کاروان تیم ملی کشتی زیر ۲۳ سال ایران",
    "summary": "وزارت خارجه آمریکا علیرغم تنش‌های شدید سیاسی و نظامی، ویزای حضور کشتی‌گیران جوان ایران در مسابقات قهرمانی جهان را صادر کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "واشنگتن / تیرانا",
    "lat": 38.8951,
    "lng": -77.0364,
    "weapon": "دیپلماسی ورزشی"
  },
  "Pakistan successfully tests Fatah-4 cruise missile with advanced avionics": {
    "title": "آزمایش موفقیت‌آمیز موشک کروز فتاح-۴ پاکستان با هدایت و اویونیک پیشرفته",
    "summary": "ارتش پاکستان از شلیک و تست میدانی سامانه موشک کروز نسل جدید Fatah-4 با برد افزایش‌یافته و رادارگریزی در آب‌های دریای عرب خبر داد.",
    "category": "missile",
    "severity": "ops",
    "region": "yemen",
    "location": "پاکستان، میدان آزمایش موشکی در دریای عرب",
    "lat": 24.8607,
    "lng": 67.0011,
    "weapon": "موشک کروز نقطه‌زن فتاح-۴"
  },
  "Qatar confirms US-Iran indirect talks continuing through Doha mediation": {
    "title": "تایید وزارت خارجه قطر: کانال مذاکرات غیرمستقیم ایران و آمریکا در دوحه فعال است",
    "summary": "سخنگوی وزارت خارجه قطر اعلام کرد میانجی‌گری دوحه برای تبادل پیام‌های امنیتی و تنش‌زدایی میان تهران و واشنگتن بدون وقفه در جریان است.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "قطر، دوحه، میز میانجی‌گری دیپلماتیک",
    "lat": 25.2854,
    "lng": 51.531,
    "weapon": "کانال‌های دیپلماتیک و میانجی‌گری منطقه‌ای"
  },
  "Israel conducts artillery strike on Beit Yahoun in southern Lebanon": {
    "title": "حملات توپخانه‌ای ارتش اسرائیل به منطقه بیت یاحون در جنوب لبنان",
    "summary": "توپخانه سنگین ارتش اسرائیل چندین گلوله فسفری و انفجاری به حومه شهرک بیت یاحون در جنوب لبنان شلیک کرد که منجر به آتش‌سوزی در اراضی کشاورزی شد.",
    "category": "combat",
    "severity": "ops",
    "region": "lebanon",
    "location": "جنوب لبنان، شهرک بیت یاحون",
    "lat": 33.15,
    "lng": 35.35,
    "weapon": "توپخانه سنگین ۱۵۵ میلی‌متری هدایت‌شونده"
  },
  "Hezbollah chief Naim Qassem vows Israel cannot remain in southern Lebanon": {
    "title": "سخنرانی شیخ نعیم قاسم: رژیم صهیونیستی توان ماندن در هیچ نقطه‌ای از جنوب لبنان را ندارد",
    "summary": "دبیرکل حزب‌الله لبنان در بیانیه‌ای تاکید کرد رزمندگان مقاومت با تکیه بر تاکتیک‌های نبرد نامتقارن، هرگونه نفوذ زمینی ارتش اسرائیل را به باتلاق تلفات تبدیل خواهند کرد.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "lebanon",
    "location": "لبنان، ضاحیه جنوبی بیروت",
    "lat": 33.85,
    "lng": 35.5,
    "weapon": "بیانیه‌های فرماندهی مقاومت"
  },
  "Iran summons French ambassador over violent crackdown on student protests": {
    "title": "احضار سفیر فرانسه در تهران به وزارت امور خارجه",
    "summary": "مدیرکل غرب اروپای وزارت خارجه ایران در اعتراض به سرکوب تجمعات دانشجویی و سیاست‌های مداخله‌جویانه پاریس، سفیر فرانسه را به وزارت خارجه فراخواند.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، وزارت امور خارجه",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "اقدامات دیپلماتیک رسمی"
  },
  "Trump says Iran could 'take out' LA and San Diego, draws backlash": {
    "title": "تکرار ادعاهای ترامپ درباره خطر حملات فرامنطقه‌ای ایران علیه بنادر غربی آمریکا",
    "summary": "دونالد ترامپ در مصاحبه دیگری ادعا کرد برد عملیاتی موشک‌ها و شناورهای ایران می‌تواند لس‌آنجلس و سن‌دیگو را با تهدید مستقیم روبرو کند.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "واشنگتن، ایالات متحده",
    "lat": 38.8951,
    "lng": -77.0364,
    "weapon": "جنگ روانی و رسانه‌ای"
  },
  "Israel's National Security Council warns of Iran/Hamas attack threat around symbolic date": {
    "title": "هشدار شورای امنیت ملی اسرائیل پیرامون احتمال حملات موشکی و پهپادی ایران و مقاومت",
    "summary": "نهادهای اطلاعاتی اسرائیل با صدور هشدار فوری از احتمال اجرای عملیات ترکیبی موشکی و پهپادی هم‌زمان با سالگرد درگیری‌ها در عمق سرزمین‌های اشغالی خبر دادند.",
    "category": "alert",
    "severity": "crit",
    "region": "israel",
    "location": "اراضی اشغالی، تل‌آویو و حیفا",
    "lat": 32.0853,
    "lng": 34.7818,
    "weapon": "آماده‌باش سراسری پدافند هوایی گنبد آهنین و پیکان"
  },
  "Syrian leader Jolani meets Saudi Crown Prince MBS in Riyadh": {
    "title": "دیدار الجولانی و محمد بن سلمان در ریاض پیرامون معادلات امنیتی شامات",
    "summary": "منابع دیپلماتیک از مذاکرات محرمانه رهبر تحریرالشام با ولیعهد عربستان در ریاض با محوریت نفوذ ایران و ترتیبات امنیتی مرزهای سوریه خبر دادند.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "syria_iraq",
    "location": "عربستان، ریاض، کاخ الیمامه",
    "lat": 24.7136,
    "lng": 46.6753,
    "weapon": "مذاکرات محرمانه امنیتی"
  },
  "Jerusalem Post: Israel was prepared to shoot down flydubai Flight 1073 during suspected hijacking": {
    "title": "گزارش جروزالم پست: آمادگی جنگنده‌های اسرائیل برای سرنگونی پرواز فلای‌دبی",
    "summary": "نیروی هوایی اسرائیل در پی دریافت هشدار احتمال هواپیماربایی توسط هسته‌های مقاومت، جنگنده‌های رهگیر خود را برای شلیک احتمالی به هواپیمای مسافربری به پرواز درآورد.",
    "category": "combat",
    "severity": "crit",
    "region": "israel",
    "location": "حریم هوایی اراضی اشغالی و شرق مدیترانه",
    "lat": 32.0,
    "lng": 34.9,
    "weapon": "جنگنده‌های رهگیر F-16I صوفا"
  },
  "CENTCOM denies Iranian state media claims of US Navy helicopter downed in Red Sea": {
    "title": "تکذیب سنتکام پیرامون گزارش‌های سرنگونی بالگرد نیروی دریایی آمریکا در دریای سرخ",
    "summary": "فرماندهی مرکزی آمریکا اخبار منتشرشده مبنی بر انهدام یک فروند بالگرد ضدزیردریایی MH-60R سی‌هاوک توسط پدافند ساحلی را رد کرد.",
    "category": "combat",
    "severity": "ops",
    "region": "yemen",
    "location": "دریای سرخ و تنگه باب‌المندب",
    "lat": 14.0,
    "lng": 42.5,
    "weapon": "بالگرد رزمی MH-60R و ناوگان اسکورت"
  },
  "British Embassy in Riyadh issues security alert to UK nationals in Saudi Arabia": {
    "title": "هشدار امنیتی سفارت انگلیس در ریاض در پی تشدید حملات موشکی به عربستان",
    "summary": "سفارت بریتانیا از تمامی اتباع خود در ریاض، جده و مناطق جنوبی خواست از حضور در نزدیکی مراکز نظامی، فرودگاه‌ها و پالایشگاه‌ها خودداری کنند.",
    "category": "alert",
    "severity": "crit",
    "region": "yemen",
    "location": "عربستان، ریاض، سفارت بریتانیا",
    "lat": 24.68,
    "lng": 46.63,
    "weapon": "هشدارهای امنیتی سطح قرمز"
  },
  "Iran SNSC Secretary Rezaei warns US: 'You lost the military war, you'll lose the economic war too'": {
    "title": "هشدار دبیر شورای دفاعی به آمریکا: در جنگ نظامی شکست خوردید، در جنگ اقتصادی هم می‌بازید",
    "summary": "محسن رضایی در واکنش به تحریم‌های جدید نفتی اعلام کرد بازدارندگی ایران تثبیت شده و تلاش واشنگتن برای محاصره تجاری به فروپاشی بازارهای مالی غرب خواهد انجامید.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "ایران، تهران، شورای عالی امنیت ملی",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "بیانیه‌های راهبردی و جنگ اقتصادی"
  },
  "Yemeni armed forces release footage of missile strikes on Saudi-backed forces in Ras al-Aara": {
    "title": "انتشار تصاویر شلیک موشک‌های نقطه‌زن به مواضع نیروهای ائتلاف در رأس العاره",
    "summary": "رسانه‌های جنگی یمن ویدیوهایی از اصابت دقیق موشک‌های هدایت‌پذیر به پادگان‌های ساحلی در منطقه استراتژیک رأس العاره مشرف به باب‌المندب را منتشر کردند.",
    "category": "missile",
    "severity": "ops",
    "region": "yemen",
    "location": "یمن، سواحل رأس العاره در مدخل باب‌المندب",
    "lat": 12.6333,
    "lng": 44.15,
    "weapon": "موشک‌های بالستیک کوتاه‌برد قاهر و بدر"
  },
  "Iran warns US and Israel of harsher response and advanced weapons in any new war": {
    "title": "هشدار قاطع ایران به تل‌آویو و واشنگتن: استفاده از تسلیحات ناشناخته در نبرد آینده",
    "summary": "فرماندهان ارشد نظامی ایران هشدار دادند در صورت هرگونه شرارت یا ماجراجویی جدید، سلاح‌های جدید موشکی و سامانه‌های پیشرفته پدافندی رونمایی و به کار گرفته خواهند شد.",
    "category": "combat",
    "severity": "crit",
    "region": "iran",
    "location": "ایران، ستاد کل نیروهای مسلح، تهران",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "موشک‌های هایپرسونیک فتاح و کلاهک‌های خوشه‌ای"
  },
  "Iran Interior Minister meets Emir of Qatar on second day of Doha visit": {
    "title": "دیدار وزیر کشور ایران با امیر قطر پیرامون امنیت دریانوردی در خلیج فارس",
    "summary": "اسکندر مؤمنی در دیدار با شیخ تمیم بن حمد آل ثانی در دوحه پیرامون همکاری‌های گارد ساحلی، مبارزه با قاچاق و پایداری خطوط کشتیرانی مشترک تبادل نظر کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "قطر، دوحه، دیوان امیری",
    "lat": 25.29,
    "lng": 51.53,
    "weapon": "دیپلماسی منطقه‌ای و امنیت دریانوردی"
  },
  "Pew Research poll: 67% of people across 36 countries hold negative view of Israel amid 2026 conflict": {
    "title": "نظرسنجی جهانی پیو: ۶۷ درصد افکار عمومی در ۳۶ کشور دیدگاه منفی نسبت به اسرائیل دارند",
    "summary": "نتایج نظرسنجی جدید موسسه پیو حاکی از انزوای شدید بین‌المللی تل‌آویو و افت بی‌سابقه وجهه عمومی رژیم در پی گسترش جنگ‌های منطقه‌ای است.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "israel",
    "location": "واشنگتن / تل‌آویو",
    "lat": 38.8951,
    "lng": -77.0364,
    "weapon": "سنجش افکار عمومی بین‌الملل"
  },
  "UN Secretary-General Guterres visits Pakistan, discusses Islamabad's mediation between Iran and US": {
    "title": "سفر آنتونیو گوترش به پاکستان و مذاکره پیرامون میانجی‌گری اسلام‌آباد میان ایران و آمریکا",
    "summary": "دبیرکل سازمان ملل در دیدار با نخست‌وزیر پاکستان نقش این کشور در برقراری تماس‌های پشت‌پرده میان تهران و واشنگتن برای مهار درگیری‌ها را بررسی کرد.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "پاکستان، اسلام‌آباد، دفتر نخست‌وزیری",
    "lat": 33.7294,
    "lng": 73.0931,
    "weapon": "میانجی‌گری دیپلماتیک بین‌المللی"
  },
  "Iranian government spokesperson signals readiness for negotiations, frames conflict as 'civilizational war'": {
    "title": "سخنگوی دولت ایران: آماده مذاکرات مشروط هستیم اما نبرد جاری تمدنی است",
    "summary": "سخنگوی دولت اعلام کرد ایران هرگز میز مذاکره عزتمندانه را ترک نکرده، اما هرگونه توقف جنگ باید با رفع تحریم‌ها و توقف کامل تجاوزات دشمن همراه باشد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، پاستور",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "مواضع رسمی دستگاه اجرایی"
  },
  "Panama-flagged cargo ship attacked near Oman coast; 11 Indian crew members injured": {
    "title": "حمله به کشتی تجاری با پرچم پاناما در سواحل عمان و جراحت ۱۱ خدمه هندی",
    "summary": "یک فروند کشتی کانتینری در دریای عمان هدف اصابت پرتابه مشکوک قرار گرفت؛ ۱۱ دریانورد زخمی و شناورهای نجات عمان عملیات امداد را اجرا کردند.",
    "category": "naval",
    "severity": "crit",
    "region": "iran",
    "location": "دریای عمان، سواحل شرقی پادشاهی عمان",
    "lat": 23.6,
    "lng": 58.6,
    "weapon": "پرتابه موشکی دریایی"
  },
  "Pakistan denies Reuters report on deployment of 40,000 troops to Saudi Arabia": {
    "title": "تکذیب قاطع اسلام‌آباد درباره اعزام ۴۰ هزار نیروی نظامی به عربستان",
    "summary": "وزارت خارجه پاکستان گزارش رویترز مبنی بر توافق اعزام لشکر رزمی به خاک عربستان برای دفاع در برابر یمن را فاقد اعتبار و کذب محض خواند.",
    "category": "diplomacy",
    "severity": "info",
    "region": "yemen",
    "location": "پاکستان، اسلام‌آباد، وزارت امور خارجه",
    "lat": 33.6844,
    "lng": 73.0479,
    "weapon": "تکذیبیه رسمی نظامی-سیاسی"
  },
  "GCC Secretary-General condemns Houthi attacks on Jazan and Najran airports": {
    "title": "محکومیت حملات موشکی یمن به فرودگاه‌های جیزان و نجران توسط دبیرکل شورای همکاری خلیج فارس",
    "summary": "جاسم البدیوی حملات متوالی موشکی و پهپادی به تأسیسات غیرنظامی و پایانه‌های فرودگاهی جنوب عربستان را به شدت محکوم کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "yemen",
    "location": "ریاض، دبیرخانه شورای همکاری خلیج فارس",
    "lat": 24.7136,
    "lng": 46.6753,
    "weapon": "بیانیه‌های منطقه‌ای"
  },
  "Pezeshkian receives Danish and Thai ambassadors, calls for stronger bilateral ties": {
    "title": "دیدار رئیس‌جمهور با سفرای جدید دانمارک و تایلند در تهران",
    "summary": "مسعود پزشکیان در دیدار با سفرای جدید کپنهاگ و بانکوک بر توسعه مناسبات بازرگانی، دیپلماسی متوازن و احترام متقابل تاکید کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، نهاد ریاست‌جمهوری",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "دیپلماسی عمومی و رسمی"
  },
  "Iran technical delegation to travel to Qatar to follow up on status of Iranian military pilots": {
    "title": "اعزام هیئت فنی-نظامی ایران به دوحه برای پیگیری وضعیت خلبانان و تبادل اسرا",
    "summary": "یک تیم تخصصی از نیروهای مسلح و وزارت خارجه برای رایزنی با مقامات قطری پیرامون مسائل امنیتی و فنی هوایی عازم دوحه شد.",
    "category": "diplomacy",
    "severity": "ops",
    "region": "iran",
    "location": "قطر، دوحه، وزارت دفاع",
    "lat": 25.2854,
    "lng": 51.531,
    "weapon": "مذاکرات تخصصی امنیتی-نظامی"
  },
  "Houthis fire ballistic missile at Abha International Airport, halting flights": {
    "title": "شلیک موشک بالستیک به فرودگاه بین‌المللی ابها و تعلیق پروازها",
    "summary": "شلیک دقیق یک فروند موشک بالستیک به باند فرودگاه ابها در جنوب عربستان منجر به فعال شدن آژیرهای هشدار و لغو پروازهای مسافربری شد.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "عربستان، فرودگاه بین‌المللی ابها در استان عسیر",
    "lat": 18.2164,
    "lng": 42.5053,
    "weapon": "موشک بالستیک سوخت جامد بدر-۱P"
  },
  "EU Commission President condemns Houthi attacks on Saudi refinery and airports": {
    "title": "محکومیت حملات انصارالله به پالایشگاه‌ها و فرودگاه‌های سعودی توسط اتحادیه اروپا",
    "summary": "اورزولا فون در لاین هدف قرار دادن تأسیسات نفت و انرژی و فرودگاه‌های تجاری در عربستان را تهدیدی برای ثبات بازار انرژی جهانی توصیف کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "yemen",
    "location": "بلژیک، بروکسل، کمیسیون اروپا",
    "lat": 50.8503,
    "lng": 4.3517,
    "weapon": "مواضع رسمی اتحادیه اروپا"
  },
  "UN Lebanon coordinator Jean Arnaud meets Iranian FM Araghchi in Tehran": {
    "title": "دیدار هماهنگ‌کننده ویژه سازمان ملل در امور لبنان با وزیر خارجه ایران در تهران",
    "summary": "ژان آرنو در دیدار با سید عباس عراقچی آخرین تحولات مرزهای جنوبی لبنان، تجاوزات ارتش اسرائیل و طرح‌های آتش‌بس سازمان ملل را به بحث گذاشت.",
    "category": "diplomacy",
    "severity": "info",
    "region": "lebanon",
    "location": "ایران، تهران، وزارت امور خارجه",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "رایزنی‌های دیپلماتیک سازمان ملل"
  },
  "Pezeshkian receives India's new ambassador, proposes strategic long-term cooperation roadmap": {
    "title": "پیشنهاد نقشه راه همکاری بلندمدت ایران و هند در دیدار مسعود پزشکیان با سفیر دهلی‌نو",
    "summary": "رئیس‌جمهور ایران در دیدار با سفیر جدید هند بر تسریع در توسعه بندر چابهار، کریدور شمال-جنوب و مبادلات مالی با روپیه-ریال تاکید کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، نهاد ریاست‌جمهوری",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "توسعه راهبردی بندر چابهار"
  },
  "Pezeshkian instructs Iran's new ambassadors to five countries to carry message of friendship and unity": {
    "title": "دستور رئیس‌جمهور به ۵ سفیر جدید ایران برای تحکیم مناسبات دیپلماتیک و خنثی‌سازی تحریم‌ها",
    "summary": "رئیس‌جمهور پیش از عزیمت سفرای جدید ایران به ماموریت، بر گسترش مناسبات اقتصادی، تعمیق روابط دوستانه و جذب سرمایه‌گذاری تاکید کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، ریاست جمهوری",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "دیپلماسی اقتصادی"
  },
  "IRGC ground forces special unit arrives in Belarus for SCO joint anti-terrorism drill": {
    "title": "ورود یگان ویژه نیروی زمینی سپاه به بلاروس برای رزمایش مشترک ضدتروریستی شانگهای",
    "summary": "نیروهای کماندویی صابرین نیروی زمینی سپاه پاسداران جهت شرکت در مانور مشترک چندجانبه نظامی در چارچوب سازمان همکاری شانگهای وارد خاک بلاروس شدند.",
    "category": "combat",
    "severity": "ops",
    "region": "iran",
    "location": "بلاروس، مینسک و پایگاه‌های آموزشی ارتش بلاروس",
    "lat": 53.9045,
    "lng": 27.5615,
    "weapon": "یگان‌های ویژه تکاوری صابرین و ادوات زرهی"
  },
  "Israeli Defense Minister orders heightened Gaza readiness ahead of October 7 anniversary": {
    "title": "دستور وزیر جنگ اسرائیل برای آماده‌باش کامل نیروها در مرزهای غزه و شمال",
    "summary": "وزیر جنگ رژیم صهیونیستی به ارتش و سرویس‌های اطلاعاتی دستور داد تا در تمام جبهه‌ها برای مقابله با حملات غافلگیرانه در بالاترین سطح هشدار قرار گیرند.",
    "category": "alert",
    "severity": "crit",
    "region": "israel",
    "location": "اراضی اشغالی، نوار مرزی غزه و پایگاه‌های فرماندهی جنوب",
    "lat": 31.5,
    "lng": 34.45,
    "weapon": "آماده‌باش یگان‌های زرهی و هوایی"
  },
  "Saudi airports suspend flights amid reports of Yemeni attack on Dammam; King Khalid airport also halted": {
    "title": "توقف پروازها در فرودگاه‌های دمام و ریاض در پی حملات موشکی",
    "summary": "سازمان هوانوردی عربستان به دنبال رهگیری اهداف پروازی در شرق و مرکز کشور، تمامی پروازهای ورودی و خروجی فرودگاه ملک فهد دمام و ملک خالد ریاض را معلق کرد.",
    "category": "alert",
    "severity": "crit",
    "region": "yemen",
    "location": "عربستان، فرودگاه‌های بین‌المللی دمام و ریاض",
    "lat": 26.4712,
    "lng": 49.7978,
    "weapon": "سامانه‌های پدافندی پاتریوت و تاد"
  },
  "US naval blockade strands at least 50 Iranian oil tankers near Iranian coast; zero crude loaded in Shahrivar": {
    "title": "محاصره دریایی آمریکا و توقف ۵۰ سوپرتانکر ایرانی در آب‌های ساحلی خلیج فارس",
    "summary": "بلومبرگ گزارش داد با تشدید گشت‌های ناوبری آمریکا و سخت‌گیری‌های تحریمی، بارگیری نفت خام در پایانه‌های اصلی متوقف شده و ۵۰ نفتکش غول‌پیکر در آب‌های لنگرگاهی متوقف مانده‌اند.",
    "category": "naval",
    "severity": "crit",
    "region": "iran",
    "location": "خلیج فارس، پایانه نفتی جزیره خارگ و عسلویه",
    "lat": 29.2333,
    "lng": 50.3167,
    "weapon": "ناوگان گشت دریایی و نفتکش‌های فوق‌سنگین VLCC"
  },
  "Trump jokes about letting Iran bomb Los Angeles and San Diego at campaign rally": {
    "title": "مزاح جنجالی ترامپ در میتینگ انتخاباتی پیرامون هدف قرار گرفتن شهرهای کالیفرنیا",
    "summary": "دونالد ترامپ در تجمعی انتخاباتی با طعنه به فرماندار کالیفرنیا گفت شاید لازم باشد بگذاریم موشک‌های ایران سن‌دیگو یا لس‌آنجلس را بزنند تا متوجه خطرات شوند!",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایالات متحده، واشنگتن / میتینگ انتخاباتی",
    "lat": 38.8951,
    "lng": -77.0364,
    "weapon": "جنگ روانی و سخنرانی تبلیغاتی"
  },
  "Iran Interior Minister visits Qatar, discusses Iranian pilots' status and bilateral security": {
    "title": "مذاکرات وزیر کشور ایران در دوحه پیرامون توافقات امنیتی و تبادل فنی",
    "summary": "اسکندر مؤمنی در رایزنی‌های سطح بالا با وزیر کشور قطر آخرین وضعیت همکاری‌های امنیتی دوجانبه و استرداد مجرمین را نهایی کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "قطر، دوحه، وزارت کشور",
    "lat": 25.2854,
    "lng": 51.531,
    "weapon": "تفاهم‌نامه‌های امنیتی دوجانبه"
  },
  "Houthi forces publish video from Dhubab city near Bab al-Mandab, denying Saudi claims of territorial loss": {
    "title": "انتشار ویدیوی انصارالله از شهر ذباب در نزدیکی باب‌المندب در رد ادعاهای سعودی",
    "summary": "رسانه جنگی یمن تصاویری زنده از استقرار کامل رزمندگان در شهر ساحلی ذباب مشرف به تنگه باب‌المندب منتشر کرد که ادعای اشغال این شهر توسط ائتلاف را خنثی ساخت.",
    "category": "combat",
    "severity": "ops",
    "region": "yemen",
    "location": "یمن، شهر ساحلی ذباب در مدخل باب‌المندب",
    "lat": 12.9644,
    "lng": 43.4358,
    "weapon": "پدافند ساحلی و یگان‌های تکاوری دریایی"
  },
  "Houthi forces attack Aramco facilities in Jeddah, causing fire": {
    "title": "حمله موشکی-پهپادی انصارالله به تأسیسات نفتی آرامکو در جده و وقوع حریق",
    "summary": "مخازن سوخت و توزیع فرآورده‌های شرکت آرامکو در شمال بندر جده هدف حمله مستقیم پهپادی و موشکی قرار گرفت و ستون‌های دود بر فراز منطقه صنعتی رویت شد.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "عربستان، مخازن نفتی آرامکو در بندر جده",
    "lat": 21.68,
    "lng": 39.17,
    "weapon": "موشک‌های کروز قدس-۳ و پهپادهای انتحاری"
  },
  "Second explosion reported at Jeddah oil refinery, possibly from Yemeni missile strike": {
    "title": "گزارش وقوع دومین انفجار پیاپی در پالایشگاه نفت جده عربستان",
    "summary": "دقایقی پس از موج نخست حمله، انفجار مهیب دومی در محوطه پالایشگاهی جده گزارش شد که حاکی از اصابت موشک دوم به خطوط انتقال است.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "عربستان، محوطه پالایشگاه نفت جده در ساحل دریای سرخ",
    "lat": 21.4858,
    "lng": 39.1925,
    "weapon": "موشک بالستیک نقطه‌زن"
  },
  "Iran's ambassador to Azerbaijan meets FM Araghchi to discuss Tehran-Baku relations": {
    "title": "دیدار سفیر ایران در باکو با وزیر امور خارجه پیرامون تحولات قفقاز و دالان ارس",
    "summary": "سید عباس موسوی با حضور در دفتر وزیر خارجه، گزارشی از آخرین وضعیت روابط دیپلماتیک با جمهوری آذربایجان و امنیت مرزهای مشترک ارائه داد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران / باکو",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "رایزنی‌های دیپلماتیک قفقاز"
  },
  "Houthi forces claim 200+ Saudi-backed casualties in unprecedented strikes at Ras al-Ara and al-Suqya": {
    "title": "تلفات سنگین ۲۰۰ نفری نیروهای ائتلاف در حملات موشکی به رأس‌العاره و السقیه",
    "summary": "سخنگوی نیروهای مسلح یمن اعلام کرد در پی شلیک موشک‌های نقطه‌زن به پادگان‌های تجمع متجاوزان در ساحل غربی بیش از ۲۰۰ تن کشته و زخمی شدند.",
    "category": "missile",
    "severity": "crit",
    "region": "yemen",
    "location": "یمن، سواحل رأس العاره و السقیه در لحج",
    "lat": 12.6333,
    "lng": 44.15,
    "weapon": "موشک‌های بالستیک بومی بدر و زلزال"
  },
  "Iranian medical universities under pressure as overdue students increase; internet outages, lab closures cited": {
    "title": "گزارش اختلالات اینترنت بین‌الملل و تأثیر آن بر مراکز دانشگاهی و پژوهشی",
    "summary": "پایش‌های صورت‌گرفته از زیرساخت ارتباطی نشان‌دهنده نوسانات مقطعی در درگاه‌های بین‌المللی و قطعی‌های پراکنده شبکه است که بر فعالیت آزمایشگاه‌ها اثر گذاشته است.",
    "category": "cyber",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران و دیتاسنترهای زیرساخت کشور",
    "lat": 35.7,
    "lng": 51.4,
    "weapon": "زیرساخت ارتباطی و ترانزیت دیتاسنتر"
  },
  "Iranian Army spokesperson says Iran holds large stockpile of new missiles and drones": {
    "title": "سخنگوی ارتش: انبارهای تسلیحاتی ایران مملو از موشک‌ها و پهپادهای نسل جدید است",
    "summary": "سخنگوی ارتش جمهوری اسلامی ایران اعلام کرد زرادخانه‌های دفاعی کشور با تجهیزات هوشمند، پهپادهای تهاجمی نقطه‌زن و موشک‌های بالستیک دوربرد کاملاً آماده مقابله با هرگونه تهاجم احتمالی هستند.",
    "category": "combat",
    "severity": "intel",
    "region": "iran",
    "location": "ایران، ستاد کل نیروهای مسلح، تهران",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "موشک‌های بالستیک خرمشهر، خیبرشکن و فتاح"
  },
  "Ukraine drones strike Moscow's major jet fuel, diesel, and petrol distribution hub": {
    "title": "حمله پهپادی اوکراین به انبار استراتژیک سوخت جت و پالایشگاه حومه مسکو",
    "summary": "چندین فروند پهپاد دوربرد انتحاری مخازن سوخت هوانوردی و خطوط انتقال بنزین در نزدیکی پایتخت روسیه را هدف قرار داده و آتش‌سوزی وسیعی ایجاد کردند.",
    "category": "combat",
    "severity": "ops",
    "region": "iran",
    "location": "روسیه، مسکو، تأسیسات انبار سوخت کاپوتنیا",
    "lat": 55.65,
    "lng": 37.78,
    "weapon": "پهپادهای تهاجمی انتحاری دوربرد"
  },
  "UN Secretary-General Guterres arrives in Islamabad for three-day official visit": {
    "title": "ورود دبیرکل سازمان ملل به اسلام‌آباد برای گفتگوهای منطقه‌ای بحران خاورمیانه",
    "summary": "آنتونیو گوترش در سفری رسمی با مقامات پاکستان دیدار کرد تا ابتکارات بین‌المللی برای جلوگیری از گسترش دامنه جنگ به جنوب آسیا را مورد بررسی قرار دهد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "پاکستان، اسلام‌آباد، فرودگاه نورخان",
    "lat": 33.6167,
    "lng": 73.1,
    "weapon": "دیپلماسی بین‌المللی سازمان ملل"
  },
  "Saudi Arabia launches airstrikes on Saada and shells village in Hajjah, Yemen": {
    "title": "موج جدید بمباران هوایی ارتش عربستان در صعده و توپخانه‌باران حجه در یمن",
    "summary": "جنگنده‌های ائتلاف سعودی مناطق مسکونی در صعده را بمباران کردند؛ هم‌زمان توپخانه مرزی روستاهای نوار مرزی استان حجه را زیر آتش گرفت.",
    "category": "combat",
    "severity": "crit",
    "region": "yemen",
    "location": "یمن، استان‌های صعده و حجه در شمال",
    "lat": 16.9402,
    "lng": 43.7639,
    "weapon": "جنگنده‌های یوروفایتر تایفون و بمب‌های هدایت لیزری"
  },
  "Yemen Defense Ministry advisor warns Saudi ground operation would be 'suicide', claims Taiz control imminent": {
    "title": "هشدار مشاور وزیر دفاع یمن: هرگونه حمله زمینی عربستان خودکشی محض خواهد بود",
    "summary": "مقام ارشد نظامی یمن اعلام کرد نیروهای مسلح برای هرگونه سناریوی پیشروی زمینی ائتلاف کمین‌های مرگبار آماده کرده‌اند و تسلط بر کل تعز نزدیک است.",
    "category": "alert",
    "severity": "ops",
    "region": "yemen",
    "location": "یمن، استان تعز و محورهای درگیری جنوب غربی",
    "lat": 13.5795,
    "lng": 44.0209,
    "weapon": "تاکتیک‌های نبرد نامتقارن و تله‌های انفجاری"
  },
  "Oil industry manager in Khuzestan arrested on bribery and financial misconduct charges": {
    "title": "بازداشت یکی از مدیران ارشد صنعت نفت در خوزستان به اتهام مفاسد مالی",
    "summary": "سازمان بازرسی و دستگاه قضایی خوزستان از بازداشت مدیر مرتبط با قراردادهای انتقال و خطوط لوله نفتی جنوب به اتهام رشوه و تبانی مالی خبر دادند.",
    "category": "alert",
    "severity": "info",
    "region": "iran",
    "location": "ایران، اهواز و حوزه میادین نفتی خوزستان",
    "lat": 31.3273,
    "lng": 48.694,
    "weapon": "نظارت قضایی و حفاظت اطلاعات اقتصادی"
  },
  "Vehicle carrying explosives intercepted before entering Mashhad after tip-off": {
    "title": "کشف و توقیف خودروی حامل محموله سنگین مواد منفجره در ورودی مشهد",
    "summary": "فرماندهی انتظامی خراسان رضوی اعلام کرد با اشراف اطلاعاتی، یک دستگاه خودروی حامل مقادیر زیادی مواد تخریبی و چاشنی پیش از ورود به شهر مشهد متوقف و متهم بازداشت شد.",
    "category": "alert",
    "severity": "crit",
    "region": "iran",
    "location": "ایران، ورودی کلانشهر مشهد در خراسان رضوی",
    "lat": 36.2972,
    "lng": 59.6067,
    "weapon": "محموله انفجاری صنعتی و چاشنی‌های الکترونیکی"
  },
  "Iran's former oil minister Pak-Nejad rejects Trump's claims about his resignation": {
    "title": "واکنش وزیر سابق نفت به ادعاهای ترامپ: استعفای من ربطی به تحریم‌های آمریکا ندارد",
    "summary": "محسن پاک‌نژاد ادعای دونالد ترامپ مبنی بر استعفا به دلیل فلج شدن صادرات نفت را کذب محض خواند و تاکید کرد شبکه صادرات کشور پایدار است.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، وزارت نفت",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "تکذیبیه رسمی و مصاحبه مطبوعاتی"
  },
  "Kayhan editor Shariatmadari criticizes 7-month parliament suspension, blames Qalibaf appointment": {
    "title": "یادداشت مدیرمسئول کیهان پیرامون ساختار قانون‌گذاری و تصمیم‌گیری‌های کلان در شرایط جنگی",
    "summary": "حسین شریعتمداری در یادداشتی انتقادی بر ضرورت تقویت انسجام مجلس و نهادهای اجرایی در مدیریت اقتصاد شرایط جنگی و مقابله با فشارهای خارجی تاکید کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، روزنامه کیهان",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "تحلیل‌های رسانه‌ای و سرمقاله مطبوعاتی"
  },
  "Explosion and fire shuts down Venezuela's second-largest refinery Cardon": {
    "title": "انفجار و حریق گسترده در پالایشگاه کاردون ونزوئلا؛ تشدید کسری سوخت در بازار نفت",
    "summary": "دومین پالایشگاه بزرگ ونزوئلا پس از وقوع انفجار در واحد تقطیر از مدار خارج شد؛ حادثه‌ای که بر شبکه همکاری پالایشی ایران و کاراکاس نیز اثرگذار است.",
    "category": "alert",
    "severity": "ops",
    "region": "iran",
    "location": "ونزوئلا، شبه‌جزیره پاراگوانا، پالایشگاه کاردون",
    "lat": 11.6333,
    "lng": -70.2167,
    "weapon": "تأسیسات پالایشگاهی نفت خام"
  },
  "US Treasury Secretary Bessent mocks Iran's new oil minister, says no oil loaded since Aug. 25": {
    "title": "ادعای وزیر خزانه‌داری آمریکا: بارگیری نفت در پایانه‌های ایران متوقف شده است",
    "summary": "اسکات بست مدعی شد تحریم‌های ثانویه و گشت‌های دریایی ناوگان ائتلاف مانع از پهلوگیری هرگونه نفتکش خارجی در پایانه‌های صادراتی ایران شده است.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "واشنگتن، وزارت خزانه‌داری ایالات متحده",
    "lat": 38.8977,
    "lng": -77.0365,
    "weapon": "تحریم‌های ثانویه اوفک و جنگ اقتصادی"
  },
  "Trump says Iran's economy 'destroyed', inflation near 300%, oil minister resigned": {
    "title": "سخنرانی ترامپ پیرامون اقتصاد ایران: تورم سنگین و ادعای توقف فروش نفت",
    "summary": "رئیس‌جمهور سابق آمریکا در کارزار انتخاباتی مدعی شد استراتژی فشار حداکثری دوم اقتصاد ایران را در آستانه بحران قرار داده و درآمد نفتی را به صفر نزدیک کرده است.",
    "category": "diplomacy",
    "severity": "intel",
    "region": "iran",
    "location": "واشنگتن، ایالات متحده",
    "lat": 38.8951,
    "lng": -77.0364,
    "weapon": "جنگ روانی و بیانیه‌های تبلیغاتی"
  },
  "IDF, Shin Bet, and Israel Police hold joint security assessment ahead of elections": {
    "title": "نشست ارزیابی امنیتی مشترک ارتش اسرائیل، شاباک و پلیس در میانه آماده‌باش جنگی",
    "summary": "فرماندهان نظامی و امنیتی اسرائیل برای بررسی آسیب‌پذیری‌های جبهه داخلی در برابر حملات موشکی مقاومت و نفوذ سایبری نشست اضطراری تشکیل دادند.",
    "category": "alert",
    "severity": "ops",
    "region": "israel",
    "location": "اراضی اشغالی، تل‌آویو، مقر کریا",
    "lat": 32.0733,
    "lng": 34.7892,
    "weapon": "سامانه‌های پدافندی و نهادهای اطلاعاتی شاباک"
  },
  "Reuters: China's independent refineries cut Iranian oil imports by half, pivot to Iraqi and Qatari crude": {
    "title": "گزارش رویترز: کاهش واردات پالایشگاه‌های مستقل چین از نفت ایران به دلیل ریسک ترانزیت",
    "summary": "رویترز گزارش داد پالایشگاه‌های تی‌پات چین در مواجهه با تهدیدات بیمه‌ای و گشت‌های دریایی خلیج فارس، بخشی از خریدهای خود را به بنادر عراق و قطر شیفت کرده‌اند.",
    "category": "naval",
    "severity": "crit",
    "region": "iran",
    "location": "پکن / بنادر شاندونگ چین و خلیج فارس",
    "lat": 36.6512,
    "lng": 117.1201,
    "weapon": "ترافیک نفتکش‌های VLCC و تحریم‌های بندری"
  },
  "Aramco CEO warns oil market pressure to continue until Strait of Hormuz fully reopens": {
    "title": "هشدار مدیرعامل آرامکو: بحران انرژی تا بازگشایی کامل و ایمن تنگه هرمز ادامه دارد",
    "summary": "امین ناصر مدیرعامل غول نفتی آرامکو تاکید کرد ناامنی تنگه هرمز ظرفیت‌های مازاد اوپک را قفل کرده و قیمت جهانی نفت را در محدوده پرریسک نگه داشته است.",
    "category": "naval",
    "severity": "crit",
    "region": "iran",
    "location": "عربستان، ظهران، مقر شرکت ملی نفت آرامکو",
    "lat": 26.3,
    "lng": 50.1333,
    "weapon": "بازار جهانی نفت خام و امنیت تنگه هرمز"
  },
  "Shell CEO: Middle East oil exports recovered to 80% of pre-war levels": {
    "title": "اظهارات مدیرعامل شل: صادرات نفت خاورمیانه به ۸۰ درصد سطح پیش از جنگ بازگشت",
    "summary": "وائل صوان مدیرعامل شرکت نفتی شل اعلام کرد با وجود حملات موشکی و پهپادی، ترانزیت انرژی با تغییر مسیرها و اسکورت‌های مسلح تا حدودی احیا شده است.",
    "category": "naval",
    "severity": "ops",
    "region": "iran",
    "location": "لندن، مقر بین‌المللی شل / دریای عمان",
    "lat": 51.5074,
    "lng": -0.1278,
    "weapon": "مسیرهای فرعی ناوبری و اسکورت دریایی"
  },
  "Pezeshkian appoints former Oil Minister Pak-Nejad as presidential advisor": {
    "title": "انتصاب محسن پاک‌نژاد به عنوان مشاور رئیس‌جمهور در امور راهبردی انرژی",
    "summary": "مسعود پزشکیان با صدور حکمی وزیر پیشین نفت را به عنوان مشاور ویژه برای مدیریت فروش نفت و دیپلماسی انرژی در شرایط تحریمی منصوب کرد.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، پاستور",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "مدیریت بحران انرژی و حکمرانی نفت"
  },
  "Iran acting Oil Minister clarifies role of trustees vs traders in oil export currency repatriation": {
    "title": "توضیحات سرپرست وزارت نفت درباره شبکه تراستی‌ها و بازگشت ارز حاصل از صادرات خام",
    "summary": "حمید بورد در تشریح سازوکارهای دور زدن تحریم‌ها تاکید کرد کانال‌های تراستی معتمد تحت نظارت بانک مرکزی تضمین‌کننده نقدشوندگی درآمدهای ارزی کشور هستند.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، ساختمان وزارت نفت",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "شبکه مالی تراستی و کانال‌های ارزی"
  },
  "Iran VP Aref expects oil ministry leap under new minister Bourd, dismisses sanctions fears": {
    "title": "محمدرضا عارف: صنعت نفت با مدیریت جدید از تنگناهای تحریم عبور خواهد کرد",
    "summary": "معاون اول رئیس‌جمهور در آیین تکریم و معارفه وزیر نفت تاکید کرد تولید نفت و گاز کشور با اتکا به متخصصان داخلی و شرکای شرقی بدون وقفه ادامه خواهد یافت.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "ایران، تهران، نهاد ریاست‌جمهوری",
    "lat": 35.6892,
    "lng": 51.389,
    "weapon": "سیاست‌های کلان اقتصاد مقاومتی"
  },
  "Saudi Arabia's East-West oil pipeline pumping 5.8 million barrels after resuming operations": {
    "title": "افزایش ظرفیت خط لوله نفت شرق به غرب عربستان به ۵.۸ میلیون بشکه در روز",
    "summary": "شرکت آرامکو برای دور زدن خطرات تنگه هرمز، انتقال نفت از میادین شرقی به بندر ینبع در ساحل دریای سرخ را با حداکثر توان عملیاتی خط لوله پیترولاین به جریان انداخت.",
    "category": "naval",
    "severity": "ops",
    "region": "yemen",
    "location": "عربستان، بندر ینبع و خط لوله پترولاین دریای سرخ",
    "lat": 24.09,
    "lng": 38.06,
    "weapon": "خط لوله انتقال نفت پترولاین شرق-غرب"
  },
  "Russia's $1 billion loan to Iran ready for transfer; Iran yet to provide account number amid internal dispute": {
    "title": "آمادگی روسیه برای واریز وام ۱ میلیارد دلاری به پروژه‌های ریلی و انرژی ایران",
    "summary": "وزارت دارایی روسیه اعلام کرد خط اعتباری مصوب برای تأمین مالی نیروگاه سیریک و خطوط راه‌آهن شمال-جنوب آماده پرداخت نهایی به حساب‌های معرفی‌شده است.",
    "category": "diplomacy",
    "severity": "info",
    "region": "iran",
    "location": "مسکو / تهران، بانک مرکزی",
    "lat": 55.7558,
    "lng": 37.6173,
    "weapon": "خطوط اعتباری بین‌المللی و توافقات بانکی"
  },
  "Oil prices rise on Middle East supply concerns; Brent reaches $100.59/barrel": {
    "title": "جهش نفت برنت به بالای ۱۰۰ دلار در پی تشدید حملات موشکی به تأسیسات انرژی خلیج فارس",
    "summary": "در پی اصابت موشک‌ها به پالایشگاه رابغ و توقف تردد نفتکش‌ها در تنگه هرمز، بهای هر بشکه نفت خام برنت در بازارهای جهانی با رشد تند به ۱۰۰.۵۹ دلار رسید.",
    "category": "naval",
    "severity": "crit",
    "region": "iran",
    "location": "خلیج فارس و بازارهای جهانی انرژی، لندن/نیویورک",
    "lat": 26.0,
    "lng": 55.0,
    "weapon": "شوک قیمت انرژی و پرمیوم ریسک جنگ"
  }
}

def get_fa_relative_time(iso_str):
    if not iso_str:
        return "چند ساعت پیش", 3.0
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff_hours = (now - dt).total_seconds() / 3600.0
        if diff_hours < 0:
            diff_hours = 0.5
        if diff_hours < 1:
            m = max(5, int(diff_hours * 60))
            return f"{m} دقیقه پیش", round(diff_hours, 1)
        elif diff_hours < 24:
            h = int(diff_hours)
            return f"{h} ساعت پیش", round(diff_hours, 1)
        else:
            d = int(diff_hours / 24)
            return f"{d} روز پیش", round(diff_hours, 1)
    except Exception:
        return "چند ساعت پیش", 4.0

def sync_from_iranmonitor():
    global LIVE_WIRE
    print("[SYNC] Fetching live crisis intelligence from iranmonitor.org/api/events...")
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            'https://www.iranmonitor.org/api/events?limit=200',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            raw = json.loads(resp.read().decode('utf-8'))
        
        raw_events = raw.get('data', [])
        if not raw_events:
            print("[SYNC] No events returned from Iran Monitor API.")
            return len(load_events())

        # Base tactical events
        existing = load_events()
        # Keep base tac events
        tac_events = [e for e in existing if e.get('id', '').startswith('tac-')]
        if not tac_events:
            tac_events = DEFAULT_EVENTS[:3]

        synced_items = []
        for ev in raw_events:
            t_en = ev.get('title', '').strip()
            meta = IRAN_MONITOR_TRANSLATIONS.get(t_en)
            if not meta:
                continue
            
            iso_time = ev.get('event_timestamp')
            fa_time, hours_ago = get_fa_relative_time(iso_time)
            
            src_details = ev.get('source_details', [])
            src_names = [s.get('display_name') for s in src_details if s.get('display_name')]
            if not src_names:
                src_str = "Iran Monitor"
            else:
                src_str = "Iran Monitor • " + " • ".join(dict.fromkeys(src_names))
            
            src_urls = ev.get('source_urls', [])

            item = {
                "id": f"im-{ev.get('id', '')[:8]}",
                "title": meta["title"],
                "category": meta["category"],
                "severity": meta["severity"],
                "region": meta["region"],
                "location": meta["location"],
                "lat": meta["lat"],
                "lng": meta["lng"],
                "time": fa_time,
                "hoursAgo": hours_ago,
                "summary": meta["summary"],
                "weapon": meta["weapon"],
                "source": src_str,
                "sourceUrls": src_urls,
                "isHot": meta["severity"] == "crit",
                "origin": "iranmonitor",
                "impact": ev.get('impact_score', 1)
            }
            synced_items.append(item)

        if synced_items:
            merged = tac_events + synced_items
            save_events(merged)
            print(f"[SYNC] Successfully updated {len(merged)} events in {DATA_FILE}.")

            # Update LIVE_WIRE with top breaking items
            new_wire = []
            for item in synced_items[:6]:
                tag = "فوری" if item['severity'] == 'crit' else ("عملیاتی" if item['severity'] == 'ops' else "تحلیلی")
                new_wire.append({
                    "source": item['source'].split('•')[0].strip() if '•' in item['source'] else item['source'],
                    "title": item['title'],
                    "time": item['time'],
                    "tag": tag
                })
            if new_wire:
                LIVE_WIRE = new_wire
            return len(merged)
        return len(existing)
    except Exception as e:
        print("[SYNC ERROR] Failed to sync from Iran Monitor:", e)
        return len(load_events())

def background_sync_worker():
    # Initial pause
    time.sleep(10)
    try:
        sync_from_iranmonitor()
    except Exception as e:
        print("[BG SYNC] Initial run error:", e)
    while True:
        try:
            time.sleep(600)  # every 10 minutes
            sync_from_iranmonitor()
        except Exception as e:
            print("[BG SYNC] Loop error:", e)


class OsintHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p in ("/events", "/osint/api/events"):
            events = load_events()
            res = json.dumps({"ok": True, "events": events, "count": len(events)}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(res)
            return

        elif p in ("/pulse", "/osint/api/pulse"):
            res = json.dumps({"ok": True, "data": IRAN_MONITOR_DATA, "timestamp": int(time.time())}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(res)
            return

        elif p in ("/live_wire", "/osint/api/live_wire"):
            res = json.dumps({"ok": True, "wire": LIVE_WIRE, "timestamp": int(time.time())}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(res)
            return

        
        elif p in ("/sync_iranmonitor", "/osint/api/sync_iranmonitor"):
            count = sync_from_iranmonitor()
            res = json.dumps({"ok": True, "count": count, "message": "همگام‌سازی رویدادها با دیده‌بان بحران Iran Monitor انجام شد."}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(res)
            return

        elif p in ("/health", "/osint/api/health"):
            res = json.dumps({"ok": True, "service": "osint-radar", "status": "operational"}).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(res)
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        p = urllib.parse.urlparse(self.path).path
        if p in ("/events", "/osint/api/events"):
            try:
                length = int(self.headers.get('content-length', 0))
                body = self.rfile.read(length).decode('utf-8')
                new_evt = json.loads(body)
                if not new_evt.get("title") or not new_evt.get("lat") or not new_evt.get("lng"):
                    self.send_error(400, "Missing required event fields")
                    return
                events = load_events()
                new_evt["id"] = f"evt-{int(time.time())}"
                new_evt["time"] = "هم‌اکنون"
                new_evt["hoursAgo"] = 0.0
                new_evt["isHot"] = True
                events.insert(0, new_evt)
                save_events(events)

                res = json.dumps({"ok": True, "event": new_evt, "count": len(events)}, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(res)
                return
            except Exception as e:
                self.send_error(500, str(e))
                return

        self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        pass

class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def run():
    # Pre-populate events.json if not present
    if not os.path.exists(DATA_FILE):
        save_events(DEFAULT_EVENTS)
    server = ThreadingServer(('127.0.0.1', PORT), OsintHandler)
    print(f"OSINT server running on 127.0.0.1:{PORT}")
    threading.Thread(target=background_sync_worker, daemon=True).start()
    server.serve_forever()

if __name__ == '__main__':
    run()
