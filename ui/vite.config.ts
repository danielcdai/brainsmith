import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
    base: '/ui',
	server: {
        // fs: {
        //     allow: ['src'],
        // },
        proxy: {
            '/auth/': {
                target: 'http://localhost:8000', 
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api\/v1\/auth/, ''),
            },
        },
    },
});
