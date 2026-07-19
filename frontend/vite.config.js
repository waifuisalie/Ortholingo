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
	}
});
