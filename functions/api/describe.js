/* Shoof "Describe it": a Cloudflare Pages Function that runs on the free Workers AI allowance.
   The app sends a short description plus a few candidate templates (picked on the user's device);
   the model picks one and writes a headline, a supporting line and a button label.
   Nothing is stored. Needs a Workers AI binding named AI on the Pages project (Settings > Bindings). */
const MODEL = '@cf/meta/llama-3.1-8b-instruct';
const PER_DAY = 25; // per visitor (IP), counted roughly per data centre; the account's free daily allowance is the hard cap
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'x-content-type-options': 'nosniff' } });
const clean = (v, max) => String(v == null ? '' : v).replace(/[\u0000-\u001f\u007f<>{}]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, max);

async function overLimit(request) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown', day = new Date().toISOString().slice(0, 10);
  const key = new Request(`https://rate-limit.shoof/${encodeURIComponent(ip)}/${day}`), cache = caches.default;
  const hit = await cache.match(key), n = hit ? (parseInt(await hit.text(), 10) || 0) : 0;
  if (n >= PER_DAY) return true;
  await cache.put(key, new Response(String(n + 1), { headers: { 'cache-control': 'max-age=86400' } }));
  return false;
}

export async function onRequestPost({ request, env }) {
  const origin = request.headers.get('Origin');
  if (origin && origin !== new URL(request.url).origin) return json({ error: 'origin' }, 403);
  if (Number(request.headers.get('content-length') || 0) > 4000) return json({ error: 'too_big' }, 413);
  let body; try { body = await request.json(); } catch { return json({ error: 'bad_json' }, 400); }
  const text = clean(body && body.text, 300);
  const cands = (Array.isArray(body && body.candidates) ? body.candidates : []).slice(0, 12)
    .map(c => ({ k: String(c && c.k || ''), n: clean(c && c.n, 60) })).filter(c => /^[a-z0-9_]{1,40}$/.test(c.k));
  if (text.length < 3 || !cands.length) return json({ error: 'bad_input' }, 400);
  if (!env.AI) return json({ error: 'ai_off' }, 503);
  if (await overLimit(request)) return json({ error: 'limit' }, 429);
  const keys = cands.map(c => c.k);
  const schema = { type: 'object', properties: { template: { type: 'string', enum: keys }, headline: { type: 'string' }, subline: { type: 'string' }, cta: { type: 'string' } }, required: ['template', 'headline', 'subline', 'cta'] };
  const messages = [
    { role: 'system', content: 'You help small businesses make social media posts and posters. Choose the template that best fits the request and write the words for it. Headline: at most 6 words, punchy. Subline: one short sentence with the key detail (date, offer, place) from the request. CTA: 1 to 3 words for a button. Use only facts from the request; never invent prices, dates or names. Answer in the language of the request. Reply with JSON only.' },
    { role: 'user', content: `Request: ${text}\n\nTemplates:\n${cands.map(c => `- ${c.k}: ${c.n}`).join('\n')}` }];
  // first ask in JSON mode; if the model cannot meet it, ask in plain text and pull the JSON out
  let r = null, why = '';
  const parse = v => { if (v && typeof v === 'object') return v; if (typeof v !== 'string') return null; const m = v.match(/\{[\s\S]*\}/); if (!m) return null; try { return JSON.parse(m[0]); } catch { return null; } };
  try { r = parse((await env.AI.run(MODEL, { messages, max_tokens: 260, temperature: 0.4, response_format: { type: 'json_schema', json_schema: schema } })).response); }
  catch (e) { why = String(e && e.message || e).slice(0, 160); }
  if (!r) {
    try {
      const plain = messages.concat([{ role: 'user', content: 'Answer with one JSON object only, exactly like {"template":"key","headline":"...","subline":"...","cta":"..."}' }]);
      r = parse((await env.AI.run(MODEL, { messages: plain, max_tokens: 260, temperature: 0.3 })).response);
    } catch (e) { why = (why ? why + ' | ' : '') + String(e && e.message || e).slice(0, 160); }
  }
  if (!r || typeof r !== 'object') return json({ error: 'ai_failed', detail: clean(why || 'no JSON in reply', 330) }, 502);
  return json({ template: keys.includes(r.template) ? r.template : keys[0], headline: clean(r.headline, 60), subline: clean(r.subline, 140), cta: clean(r.cta, 28) });
}

export function onRequest() { return json({ error: 'method' }, 405); }
