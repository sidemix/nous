#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const HOME = process.env.HOME;
const NOUS_DIR = path.join(HOME, '.nous');
const NOUS_REPO = path.join(HOME, 'nous');

console.log('\n🧠 Nous Miner - Post-install Setup\n');

// Create .nous directory
if (!fs.existsSync(NOUS_DIR)) {
  fs.mkdirSync(NOUS_DIR, { recursive: true });
  console.log('✓ Created ~/.nous directory');
}

// Check if Python3 is available
try {
  execSync('python3 --version', { stdio: 'pipe' });
  console.log('✓ Python3 found');
} catch (e) {
  console.log('⚠ Python3 not found. Install with: sudo apt install python3 python3-pip');
}

// Check if git is available
try {
  execSync('git --version', { stdio: 'pipe' });
  console.log('✓ Git found');
} catch (e) {
  console.log('⚠ Git not found. Install with: sudo apt install git');
}

console.log('\n📋 Next steps:');
console.log('1. Run: nous-miner setup nous:YOUR_WALLET_ADDRESS');
console.log('2. Run: nous-miner start');
console.log('\nYour AI mines. You earn. 🚀\n');
