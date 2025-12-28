import { defineConfig } from "vitest/config";
import { sveltekit } from "@sveltejs/kit/vite";

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    globals: true,
    css: true,
    environmentOptions: {
      jsdom: {
        resources: "usable",
        runScripts: "dangerously",
      },
    },
    include: ["tests/**/*.{test,spec}.{js,ts}"],
    exclude: ["tests/e2e/**/*", "node_modules/**/*"],
  },
});
