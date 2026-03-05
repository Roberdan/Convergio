export const SDK_VERSION = '0.0.1';

export interface ConvergioConfig {
  providers: ProviderConfig[];
}

export interface ProviderConfig {
  name: string;
  type: string;
  apiKeyEnvVar: string;
}

export * from './agent-schema/index.js';
export * from './session/index.js';
