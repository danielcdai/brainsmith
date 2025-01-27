import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {

	preprocess: vitePreprocess(),

	kit: {
		paths: {
			base: '/ui',
		  },
		adapter: adapter(
			{
				host: '0.0.0.0',
				port: 5173,
				fallback: 'index.html',
				page: 'build',
      			assets: 'build'
			}
		),
		alias: {
			// "@/*": "src/lib/*",
			// "$/*": "src/routes/*",
			"~/*": "src/*",
		}
	}

};

export default config;
