# klimaticiplovdiv.com

Статичен сайт за климатична техника в Пловдив — монтаж, сервиз, профилактика.

## Структура

- `src/` — уникалното съдържание на всяка страница (само тялото, без header/footer)
- `build.py` — генератор: обвива `src/*.html` в общия layout, добавя JSON-LD, sitemap, robots, favicon
- `check.py` — проверка за брой думи (мин. 750/страница) и за дублирано съдържание между страниците
- `img/` — изображения, генерирани с Gemini (`gemini-3.1-flash-image`), 1200×675 WebP
- `public/` — генерираният сайт (артефакт от `build.py`)
- `wrangler.jsonc` — конфигурация за Cloudflare Worker със static assets

## Команди

```bash
python3 build.py     # генерира public/
python3 check.py     # проверява дължина и уникалност на текстовете
npx wrangler deploy  # публикува на Cloudflare
```

## Страници

`/`, `/montazh/`, `/serviz/`, `/profilaktika/`, `/invertorni/`, `/izbor-btu/`,
`/tseni/`, `/marki/`, `/kvartali/`, `/vaprosi/`, `/kontakti/`
