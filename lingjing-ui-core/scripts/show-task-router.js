#!/usr/bin/env node
const path = require('path');
const fs = require('fs');

const SKILL_ROOT = path.resolve(__dirname, '..');
const routerPath = path.join(SKILL_ROOT, 'data/task_router.json');

if (!fs.existsSync(routerPath)) {
  console.error('[ERROR] data/task_router.json not found.');
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(routerPath, 'utf8'));
console.log(JSON.stringify(data, null, 2));
