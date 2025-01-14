import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// adapter-auto only supports some environments, see https://svelte.dev/docs/kit/adapter-auto for a list.
		// If your environment is not supported, or you settled on a specific environment, switch out the adapter.
		// See https://svelte.dev/docs/kit/adapters for more information about adapters.
		adapter: adapter(
			{
				host: '0.0.0.0',
				port: 5173
			}
		),
	
		files: {
			assets: 'static'
		  },
		  paths: {
			base: ''
		  },
		  serviceWorker: {
			register: true
		  }
	},
	routes: [
		{ pattern: /^\/$/, dest: 'index.html' },
		// 其他路由配置
	  ]
};

export default config;
