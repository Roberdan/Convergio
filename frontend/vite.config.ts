import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	
	// Development server configuration
	server: {
		port: 4000,
		host: '0.0.0.0',
		cors: true,
		proxy: {
			// Proxy API requests to the backend
			'/api': {
				target: 'http://localhost:9000',
				changeOrigin: true,
				secure: false
			},
			'/health': {
				target: 'http://localhost:9000',
				changeOrigin: true,
				secure: false
			}
		}
	},
	
	// Build configuration
	build: {
		target: 'es2022',
		sourcemap: true
	},
	
	// Optimization
	optimizeDeps: {
		include: ['chart.js', 'd3', 'date-fns']
	},
	
	// CSS configuration
	css: {
		postcss: './postcss.config.js'
	},
	
	define: {
		// Environment variables
		__BUILD_TIME__: JSON.stringify(new Date().toISOString()),
		__VERSION__: JSON.stringify(process.env.npm_package_version || '2030.1.0')
	}
});