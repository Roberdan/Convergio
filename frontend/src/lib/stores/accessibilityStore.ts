/**
 * Accessibility Store
 * Manages accessibility preferences for the application
 */

import { writable, derived } from "svelte/store";
import { browser } from "$app/environment";

export type AccessibilityProfile =
  | "default"
  | "dyslexia"
  | "adhd"
  | "autism"
  | "motor"
  | "low-vision";
export type FontFamily =
  | "system"
  | "opendyslexic"
  | "arial"
  | "verdana"
  | "times";
export type ColorTheme =
  | "light"
  | "dark"
  | "cream"
  | "high-contrast"
  | "blue-light";

export interface AccessibilityState {
  profile: AccessibilityProfile;

  // Font settings (DY01-DY07)
  fontFamily: FontFamily;
  fontSize: number; // percentage, 100 = default
  lineHeight: number; // multiplier, 1.5 = DY02
  letterSpacing: number; // em units
  maxLineWidth: number; // characters, 60 = DY03

  // Color settings (DY04)
  colorTheme: ColorTheme;
  customBackgroundColor: string | null;

  // Motion settings (AU04)
  reduceMotion: boolean;
  reduceTransparency: boolean;

  // Focus settings (AD04)
  focusModeEnabled: boolean;
  hideNonEssentialUI: boolean;

  // Reading support (DY05, DY06)
  textToSpeechEnabled: boolean;
  syllableHighlighting: boolean;
  readingRulerEnabled: boolean;
  readingRulerHeight: number; // pixels

  // Navigation (CP01-CP05)
  extendedTimeouts: boolean;
  timeoutMultiplier: number;
  largeClickTargets: boolean;
  keyboardNavigationEnhanced: boolean;

  // ADHD support (AD01-AD06)
  maxBulletPoints: number;
  showProgressBars: boolean;
  microCelebrations: boolean;
  breakReminders: boolean;
  breakIntervalMinutes: number;
}

const defaultState: AccessibilityState = {
  profile: "default",
  fontFamily: "system",
  fontSize: 100,
  lineHeight: 1.5,
  letterSpacing: 0,
  maxLineWidth: 80,
  colorTheme: "light",
  customBackgroundColor: null,
  reduceMotion: false,
  reduceTransparency: false,
  focusModeEnabled: false,
  hideNonEssentialUI: false,
  textToSpeechEnabled: false,
  syllableHighlighting: false,
  readingRulerEnabled: false,
  readingRulerHeight: 40,
  extendedTimeouts: false,
  timeoutMultiplier: 1,
  largeClickTargets: false,
  keyboardNavigationEnhanced: false,
  maxBulletPoints: 10,
  showProgressBars: true,
  microCelebrations: false,
  breakReminders: false,
  breakIntervalMinutes: 25,
};

const profilePresets: Record<
  AccessibilityProfile,
  Partial<AccessibilityState>
> = {
  default: {},
  dyslexia: {
    fontFamily: "opendyslexic",
    fontSize: 110,
    lineHeight: 1.8,
    letterSpacing: 0.05,
    maxLineWidth: 60,
    colorTheme: "cream",
    textToSpeechEnabled: true,
    syllableHighlighting: true,
  },
  adhd: {
    focusModeEnabled: true,
    hideNonEssentialUI: true,
    maxBulletPoints: 4,
    showProgressBars: true,
    microCelebrations: true,
    breakReminders: true,
    breakIntervalMinutes: 25,
    reduceMotion: false, // Controlled animations are OK
  },
  autism: {
    reduceMotion: true,
    reduceTransparency: true,
    hideNonEssentialUI: false,
    showProgressBars: true,
    colorTheme: "light", // Predictable, not too stimulating
  },
  motor: {
    extendedTimeouts: true,
    timeoutMultiplier: 3,
    largeClickTargets: true,
    keyboardNavigationEnhanced: true,
    fontSize: 110,
  },
  "low-vision": {
    fontSize: 130,
    lineHeight: 1.6,
    colorTheme: "high-contrast",
    largeClickTargets: true,
    keyboardNavigationEnhanced: true,
  },
};

function loadFromStorage(): AccessibilityState {
  if (!browser) return defaultState;

  try {
    const stored = localStorage.getItem("convergio-accessibility");
    if (stored) {
      return { ...defaultState, ...JSON.parse(stored) };
    }
  } catch {
    // Silent failure
  }

  // Check system preferences
  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
  const prefersHighContrast = window.matchMedia(
    "(prefers-contrast: high)",
  ).matches;
  const prefersDarkMode = window.matchMedia(
    "(prefers-color-scheme: dark)",
  ).matches;

  return {
    ...defaultState,
    reduceMotion: prefersReducedMotion,
    colorTheme: prefersHighContrast
      ? "high-contrast"
      : prefersDarkMode
        ? "dark"
        : "light",
  };
}

function saveToStorage(state: AccessibilityState) {
  if (!browser) return;

  try {
    localStorage.setItem("convergio-accessibility", JSON.stringify(state));
  } catch {
    // Silent failure
  }
}

function createAccessibilityStore() {
  const { subscribe, set, update } =
    writable<AccessibilityState>(loadFromStorage());

  return {
    subscribe,

    setProfile(profile: AccessibilityProfile) {
      update((_state) => {
        const preset = profilePresets[profile];
        const newState = { ...defaultState, ...preset, profile };
        saveToStorage(newState);
        applyStyles(newState);
        return newState;
      });
    },

    updateSetting<K extends keyof AccessibilityState>(
      key: K,
      value: AccessibilityState[K],
    ) {
      update((state) => {
        const newState = {
          ...state,
          [key]: value,
          profile: "default" as AccessibilityProfile,
        };
        saveToStorage(newState);
        applyStyles(newState);
        return newState;
      });
    },

    reset() {
      const state = defaultState;
      saveToStorage(state);
      applyStyles(state);
      set(state);
    },

    init() {
      const state = loadFromStorage();
      applyStyles(state);
      set(state);
    },
  };
}

function applyStyles(state: AccessibilityState) {
  if (!browser) return;

  const root = document.documentElement;

  // Font settings
  root.style.setProperty("--a11y-font-size", `${state.fontSize}%`);
  root.style.setProperty("--a11y-line-height", `${state.lineHeight}`);
  root.style.setProperty("--a11y-letter-spacing", `${state.letterSpacing}em`);
  root.style.setProperty("--a11y-max-line-width", `${state.maxLineWidth}ch`);

  // Font family
  const fontFamilies: Record<FontFamily, string> = {
    system: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    opendyslexic: '"OpenDyslexic", sans-serif',
    arial: "Arial, sans-serif",
    verdana: "Verdana, sans-serif",
    times: '"Times New Roman", serif',
  };
  root.style.setProperty("--a11y-font-family", fontFamilies[state.fontFamily]);

  // Color theme classes
  root.classList.remove(
    "theme-light",
    "theme-dark",
    "theme-cream",
    "theme-high-contrast",
    "theme-blue-light",
  );
  root.classList.add(`theme-${state.colorTheme}`);

  // Motion
  if (state.reduceMotion) {
    root.classList.add("reduce-motion");
  } else {
    root.classList.remove("reduce-motion");
  }

  // Large click targets
  if (state.largeClickTargets) {
    root.classList.add("large-targets");
  } else {
    root.classList.remove("large-targets");
  }

  // Focus mode
  if (state.focusModeEnabled) {
    root.classList.add("focus-mode");
  } else {
    root.classList.remove("focus-mode");
  }
}

export const accessibilityStore = createAccessibilityStore();

// Derived stores for specific features
export const isReducedMotion = derived(
  accessibilityStore,
  ($state) => $state.reduceMotion,
);
export const isFocusMode = derived(
  accessibilityStore,
  ($state) => $state.focusModeEnabled,
);
export const isHighContrast = derived(
  accessibilityStore,
  ($state) => $state.colorTheme === "high-contrast",
);
export const isTTSEnabled = derived(
  accessibilityStore,
  ($state) => $state.textToSpeechEnabled,
);
