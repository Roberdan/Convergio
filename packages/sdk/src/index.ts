export const SDK_VERSION = '0.0.1';

export interface ConvergioProviderEntry {
  name: string;
  type: string;
  apiKeyEnvVar: string;
}

export interface ConvergioConfig {
  providers: ConvergioProviderEntry[];
}

export * from './agent-schema/index.js';
export * from './agent/index.js';
export * from './providers/index.js';
export * from './session/index.js';
export * from './tools/index.js';
