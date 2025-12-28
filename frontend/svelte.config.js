import adapter from "@sveltejs/adapter-node";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter({
      out: "build",
      precompress: false,
      envPrefix: "CONVERGIO_",
    }),

    // Configure the development server
    files: {
      assets: "static",
      hooks: {
        client: "src/hooks.client.ts",
        server: "src/hooks.server.ts",
      },
      lib: "src/lib",
      params: "src/params",
      routes: "src/routes",
      serviceWorker: "src/service-worker",
      appTemplate: "src/app.html",
    },

    // Security headers
    csp: {
      mode: "auto",
      directives: {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],
        "style-src": [
          "'self'",
          "'unsafe-inline'",
          "https://fonts.googleapis.com",
        ],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "img-src": ["'self'", "data:", "https:"],
        "connect-src": ["'self'", "http://localhost:9000", "ws://localhost:*"],
      },
    },

    // Configure alias for cleaner imports
    alias: {
      $components: "src/lib/components",
      $stores: "src/lib/stores",
      $types: "src/lib/types",
      $utils: "src/lib/utils",
      $api: "src/lib/api",
    },
  },
};

export default config;
