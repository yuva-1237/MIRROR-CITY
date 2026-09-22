import * as esbuild from 'esbuild';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const entry = path.join(__dirname, 'climate.test.mjs');
const outfile = path.join(__dirname, 'bundle.test.cjs');

console.log('[Test Runner] Bundling JSX/TSX tests with esbuild...');
await esbuild.build({
  entryPoints: [entry],
  bundle: true,
  outfile,
  platform: 'node',
  format: 'cjs',
  jsx: 'automatic',
  loader: { '.tsx': 'tsx', '.ts': 'ts' },
  external: ['react', 'react-dom', 'react-dom/server', 'node:test', 'node:assert/strict']
});

console.log('[Test Runner] Running Node test runner on bundled tests...');
const proc = spawn(process.execPath, ['--test', outfile], { stdio: 'inherit' });
proc.on('close', (code) => {
  process.exit(code);
});
