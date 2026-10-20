// Service worker for the Tai Chi Company home-screen app (scope /tai-chi-company/).
// It only shows a friendly page when there is no internet. It never caches videos,
// articles or account data: those always come fresh from the server.
const OFFLINE_CACHE = "tcc-offline-v1";
const OFFLINE_URL = "/tcc-offline.html";

self.addEventListener("install", (event) => {
    event.waitUntil(caches.open(OFFLINE_CACHE).then((cache) => cache.add(OFFLINE_URL)));
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(keys.filter((k) => k !== OFFLINE_CACHE).map((k) => caches.delete(k))))
            .then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", (event) => {
    if (event.request.mode !== "navigate") return;
    event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE_URL)));
});
