// 只快取靜態檔（頁面、icon、Leaflet）。警廣、119 資料、地圖圖磚、搜尋一律走網路、不進快取。
// 同一網域（highker21.github.io）的 App 共用 Cache Storage：只刪自己前綴 live-static- 的舊版，不碰別的 App
const CACHE = 'live-static-2026-11-11b';
const STATIC = ['./', 'index.html', 'manifest.webmanifest', 'icon.svg', 'icon-180.png', 'icon-192.png', 'icon-512.png',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js'];
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys()
  .then(ks => Promise.all(ks.filter(k => k.startsWith('live-static-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  const ok = e.request.method === 'GET' &&
    ((u.origin === location.origin && u.pathname.startsWith(new URL('./', self.registration.scope).pathname) && !u.search) || (u.hostname === 'cdnjs.cloudflare.com' && u.pathname.includes('/leaflet/1.9.4/')));
  if (!ok) return;
  // 網路優先，失敗才用快取，避免卡在舊版頁面
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
    return r;
  }).catch(() => caches.match(e.request)));
});
// 點通知 → 回到已開的 App，沒開就開新的
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({type: 'window', includeUncontrolled: true}).then(cs => {
    const c = cs.find(c => c.url.startsWith(self.registration.scope));
    return c ? c.focus() : self.clients.openWindow(self.registration.scope);
  }));
});
