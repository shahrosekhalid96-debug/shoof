/* Magic layers learns: a Cloudflare Pages Function that counts anonymous events from Magic layers in the free D1
   database already used by Shoofy (binding DB, table ml_stats). Never a picture, never any text from it:
   only keys such as "fx:Inter|Montserrat!|m" (a font someone swapped to, by text size), "ev:del_text",
   "why:ghost", "rate:bad", "rq:bad:4" (rating + self-check score bucket).
   GET  api/mlearn            -> {fx:{key:n}} learned font swaps (n ≥ 2), cached at the edge for 10 minutes
   POST api/mlearn {keys:[…]} -> counts each listed key once (≤20 keys, 30 posts per visitor per day)
   Read everything with: SELECT key, n, datetime(ts/1000,'unixepoch') FROM ml_stats ORDER BY n DESC; */
const KEY_RE = /^(fx:[A-Za-z0-9 ]{1,40}!?\|[A-Za-z0-9 ]{1,40}!?\|[sml]|ev:(run|kept|del_text|del_subj|del_shape|del_pic|text_fix|lift_more|undone)|why:(text|font|ghost|cut|fill|missed)|rate:(good|bad)|rq:(good|bad):[0-9])$/;
const PER_DAY = 30;
const json = (body, status = 200, cache = 'no-store') => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': cache, 'x-content-type-options': 'nosniff' } });
const ready = db => db.prepare('CREATE TABLE IF NOT EXISTS ml_stats (key TEXT PRIMARY KEY, n INTEGER NOT NULL DEFAULT 0, ts INTEGER)').run();

async function overLimit(request) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown', day = new Date().toISOString().slice(0, 10);
  const key = new Request(`https://rate-limit.shoof/mlearn/${encodeURIComponent(ip)}/${day}`), cache = caches.default;
  const hit = await cache.match(key), n = hit ? (parseInt(await hit.text(), 10) || 0) : 0;
  if (n >= PER_DAY) return true;
  await cache.put(key, new Response(String(n + 1), { headers: { 'cache-control': 'max-age=86400' } }));
  return false;
}

export async function onRequestGet({ request, env }) {
  if (!env.DB) return json({ fx: {} });
  const cache = caches.default, key = new Request(new URL('/api/mlearn?v=1', request.url).toString()), hit = await cache.match(key);
  if (hit) return hit;
  await ready(env.DB);
  const { results } = await env.DB.prepare("SELECT key, n FROM ml_stats WHERE key LIKE 'fx:%' AND n >= 2 ORDER BY n DESC LIMIT 400").all();
  const fx = {}; for (const r of results || []) if (KEY_RE.test(r.key)) fx[r.key] = r.n;
  const res = json({ fx }, 200, 'public, max-age=600');
  await cache.put(key, res.clone());
  return res;
}

export async function onRequestPost({ request, env }) {
  const origin = request.headers.get('Origin');
  if (origin && origin !== new URL(request.url).origin) return json({ error: 'origin' }, 403);
  let raw = ''; try { raw = await request.text(); } catch { return json({ error: 'bad_json' }, 400); }
  if (raw.length > 4000) return json({ error: 'too_big' }, 413);
  let body; try { body = JSON.parse(raw); } catch { return json({ error: 'bad_json' }, 400); }
  const keys = [...new Set((Array.isArray(body && body.keys) ? body.keys : []).filter(k => typeof k === 'string' && KEY_RE.test(k)))].slice(0, 20);
  if (!keys.length) return json({ error: 'bad_input' }, 400);
  if (!env.DB) return json({ ok: true, stored: 0 });
  if (await overLimit(request)) return json({ error: 'limit' }, 429);
  await ready(env.DB);
  const now = Date.now();
  await env.DB.batch(keys.map(k => env.DB.prepare('INSERT INTO ml_stats (key, n, ts) VALUES (?, 1, ?) ON CONFLICT(key) DO UPDATE SET n = n + 1, ts = excluded.ts').bind(k, now)));
  return json({ ok: true, stored: keys.length });
}
