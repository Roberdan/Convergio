/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Convergio purple/violet brand colors (Design System) - Unified with CSS variables
        primary: {
          50: "var(--color-primary-50)",
          100: "var(--color-primary-100)",
          200: "var(--color-primary-200)",
          300: "var(--color-primary-300)",
          400: "var(--color-primary-400)",
          500: "var(--color-primary-500)",
          600: "var(--color-primary-600)", // Main brand color
          700: "var(--color-primary-700)",
          800: "var(--color-primary-800)",
          900: "var(--color-primary-900)",
          950: "var(--color-primary-950)",
        },
        // Override default blue with purple everywhere
        blue: {
          50: "var(--color-primary-50)",
          100: "var(--color-primary-100)",
          200: "var(--color-primary-200)",
          300: "var(--color-primary-300)",
          400: "var(--color-primary-400)",
          500: "var(--color-primary-500)",
          600: "var(--color-primary-600)", // Main brand color
          700: "var(--color-primary-700)",
          800: "var(--color-primary-800)",
          900: "var(--color-primary-900)",
          950: "var(--color-primary-950)",
        },
        gray: {
          50: "var(--color-surface-50)",
          100: "var(--color-surface-100)",
          200: "var(--color-surface-200)",
          300: "var(--color-surface-300)",
          400: "var(--color-surface-400)",
          500: "var(--color-surface-500)",
          600: "var(--color-surface-600)",
          700: "var(--color-surface-700)",
          800: "var(--color-surface-800)",
          900: "var(--color-surface-900)",
          950: "var(--color-surface-950)",
        },
        // Surface colors for design system - Unified with CSS variables
        surface: {
          0: "var(--color-surface-0)",
          50: "var(--color-surface-50)",
          100: "var(--color-surface-100)",
          200: "var(--color-surface-200)",
          300: "var(--color-surface-300)",
          400: "var(--color-surface-400)",
          500: "var(--color-surface-500)",
          600: "var(--color-surface-600)",
          700: "var(--color-surface-700)",
          800: "var(--color-surface-800)",
          900: "var(--color-surface-900)",
          950: "var(--color-surface-950)",
          // Legacy aliases for backward compatibility
          white: "var(--color-surface-0)",
          light: "var(--color-surface-50)",
          neutral: "var(--color-surface-100)",
          border: "var(--color-border-light)",
        },
        // Semantic colors - Unified with CSS variables
        success: {
          DEFAULT: "var(--color-success)",
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "var(--color-success)", // Main success green
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
        },
        warning: {
          DEFAULT: "var(--color-warning)",
          50: "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "var(--color-warning)", // Main warning orange
          600: "#d97706",
          700: "#b45309",
          800: "#92400e",
          900: "#78350f",
        },
        error: {
          DEFAULT: "var(--color-error)",
          50: "#fef2f2",
          100: "#fee2e2",
          200: "#fecaca",
          300: "#fca5a5",
          400: "#f87171",
          500: "var(--color-error)", // Main error red
          600: "#dc2626",
          700: "#b91c1c",
          800: "#991b1b",
          900: "#7f1d1d",
        },
        info: {
          DEFAULT: "var(--color-info)",
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "var(--color-info)", // Main info blue
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
      },
      fontFamily: {
        // Design system typography - Unified with CSS variables
        primary: ["var(--font-primary)"],
        secondary: ["var(--font-secondary)"],
        sans: ["var(--font-secondary)"],
        mono: ["var(--font-primary)"],
      },
      fontSize: {
        // Design system typography scale - Unified with CSS variables
        "2xs": ["var(--text-xs)", { lineHeight: "0.75rem" }], // 10px
        xs: ["var(--text-xs)", { lineHeight: "1rem" }], // 12px
        sm: ["var(--text-sm)", { lineHeight: "1.25rem" }], // 14px
        base: ["var(--text-base)", { lineHeight: "1.5rem" }], // 16px
        lg: ["var(--text-lg)", { lineHeight: "1.75rem" }], // 18px
        xl: ["var(--text-xl)", { lineHeight: "1.75rem" }], // 20px
        "2xl": ["var(--text-2xl)", { lineHeight: "2rem" }], // 24px
        "3xl": ["var(--text-3xl)", { lineHeight: "2.25rem" }], // 30px
        "4xl": ["var(--text-4xl)", { lineHeight: "2.5rem" }], // 36px
      },
      textColor: {
        primary: "var(--color-text-primary)",
        secondary: "var(--color-text-secondary)",
        muted: "var(--color-text-muted)",
        inverse: "var(--color-text-inverse)",
      },
      spacing: {
        // Design system spacing scale - Unified with CSS variables
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        5: "var(--space-5)",
        6: "var(--space-6)",
        8: "var(--space-8)",
        10: "var(--space-10)",
        12: "var(--space-12)",
        16: "var(--space-16)",
        // Extended spacing
        18: "4.5rem",
        88: "22rem",
        128: "32rem",
      },
      maxWidth: {
        "8xl": "88rem",
        "9xl": "96rem",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-in": "slideIn 0.3s ease-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 3s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideIn: {
          "0%": { transform: "translateY(-10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
      backdropBlur: {
        xs: "2px",
      },
      borderRadius: {
        // Design system border radius - Unified with CSS variables
        none: "0",
        sm: "var(--radius-sm)",
        DEFAULT: "var(--radius-md)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        "2xl": "var(--radius-2xl)",
        "3xl": "1.75rem", // Custom size
        "4xl": "2rem", // Custom size
        full: "var(--radius-full)",
      },
    },
  },
  plugins: [
    // All CSS variables are now handled by unified-design-system.css
    // This ensures a single source of truth for the design system
  ],
};
