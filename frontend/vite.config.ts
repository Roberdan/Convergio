import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
import { readFileSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

// Resolve repo root and read version from top-level VERSION file
const __dirnameLocal = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirnameLocal, "..");
let appVersion = "0.0.0";
try {
  const versionPath = path.resolve(repoRoot, "VERSION");
  appVersion = readFileSync(versionPath, "utf8").trim();
} catch (err) {
  // Fallback to package.json version if VERSION file not found
  appVersion = process.env.npm_package_version || "0.0.0";
}

export default defineConfig({
  plugins: [sveltekit()],

  // Development server configuration
  server: {
    port: 4000,
    host: "0.0.0.0",
    cors: true,
    proxy: {
      // Proxy API requests to the backend
      "/api": {
        target: "http://localhost:9000",
        changeOrigin: true,
        secure: false,
      },
      "/health": {
        target: "http://localhost:9000",
        changeOrigin: true,
        secure: false,
      },
    },
  },

  // Build configuration
  build: {
    target: "es2022",
    sourcemap: true,
  },

  // Optimization
  optimizeDeps: {
    include: ["chart.js", "d3", "date-fns"],
  },

  // CSS configuration
  css: {
    postcss: "./postcss.config.js",
  },

  define: {
    // Build-time constants
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    __VERSION__: JSON.stringify(appVersion),
    __APP_VERSION__: JSON.stringify(appVersion),
  },
});
