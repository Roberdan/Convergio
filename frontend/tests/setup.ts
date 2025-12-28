/**
 * Test setup file for vitest
 * Configures testing environment and global test utilities
 */

import { vi } from "vitest";

// Mock browser APIs that might not be available in test environment
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock performance API if not available
if (!global.performance) {
  global.performance = {
    now: () => Date.now(),
    mark: vi.fn(),
    measure: vi.fn(),
    clearMarks: vi.fn(),
    clearMeasures: vi.fn(),
    getEntriesByType: vi.fn(() => []),
    getEntriesByName: vi.fn(() => []),
    getEntries: vi.fn(() => []),
    timeOrigin: Date.now(),
  } as any;
}

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  // Uncomment to suppress console.log in tests
  // log: vi.fn(),
  // warn: vi.fn(),
  // error: vi.fn(),
};

// Mock SvelteKit environment variables
Object.defineProperty(global, "$app/environment", {
  value: {
    browser: true,
    dev: false,
    building: false,
    version: "test",
  },
});

// Mock SvelteKit navigation
Object.defineProperty(global, "$app/navigation", {
  value: {
    goto: vi.fn(),
    invalidate: vi.fn(),
    invalidateAll: vi.fn(),
    preloadData: vi.fn(),
    preloadCode: vi.fn(),
    onNavigate: vi.fn(),
    beforeNavigate: vi.fn(),
    afterNavigate: vi.fn(),
  },
});

// Mock SvelteKit stores
Object.defineProperty(global, "$app/stores", {
  value: {
    page: { subscribe: vi.fn() },
    navigating: { subscribe: vi.fn() },
    updated: { subscribe: vi.fn() },
  },
});

// Setup global test utilities
global.testUtils = {
  // Helper to wait for next tick
  nextTick: () => new Promise((resolve) => setTimeout(resolve, 0)),

  // Helper to wait for element to be present
  waitForElement: (selector: string, timeout = 1000) => {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();

      const checkElement = () => {
        const element = document.querySelector(selector);
        if (element) {
          resolve(element);
          return;
        }

        if (Date.now() - startTime > timeout) {
          reject(
            new Error(`Element ${selector} not found within ${timeout}ms`),
          );
          return;
        }

        setTimeout(checkElement, 10);
      };

      checkElement();
    });
  },
};
