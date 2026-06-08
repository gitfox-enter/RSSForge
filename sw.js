const CACHE_NAME = 'xianbao-v4';
const ASSETS = [
  '/site-update-monitor/public/favicon.svg',
  '/site-update-monitor/offline.html'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  // Network first for HTML pages and data - always get fresh content
  if (e.request.url.includes('items.json') ||
      e.request.headers.get('accept')?.includes('text/html') ||
      e.request.url.endsWith('.html') ||
      e.request.url.endsWith('/')) {
    e.respondWith(
      fetch(e.request)
        .then(res => {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
          return res;
        })
        .catch(async () => {
          const cached = await caches.match(e.request);
          if (cached) return cached;
          // For navigation requests, show offline page
          if (e.request.mode === 'navigate') {
            const offlinePage = await caches.match('/site-update-monitor/offline.html');
            if (offlinePage) return offlinePage;
          }
          return new Response('离线 - 线报聚合', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
        })
    );
    return;
  }
  // Cache first for static assets (images, fonts, etc.)
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(res => {
      const clone = res.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
      return res;
    }))
  );
});
