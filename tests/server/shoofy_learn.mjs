/* Unit test for functions/api/shoofy.js learning (no network): fake AI, fake D1, fake edge cache. Run: node tests/server/shoofy_learn.mjs */
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs'; import { tmpdir } from 'node:os'; import { join } from 'node:path';
const here = new URL('.', import.meta.url).pathname, dir = mkdtempSync(join(tmpdir(), 'shoofy-'));
writeFileSync(join(dir, 's.mjs'), readFileSync(join(here, '../../functions/api/shoofy.js')));
const store = new Map(); globalThis.caches = { default: { match: async k => store.has(k.url) ? new Response(store.get(k.url)) : undefined, put: async (k, r) => store.set(k.url, await r.text()) } };
const rows = [], looks = {}; let sys = '';
const DB = { prepare(sql) { return { bind(...a) { this.a = a; return this; },
  async run() { if (sql.includes('INTO looks')) { looks[this.a[0]] = (looks[this.a[0]] || 0) + this.a[1]; return { meta: {} }; } if (sql.startsWith('INSERT')) { rows.push({ id: rows.length + 1, ts: this.a[0], req: this.a[1], words: this.a[2], actions: this.a[4], score: 0 }); return { meta: { last_row_id: rows.length } }; }
    if (sql.startsWith('UPDATE')) { const r = rows.find(x => x.id === this.a[1]); r.score = Math.max(-10, Math.min(30, r.score + this.a[0])); } return { meta: {} }; },
  async all() { if (sql.includes('FROM notes')) return { results: [{ rule: 'Items must stand out from what they sit on.' }] }; return { results: rows.filter(r => r.score >= 2 || r.score <= -2) }; } }; } };
let lastModel = '', lastMsgs = null;
const AI = { run: async (m, o) => { lastModel = m; lastMsgs = o.messages; sys = o.messages[0].content; return { response: JSON.stringify({ reply: 'Tidied.', actions: [{ do: 'polish' }, { do: 'set', target: 'el:2', props: { fill: '#ff0000' } }] }) }; } };
const { onRequestPost } = await import(join(dir, 's.mjs'));
const call = (b, env = { AI, DB }) => onRequestPost({ request: new Request('https://shoof.pages.dev/api/shoofy', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(b) }), env });
const ok = (c, m) => { if (!c) { console.error('FAIL ' + m); process.exit(1); } };
let r = await (await call({ messages: [{ role: 'user', content: 'tidy the layout of my bakery poster, mail me@x.com or +966 555 123 456' }], design: { elements: [{ n: 2, type: 'text', text: 'Bakery' }] } })).json();
ok(/^1\.[0-9a-f]{64}$/.test(r.rid), 'answer gets a signed id');
ok(!/me@x|555/.test(rows[0].req), 'emails and phone numbers are scrubbed: ' + rows[0].req);
ok(rows[0].actions.includes('el:N (text'), 'element targets stored as descriptions');
ok((await (await call({ feedback: { rid: r.rid, v: 2 } })).json()).ok && rows[0].score === 2, 'thumbs up raises the score');
ok((await call({ feedback: { rid: '1.' + '0'.repeat(64), v: 2 } })).status === 400, 'forged id refused');
ok((await call({ feedback: { rid: r.rid, v: 99 } })).status === 400, 'bad vote refused');
await call({ messages: [{ role: 'user', content: 'please tidy my bakery poster layout' }], mine: [{ q: 'make it pink', actions: [{ do: 'set_background', color: '#ffc0cb' }, { do: 'evil' }] }] });
ok(/PEOPLE LIKED/.test(sys) && sys.includes('"polish"') && sys.includes('make it pink') && !sys.includes('evil'), 'liked answers (shared + this user) become examples');
ok(sys.includes('LESSONS LEARNED') && sys.includes('Items must stand out'), 'standing lessons from the notebook are in the prompt');
r = await (await call({ messages: [{ role: 'user', content: 'hi' }] }, { AI })).json();
ok(!r.rid, 'without a database nothing is stored');
ok((await (await call({ feedback: { v: -4, look: ['hues:L|30,60,330', 'style:bold_type_pop', 'evil<script>'] } })).json()).ok && looks['hues:L|30,60,330'] === -2 && !Object.keys(looks).some(k => k.includes('<')), 'looks scored, junk keys dropped ' + JSON.stringify(looks));
await call({ feedback: { v: -4, look: ['hues:L|30,60,330'] } }); ok(looks['hues:L|30,60,330'] === -2, 'one look vote per visitor per day');
const snapR = await (await call({ messages: [{ role: 'user', content: 'what do you think' }], snapshot: 'data:image/jpeg;base64,' + 'A'.repeat(400) })).json();
ok(lastModel.includes('gemma-4') && Array.isArray(lastMsgs[lastMsgs.length - 1].content) && lastMsgs[lastMsgs.length - 1].content.some(c => c.type === 'image_url') && snapR.saw === true, 'snapshot goes to a vision model as an image');
await call({ messages: [{ role: 'user', content: 'what do you think' }], snapshot: 'javascript:alert(1)' }); ok(typeof lastMsgs[lastMsgs.length - 1].content === 'string', 'bad snapshot ignored');
console.log('shoofy learn: ok');
