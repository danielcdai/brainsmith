import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
        // fs: {
        //     allow: ['src'],
        // },
        proxy: {
            '/auth/': {
                target: 'http://localhost:8000', 
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/auth/, ''),
            },
        },
    },
});
