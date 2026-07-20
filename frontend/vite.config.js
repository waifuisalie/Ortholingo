import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		// speech scoring backend (backend/main.py) during development
		proxy: { '/api': 'http://localhost:8000' },
		// phone testing via `cloudflared tunnel --url http://localhost:5173`
		// (quick tunnels mint a random subdomain per run, so allow the suffix)
		allowedHosts: ['.trycloudflare.com']
	},
	preview: {
		// `vite preview` serves the production build on 4173 by default;
		// run with --port 5173 to reuse a tunnel opened for the dev server
		proxy: { '/api': 'http://localhost:8000' },
		allowedHosts: ['.trycloudflare.com']
	}
});
