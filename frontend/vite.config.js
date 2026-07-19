import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		// speech scoring backend (backend/main.py) during development
		proxy: { '/api': 'http://localhost:8000' }
	}
});
