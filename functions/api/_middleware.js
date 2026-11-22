/* Shoof AI gate: runs before every /api/* function. When accounts are switched on (see functions/_lib/session.js),
   the AI tools that run on Cloudflare (Describe it, Presentation maker, Ask Shoof chat) need a signed-in account and
   count against that account's daily allowance; everything else (photos, feedback, votes, learning stats) passes as before.
   A use is given back when the AI itself fails. The answer carries x-shoof-left: uses left today. */
import { configured, json, currentUser, spend, refund } from '../_lib/session.js';

const GATED = { '/api/describe': 'describe', '/api/slides': 'slides', '/api/shoofy': 'chat' };

export async function onRequest(context) {
  const { request, env } = context, kind = GATED[new URL(request.url).pathname];
  if (!kind || request.method !== 'POST' || !configured(env)) return context.next();
  if (kind === 'chat') { // only chat messages cost AI; thumbs-up/down and look votes stay open
    let b = null; try { b = await request.clone().json(); } catch {}
    if (!b || !Array.isArray(b.messages)) return context.next();
  }
  const u = await currentUser(request, env);
  if (!u) return json({ error: 'sign_in' }, 401);
  const left = await spend(env, u.id, kind);
  if (left < 0) return json({ error: 'limit', left: 0 }, 429);
  const res = await context.next(), back = res.status >= 500 || res.status === 403 || res.status === 429;
  if (back) await refund(env, u.id, kind); // AI failed, bot check or network limit: not counted
  const out = new Response(res.body, res);
  out.headers.set('x-shoof-left', String(back ? left + 1 : left));
  return out;
}
