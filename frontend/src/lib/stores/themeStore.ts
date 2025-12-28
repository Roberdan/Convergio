/**
 * 🎨 Theme Store - Light theme only
 * Dark theme removed per user request
 */

import { writable } from "svelte/store";
import { browser } from "$app/environment";

export type Theme = "light";

// Store per il tema corrente - sempre light
export const theme = writable<Theme>("light");

// Store per il tema effettivo applicato - sempre light
export const resolvedTheme = writable<"light">("light");

/**
 * Inizializza il sistema temi - forza sempre light
 */
export function initializeTheme() {
  if (!browser) return;

  // Rimuovi classe dark se presente
  document.documentElement.classList.remove("dark");

  // Forza tema chiaro
  localStorage.setItem("theme", "light");

  // Aggiorna meta theme-color per mobile
  updateMetaThemeColor();
}

/**
 * Aggiorna meta theme-color per dispositivi mobili
 */
function updateMetaThemeColor() {
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  const color = "#ffffff";

  if (metaThemeColor) {
    metaThemeColor.setAttribute("content", color);
  } else {
    const meta = document.createElement("meta");
    meta.name = "theme-color";
    meta.content = color;
    document.head.appendChild(meta);
  }
}

/**
 * Utility functions - mantenute per retrocompatibilità ma non fanno nulla
 */
export const themeUtils = {
  setTheme(_newTheme: Theme) {
    // No-op: sempre light
  },

  toggleTheme() {
    // No-op: sempre light
  },

  cycleTheme() {
    // No-op: sempre light
  },

  isDark(): boolean {
    return false; // Sempre false
  },
};

// Auto-inizializzazione se in browser
if (browser) {
  initializeTheme();
}
