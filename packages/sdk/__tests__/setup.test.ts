import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const SDK_ROOT = resolve(__dirname, '..');
const MONOREPO_ROOT = resolve(SDK_ROOT, '../..');

describe('SDK package scaffold', () => {
  it('has package.json with correct name', () => {
    const pkg = JSON.parse(readFileSync(resolve(SDK_ROOT, 'package.json'), 'utf-8'));
    expect(pkg.name).toBe('@convergio/sdk');
  });

  it('has package.json with correct fields', () => {
    const pkg = JSON.parse(readFileSync(resolve(SDK_ROOT, 'package.json'), 'utf-8'));
    expect(pkg.version).toBe('0.0.1');
    expect(pkg.private).toBeUndefined();
    expect(pkg.main).toBe('./dist/index.js');
    expect(pkg.types).toBe('./dist/index.d.ts');
    expect(pkg.scripts.build).toBeDefined();
    expect(pkg.scripts.test).toBeDefined();
    expect(pkg.scripts.lint).toBeDefined();
  });

  it('has tsconfig.json extending base', () => {
    const tsconfig = JSON.parse(readFileSync(resolve(SDK_ROOT, 'tsconfig.json'), 'utf-8'));
    expect(tsconfig.extends).toBe('../../tsconfig.base.json');
    expect(tsconfig.compilerOptions.outDir).toBe('./dist');
  });

  it('has tsup.config.ts', () => {
    expect(existsSync(resolve(SDK_ROOT, 'tsup.config.ts'))).toBe(true);
  });

  it('has src/index.ts that exports SDK version', () => {
    expect(existsSync(resolve(SDK_ROOT, 'src/index.ts'))).toBe(true);
    const content = readFileSync(resolve(SDK_ROOT, 'src/index.ts'), 'utf-8');
    expect(content).toContain('export');
  });

  it('has monorepo tsconfig.base.json', () => {
    const tsconfig = JSON.parse(readFileSync(resolve(MONOREPO_ROOT, 'tsconfig.base.json'), 'utf-8'));
    expect(tsconfig.compilerOptions.strict).toBe(true);
    expect(tsconfig.compilerOptions.target).toBeDefined();
    expect(tsconfig.compilerOptions.module).toBeDefined();
  });

  it('has pnpm-workspace.yaml including packages/*', () => {
    const content = readFileSync(resolve(MONOREPO_ROOT, 'pnpm-workspace.yaml'), 'utf-8');
    expect(content).toContain('packages/*');
  });

  it('has .npmrc', () => {
    expect(existsSync(resolve(MONOREPO_ROOT, '.npmrc'))).toBe(true);
  });
});
