/* Shoof accounts: sign in with Google (server-side OAuth code flow; the client secret never leaves Cloudflare).
   GET  /api/auth/google?accept=1  -> asks Google (only after the Privacy & Terms box was ticked)
   GET  /api/auth/callback         -> Google sends the person back; account made or updated, 30-day sign-in cookie set
   GET  /api/auth/me               -> { auth:'on'|'off', user, usage }
   POST /api/auth/logout           -> signs out on this browser
   POST /api/auth/delete           -> deletes the account and its usage counts at once
   Needs GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SESSION_SECRET (Pages > Settings > Variables) and the D1 binding DB. */
import { TERMS_V, configured, json, sameOrigin, randomHex, cookieOf, sessionCookie, clearSession, setup, currentUser, usageToday } from '../../_lib/session.js';

const STATE_COOKIE = 'sh_oauth', SIGNINS_PER_DAY = 20;
const clean = (v, max) => String(v == null ? '' : v).replace(/[\u0000-\u001f\u007f<>]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, max);
const escH = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* small page shown in the sign-in window; tells the editor (any tab) through BroadcastChannel, then closes itself */
function page(ok, msg, cookies = []) {
  const nonce = randomHex(16);
  const h = new Headers({ 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store', 'x-content-type-options': 'nosniff', 'x-frame-options': 'DENY',
    'content-security-policy': `default-src 'none'; script-src 'nonce-${nonce}'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`, 'referrer-policy': 'no-referrer' });
  cookies.forEach(c => h.append('set-cookie', c));
  const body = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Shoof · ${ok ? 'Signed in' : 'Sign-in problem'}</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#07060c;color:#ece9f6;font:16px/1.5 system-ui,sans-serif}main{max-width:380px;padding:28px;text-align:center}h1{font-size:22px;margin:0 0 8px}a{color:#b7a6ff}</style>
<main><h1>${ok ? 'You are signed in' : 'Could not sign in'}</h1><p>${escH(msg)}</p><p><a href="/editor?go=1">Back to Shoof</a></p></main>
<script nonce="${nonce}">try{new BroadcastChannel('shoof-auth').postMessage(${ok ? "'signed-in'" : "'failed'"});}catch(e){}${ok ? 'setTimeout(function(){window.close();},900);' : ''}</script></html>`;
  return new Response(body, { status: ok ? 200 : 400, headers: h });
}

async function tooMany(request) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown', key = new Request(`https://rate-limit.shoof/signin/${encodeURIComponent(ip)}/${new Date().toISOString().slice(0, 10)}`), c = caches.default;
  const hit = await c.match(key), n = hit ? (parseInt(await hit.text(), 10) || 0) : 0;
  if (n >= SIGNINS_PER_DAY) return true;
  await c.put(key, new Response(String(n + 1), { headers: { 'cache-control': 'max-age=86400' } }));
  return false;
}

function idClaims(token) {
  try { const p = String(token).split('.')[1]; return JSON.parse(atob(p.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((p.length + 3) % 4))); } catch { return null; }
}

async function start(request, env, url) {
  if (url.searchParams.get('accept') !== '1') return page(false, 'Please tick the box to accept the Privacy Policy and Terms first.');
  const state = randomHex(16);
  const q = new URLSearchParams({ client_id: env.GOOGLE_CLIENT_ID, redirect_uri: url.origin + '/api/auth/callback', response_type: 'code', scope: 'openid email profile', state, prompt: 'select_account' });
  return new Response(null, { status: 302, headers: { location: 'https://accounts.google.com/o/oauth2/v2/auth?' + q, 'cache-control': 'no-store',
    'set-cookie': `${STATE_COOKIE}=${state}.${TERMS_V}; Path=/api/auth; Max-Age=600; HttpOnly; Secure; SameSite=Lax` } });
}

async function callback(request, env, url) {
  const clearState = `${STATE_COOKIE}=; Path=/api/auth; Max-Age=0; HttpOnly; Secure; SameSite=Lax`;
  const m = cookieOf(request, STATE_COOKIE).match(/^([0-9a-f]{32})\.(\d{1,4})$/), state = url.searchParams.get('state') || '', code = url.searchParams.get('code') || '';
  if (url.searchParams.get('error')) return page(false, 'Sign-in was cancelled. You can keep using Shoof; AI tools need an account.', [clearState]);
  if (!m || m[1] !== state || !code || code.length > 2048) return page(false, 'This sign-in link expired. Please try again from Shoof.', [clearState]);
  if (Number(m[2]) < TERMS_V) return page(false, 'Please accept the current Privacy Policy and Terms and try again.', [clearState]);
  if (await tooMany(request)) return page(false, 'Too many sign-ins from this network today. Please try again tomorrow.', [clearState]);
  let tok;
  try {
    const r = await fetch('https://oauth2.googleapis.com/token', { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ code, client_id: env.GOOGLE_CLIENT_ID, client_secret: env.GOOGLE_CLIENT_SECRET, redirect_uri: url.origin + '/api/auth/callback', grant_type: 'authorization_code' }) });
    tok = await r.json();
  } catch { tok = null; }
  // the ID token came straight from Google over TLS, so its claims can be read without checking the signature (OpenID Connect 3.1.3.7)
  const c = tok && idClaims(tok.id_token);
  if (!c || !['accounts.google.com', 'https://accounts.google.com'].includes(c.iss) || c.aud !== env.GOOGLE_CLIENT_ID || !(c.exp * 1000 > Date.now()) || !c.sub)
    return page(false, 'Google did not confirm the sign-in. Please try again.', [clearState]);
  if (c.email_verified !== true || !c.email) return page(false, 'Your Google account needs a verified email address.', [clearState]);
  const sub = clean(c.sub, 64), email = clean(c.email, 200).toLowerCase(), name = clean(c.name, 80), now = Date.now();
  await setup(env.DB);
  const old = await env.DB.prepare('SELECT id FROM users WHERE google_sub = ?1').bind(sub).first();
  const uid = old ? old.id : randomHex(16);
  if (old) await env.DB.prepare('UPDATE users SET email = ?1, name = ?2, last_seen = ?3, terms_v = ?4, terms_at = ?3 WHERE id = ?5').bind(email, name, now, TERMS_V, uid).run();
  else await env.DB.prepare('INSERT INTO users (id, google_sub, email, name, created, last_seen, terms_v, terms_at) VALUES (?1, ?2, ?3, ?4, ?5, ?5, ?6, ?5)').bind(uid, sub, email, name, now, TERMS_V).run();
  return page(true, `Signed in as ${email}. This window closes by itself; if not, close it and go back to Shoof.`, [clearState, await sessionCookie(uid, env)]);
}

export async function onRequest({ request, env, params }) {
  const url = new URL(request.url), path = [].concat(params.path || []).join('/'), method = request.method;
  if (path === 'me' && method === 'GET') {
    if (!configured(env)) return json({ auth: 'off' });
    const u = await currentUser(request, env, { anyTerms: true });
    if (!u) return json({ auth: 'on', user: null, terms: TERMS_V });
    if (u.terms_v < TERMS_V) return json({ auth: 'on', user: null, terms: TERMS_V, again: true });
    return json({ auth: 'on', user: { email: u.email, name: u.name }, terms: TERMS_V, usage: await usageToday(env, u.id) });
  }
  if (!configured(env)) return json({ error: 'auth_off' }, 503);
  if (path === 'google' && method === 'GET') return start(request, env, url);
  if (path === 'callback' && method === 'GET') return callback(request, env, url);
  if ((path === 'logout' || path === 'delete') && method === 'POST') {
    if (!sameOrigin(request)) return json({ error: 'origin' }, 403);
    if (path === 'delete') {
      const u = await currentUser(request, env, { anyTerms: true });
      if (!u) return json({ error: 'sign_in' }, 401);
      await env.DB.batch([env.DB.prepare('DELETE FROM usage WHERE user_id = ?1').bind(u.id), env.DB.prepare('DELETE FROM users WHERE id = ?1').bind(u.id)]);
    }
    return json({ ok: true }, 200, [clearSession()]);
  }
  return json({ error: 'not_found' }, 404);
}
