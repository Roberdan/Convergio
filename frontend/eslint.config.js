import js from "@eslint/js";
import typescript from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import svelte from "eslint-plugin-svelte";
import prettier from "eslint-config-prettier";
import globals from "globals";

/** @type {import('eslint').Linter.Config[]} */
export default [
  js.configs.recommended,

  // TypeScript configuration
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: "module",
        project: "./tsconfig.json",
      },
      globals: {
        ...globals.browser,
        ...globals.es2017,
      },
    },
    plugins: {
      "@typescript-eslint": typescript,
    },
    rules: {
      ...typescript.configs.recommended.rules,
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/explicit-module-boundary-types": "off",
      "@typescript-eslint/no-explicit-any": "off",
    },
  },

  // Svelte configuration
  ...svelte.configs["flat/recommended"],
  {
    files: ["**/*.svelte"],
    languageOptions: {
      parserOptions: {
        parser: tsParser,
        extraFileExtensions: [".svelte"],
      },
      globals: {
        ...globals.browser,
        ...globals.es2021,
        // also allow Node-like typing references occasionally used in TS annotations
        ...globals.node,
      },
    },
    plugins: {
      "@typescript-eslint": typescript,
    },
    rules: {
      "svelte/no-at-html-tags": "warn",
      "svelte/valid-compile": "error",
      // TS already checks undefined types; avoid false positives in Svelte TS
      "no-undef": "off",
      // Disable base rule in favor of TypeScript rule
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-explicit-any": "off",
    },
  },

  // JavaScript configuration
  {
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },

  // Prettier integration (must be last)
  prettier,

  // Global ignores
  {
    ignores: [
      "node_modules/**",
      "build/**",
      ".svelte-kit/**",
      "dist/**",
      "coverage/**",
      "playwright-report/**",
      "test-results/**",
      // Build/tool config files (not included in tsconfig.json)
      "vite.config.ts",
      "vitest.config.ts",
      "svelte.config.js",
      "postcss.config.js",
      "tailwind.config.js",
      "playwright.config.ts",
      "eslint.config.js",
      // Test files (have separate tsconfig handling)
      "tests/**",
    ],
  },
];
