#!/usr/bin/env node

import { SDK_VERSION } from '@convergio/sdk';

function main(): void {
  const args = process.argv.slice(2);
  if (args.includes('--version') || args.includes('-v')) {
    console.log(`convergio-cli v${SDK_VERSION}`);
    return;
  }
  console.log('Convergio CLI - use --help for usage');
}

main();
