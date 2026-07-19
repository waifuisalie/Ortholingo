/// <reference types="@sveltejs/kit" />
/* Offline support: precache the app shell and the whole audio corpus
 * (~2–3MB — the entire voice of the app), so lessons work in airplane mode.
 * Speech scoring (/api) is network-only and the UI already degrades kindly.
 */
import { build, files, version } from '$service-worker';

const CACHE = `ortholingo-${version}`;
const PRECACHE = ['/', ...build, ...files];

self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
	);
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then(async (keys) => {
			await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
			await self.clients.claim();
		})
	);
});

self.addEventListener('fetch', (event) => {
	const { request } = event;
	if (request.method !== 'GET') return;
	const url = new URL(request.url);
	if (url.origin !== location.origin || url.pathname.startsWith('/api')) return;

	event.respondWith(
		(async () => {
			const cache = await caches.open(CACHE);
			// SPA navigations: serve the cached shell
			if (request.mode === 'navigate') {
				return (await cache.match('/')) ?? fetch(request);
			}
			const cached = await cache.match(request);
			if (cached) return cached;
			try {
				const res = await fetch(request);
				if (res.ok) cache.put(request, res.clone());
				return res;
			} catch (err) {
				throw err;
			}
		})()
	);
});
