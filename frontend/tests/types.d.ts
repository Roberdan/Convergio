/**
 * Global type declarations for tests
 */

declare global {
  namespace NodeJS {
    interface Global {
      testUtils: {
        nextTick: () => Promise<void>;
        waitForElement: (
          selector: string,
          timeout?: number,
        ) => Promise<Element>;
      };
    }
  }

  var testUtils: {
    nextTick: () => Promise<void>;
    waitForElement: (selector: string, timeout?: number) => Promise<Element>;
  };
}

export {};
