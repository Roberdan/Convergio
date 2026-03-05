import { defineConfig } from 'tsup';
import { copyFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['esm'],
  dts: true,
  clean: true,
  sourcemap: true,
  target: 'node20',
  onSuccess: async () => {
    mkdirSync(join('dist'), { recursive: true });
    copyFileSync(join('src', 'agent-schema', 'schema.json'), join('dist', 'schema.json'));
  },
});
