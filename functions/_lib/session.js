/* Shoof accounts: shared helpers for the sign-in routes (functions/api/auth) and the AI gate (functions/api/_middleware.js).
   Accounts are only switched on when GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SESSION_SECRET and the D1 binding DB are all set;
   without them Shoof works exactly as before (no sign-in asked).
   Stored per account (D1 table users): a random id, Google's account number (sub), email, name, when the account was made and
   last used, and which version of the Privacy & Terms was accepted and when. Table usage: AI uses per account per day. */
export const TERMS_V = 1; // bump when privacy.html changes in a way people must accept again
export const LIMITS = { describe: 25, slides: 8, chat: 40 }; // AI uses per account per day
const DAY_MS = 864e5, SESSION_DAYS = 30, INACTIVE_DAYS = 730;

export const configured = env => !!(env && env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET && env.SESSION_SECRET && env.DB);
export const today = () => new Date().toISOString().slice(0, 10);
export const json = (body, status = 200, cookies = []) => {
  const h = new Headers({ 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'x-content-type-options': 'nosniff' });
  cookies.forEach(c => h.append('set-cookie', c));
  return new Response(JSON.stringify(body), { status, headers: h });
};
export const sameOrigin = request => { const o = request.headers.get('Origin'); return !o || o === new URL(request.url).origin; };
export const randomHex = n => [...crypto.getRandomValues(new Uint8Array(n))].map(b => b.toString(16).padStart(2, '0')).join('');

async function hmac(text, secret) {
  const k = await crypto.subtle.importKey('raw', new TextEncoder().encode('session:' + secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return [...new Uint8Array(await crypto.subtle.sign('HMAC', k, new TextEncoder().encode(text)))].map(b => b.toString(16).padStart(2, '0')).join('');
}
function same(a, b) { if (a.length !== b.length) return false; let d = 0; for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i); return d === 0; }
export const cookieOf = (request, name) => { const m = (request.headers.get('cookie') || '').match(new RegExp('(?:^|;\\s*)' + name + '=([^;]*)')); return m ? m[1] : ''; };

export async function sessionCookie(uid, env) {
  const exp = String(Date.now() + SESSION_DAYS * DAY_MS);
  return `sh_sess=${uid}.${exp}.${await hmac(uid + '.' + exp, env.SESSION_SECRET)}; Path=/; Max-Age=${SESSION_DAYS * 86400}; HttpOnly; Secure; SameSite=Lax`;
}
export const clearSession = () => 'sh_sess=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax';

let ready = false;
export async function setup(DB) {
  if (ready) return;
  await DB.batch([
    DB.prepare('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, google_sub TEXT UNIQUE NOT NULL, email TEXT NOT NULL, name TEXT NOT NULL DEFAULT \'\', created INTEGER NOT NULL, last_seen INTEGER NOT NULL, terms_v INTEGER NOT NULL, terms_at INTEGER NOT NULL)'),
    DB.prepare('CREATE TABLE IF NOT EXISTS usage (user_id TEXT NOT NULL, day TEXT NOT NULL, kind TEXT NOT NULL, n INTEGER NOT NULL, PRIMARY KEY (user_id, day, kind))')]);
  ready = true;
}

/* the signed-in account for this request, or null (bad / expired cookie, deleted account, old terms) */
export async function currentUser(request, env, { anyTerms = false } = {}) {
  const m = cookieOf(request, 'sh_sess').match(/^([0-9a-f]{32})\.(\d{10,14})\.([0-9a-f]{64})$/);
  if (!m || Number(m[2]) < Date.now()) return null;
  if (!same(m[3], await hmac(m[1] + '.' + m[2], env.SESSION_SECRET))) return null;
  await setup(env.DB);
  const u = await env.DB.prepare('SELECT id, email, name, terms_v FROM users WHERE id = ?1').bind(m[1]).first();
  if (!u || (!anyTerms && u.terms_v < TERMS_V)) return null;
  return u;
}

/* counts one AI use; returns how many are left today, or -1 when the day's allowance is used up */
export async function spend(env, uid, kind) {
  const max = LIMITS[kind];
  const row = await env.DB.prepare('INSERT INTO usage (user_id, day, kind, n) VALUES (?1, ?2, ?3, 1) ON CONFLICT (user_id, day, kind) DO UPDATE SET n = n + 1 WHERE n < ?4 RETURNING n')
    .bind(uid, today(), kind, max).first();
  const now = Date.now();
  await env.DB.prepare('UPDATE users SET last_seen = ?1 WHERE id = ?2 AND last_seen < ?3').bind(now, uid, now - DAY_MS).run();
  if (Math.random() < 0.02) await env.DB.batch([ // housekeeping promised in privacy.html: usage counts kept 7 days, unused accounts removed after 24 months
    env.DB.prepare('DELETE FROM usage WHERE day < ?1').bind(new Date(now - 7 * DAY_MS).toISOString().slice(0, 10)),
    env.DB.prepare('DELETE FROM users WHERE last_seen < ?1').bind(now - INACTIVE_DAYS * DAY_MS)]);
  return row && typeof row.n === 'number' ? max - row.n : -1;
}
export async function refund(env, uid, kind) {
  await env.DB.prepare('UPDATE usage SET n = MAX(0, n - 1) WHERE user_id = ?1 AND day = ?2 AND kind = ?3').bind(uid, today(), kind).run();
}
export async function usageToday(env, uid) {
  const { results } = await env.DB.prepare('SELECT kind, n FROM usage WHERE user_id = ?1 AND day = ?2').bind(uid, today()).all();
  const used = {}; (results || []).forEach(r => { used[r.kind] = r.n; });
  const out = {}; Object.keys(LIMITS).forEach(k => { out[k] = { used: used[k] || 0, limit: LIMITS[k] }; });
  return out;
}
