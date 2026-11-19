/* Free photo search backup: a Cloudflare Pages Function that asks Openverse for CC0 / public-domain photos when the
   visitor's browser cannot reach api.openverse.org itself (ad blockers, privacy lists, strict networks).
   GET api/photos?q=<words>  -> the same JSON shape Openverse returns, trimmed to id, title, license
   GET api/photos?thumb=<uuid> -> that photo's Openverse thumbnail (image only, ≤8 MB)
   Nothing is stored; answers are cached at the edge for a day. Same-origin pages only. */
const API = 'https://api.openverse.org/v1/images/';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const json = (body, status = 200, cache = 'no-store') => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': cache, 'x-content-type-options': 'nosniff' } });

export async function onRequestGet({ request }) {
  const url = new URL(request.url), site = request.headers.get('Sec-Fetch-Site');
  if (site && site !== 'same-origin') return json({ error: 'origin' }, 403);
  const cache = caches.default, key = new Request(url.toString().replace(/[?&]_=[^&]*/, ''));
  const hit = await cache.match(key); if (hit) return hit;
  const thumb = url.searchParams.get('thumb');
  let res;
  if (thumb !== null) {
    if (!UUID.test(thumb)) return json({ error: 'bad_input' }, 400);
    const r = await fetch(API + thumb + '/thumb/', { headers: { 'user-agent': 'Shoof (shoof.pages.dev)' } });
    const type = (r.headers.get('content-type') || '').split(';')[0];
    if (!r.ok || !/^image\/(jpeg|png|webp)$/.test(type)) return json({ error: 'upstream' }, 502);
    const buf = await r.arrayBuffer(); if (buf.byteLength > 8e6) return json({ error: 'too_big' }, 413);
    res = new Response(buf, { headers: { 'content-type': type, 'cache-control': 'public, max-age=86400', 'x-content-type-options': 'nosniff' } });
  } else {
    const q = String(url.searchParams.get('q') || '').replace(/[\u0000-\u001f<>]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 60);
    if (!q) return json({ error: 'bad_input' }, 400);
    const r = await fetch(API + '?q=' + encodeURIComponent(q) + '&license=cc0,pdm&page_size=20&mature=false', { headers: { 'user-agent': 'Shoof (shoof.pages.dev)' } });
    if (r.status === 429) return json({ error: 'limit' }, 429);
    if (!r.ok) return json({ error: 'upstream' }, 502);
    const j = await r.json();
    const results = (Array.isArray(j.results) ? j.results : []).filter(x => x && UUID.test(String(x.id)) && (x.license === 'cc0' || x.license === 'pdm')).slice(0, 20).map(x => ({ id: x.id, title: String(x.title || 'Photo').slice(0, 80), license: x.license }));
    res = json({ results }, 200, 'public, max-age=86400');
  }
  await cache.put(key, res.clone());
  return res;
}
