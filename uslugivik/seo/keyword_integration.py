#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyword integration for uslugivik.com
=====================================

What it does
------------
1. Loads Google keywords:
     * seo/keywords/google_suggest.txt      - Google autocomplete suggestions (one per line)
     * seo/keywords/gsc/*.csv               - optional Google Search Console "Queries" exports
                                              (Performance report -> Export -> CSV, full date range)
2. Drops keywords that are not about ВиК services in Sofia (other cities, water-utility
   account queries, competitor brands, product purchases, off-topic phrases).
3. Maps every remaining keyword to the page that should rank for it (service page,
   neighbourhood page or a hub page).
4. Checks whether the keyword already appears in that page's visible text. If it does not,
   the page gets a "Какво още търсят клиентите" block with natural Bulgarian sentences that
   contain the keyword verbatim, plus internal links.
5. Adds keyword-anchored internal links (service <-> neighbourhood <-> hub pages).
6. Bumps <lastmod> in sitemap.xml and "dateModified" in JSON-LD for every changed page and
   writes seo/keyword_report.csv.

The block is wrapped in <!--kwsec--> ... <!--/kwsec--> markers, so the script is idempotent:
re-running it (for example after adding a fresh Search Console export) replaces the block.

Usage (from the uslugivik/ directory):
    python3 seo/keyword_integration.py            # apply
    python3 seo/keyword_integration.py --dry-run  # only report
"""
import argparse
import collections
import csv
import datetime
import glob
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
PUBLIC = os.path.join(BASE, "public")
KW_DIR = os.path.join(HERE, "keywords")
REPORT = os.path.join(HERE, "keyword_report.csv")
TODAY = datetime.date.today().isoformat()

# --------------------------------------------------------------------------------------
# Site model
# --------------------------------------------------------------------------------------
# slug -> (display name, lowercase phrase used inside generated sentences/anchors)
SERVICES = {
    "otpushvane-na-kanali": ("Отпушване на канали", "отпушване на канали"),
    "otpushvane-na-toaletna": ("Отпушване на тоалетна", "отпушване на тоалетна"),
    "otpushvane-na-mivka": ("Отпушване на мивка и сифон", "отпушване на мивка и сифон"),
    "vodoprovodchik": ("Водопроводчик София", "водопроводчик"),
    "avariyni-vik-uslugi": ("Аварийни ВиК услуги 24/7", "аварийни ВиК услуги"),
    "otkrivane-na-techove": ("Откриване на течове", "откриване на течове"),
    "smyana-na-shtrangove": ("Смяна на щрангове", "смяна на щрангове"),
    "remont-na-vodoprovod": ("Ремонт на спукана тръба и водопровод", "ремонт на водопровод"),
    "montazh-na-boyler": ("Монтаж на бойлер", "монтаж на бойлер"),
    "smyana-na-vodomer": ("Смяна на водомер", "смяна на водомер"),
    "montazh-na-toaletna-chiniya": ("Монтаж на тоалетна чиния", "монтаж на тоалетна чиния"),
    "remont-na-toaletno-kazanche": ("Ремонт на тоалетно казанче", "ремонт на тоалетно казанче"),
    "montazh-na-mivka-i-smesitel": ("Монтаж на мивка и смесител", "монтаж на мивка и смесител"),
    "montazh-na-dush-kabina": ("Монтаж на душ кабина и вана", "монтаж на душ кабина"),
    "montazh-na-peralnya": ("Монтаж на пералня и съдомиялна", "монтаж на пералня"),
    "vik-instalatsiya-za-banya": ("ВиК инсталация за баня", "ВиК инсталация за баня"),
    "vik-instalatsiya-na-kashta": ("ВиК инсталация на къща", "ВиК инсталация на къща"),
    "kanalizatsiya": ("Канализация — изграждане и ремонт", "канализация"),
    "videodiagnostika-na-kanali": ("Видеодиагностика на канали", "видеодиагностика на канали"),
    "montazh-na-hidrofor": ("Монтаж на хидрофор", "монтаж на хидрофор"),
    "montazh-na-radiatori": ("Монтаж на радиатори", "монтаж на радиатори"),
}

HUBS = {
    "/": "Начало",
    "/uslugi/": "Услуги",
    "/kvartali/": "Квартали",
    "/tseni/": "Цени",
    "/za-nas/": "За нас",
    "/kontakti/": "Контакти",
    "/zayavka/": "Заявка",
}

# Keyword anchors (real Google queries) used for the "Вижте също" interlinking blocks.
SERVICE_ANCHORS = [
    ("отпушване на канали софия", "/uslugi/otpushvane-na-kanali/"),
    ("водопроводчик софия", "/uslugi/vodoprovodchik/"),
    ("аварийни вик услуги софия", "/uslugi/avariyni-vik-uslugi/"),
    ("откриване на течове софия", "/uslugi/otkrivane-na-techove/"),
    ("смяна на щрангове софия", "/uslugi/smyana-na-shtrangove/"),
    ("монтаж на бойлер софия", "/uslugi/montazh-na-boyler/"),
    ("отпушване на тоалетна", "/uslugi/otpushvane-na-toaletna/"),
    ("отпушване на мивка", "/uslugi/otpushvane-na-mivka/"),
    ("ремонт на водопровод", "/uslugi/remont-na-vodoprovod/"),
    ("смяна на водомери софия", "/uslugi/smyana-na-vodomer/"),
    ("ремонт на тоалетно казанче софия", "/uslugi/remont-na-toaletno-kazanche/"),
    ("монтаж на тоалетна чиния", "/uslugi/montazh-na-toaletna-chiniya/"),
    ("монтаж на мивка", "/uslugi/montazh-na-mivka-i-smesitel/"),
    ("монтаж на душ кабина", "/uslugi/montazh-na-dush-kabina/"),
    ("монтаж на пералня софия", "/uslugi/montazh-na-peralnya/"),
    ("вик инсталация за баня", "/uslugi/vik-instalatsiya-za-banya/"),
    ("вик инсталация на къща", "/uslugi/vik-instalatsiya-na-kashta/"),
    ("канализация софия", "/uslugi/kanalizatsiya/"),
    ("видеодиагностика на канали софия", "/uslugi/videodiagnostika-na-kanali/"),
    ("монтаж на хидрофор", "/uslugi/montazh-na-hidrofor/"),
    ("монтаж на радиатори софия", "/uslugi/montazh-na-radiatori/"),
]

# --------------------------------------------------------------------------------------
# Keyword filters: (reason, regex). A keyword matching any of them is excluded.
# --------------------------------------------------------------------------------------
OTHER_PLACES = [
    "пловдив", "варна", "бургас", "русе", "стара загора", "плевен", "добрич", "шумен", "перник",
    "асеновград", "пазарджик", "велико търново", "търново", "казанлък", "карлово", "сливен",
    "ямбол", "хасково", "кърджали", "благоевград", "видин", "враца", "монтана", "ловеч",
    "габрово", "разград", "силистра", "търговище", "смолян", "кюстендил", "дупница", "ихтиман",
    "елин пелин", "костинброд", "златица", "етрополе", "годеч", "айтос", "балчик", "каварна",
    "шабла", "несебър", "поморие", "царево", "обзор", "свети влас", "влас", "созопол",
    "на морето", "златни пясъци", "горна оряховица", "лясковец", "дряново", "трявна", "тетевен",
    "троян", "луковит", "лом", "оряхово", "мездра", "червен бряг", "ябланица", "исперих",
    "омуртаг", "нови пазар", "нова загора", "чирпан", "димитровград", "харманли", "чепеларе",
    "карнобат", "долни чифлик", "щръклево", "земен", "бяла слатина", "дунав", "южен", "юг",
    "юрий венелин",
]
EXCLUDE = [
    ("other-city", r"\b(" + "|".join(re.escape(p) for p in OTHER_PLACES) + r")\b"),
    ("water-utility", r"проверка|самоотчет|самоотчитане|фактур|\bвход\b|график|жалб|задължения|холдинг|"
                      r"инкасатор|отчитане|\bотчет\b|телефон|контакти|работно време|\bадрес\b|абонатен|"
                      r"сметк|онлайн|планирани ремонти|управител|заплати|новини|ръководство|"
                      r"софийска вода|\bеоод\b|\bоод\b|водопровод и канализация|водоснабдяване и канализация|"
                      r"уличен водопровод|ниско налягане на водата (софия|решение)$|жалба"),
    ("competitor-brand", r"каналито|евроканал|стевика|\bтубо\b|юлекс|елвидом|водострой|капитал сити|"
                         r"мвд сервиз|експресен|елит инженеринг|техем|вик експерт|юроком|щурците|вик жан|"
                         r"хедра|мапей|сика|церезит|практикер|услуги предлагани от"),
    ("off-topic", r"слъзен|гърда|кърмене|окото|на зъб|шибидах|колата|съновник|сънувах|английски|"
                  r"википедия|значение|филм|за помощ|ютуб|юфс|що вик|\bвик ю\b|вик и ват|\bщит\b|"
                  r"горный|южный|хмельницкий|канализационных|\bработа\b|инженер|магазин|\bчасти\b|"
                  r"материали|инструменти|фитинги|железария|щуцер|бг мама|газова бутилка|диспенсър|"
                  r"водосточни|бойлерен ключ|бойлерно табло|слънчев бойлер|^вик тръби$|^вик$|електро|ел услуги|техники"),
    ("product-purchase", r"под наем|камион|машина за|пружина|спирала за|\bтел за|жило|помпа за|уред за|"
                         r"\bкамера за|термокамера за"),
    ("russian", r"[ыэё]"),
    ("duplicate-word", r"\b(\w+) \1\b"),
]

# --------------------------------------------------------------------------------------
# Topic rules: first matching regex decides the service/hub page.
# --------------------------------------------------------------------------------------
TOPIC_RULES = [
    (r"видеодиагностика", "/uslugi/videodiagnostika-na-kanali/"),
    (r"казанче|течаща тоалетна", "/uslugi/remont-na-toaletno-kazanche/"),
    (r"термокамера|\bтеч", "/uslugi/otkrivane-na-techove/"),
    (r"хидрофор", "/uslugi/montazh-na-hidrofor/"),
    (r"радиатор|парно", "/uslugi/montazh-na-radiatori/"),
    (r"пералня", "/uslugi/montazh-na-peralnya/"),
    (r"бойлер", "/uslugi/montazh-na-boyler/"),
    (r"водомер", "/uslugi/smyana-na-vodomer/"),
    (r"(монтаж|демонтаж).*тоалетна|висяща тоалетна|конзолна тоалетна", "/uslugi/montazh-na-toaletna-chiniya/"),
    (r"отпушване на тоалетна|запушена тоалетна|запушен канал на тоалетна", "/uslugi/otpushvane-na-toaletna/"),
    (r"отпушване (на )?(мивка|сифон)|запушена (кухненска )?мивка|запушен канал на мивка|запушена тръба на мивка|"
     r"препарат за запушена мивка|при запушена мивка|много запушена мивка|силно запушена мивка",
     "/uslugi/otpushvane-na-mivka/"),
    (r"душ кабина", "/uslugi/montazh-na-dush-kabina/"),
    (r"монтаж на мивка|смесител|кранче|сифон|батерия", "/uslugi/montazh-na-mivka-i-smesitel/"),
    (r"щранг", "/uslugi/smyana-na-shtrangove/"),
    (r"вик инсталация за баня|вик за баня|хидроизолация", "/uslugi/vik-instalatsiya-za-banya/"),
    (r"вик инсталация|изграждане на вик", "/uslugi/vik-instalatsiya-na-kashta/"),
    (r"отпушване|почистване на канал|запушен канал|канализац.*(отпуш|почист)|машинно|водоструйка|спирала",
     "/uslugi/otpushvane-na-kanali/"),
    (r"канализац|каменинови|вик шахта", "/uslugi/kanalizatsiya/"),
    (r"спукана .*тръба|ремонт (на )?водопровод|смяна на тръби|подмяна на .*тръби|ремонт на вик тръби|"
     r"ниско налягане|смяна на кран|капещ кран|ремонт на водопроводен кран|ремонт на вик инсталации|"
     r"замразяване|подмяна на тръби",
     "/uslugi/remont-na-vodoprovod/"),
    (r"авари|спешн|денонощ", "/uslugi/avariyni-vik-uslugi/"),
    (r"софия област|област софия", "/kvartali/"),
    (r"отзиви|мнения|reviews", "/za-nas/"),
    (r"водопроводчик|вик майстор|вик фирм|ремонт (на )?вик|вик ремонти|водопроводни услуги|търся|"
     r"вик услуги по домовете",
     "/uslugi/vodoprovodchik/"),
    (r"\bцен[аи]\b|за труд|цена на точка", "/tseni/"),
    (r"вик услуги|вик софия|вик и цени", "/"),
]

CATEGORY_RULES = [
    ("diy", r"домашни|препарат|сода|оцет|\bсол\b|кислол|съвет|ароматизатор|мокри кърпи|хартия|пластмаса|"
            r"фекалии|косми|много запушена|силно запушена"),
    ("reviews", r"отзиви|мнения|reviews"),
    ("price", r"\bцен[аи]\b|за труд|цена на точка"),
    ("urgent", r"авари|спешн|денонощ"),
    ("brand", r"grohe|идеал стандарт|интер керамик|bella|\bаег\b|миеле|елдом|теси|видима|грое|рока|фаянс|"
              r"алпака|моноблок|полипропилен"),
]


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def norm(t):
    t = t.lower().replace("ё", "е")
    t = re.sub(r"[„“”\"«»'’‘`]", " ", t)
    t = re.sub(r"[-–—]", " ", t)
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def visible_text(s, strip_block=False):
    if strip_block:  # ignore a block generated by an earlier run, so re-runs are idempotent
        s = re.sub(r"<!--kwsec-->.*?<!--/kwsec-->", " ", s, flags=re.S)
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return norm(html.unescape(s))


KV_PLAIN = set()


def quote_list(kws):
    q = ["„%s“" % pretty_anchor(k, first=False) for k in kws]
    if len(q) == 1:
        return q[0]
    return ", ".join(q[:-1]) + " и " + q[-1]


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def pretty_anchor(kw, first=True):
    """Capitalise ВиК / София / neighbourhood names (and optionally the first word) of a lowercase query."""
    for plain in sorted(KV_PLAIN, key=len, reverse=True):
        kw = re.sub(r"\b" + re.escape(plain) + r"\b", " ".join(x[:1].upper() + x[1:] for x in plain.split()), kw)
    words = kw.split()
    out = []
    for i, w in enumerate(words):
        if w == "вик":
            out.append("ВиК")
        elif w == "софия" or (i == 0 and first):
            out.append(w[:1].upper() + w[1:])
        else:
            out.append(w)
    return " ".join(out)


def page_path_of(fp):
    rel = os.path.relpath(fp, PUBLIC).replace(os.sep, "/")
    return "/" + rel[:-len("index.html")] if rel.endswith("index.html") else "/" + rel


def fp_of(path):
    return os.path.join(PUBLIC, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(PUBLIC, path.strip("/"))


# --------------------------------------------------------------------------------------
# Load site: neighbourhood names
# --------------------------------------------------------------------------------------
def load_kvartali():
    """slug -> {'plain': 'Люлин', 'display': 'ж.к. Люлин'}"""
    idx = open(fp_of("/kvartali/"), encoding="utf-8").read()
    kv = {}
    for slug, name in re.findall(r'href="/kvartali/([a-z0-9-]+)/">(?:ВиК услуги|Водопроводчик) — (.+?)</a>', idx):
        name = html.unescape(name).strip()
        plain = re.sub(r"^(ж\.к\.|кв\.|с\.|гр\.)\s*", "", name)
        kv[slug] = {"plain": plain, "display": name}
    for slug in kv:
        page = open(fp_of("/kvartali/%s/" % slug), encoding="utf-8").read()
        m = re.search(r'<div class="w crumb">.*?› ([^<]+)</div>', page)
        if m:
            kv[slug]["display"] = html.unescape(m.group(1)).strip()
    return kv


# --------------------------------------------------------------------------------------
# Load keywords
# --------------------------------------------------------------------------------------
def load_keywords():
    kws = collections.OrderedDict()  # keyword -> set(sources)
    p = os.path.join(KW_DIR, "google_suggest.txt")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            k = norm(line)
            if k:
                kws.setdefault(k, set()).add("google-suggest")
    for f in sorted(glob.glob(os.path.join(KW_DIR, "gsc", "*.csv"))):
        with open(f, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh))
        if not rows:
            continue
        for row in rows[1:]:
            if not row:
                continue
            k = norm(row[0])
            if k:
                kws.setdefault(k, set()).add("gsc:" + os.path.basename(f))
    return kws


def exclusion_reason(kw):
    for reason, rx in EXCLUDE:
        if re.search(rx, kw):
            return reason
    return None


def category_of(kw, page):
    for cat, rx in CATEGORY_RULES:
        if re.search(rx, kw):
            if cat == "urgent" and page == "/uslugi/avariyni-vik-uslugi/":
                continue
            if cat == "price" and page == "/tseni/":
                continue
            return cat
    return "generic"


def topic_page(kw):
    for rx, page in TOPIC_RULES:
        if re.search(rx, kw):
            return page
    return "/"


def kvartal_targets(kw, kv_names):
    """Return list of kvartal slugs mentioned in the keyword (longest names first)."""
    hits = []
    for plain, slugs in kv_names:
        if re.search(r"\b" + re.escape(plain) + r"\b", kw):
            hits.extend(slugs)
            break
    return hits


# --------------------------------------------------------------------------------------
# Sentence generation
# --------------------------------------------------------------------------------------
def build_paragraphs(page, groups, ctx):
    """groups: category -> [keywords]; ctx: dict with page info. Returns list of <p> strings."""
    ps = []
    where = ctx.get("where", "в София")
    svc = ctx.get("service_phrase")
    svc_link = ctx.get("service_link")

    def emit(cat, first_tpl):
        for n, kws in enumerate(chunks(groups.get(cat, []), 10)):
            if n == 0:
                ps.append(first_tpl % quote_list(kws))
            else:
                ps.append("<p>Същото важи и за търсенията %s.</p>" % quote_list(kws))

    emit("loc",
         "<p>Търсенията %s водят точно тук: " + ctx.get("display", "районът") + " е в ежедневните ни маршрути, "
         "аварийният екип пристига до 60 минути, а цената научавате предварително в отговора на "
         "<a href=\"#zayavka\">заявката</a>.</p>")
    emit("price",
         "<p>Ако сте написали %s — ориентир дава <a href=\"/tseni/\">ценоразписът</a>: фиксирани цени за "
         "стандартните услуги, без такса за транспорт " + where + ", а точната сума ви казваме преди посещението.</p>")
    fix = ("<a href=\"%s\">%s</a>" % (svc_link, svc)) if svc_link else "<a href=\"#zayavka\">изпратете заявка</a>"
    emit("diy",
         "<p>Мнозина първо опитват %s. Домашните методи помагат при леко задръстване в първите сантиметри "
         "на сифона, но когато водата спира отново или изобщо не се оттича, запушването е по-надолу в тръбата "
         "и се решава машинно — " + fix + ".</p>")
    how = "как работим" if page == "/za-nas/" else "<a href=\"/za-nas/\">как работим</a>"
    emit("reviews",
         "<p>Заявки като %s получаваме от хора, които искат да ни проверят, преди да се обадят — вижте "
         "отзивите на клиентите на тази страница и " + how + ".</p>")
    emit("urgent",
         "<p>При %s тръгва аварийният екип: <a href=\"/uslugi/avariyni-vik-uslugi/\">аварийни ВиК услуги</a> "
         "денонощно, включително в празници, с реакция до 60 минути " + where + ".</p>")
    emit("brand",
         "<p>Работим с всички марки и модели — включително търсенията %s — със същите цени и 12 месеца "
         "гаранция за труда.</p>")
    emit("generic",
         "<p>Тази страница отговаря и на търсения като %s — една заявка, конкретна цена преди посещението "
         "и техник с оборудван бус " + where + ".</p>")
    return ps


def build_links(page, kv, kv_demand, kw_by_kvartal_topic):
    """Return list of (anchor_text, href) for the 'Вижте също' line of a page."""
    links = []
    if page.startswith("/uslugi/") and page != "/uslugi/":
        slug = page.strip("/").split("/")[1]
        phrase = SERVICES[slug][1]
        # neighbourhood pages that Google shows demand for, anchored with the service phrase
        for kslug in kv_demand[:8]:
            links.append(("%s — %s" % (phrase[:1].upper() + phrase[1:], kv[kslug]["display"]), "/kvartali/%s/" % kslug))
        # real "<service> <kvartal>" queries pointing to the neighbourhood pages
        for kw, kslug in kw_by_kvartal_topic.get(page, []):
            links.append((pretty_anchor(kw), "/kvartali/%s/" % kslug))
        # two neighbouring services
        others = [a for a in SERVICE_ANCHORS if a[1] != page]
        i = [a[1] for a in SERVICE_ANCHORS].index(page) if page in [a[1] for a in SERVICE_ANCHORS] else 0
        for a in (others[i % len(others)], others[(i + 1) % len(others)]):
            links.append((pretty_anchor(a[0]), a[1]))
    elif page.startswith("/kvartali/") and page != "/kvartali/":
        for kw, href in SERVICE_ANCHORS[:10]:
            links.append((pretty_anchor(kw), href))
    else:  # hubs
        for kw, href in SERVICE_ANCHORS[:12]:
            links.append((pretty_anchor(kw), href))
        for kslug in kv_demand[:8]:
            links.append(("Водопроводчик — %s" % kv[kslug]["display"], "/kvartali/%s/" % kslug))
    # de-duplicate by href, keep order
    seen, out = set(), []
    for text, href in links:
        if href in seen or href == page:
            continue
        seen.add(href)
        out.append((text, href))
    return out


def build_block(page, groups, ctx, links):
    title = "Какво още търсят клиентите"
    if ctx.get("title_suffix"):
        title += " — " + ctx["title_suffix"]
    ps = build_paragraphs(page, groups, ctx)
    if not ps and not links:
        return ""
    parts = ["<div class=\"kwsec\">", "<h2>%s</h2>" % title]
    parts.extend(ps)
    if links:
        parts.append("<p><b>Вижте също:</b> " + " · ".join("<a href=\"%s\">%s</a>" % (h, t) for t, h in links) + "</p>")
    parts.append("</div>")
    return "\n".join(parts)


def insert_block(s, block):
    """Insert (or replace) the generated block. Everything the script adds sits between the
    <!--kwsec--> ... <!--/kwsec--> markers, including the section wrapper used on pages
    without an FAQ heading, so a re-run removes exactly what the previous run added."""
    s = re.sub(r"<!--kwsec-->.*?<!--/kwsec-->\n?", "", s, flags=re.S)
    if not block:
        return s
    m = re.search(r"<h2[^>]*>Чест[ои] (задавани )?въпроси", s)
    if m:  # inside the existing article (.prose), right before the FAQ heading
        return s[:m.start()] + "<!--kwsec-->" + block + "<!--/kwsec-->\n" + s[m.start():]
    wrapped = '<!--kwsec--><div class="sec"><div class="w prose">\n' + block + "\n</div></div><!--/kwsec-->\n"
    m = re.search(r'<div class="sec soft" id="zayavka-sec">', s)
    i = m.start() if m else s.find("<footer>")
    return s[:i] + wrapped + s[i:]


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="only write the report, do not touch pages")
    args = ap.parse_args()

    kv = load_kvartali()
    KV_PLAIN.update(d["plain"].lower() for d in kv.values())
    # plain-name lookup: longest names first; bare "младост" -> all Mladost pages, etc.
    by_plain = collections.OrderedDict()
    for slug, d in kv.items():
        by_plain.setdefault(d["plain"].lower(), []).append(slug)
    bare = collections.defaultdict(list)
    for plain, slugs in by_plain.items():
        root = re.sub(r" \d+$| [вг]$", "", plain)
        if root != plain:
            bare[root].extend(slugs)
    for root, slugs in bare.items():
        if root not in by_plain:
            by_plain[root] = slugs
    by_plain["център"] = by_plain.get("център", ["tsentar"])
    kv_names = sorted(by_plain.items(), key=lambda x: -len(x[0]))

    keywords = load_keywords()
    pages = sorted(glob.glob(os.path.join(PUBLIC, "**", "index.html"), recursive=True))
    texts = {page_path_of(fp): visible_text(open(fp, encoding="utf-8").read(), strip_block=True) for fp in pages}

    report = []
    missing = collections.defaultdict(lambda: collections.defaultdict(list))  # page -> cat -> [kw]
    kw_by_kvartal_topic = collections.defaultdict(list)  # topic page -> [(kw, kvartal slug)]
    kv_demand_counter = collections.Counter()

    for kw, sources in keywords.items():
        src = ";".join(sorted(sources))
        reason = exclusion_reason(kw)
        if reason:
            report.append((kw, src, "excluded:" + reason, "", ""))
            continue
        kslugs = kvartal_targets(kw, kv_names)
        topic = topic_page(kw)
        if kslugs:
            targets = ["/kvartali/%s/" % s for s in kslugs]
            for s in kslugs:
                kv_demand_counter[s] += 1
                kw_by_kvartal_topic[topic if topic.startswith("/uslugi/") else "/uslugi/vodoprovodchik/"].append((kw, s))
        else:
            targets = [topic]
        for t in targets:
            if t not in texts:
                report.append((kw, src, "error:no-page", t, ""))
                continue
            cat = "loc" if kslugs else category_of(kw, t)
            if norm(kw) in texts[t]:
                report.append((kw, src, "present", t, cat))
            else:
                missing[t][cat].append(kw)
                report.append((kw, src, "added", t, cat))

    kv_demand = [s for s, _ in kv_demand_counter.most_common()]
    # keep the "<service> <kvartal>" anchor lists short and unique per page
    for p in kw_by_kvartal_topic:
        seen, uniq = set(), []
        for kw, s in kw_by_kvartal_topic[p]:
            if s in seen:
                continue
            seen.add(s)
            uniq.append((kw, s))
        kw_by_kvartal_topic[p] = uniq[:15]

    changed = []
    for fp in pages:
        page = page_path_of(fp)
        ctx = {}
        if page.startswith("/uslugi/") and page != "/uslugi/":
            slug = page.strip("/").split("/")[1]
            ctx = {"title_suffix": SERVICES[slug][1], "service_phrase": SERVICES[slug][1], "service_link": None}
        elif page.startswith("/kvartali/") and page != "/kvartali/":
            slug = page.strip("/").split("/")[1]
            ctx = {"title_suffix": kv[slug]["display"], "display": kv[slug]["display"],
                   "where": "в " + kv[slug]["display"], "service_phrase": "отпушване на канали",
                   "service_link": "/uslugi/otpushvane-na-kanali/"}
        elif page == "/":
            ctx = {"title_suffix": "ВиК услуги София"}
        else:
            ctx = {"title_suffix": HUBS.get(page, ""), "where": "в София и Столична община"}
        # DIY keywords on a page other than the service page link to that service
        groups = missing.get(page, {})
        if "diy" in groups and not ctx.get("service_link") and page.startswith("/uslugi/"):
            ctx["service_link"] = None
        links = build_links(page, kv, kv_demand, kw_by_kvartal_topic)
        block = build_block(page, groups, ctx, links)
        s = open(fp, encoding="utf-8").read()
        new = insert_block(s, block)
        if new != s:
            new = re.sub(r'"dateModified":"\d{4}-\d{2}-\d{2}"', '"dateModified":"%s"' % TODAY, new)
            changed.append(page)
            if not args.dry_run:
                open(fp, "w", encoding="utf-8").write(new)

    # verify: every "added" keyword must now be present in the page text
    if not args.dry_run:
        texts2 = {page_path_of(fp): visible_text(open(fp, encoding="utf-8").read()) for fp in pages}
        for i, (kw, src, status, page, cat) in enumerate(report):
            if status == "added" and norm(kw) not in texts2.get(page, ""):
                report[i] = (kw, src, "error:not-inserted", page, cat)

        sm_path = os.path.join(PUBLIC, "sitemap.xml")
        sm = open(sm_path, encoding="utf-8").read()
        for page in changed:
            sm = re.sub(r"(<loc>https://uslugivik\.com%s</loc><lastmod>)[^<]+" % re.escape(page), r"\g<1>" + TODAY, sm)
        open(sm_path, "w", encoding="utf-8").write(sm)

    with open(REPORT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["keyword", "source", "status", "page", "category"])
        w.writerows(sorted(report, key=lambda r: (r[2], r[3], r[0])))

    c = collections.Counter(r[2].split(":")[0] for r in report)
    print("keywords: %d  present: %d  added: %d  excluded: %d  errors: %d"
          % (len(report), c["present"], c["added"], c["excluded"], c["error"]))
    print("pages changed: %d of %d%s" % (len(changed), len(pages), " (dry run)" if args.dry_run else ""))
    print("report: %s" % os.path.relpath(REPORT, BASE))
    return 1 if c["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
