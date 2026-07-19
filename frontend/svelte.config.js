import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
export default {
	kit: {
		// SPA: everything renders client-side against assets/manifest.json
		adapter: adapter({ fallback: 'index.html' })
	}
};
