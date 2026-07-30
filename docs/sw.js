// FeedForge Service Worker - PWA 离线支持
const CACHE_NAME = 'feedforge-v1';
const STATIC_ASSETS = [
  '/feedforge/',
  '/feedforge/index.html',
  '/feedforge/manifest.json'
];

// 安装时缓存静态资源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// 激活时清理旧缓存
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// 网络优先，失败则从缓存读取
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // RSS 请求不缓存（走代理）
  if (url.pathname.includes('proxy') || url.hostname !== location.hostname) {
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => {
        // 缓存成功响应
        if (response.ok) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // 网络失败，从缓存读取
        return caches.match(request);
      })
  );
});
