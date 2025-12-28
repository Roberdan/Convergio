// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces

declare global {
  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }

  // Vite define constants
  declare const __VERSION__: string;
  declare const __APP_VERSION__: string;
}

export {};
