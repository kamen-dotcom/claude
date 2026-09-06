# uslugivik.com — site source + Google keyword integration

`uslugivik.com` (ВиК услуги София) runs as the Cloudflare Worker **`uslugivik`**: the static
site in `public/` is served through Workers Static Assets and `worker.js` handles the request
form (`/api/zayavka`, stored in KV) and the protected `/zayavki.txt` export.

```
uslugivik/
├── public/                 the site (139 pages + favicon, robots.txt, sitemap.xml)
├── worker.js               form handler + static assets
├── wrangler.toml           deploy config (check the KV binding id before the first deploy)
└── seo/
    ├── keyword_integration.py        adds missing Google keywords to page text + interlinks
    ├── keyword_report.csv            what happened to every keyword (present / added / excluded)
    └── keywords/
        ├── google_suggest.txt        Google autocomplete queries (one per line)
        ├── google_suggest_by_seed.json  the same, grouped by the seed query
        └── gsc/                      drop Google Search Console CSV exports here
```

## Deploy

```
cd uslugivik
npx wrangler deploy
```

Before the first deploy confirm in the Cloudflare dashboard (Workers & Pages → uslugivik →
Settings → Bindings) that the KV namespace bound as `LEADS` matches the id in `wrangler.toml`,
and that the `LEADS_KEY` secret is set.

## Keyword integration

`seo/keyword_integration.py` takes every Google query in `seo/keywords/`, drops the ones that
are not about ВиК services in Sofia (other cities, water-utility account queries, competitor
brands, product purchases, off-topic phrases), maps each remaining query to the page that should
rank for it, and — if the query is not already in that page's visible text — adds a
"Какво още търсят клиентите" block with sentences containing the query verbatim plus
keyword-anchored internal links (service ↔ neighbourhood ↔ hub pages). It also bumps
`<lastmod>` in `sitemap.xml` and `dateModified` in the JSON-LD of changed pages.

```
python3 seo/keyword_integration.py --dry-run   # only refresh seo/keyword_report.csv
python3 seo/keyword_integration.py             # apply to public/
```

The generated block sits between `<!--kwsec-->` and `<!--/kwsec-->` markers, so re-running the
script replaces it instead of adding a second one.

### Adding Search Console data (all time)

1. Search Console → Performance → Search results → date range **Full** (or the widest available).
2. Export → **Download CSV** and copy the `Queries` sheet (`Заявки.csv` / `Queries.csv`) into
   `seo/keywords/gsc/`. The first column must be the query; other columns are ignored.
3. Run `python3 seo/keyword_integration.py`, review `seo/keyword_report.csv`, deploy.

Keywords that should be ignored can be added to the `EXCLUDE` list; the page mapping lives in
`TOPIC_RULES` inside the script.
