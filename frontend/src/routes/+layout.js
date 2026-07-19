import { loadManifest } from '$lib/content.js';

export const ssr = false;
export const prerender = false;

export async function load({ fetch }) {
	return { manifest: await loadManifest(fetch) };
}
