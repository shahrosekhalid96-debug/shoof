/* Unit test for Shoof accounts: functions/api/auth/[[path]].js + functions/api/_middleware.js + functions/_lib/session.js.
   No network: fake Google token endpoint, fake D1 (just the statements these files use), fake edge cache. Run: node tests/server/auth.mjs */
import { readFileSync, writeFileSync, mkdtempSync, mkdirSync } from 'node:fs'; import { tmpdir } from 'node:os'; import { join } from 'node:path';
const here = new URL('.', import.meta.url).pathname, fn = join(here, '../../functions'), dir = mkdtempSync(join(tmpdir(), 'shoof-auth-'));
mkdirSync(join(dir, '_lib')); mkdirSync(join(dir, 'api/auth'), { recursive: true });
const fix = s => s.replace(/session\.js'/g, "session.mjs'");
writeFileSync(join(dir, '_lib/session.mjs'), readFileSync(join(fn, '_lib/session.js')));
writeFileSync(join(dir, 'api/auth/path.mjs'), fix(readFileSync(join(fn, 'api/auth/[[path]].js'), 'utf8')));
writeFileSync(join(dir, 'api/mw.mjs'), fix(readFileSync(join(fn, 'api/_middleware.js'), 'utf8')));
const store = new Map(); globalThis.caches = { default: { match: async k => store.has(k.url) ? new Response(store.get(k.url)) : undefined, put: async (k, r) => store.set(k.url, await r.text()) } };

/* fake D1 */
const users = new Map(), usage = new Map();
const DB = {
  prepare(sql) {
    const st = { a: [], bind(...a) { this.a = a; return this; },
      async run() { return this.exec(); }, async first() { const r = this.exec(); return Array.isArray(r) ? (r[0] || null) : r; }, async all() { return { results: this.exec() }; },
      exec() {
        const a = this.a;
        if (sql.startsWith('CREATE')) return {};
        if (sql.startsWith('SELECT id, email, name, terms_v FROM users WHERE id')) { const u = users.get(a[0]); return u ? [u] : []; }
        if (sql.startsWith('SELECT id FROM users WHERE google_sub')) return [...users.values()].filter(u => u.google_sub === a[0]);
        if (sql.startsWith('UPDATE users SET last_seen')) { const u = users.get(a[1]); if (u) u.last_seen = a[0]; return {}; }
        if (sql.startsWith('DELETE FROM users WHERE last_seen')) return {};
        if (sql.startsWith('UPDATE users SET')) { const u = users.get(a[4]); Object.assign(u, { email: a[0], name: a[1], last_seen: a[2], terms_v: a[3] }); return {}; }
        if (sql.startsWith('INSERT INTO users')) { users.set(a[0], { id: a[0], google_sub: a[1], email: a[2], name: a[3], terms_v: a[5] }); return {}; }
        if (sql.startsWith('INSERT INTO usage')) { const k = a.slice(0, 3).join('|'), n = usage.get(k) || 0; if (n >= a[3]) return []; usage.set(k, n + 1); return [{ n: n + 1 }]; }
        if (sql.startsWith('UPDATE usage')) { const k = a.join('|'); usage.set(k, Math.max(0, (usage.get(k) || 0) - 1)); return {}; }
        if (sql.startsWith('SELECT kind, n FROM usage')) return [...usage.entries()].filter(([k]) => k.startsWith(a[0] + '|' + a[1] + '|')).map(([k, n]) => ({ kind: k.split('|')[2], n }));
        if (sql.startsWith('DELETE FROM usage WHERE user_id')) { [...usage.keys()].filter(k => k.startsWith(a[0] + '|')).forEach(k => usage.delete(k)); return {}; }
        if (sql.startsWith('DELETE FROM usage WHERE day')) return {};
        if (sql.startsWith('DELETE FROM users')) { users.delete(a[0]); return {}; }
        throw new Error('unexpected SQL ' + sql);
      } };
    return st;
  },
  async batch(list) { return Promise.all(list.map(s => s.run())); }
};

/* fake Google */
const CID = 'cid.apps.googleusercontent.com';
let claims = {};
globalThis.fetch = async (url, o) => {
  if (String(url) !== 'https://oauth2.googleapis.com/token') throw new Error('unexpected fetch ' + url);
  const f = new URLSearchParams(o.body); if (f.get('client_secret') !== 'sec' || f.get('code') !== 'good') return new Response('{"error":"invalid_grant"}', { status: 400 });
  const b64 = o => Buffer.from(JSON.stringify(o)).toString('base64url');
  return new Response(JSON.stringify({ id_token: b64({ alg: 'RS256' }) + '.' + b64(claims) + '.sig' }));
};

const { onRequest: auth } = await import(join(dir, 'api/auth/path.mjs'));
const { onRequest: mw } = await import(join(dir, 'api/mw.mjs'));
const { TERMS_V, LIMITS } = await import(join(dir, '_lib/session.mjs'));
const env = { GOOGLE_CLIENT_ID: CID, GOOGLE_CLIENT_SECRET: 'sec', SESSION_SECRET: 'shh', DB };
const ok = (c, m) => { if (!c) { console.error('FAIL ' + m); process.exit(1); } };
const O = 'https://shoof.pages.dev';
const req = (path, { method = 'GET', cookie = '', body, h = {} } = {}) => new Request(O + path, { method, headers: { 'CF-Connecting-IP': '1.2.3.4', ...(cookie ? { cookie } : {}), ...(body ? { 'content-type': 'application/json' } : {}), ...h }, body: body ? JSON.stringify(body) : undefined });
const A = (path, o, e = env) => auth({ request: req('/api/auth/' + path, o), env: e, params: { path: path.split('?')[0].split('/') } });
const cookieVal = (res, name) => { const c = (res.headers.getSetCookie ? res.headers.getSetCookie() : [res.headers.get('set-cookie')]).find(x => x && x.startsWith(name + '=')); return c ? c.split(';')[0] : ''; };
let aiCalls = 0, aiStatus = 200;
const next = async () => { aiCalls++; return new Response('{"ok":1}', { status: aiStatus, headers: { 'content-type': 'application/json' } }); };
const M = (path, o, e = env) => mw({ request: req(path, o), env: e, next });

// accounts off: nothing changes
ok((await (await A('me', {}, {})).json()).auth === 'off', 'me says off without settings');
ok((await M('/api/describe', { method: 'POST', body: { text: 'x' } }, {})).status === 200 && aiCalls === 1, 'gate open when accounts are off');

// on: AI tools need an account; other endpoints pass
let r = await M('/api/describe', { method: 'POST', body: { text: 'hello' } });
ok(r.status === 401 && (await r.json()).error === 'sign_in' && aiCalls === 1, 'describe needs sign-in');
ok((await M('/api/slides', { method: 'POST', body: {} })).status === 401, 'slides needs sign-in');
ok((await M('/api/shoofy', { method: 'POST', body: { messages: [] } })).status === 401, 'chat needs sign-in');
ok((await M('/api/shoofy', { method: 'POST', body: { feedback: { v: 1 } } })).status === 200, 'votes stay open');
ok((await M('/api/feedback', { method: 'POST', body: { text: 'hi there' } })).status === 200, 'feedback stays open');
ok((await M('/api/describe', { method: 'GET' })).status === 200, 'GET passes (function answers 405 itself)');
ok((await (await A('me')).json()).user === null, 'me: signed out');

// sign in: must accept the terms first
r = await A('google'); ok(r.status === 400, 'no accept, no Google');
r = await A('google?accept=1'); ok(r.status === 302, 'accept -> Google');
const loc = new URL(r.headers.get('location')), st = cookieVal(r, 'sh_oauth');
ok(loc.host === 'accounts.google.com' && loc.searchParams.get('client_id') === CID && loc.searchParams.get('redirect_uri') === O + '/api/auth/callback' && /openid/.test(loc.searchParams.get('scope')), 'Google URL right');
ok(st.endsWith('.' + TERMS_V) && loc.searchParams.get('state') === st.split('=')[1].split('.')[0], 'state cookie carries the accepted terms version');
const state = loc.searchParams.get('state');
const now = Math.floor(Date.now() / 1000);
claims = { iss: 'https://accounts.google.com', aud: CID, exp: now + 600, sub: '1234567890', email: 'Shary@Example.com', email_verified: true, name: 'Shary <b>K</b>' };
ok((await A(`callback?code=good&state=${state}`)).status === 400, 'no state cookie refused');
ok((await A(`callback?code=good&state=bad${state.slice(3)}`, { cookie: st })).status === 400, 'wrong state refused');
ok((await A(`callback?code=nope&state=${state}`, { cookie: st })).status === 400 && users.size === 0, 'bad code refused');
claims.aud = 'someone-else'; ok((await A(`callback?code=good&state=${state}`, { cookie: st })).status === 400 && users.size === 0, 'token for another app refused'); claims.aud = CID;
claims.email_verified = false; ok((await A(`callback?code=good&state=${state}`, { cookie: st })).status === 400 && users.size === 0, 'unverified email refused'); claims.email_verified = true;
ok((await A(`callback?code=good&state=${state}`, { cookie: st.replace(/\.\d+$/, '.0') })).status === 400, 'old terms acceptance refused');
r = await A(`callback?code=good&state=${state}`, { cookie: st });
const html = await r.text(), sess = cookieVal(r, 'sh_sess');
ok(r.status === 200 && /signed in/i.test(html) && /BroadcastChannel/.test(html) && /nonce-/.test(r.headers.get('content-security-policy')), 'callback page ok');
ok(users.size === 1 && sess.startsWith('sh_sess='), 'account made, cookie set');
const u = [...users.values()][0];
ok(u.email === 'shary@example.com' && !/[<>]/.test(u.name) && u.terms_v === TERMS_V && u.google_sub === '1234567890', 'stored fields: ' + JSON.stringify(u));
ok(!JSON.stringify(u).includes('1.2.3.4'), 'no IP stored');
ok(!html.includes('<b>'), 'name not injected into page');
// again with the same Google account: same Shoof account
const r2 = await A('google?accept=1'), st2 = cookieVal(r2, 'sh_oauth'), s2 = new URL(r2.headers.get('location')).searchParams.get('state');
await A(`callback?code=good&state=${s2}`, { cookie: st2 }); ok(users.size === 1, 'no duplicate account');

// signed in: me + usage
let me = await (await A('me', { cookie: sess })).json();
ok(me.user && me.user.email === 'shary@example.com' && me.usage.describe.used === 0 && me.usage.describe.limit === LIMITS.describe, 'me shows account and allowance');
ok((await (await A('me', { cookie: sess.slice(0, -2) + '00' })).json()).user === null, 'tampered cookie refused');
r = await M('/api/describe', { method: 'POST', body: { text: 'hi' }, cookie: sess });
ok(r.status === 200 && r.headers.get('x-shoof-left') === String(LIMITS.describe - 1), 'describe works signed in, left header');
aiStatus = 502; r = await M('/api/describe', { method: 'POST', body: { text: 'hi' }, cookie: sess }); aiStatus = 200;
ok(r.headers.get('x-shoof-left') === String(LIMITS.describe - 1), 'failed AI call not counted');
for (let i = 0; i < LIMITS.slides; i++) await M('/api/slides', { method: 'POST', body: {}, cookie: sess });
const before = aiCalls; r = await M('/api/slides', { method: 'POST', body: {}, cookie: sess });
ok(r.status === 429 && aiCalls === before && (await r.json()).error === 'limit', 'daily allowance per account enforced');
me = await (await A('me', { cookie: sess })).json(); ok(me.usage.slides.used === LIMITS.slides && me.usage.describe.used === 1, 'usage shown');

// sign out / delete
ok((await A('logout', { method: 'POST', cookie: sess, h: { Origin: 'https://evil.example' } })).status === 403, 'other sites cannot sign you out');
r = await A('logout', { method: 'POST', cookie: sess }); ok(r.status === 200 && /Max-Age=0/.test(r.headers.get('set-cookie')), 'logout clears cookie');
ok((await A('delete', { method: 'POST', cookie: sess, h: { Origin: 'https://evil.example' } })).status === 403 && users.size === 1, 'other sites cannot delete');
r = await A('delete', { method: 'POST', cookie: sess }); ok(r.status === 200 && users.size === 0 && usage.size === 0, 'delete removes account and usage');
ok((await M('/api/describe', { method: 'POST', body: { text: 'hi' }, cookie: sess })).status === 401, 'deleted account cookie no longer works');
ok((await A('nothing')).status === 404, 'unknown path');
console.log('auth: ok');
