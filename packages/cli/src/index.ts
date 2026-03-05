#!/usr/bin/env node

declare const __CLI_VERSION__: string;

function main(): void {
  const args = process.argv.slice(2);
  if (args.includes('--version') || args.includes('-v')) {
    console.log(`convergio-cli v${__CLI_VERSION__}`);
    return;
  }
  console.log('Convergio CLI - use --help for usage');
}

main();
