/* Shoof feedback box: a Cloudflare Pages Function that saves what visitors type (a problem, an idea, a question)
   into the free D1 database already used by Shoofy (binding DB, table feedback). Nothing else is collected:
   no IP address, no cookies. An email address is stored only if the visitor chooses to type one.
   Read the messages with:  SELECT id, datetime(ts/1000,'unixepoch') AS at, kind, page, text, contact FROM feedback WHERE done = 0 ORDER BY id DESC;
   Mark one as handled with: UPDATE feedback SET done = 1 WHERE id = ?; */
const PER_DAY = 8; // per visitor (IP), counted roughly per data centre
const KINDS = ['problem', 'idea', 'question', 'other'];
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'x-content-type-options': 'nosniff' } });
// keeps line breaks, drops control characters and angle brackets (messages are only ever read as plain text)
const clean = (v, max) => String(v == null ? '' : v).replace(/[\u0000-\u0009\u000b-\u001f\u007f<>]/g, ' ').replace(/[ \t]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim().slice(0, max);

async function overLimit(request) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown', day = new Date().toISOString().slice(0, 10);
  const key = new Request(`https://rate-limit.shoof/feedback/${encodeURIComponent(ip)}/${day}`), cache = caches.default;
  const hit = await cache.match(key), n = hit ? (parseInt(await hit.text(), 10) || 0) : 0;
  if (n >= PER_DAY) return true;
  await cache.put(key, new Response(String(n + 1), { headers: { 'cache-control': 'max-age=86400' } }));
  return false;
}

export async function onRequestPost({ request, env }) {
  const origin = request.headers.get('Origin');
  if (origin && origin !== new URL(request.url).origin) return json({ error: 'origin' }, 403);
  if (Number(request.headers.get('content-length') || 0) > 6000) return json({ error: 'too_big' }, 413);
  let raw = ''; try { raw = await request.text(); } catch { return json({ error: 'bad_json' }, 400); }
  if (raw.length > 6000) return json({ error: 'too_big' }, 413);
  let body; try { body = JSON.parse(raw); } catch { return json({ error: 'bad_json' }, 400); }
  if (!body || typeof body !== 'object') return json({ error: 'bad_input' }, 400);
  // "website" is a hidden field people never see; only automated form fillers put something in it
  if (body.website) return json({ ok: true });
  const text = clean(body.text, 1500);
  if (text.length < 5) return json({ error: 'short' }, 400);
  const kind = KINDS.includes(body.kind) ? body.kind : 'other';
  const page = body.page === 'home' ? 'home' : 'editor';
  let contact = clean(body.contact, 120).replace(/\s/g, '');
  if (contact && !/^[^@\s]{1,64}@[^@\s]{1,80}\.[a-z]{2,24}$/i.test(contact)) contact = '';
  const lang = /^[a-z]{2}(-[A-Za-z]{2})?$/.test(String(body.lang || '')) ? String(body.lang) : '';
  const ua = clean(request.headers.get('User-Agent'), 160);
  if (!env.DB) return json({ error: 'off' }, 503);
  if (await overLimit(request)) return json({ error: 'limit' }, 429);
  try {
    await env.DB.prepare('CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, kind TEXT NOT NULL, page TEXT NOT NULL, text TEXT NOT NULL, contact TEXT, lang TEXT, ua TEXT, done INTEGER NOT NULL DEFAULT 0)').run();
    await env.DB.prepare('INSERT INTO feedback (ts, kind, page, text, contact, lang, ua) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)').bind(Date.now(), kind, page, text, contact, lang, ua).run();
  } catch (e) { return json({ error: 'save_failed' }, 500); }
  return json({ ok: true });
}

export const onRequest = () => json({ error: 'method' }, 405);
