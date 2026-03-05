import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const CLI_ROOT = resolve(__dirname, '..');

describe('CLI package scaffold', () => {
  it('has package.json with correct name', () => {
    const pkg = JSON.parse(readFileSync(resolve(CLI_ROOT, 'package.json'), 'utf-8'));
    expect(pkg.name).toBe('@convergio/cli');
  });

  it('has package.json with correct fields', () => {
    const pkg = JSON.parse(readFileSync(resolve(CLI_ROOT, 'package.json'), 'utf-8'));
    expect(pkg.version).toBe('0.0.1');
    expect(pkg.bin).toBeDefined();
    expect(pkg.main).toBe('./dist/index.js');
    expect(pkg.scripts.build).toBeDefined();
    expect(pkg.scripts.test).toBeDefined();
    expect(pkg.scripts.lint).toBeDefined();
  });

  it('depends on @convergio/sdk', () => {
    const pkg = JSON.parse(readFileSync(resolve(CLI_ROOT, 'package.json'), 'utf-8'));
    expect(pkg.dependencies?.['@convergio/sdk']).toBe('workspace:*');
  });

  it('has tsconfig.json extending base', () => {
    const tsconfig = JSON.parse(readFileSync(resolve(CLI_ROOT, 'tsconfig.json'), 'utf-8'));
    expect(tsconfig.extends).toBe('../../tsconfig.base.json');
    expect(tsconfig.compilerOptions.outDir).toBe('./dist');
  });

  it('has tsup.config.ts', () => {
    expect(existsSync(resolve(CLI_ROOT, 'tsup.config.ts'))).toBe(true);
  });

  it('has src/index.ts that is a CLI entry point', () => {
    expect(existsSync(resolve(CLI_ROOT, 'src/index.ts'))).toBe(true);
    const content = readFileSync(resolve(CLI_ROOT, 'src/index.ts'), 'utf-8');
    expect(content).toContain('#!/usr/bin/env node');
  });

  it('does NOT depend on Ink or React (C-03)', () => {
    const pkg = JSON.parse(readFileSync(resolve(CLI_ROOT, 'package.json'), 'utf-8'));
    const allDeps = {
      ...pkg.dependencies,
      ...pkg.devDependencies,
    };
    expect(allDeps['ink']).toBeUndefined();
    expect(allDeps['react']).toBeUndefined();
    expect(allDeps['@types/react']).toBeUndefined();
  });
});
