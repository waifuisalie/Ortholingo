/// <reference types="@sveltejs/kit" />
/* Offline support, failure-tolerant (the naive atomic addAll of ~170 files
 * meant one flaky fetch aborted the whole install — nothing got cached).
 *
 * Tiers:
 *  1. install  — CRITICAL ('/' + built JS/CSS) via addAll: small, must succeed
 *                or the install retries on the next visit
 *  2. install  — remaining shell files (icons, mascot, manifests) best-effort
 *  3. activate — the audio corpus + timings warmed in the background,
 *                individually, tolerating failures
 *  4. runtime  — cache-first; successful 200s fill any remaining gaps, so
 *                anything you've heard once is yours offline
 * /api is network-only; the speak-check UI already degrades kindly.
 */
import { build, files, version } from '$service-worker';

const CACHE = `ortholingo-${version}`;

const isMedia = (p) => p.startsWith('/assets/audio/') || p.startsWith('/assets/timings/');
const CRITICAL = ['/', ...build];
const SHELL = files.filter((f) => !isMedia(f));
const MEDIA = files.filter(isMedia);

/** fetch-and-put one URL, swallowing failures (runtime caching self-heals) */
async function warm(cache, urls) {
	await Promise.allSettled(
		urls.map(async (url) => {
			const res = await fetch(url);
			if (res.status === 200) await cache.put(url, res);
		})
	);
}

self.addEventListener('install', (event) => {
	event.waitUntil(
		(async () => {
			const cache = await caches.open(CACHE);
			await cache.addAll(CRITICAL);
			await warm(cache, SHELL);
			self.skipWaiting();
		})()
	);
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		(async () => {
			const keys = await caches.keys();
			await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
			await self.clients.claim();
			// warm the corpus AFTER the page is controlled — slow networks
			// keep working via runtime caching while this fills in
			await warm(await caches.open(CACHE), MEDIA);
		})()
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
			// SPA navigations: cached shell first, network as fallback
			if (request.mode === 'navigate') {
				return (await cache.match('/')) ?? fetch(request);
			}
			// Cache API matching ignores request headers, so media Range
			// requests still hit the cached full response — Chrome accepts it
			const cached = await cache.match(url.pathname);
			if (cached) return cached;
			const res = await fetch(request);
			// only cache full 200s (a 206 partial would poison the cache)
			if (res.status === 200) cache.put(url.pathname, res.clone());
			return res;
		})()
	);
});
