const CACHE='via-active-etf-v1';
const ASSETS=['VIA_ActiveETF_Console.html','icon-192.png','icon-512.png','VIA_ActiveETF.webmanifest'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(self.clients.claim());});
self.addEventListener('fetch',e=>{e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).catch(()=>r)));});
