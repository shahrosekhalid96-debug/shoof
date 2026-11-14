/* Shoof offline support. Pages: network first, so updates arrive at once; the saved copy is used when offline.
   Files (scripts, fonts, pictures, the AI model): served from the saved copy, refreshed in the background.
   Never caches the AI writer (api/) or other sites. */
const CACHE = 'shoof-v1';
const CORE = ['./editor', './', 'vendor/konva.min.js', 'fonts/fonts.css', 'manifest.webmanifest', 'icons/icon-192.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => Promise.all(CORE.map(u => fetch(u).then(r => r.ok && c.put(u, copy(r))).catch(() => {})))).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
/* a redirected response cannot answer a page request, so store a clean copy */
function copy(r) { return r.redirected ? r.blob().then(b => new Response(b, { status: r.status, headers: r.headers })) : r; }
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin || url.pathname.includes('/api/')) return;
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).then(r => { if (r.ok) { const c2 = r.clone(); caches.open(CACHE).then(c => Promise.resolve(copy(c2)).then(x => c.put(req, x))); } return r; })
      .catch(() => caches.match(req).then(m => m || caches.match(url.pathname.endsWith('/') ? './' : './editor'))));
    return;
  }
  e.respondWith(caches.open(CACHE).then(c => c.match(req).then(hit => {
    const net = fetch(req).then(r => { if (r.ok && r.status === 200) c.put(req, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  })));
});
