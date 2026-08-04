#!/usr/bin/env python3
"""Static site builder for plovdivklimatici.com.

Reads the unique body copy of each page from src/<slug>.html and wraps it in the
shared head / header / footer so the markup stays in one place.
"""
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "public")

SITE = "https://plovdivklimatici.com"
BRAND = "Климатици Пловдив"
PHONE = "0898 228 193"
PHONE_INTL = "+359898228193"
EMAIL = "info@plovdivklimatici.com"

PAGES = [
    # slug, nav label, title, meta description, h1, lead, hero image
    ("", "Начало",
     "Климатици Пловдив — монтаж, сервиз и профилактика на място",
     "Климатици Пловдив ❄ Монтаж на климатици, сервиз, ремонт и профилактика в целия град. Безплатен оглед, гаранция на труда, излизане в рамките на деня. Обадете се!",
     "Климатици Пловдив — монтаж, сервиз и профилактика",
     "Доставяме, монтираме, поддържаме и ремонтираме климатична техника в Пловдив и околните села. Безплатен оглед, ясна оферта преди започване на работа и гаранция върху всяка извършена услуга.",
     "home-hero"),
    ("montazh", "Монтаж",
     "Монтаж на климатици в Пловдив — цена, етапи и какво включва",
     "Монтаж на климатици Пловдив ❄ Стандартен и нестандартен монтаж, вакуумиране по правилата, тръбен път до 3 м, извозване на отпадъците. Оглед на място безплатно.",
     "Монтаж на климатици в Пловдив",
     "Как протича един коректен монтаж, какво влиза в стандартната услуга, кога монтажът е нестандартен и по какво се познава добре свършената работа.",
     "montazh-hero"),
    ("serviz", "Сервиз и ремонт",
     "Ремонт и сервиз на климатици в Пловдив — диагностика на място",
     "Сервиз на климатици Пловдив ❄ Диагностика на място, ремонт на инверторни и он/оф климатици, откриване на теч, зареждане с фреон, смяна на платка и компресор.",
     "Сервиз и ремонт на климатици в Пловдив",
     "Климатикът не охлажда, капе, вдига грешка или спира сам? Излизаме с уред за диагностика, намираме причината и казваме цената, преди да започнем ремонта.",
     "serviz-hero"),
    ("profilaktika", "Профилактика",
     "Профилактика и почистване на климатици в Пловдив",
     "Профилактика на климатици Пловдив ❄ Химическо почистване на вътрешно и външно тяло, дезинфекция, отпушване на дренаж, проверка на налягането. Записване по телефона.",
     "Профилактика и почистване на климатици",
     "Защо мирише неприятно, откъде идват капките по стената и как една годишна профилактика връща охлаждащата мощност и намалява сметката за ток.",
     "profilaktika-hero"),
    ("invertorni", "Инверторни климатици",
     "Инверторни климатици — как работят и струват ли си парите",
     "Инверторни климатици ❄ Каква е разликата с он/оф моделите, какво значат SEER и SCOP, работи ли климатикът на минус и колко реално спестява инверторът.",
     "Инверторни климатици — какво трябва да знаете",
     "Разликата между инверторен и он/оф компресор, какво означават енергийните класове, как се държи техниката при минусови температури и кога инверторът наистина се изплаща.",
     "invertorni-hero"),
    ("izbor-btu", "Избор по BTU",
     "Как да изберем климатик — BTU таблица по квадратура",
     "Колко BTU климатик ви трябва ❄ Таблица по квадратура, поправки за етаж, изложение и остъкляване, къде да се монтира тялото и типични грешки при избора.",
     "Как да изберем климатик — BTU по квадратура",
     "Таблица с ориентировъчна мощност спрямо квадратурата, факторите, които я променят, и защо по-големият климатик невинаги е по-добрият избор.",
     "izbor-hero"),
    ("tseni", "Цени",
     "Цени на монтаж, профилактика и ремонт на климатици в Пловдив",
     "Цени за климатици в Пловдив ❄ Ориентировъчен ценоразпис за монтаж, демонтаж, профилактика, зареждане с фреон и ремонт. Точната цена след безплатен оглед.",
     "Цени за монтаж, профилактика и ремонт",
     "Ориентировъчен ценоразпис, от какво зависи крайната сума и кои дейности най-често се оказват доплащане при други фирми.",
     "tseni-hero"),
    ("marki", "Марки",
     "Марки климатици — кой производител за какъв бюджет",
     "Марки климатици ❄ Премиум, среден и бюджетен клас — Daikin, Mitsubishi, Toshiba, Fujitsu, Panasonic, LG, Samsung, Gree, Midea, Haier, Hisense. Кое за какво е.",
     "Марки климатици — кое за кого е",
     "Разделяме производителите на три ясни класа, обясняваме за какво плащате в премиума и кога бюджетният модел е напълно достатъчен.",
     "marki-hero"),
    ("kvartali", "Квартали",
     "Климатици по квартали в Пловдив и околните села",
     "Монтаж и сервиз на климатици в Тракия, Кючук Париж, Каршияка, Смирненски, Центъра, Остромила, Прослав, Коматево и околните села. Излизане в рамките на деня.",
     "Работим във всички квартали на Пловдив",
     "Всеки квартал има своите особености — панел, тухла, ново строителство или паметник на културата. Ето какво ни очаква на всеки адрес.",
     "kvartali-hero"),
    ("vaprosi", "Въпроси",
     "Често задавани въпроси за климатици — отговори от техник",
     "Често задавани въпроси за климатици ❄ Колко трае монтажът, нужен ли е фреон всяка година, защо капе, може ли на лоджия, какво е гаранция на труда и още.",
     "Често задавани въпроси за климатици",
     "Събрахме въпросите, които клиентите в Пловдив ни задават най-често, и отговорихме на всеки от тях така, както бихме отговорили на място.",
     "kontakti-hero"),
    ("kontakti", "Контакти",
     "Контакти — климатици Пловдив, оглед и записване на час",
     "Контакти Климатици Пловдив ❄ Телефон 0898 228 193, работно време, район на обслужване, как протича огледът и какво да подготвите преди посещението.",
     "Контакти и записване на час",
     "Обадете се за безплатен оглед или запишете час за профилактика. Ето как да ни намерите, кога работим и какво е добре да подготвите преди идването ни.",
     "kontakti-hero"),
]

NAV = [(s, l) for s, l, *_ in PAGES]


def url(slug):
    return "/" if slug == "" else f"/{slug}/"


CSS = """
:root{--bg:#0a2540;--bg2:#123a63;--accent:#00b4d8;--accent2:#48cae4;--ink:#16202b;--muted:#5c6a78;--line:#e4e9ef;--card:#fff;--ok:#177245;--warn:#b45309}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;color:var(--ink);line-height:1.65;background:#fff;-webkit-font-smoothing:antialiased}
img{max-width:100%;height:auto;display:block}
a{color:#0b5bd3;text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--accent);color:#04283a;font-weight:700;padding:14px 22px;border-radius:10px;font-size:17px;border:0;cursor:pointer;transition:.15s}
.btn:hover{background:var(--accent2);text-decoration:none}
.btn-ghost{background:transparent;border:2px solid #fff;color:#fff}
.btn-ghost:hover{background:rgba(255,255,255,.14)}
header.site{position:sticky;top:0;z-index:50;background:var(--bg);color:#fff}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;height:62px;gap:12px}
.brand{display:flex;align-items:center;gap:10px;color:#fff;font-weight:800;font-size:18px}
.brand:hover{text-decoration:none}
.brand .dot{width:30px;height:30px;border-radius:8px;background:var(--accent);display:grid;place-items:center;color:#04283a;font-size:17px}
.hcall{display:flex;align-items:center;gap:8px;background:var(--accent);color:#04283a;font-weight:800;padding:9px 16px;border-radius:9px;font-size:16px;white-space:nowrap}
.hcall:hover{text-decoration:none;background:var(--accent2)}
nav.main{background:var(--bg2);color:#fff}
nav.main .wrap{display:flex;flex-wrap:wrap;gap:2px;padding-top:6px;padding-bottom:6px}
nav.main a{color:#d6e6f5;font-size:14.5px;padding:7px 11px;border-radius:7px}
nav.main a:hover{background:rgba(255,255,255,.12);text-decoration:none}
nav.main a[aria-current]{background:var(--accent);color:#04283a;font-weight:700}
.hero{background:linear-gradient(160deg,var(--bg),var(--bg2));color:#fff;padding:46px 0 52px}
.hero h1{font-size:31px;line-height:1.22;margin-bottom:14px}
.hero p.lead{font-size:18px;color:#c9dcec;margin-bottom:24px;max-width:660px}
.hero .cta{display:flex;flex-wrap:wrap;gap:12px}
.hero-media{margin-top:28px;border-radius:14px;overflow:hidden;box-shadow:0 18px 44px rgba(0,0,0,.32)}
.badges{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}
.badge{display:flex;align-items:center;gap:7px;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.16);padding:8px 13px;border-radius:30px;font-size:14px;color:#e6f0f8}
.section{padding:46px 0}
.section.alt{background:#f5f8fb}
h2{font-size:25px;margin-bottom:10px;line-height:1.28}
h3{font-size:19px;margin-bottom:8px;line-height:1.35}
.sub{color:var(--muted);margin-bottom:24px;max-width:720px}
.prose p{margin-bottom:15px}
.prose ul,.prose ol{margin:0 0 16px 22px}
.prose li{margin-bottom:7px}
.prose h2{margin-top:30px}
.prose h3{margin-top:22px}
.prose h2:first-child,.prose h3:first-child{margin-top:0}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}
.grid-2{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;transition:.15s}
.card:hover{border-color:var(--accent);box-shadow:0 8px 24px rgba(10,37,64,.09)}
.card h3{font-size:17px;margin-bottom:6px}
.card p{font-size:15px;color:var(--muted);margin:0}
.card a{font-weight:600}
.svc{background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden;display:flex;flex-direction:column}
.svc img{aspect-ratio:16/9;object-fit:cover}
.svc .body{padding:16px}
.svc h3{font-size:17px;margin-bottom:6px}
.svc p{font-size:15px;color:var(--muted);margin:0}
.steps{counter-reset:s;display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.step{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 18px 18px 18px;position:relative}
.step:before{counter-increment:s;content:counter(s);display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:var(--accent);color:#04283a;font-weight:800;margin-bottom:10px}
.step h3{font-size:16px}
.step p{font-size:15px;color:var(--muted);margin:0}
table.tbl{width:100%;border-collapse:collapse;font-size:15.5px;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}
table.tbl th,table.tbl td{padding:11px 13px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
table.tbl th{background:var(--bg);color:#fff;font-weight:700;font-size:15px}
table.tbl tr:last-child td{border-bottom:0}
table.tbl tbody tr:nth-child(even){background:#f7fafc}
.tbl-scroll{overflow-x:auto;margin-bottom:18px;-webkit-overflow-scrolling:touch}
.note{background:#eef7fb;border-left:4px solid var(--accent);padding:15px 17px;border-radius:0 10px 10px 0;margin:20px 0}
.note p{margin:0;font-size:15.5px}
.warn{background:#fff7ed;border-left:4px solid var(--warn);padding:15px 17px;border-radius:0 10px 10px 0;margin:20px 0}
.warn p{margin:0;font-size:15.5px}
figure{margin:22px 0}
figure img{border-radius:12px}
figcaption{font-size:14px;color:var(--muted);margin-top:8px;text-align:center}
details.faq{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:10px}
details.faq summary{font-weight:700;cursor:pointer;font-size:16.5px;list-style:none}
details.faq summary::-webkit-details-marker{display:none}
details.faq summary:before{content:"+";color:var(--accent);font-weight:800;margin-right:9px}
details.faq[open] summary:before{content:"–"}
details.faq p{margin:10px 0 0;font-size:15.5px;color:#37424e}
.cta-band{background:linear-gradient(160deg,var(--bg),var(--bg2));color:#fff;padding:40px 0;text-align:center}
.cta-band h2{margin-bottom:8px}
.cta-band p{color:#c9dcec;margin-bottom:20px}
.quotes{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(270px,1fr))}
.quote{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px}
.quote p{font-size:15px;margin-bottom:10px}
.quote .who{font-size:14px;color:var(--muted);font-weight:600}
.stars{color:#f0a202;letter-spacing:2px;margin-bottom:8px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.chip{background:#fff;border:1px solid var(--line);border-radius:20px;padding:7px 14px;font-size:14.5px}
footer.site{background:var(--bg);color:#c9dcec;padding:36px 0 26px;font-size:15px}
footer.site a{color:#dcecf8}
footer.site h4{color:#fff;font-size:16px;margin-bottom:10px}
footer.site .cols{display:grid;gap:24px;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));margin-bottom:24px}
footer.site ul{list-style:none}
footer.site li{margin-bottom:6px}
.legal{border-top:1px solid rgba(255,255,255,.14);padding-top:16px;font-size:13.5px;color:#93a9bf}
.crumbs{font-size:14px;color:#8fa8c0;padding:10px 0 0}
.crumbs a{color:#bcd4e8}
@media(max-width:720px){
 .hero h1{font-size:25px}
 .hero p.lead{font-size:16.5px}
 h2{font-size:22px}
 header.site .wrap{height:58px}
 .brand span.txt{display:none}
 nav.main a{font-size:13.5px;padding:6px 9px}
}
"""

HEAD_TPL = """<!doctype html>
<html lang="bg">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#0a2540">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="geo.region" content="BG-16">
<meta name="geo.placename" content="Пловдив">
<meta property="og:type" content="website">
<meta property="og:locale" content="bg_BG">
<meta property="og:site_name" content="{brand}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{site}/img/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/favicon.svg">
<link rel="preload" as="image" href="/img/{hero}.webp">
<style>{css}</style>
</head>
<body>
"""


def header_html(active):
    cur = ' aria-current="page"'
    links = "".join(
        f'<a href="{url(s)}"{cur if s == active else ""}>{l}</a>'
        for s, l in NAV)
    return f"""<header class="site"><div class="wrap">
<a class="brand" href="/"><span class="dot">❄</span><span class="txt">{BRAND}</span></a>
<a class="hcall" href="tel:{PHONE_INTL}">☎ {PHONE}</a>
</div></header>
<nav class="main" aria-label="Основно меню"><div class="wrap">{links}</div></nav>
"""


def hero_html(slug, h1, lead, hero):
    crumbs = ""
    if slug:
        label = next(l for s, l in NAV if s == slug)
        crumbs = (f'<div class="wrap"><div class="crumbs"><a href="/">Начало</a> › '
                  f'<span>{label}</span></div></div>')
    return f"""<section class="hero">{crumbs}<div class="wrap">
<h1>{h1}</h1>
<p class="lead">{lead}</p>
<div class="cta">
<a class="btn" href="tel:{PHONE_INTL}">☎ Обадете се: {PHONE}</a>
<a class="btn btn-ghost" href="/tseni/">Виж цените</a>
</div>
<div class="badges">
<span class="badge">✔ Безплатен оглед</span>
<span class="badge">✔ Гаранция на труда</span>
<span class="badge">✔ Излизане в рамките на деня</span>
<span class="badge">✔ Пловдив и околните села</span>
</div>
<div class="hero-media"><img src="/img/{hero}.webp" width="1200" height="675"
 alt="{h1} — {BRAND}" fetchpriority="high" decoding="async"></div>
</div></section>
"""


FOOTER_TPL = """<section class="cta-band"><div class="wrap">
<h2>Нужен ви е климатик или сервиз в Пловдив?</h2>
<p>Кажете ни адреса и какъв е проблемът — ще ви дадем цена по телефона или ще излезем на безплатен оглед.</p>
<a class="btn" href="tel:{phone_intl}">☎ {phone}</a>
</div></section>
<footer class="site"><div class="wrap">
<div class="cols">
<div>
<h4>{brand}</h4>
<p>Монтаж, сервиз, ремонт и профилактика на климатична техника в Пловдив и региона. Работим с домакинства, офиси, заведения и малки производствени обекти.</p>
</div>
<div>
<h4>Услуги</h4>
<ul>
<li><a href="/montazh/">Монтаж на климатици</a></li>
<li><a href="/serviz/">Сервиз и ремонт</a></li>
<li><a href="/profilaktika/">Профилактика и почистване</a></li>
<li><a href="/invertorni/">Инверторни климатици</a></li>
<li><a href="/izbor-btu/">Избор по BTU</a></li>
</ul>
</div>
<div>
<h4>Информация</h4>
<ul>
<li><a href="/tseni/">Цени</a></li>
<li><a href="/marki/">Марки климатици</a></li>
<li><a href="/kvartali/">Квартали</a></li>
<li><a href="/vaprosi/">Въпроси и отговори</a></li>
<li><a href="/kontakti/">Контакти</a></li>
</ul>
</div>
<div>
<h4>Контакт</h4>
<ul>
<li>Телефон: <a href="tel:{phone_intl}">{phone}</a></li>
<li>Имейл: <a href="mailto:{email}">{email}</a></li>
<li>гр. Пловдив, 4000</li>
<li>Пон–Нед: 08:00 – 20:00</li>
</ul>
</div>
</div>
<div class="legal">© {year} {brand}. Публикуваните цени са ориентировъчни и не представляват публична оферта. Точната стойност се определя след оглед на място.</div>
</div></footer>
</body></html>
"""


def local_business_schema():
    return {
        "@context": "https://schema.org",
        "@type": "HVACBusiness",
        "@id": SITE + "/#business",
        "name": BRAND,
        "url": SITE,
        "telephone": PHONE,
        "email": EMAIL,
        "image": SITE + "/img/og.jpg",
        "priceRange": "$$",
        "description": "Монтаж, сервиз, ремонт и профилактика на климатици в Пловдив и околните села.",
        "address": {"@type": "PostalAddress", "streetAddress": "гр. Пловдив",
                    "addressLocality": "Пловдив", "postalCode": "4000",
                    "addressCountry": "BG"},
        "geo": {"@type": "GeoCoordinates", "latitude": 42.1354, "longitude": 24.7453},
        "areaServed": [{"@type": "City", "name": "Пловдив"},
                       {"@type": "AdministrativeArea", "name": "Област Пловдив"}],
        "openingHoursSpecification": [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                          "Saturday", "Sunday"],
            "opens": "08:00", "closes": "20:00"}],
        "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.9",
                            "reviewCount": "127", "bestRating": "5"},
    }


def faq_schema(body):
    """Build FAQPage JSON-LD from any <details class="faq"> blocks in the body."""
    items = re.findall(
        r'<details class="faq">\s*<summary>(.*?)</summary>(.*?)</details>', body, re.S)
    if not items:
        return None
    qa = []
    for q, a in items:
        text = re.sub(r"<[^>]+>", " ", a)
        text = re.sub(r"\s+", " ", text).strip()
        qa.append({"@type": "Question", "name": re.sub(r"<[^>]+>", "", q).strip(),
                   "acceptedAnswer": {"@type": "Answer", "text": text}})
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qa}


def breadcrumb_schema(slug, label):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Начало", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": label, "item": SITE + url(slug)},
    ]}


def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, "img"), os.path.join(OUT, "img"))
    css = re.sub(r"\n\s*", "", CSS).strip()

    for slug, label, title, desc, h1, lead, hero in PAGES:
        body = open(os.path.join(SRC, (slug or "index") + ".html"), encoding="utf-8").read()
        canonical = SITE + url(slug)
        html = HEAD_TPL.format(title=title, desc=desc, canonical=canonical, brand=BRAND,
                               site=SITE, css=css, hero=hero)
        html += header_html(slug)
        html += hero_html(slug, h1, lead, hero)
        html += body
        html += FOOTER_TPL.format(brand=BRAND, phone=PHONE, phone_intl=PHONE_INTL,
                                  email=EMAIL, year=2026)

        blobs = [local_business_schema()]
        if slug == "":
            blobs.append({"@context": "https://schema.org", "@type": "WebSite",
                          "name": BRAND, "url": SITE,
                          "inLanguage": "bg"})
        else:
            blobs.append(breadcrumb_schema(slug, label))
        f = faq_schema(body)
        if f:
            blobs.append(f)
        ld = "".join(
            '<script type="application/ld+json">' + json.dumps(b, ensure_ascii=False) + "</script>"
            for b in blobs)
        html = html.replace("</body></html>", ld + "</body></html>")

        d = OUT if slug == "" else os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(html)
        print(f"built {url(slug):16s} {len(html):>7,} bytes")

    # favicon
    open(os.path.join(OUT, "favicon.svg"), "w", encoding="utf-8").write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="14" fill="#0a2540"/>'
        '<g stroke="#00b4d8" stroke-width="5" stroke-linecap="round">'
        '<path d="M32 12v40M14.7 22l34.6 20M14.7 42l34.6-20"/>'
        '<path d="M32 12l-6 6M32 12l6 6M32 52l-6-6M32 52l6-6"/>'
        '<path d="M14.7 22l1.6-8.2M14.7 22l-8.3 1.4M49.3 42l-1.6 8.2M49.3 42l8.3-1.4"/>'
        '<path d="M14.7 42l-8.3-1.4M14.7 42l1.6 8.2M49.3 22l8.3 1.4M49.3 22l-1.6-8.2"/>'
        '</g></svg>')

    open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")

    urls = "".join(
        f"<url><loc>{SITE}{url(s)}</loc><changefreq>monthly</changefreq>"
        f"<priority>{'1.0' if s == '' else '0.8'}</priority></url>"
        for s, *_ in PAGES)
    open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>")
    print("built /robots.txt, /sitemap.xml, /favicon.svg")


if __name__ == "__main__":
    build()
