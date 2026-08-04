#!/usr/bin/env python3
"""Word-count and duplicate-content check for the unique copy of each page."""
import os
import re
from collections import Counter

import build
import locations

ROOT = os.path.dirname(os.path.abspath(__file__))


def text_of(path):
    html = open(path, encoding="utf-8").read()
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", html).strip()


def words(t):
    return re.findall(r"[0-9A-Za-zА-Яа-яЁёЪъЬьЮюЯя]+", t.lower())


pages = {}
for slug, label, title, desc, h1, lead, hero in build.PAGES:
    body = text_of(os.path.join(ROOT, "src", (slug or "index") + ".html"))
    # unique per-page copy = h1 + lead + body (nav/header/footer are shared boilerplate)
    pages[build.url(slug)] = f"{h1} {lead} {body}"

for entry in locations.ALL:
    body = text_of(os.path.join(ROOT, "src", "loc", entry["slug"] + ".html"))
    pages[locations.url(entry)] = f"{entry['title']} {body}"

print(f"{'page':<30}{'words':>7}{'status':>10}")
fails = 0
for u, t in pages.items():
    n = len(words(t))
    ok = n >= 750
    fails += not ok
    print(f"{u:<30}{n:>7}{'OK' if ok else 'SHORT':>10}")

print("\n--- cross-page duplicate check (8-word shingles) ---")
sh = {}
for u, t in pages.items():
    w = words(t)
    sh[u] = {" ".join(w[i:i + 8]) for i in range(len(w) - 7)}

# 45 pages covering one trade in one city share unavoidable terminology
# (BTU classes, refrigerant names, "външно тяло"). Anything under 3% between a
# given pair is vocabulary, not recycled copy.
THRESHOLD = 3.0
keys = list(sh)
worst = 0
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a, b = sh[keys[i]], sh[keys[j]]
        inter = a & b
        pct = 100 * len(inter) / max(1, min(len(a), len(b)))
        worst = max(worst, pct)
        if pct > THRESHOLD:
            print(f"  {keys[i]} vs {keys[j]}: {pct:.1f}% overlap ({len(inter)} shingles)")
            for s in list(inter)[:5]:
                print("     ", s)
print(f"  max pairwise overlap: {worst:.2f}%  ({'OK' if worst < THRESHOLD else 'CHECK'})")

print("\n--- internal repetition (most repeated 8-word shingles across whole site) ---")
c = Counter()
for u, t in pages.items():
    w = words(t)
    c.update({" ".join(w[i:i + 8]) for i in range(len(w) - 7)})
rep = [(k, v) for k, v in c.items() if v > 1]
print(f"  shingles appearing on >1 page: {len(rep)}")
for k, v in sorted(rep, key=lambda x: -x[1])[:10]:
    print(f"   x{v}  {k}")

total = sum(len(words(t)) for t in pages.values())
print(f"\ntotal unique words across site: {total:,}")
raise SystemExit(1 if fails else 0)
