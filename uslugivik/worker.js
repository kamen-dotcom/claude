// Cloudflare Worker for uslugivik.com
// Serves the static site from ./public (Workers Static Assets, binding ASSETS)
// and stores request-form submissions in KV (binding LEADS).
const FILE = 'zayavki.txt';

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });

const clean = (v, max = 500) => String(v == null ? '' : v).trim().slice(0, max);

async function readBody(request) {
  const ct = request.headers.get('content-type') || '';
  return ct.includes('application/json')
    ? await request.json()
    : Object.fromEntries((await request.formData()).entries());
}

async function appendLine(env, line) {
  try {
    if (env.LEADS) {
      const existing = (await env.LEADS.get(FILE)) || '';
      await env.LEADS.put(FILE, existing + line + '\n');
    } else {
      console.log('LEAD (no KV bound):', line);
    }
  } catch (e) {
    console.log('LEAD store error:', e && e.message);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/api/zayavka') {
      if (request.method !== 'POST') return json({ ok: false, error: 'method' }, 405);
      let body = {};
      try {
        body = await readBody(request);
      } catch (_) {
        return json({ ok: false, error: 'parse' }, 400);
      }
      if (clean(body.website)) return json({ ok: true }); // honeypot
      const z = {
        name: clean(body.name, 120),
        phone: clean(body.phone, 40),
        email: clean(body.email, 120),
        area: clean(body.area, 100),
        service: clean(body.service, 120),
        urgency: clean(body.urgency, 60),
        msg: clean(body.msg, 1500),
        page: clean(body.page, 200),
        ts: new Date().toISOString(),
      };
      if (!z.name || !z.phone || !z.msg) return json({ ok: false, error: 'validation' }, 422);
      const line = [
        z.ts,
        'Име: ' + z.name,
        'Тел: ' + z.phone,
        'Имейл: ' + (z.email || '-'),
        'Район: ' + (z.area || '-'),
        'Услуга: ' + (z.service || '-'),
        'Спешност: ' + (z.urgency || '-'),
        'Описание: ' + z.msg.replace(/\s+/g, ' '),
        'Страница: ' + (z.page || '-'),
        'IP: ' + (request.headers.get('cf-connecting-ip') || '-'),
      ].join(' | ');
      await appendLine(env, line);
      return json({ ok: true });
    }

    if (url.pathname === '/zayavki.txt') {
      if (!env.LEADS_KEY || url.searchParams.get('key') !== env.LEADS_KEY) {
        return new Response('Not found', { status: 404 });
      }
      const txt = (env.LEADS && (await env.LEADS.get(FILE))) || 'Няма заявки още.\n';
      return new Response(txt, {
        headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' },
      });
    }

    return env.ASSETS.fetch(request);
  },
};
