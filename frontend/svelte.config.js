import adapter from "@sveltejs/adapter-vercel";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),

  kit: {
    adapter: adapter({
      runtime: "nodejs20.x",
      regions: ["fra1"],
    }),

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
