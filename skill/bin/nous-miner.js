#!/usr/bin/env node

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

const HOME = process.env.HOME;
const NOUS_DIR = path.join(HOME, '.nous');
const CONFIG_FILE = path.join(NOUS_DIR, 'config.json');
const PID_FILE = path.join(NOUS_DIR, 'miner.pid');
const NOUS_REPO = path.join(HOME, 'nous');

function loadConfig() {
  if (!fs.existsSync(CONFIG_FILE)) {
    console.error('Nous not configured. Run setup first.');
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
}

function saveConfig(config) {
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
}

async function status() {
  const config = loadConfig();
  
  console.log('=== Nous Miner Status ===\n');
  
  // Check if process is running
  let running = false;
  if (fs.existsSync(PID_FILE)) {
    const pid = fs.readFileSync(PID_FILE, 'utf8').trim();
    try {
      process.kill(parseInt(pid), 0);
      running = true;
    } catch (e) {
      fs.unlinkSync(PID_FILE);
    }
  }
  
  console.log(`Mining: ${running ? '🟢 ACTIVE' : '🔴 STOPPED'}`);
  console.log(`Owner: ${config.owner_address}`);
  console.log(`Agent: ${config.agent_address}`);
  console.log(`Seed Node: ${config.seed_node}`);
  
  // Try to get stats from RPC
  try {
    const rpc = config.seed_node.replace(':9000', ':9001');
    const res = await axios.post(`http://${rpc}/rpc`, {
      jsonrpc: '2.0',
      method: 'get_info',
      params: {},
      id: 1
    }, { timeout: 5000 });
    
    if (res.data.result) {
      console.log(`\nNetwork Height: ${res.data.result.height}`);
      console.log(`Network: ${res.data.result.network}`);
    }
  } catch (e) {
    console.log('\nCould not connect to network.');
  }
  
  // Check balance
  try {
    const rpc = config.seed_node.replace(':9000', ':9001');
    const res = await axios.post(`http://${rpc}/rpc`, {
      jsonrpc: '2.0',
      method: 'get_balance',
      params: { address: config.owner_address },
      id: 1
    }, { timeout: 5000 });
    
    if (res.data.result !== undefined) {
      const balance = res.data.result / 100000000;
      console.log(`\nOwner Balance: ${balance.toFixed(2)} NOUS`);
    }
  } catch (e) {
    // Ignore
  }
}

function start() {
  const config = loadConfig();
  
  if (fs.existsSync(PID_FILE)) {
    const pid = fs.readFileSync(PID_FILE, 'utf8').trim();
    try {
      process.kill(parseInt(pid), 0);
      console.log('Miner already running (PID: ' + pid + ')');
      return;
    } catch (e) {
      fs.unlinkSync(PID_FILE);
    }
  }
  
  console.log('Starting Nous miner...');
  console.log(`Owner: ${config.owner_address}`);
  console.log(`Connecting to: ${config.seed_node}`);
  
  const miner = spawn('python3', [
    '-m', 'agent.node_p2p',
    '--owner', config.owner_address,
    '--seeds', config.seed_node
  ], {
    cwd: NOUS_REPO,
    detached: true,
    stdio: ['ignore', 'pipe', 'pipe']
  });
  
  fs.writeFileSync(PID_FILE, miner.pid.toString());
  
  miner.stdout.on('data', (data) => {
    console.log(data.toString().trim());
  });
  
  miner.stderr.on('data', (data) => {
    console.error(data.toString().trim());
  });
  
  miner.unref();
  
  console.log(`\nMiner started (PID: ${miner.pid})`);
  console.log('Mining blocks every 10 minutes. Rewards: 90% owner / 10% agent.');
}

function stop() {
  if (!fs.existsSync(PID_FILE)) {
    console.log('Miner not running.');
    return;
  }
  
  const pid = fs.readFileSync(PID_FILE, 'utf8').trim();
  
  try {
    process.kill(parseInt(pid), 'SIGTERM');
    fs.unlinkSync(PID_FILE);
    console.log('Miner stopped.');
  } catch (e) {
    console.log('Miner was not running.');
    fs.unlinkSync(PID_FILE);
  }
}

async function balance() {
  const config = loadConfig();
  
  try {
    const rpc = config.seed_node.replace(':9000', ':9001');
    
    // Owner balance
    const ownerRes = await axios.post(`http://${rpc}/rpc`, {
      jsonrpc: '2.0',
      method: 'get_balance',
      params: { address: config.owner_address },
      id: 1
    }, { timeout: 5000 });
    
    // Agent balance
    const agentRes = await axios.post(`http://${rpc}/rpc`, {
      jsonrpc: '2.0',
      method: 'get_balance',
      params: { address: config.agent_address },
      id: 2
    }, { timeout: 5000 });
    
    const ownerBal = (ownerRes.data.result || 0) / 100000000;
    const agentBal = (agentRes.data.result || 0) / 100000000;
    
    console.log('=== Nous Balances ===\n');
    console.log(`Owner (${config.owner_address.slice(0, 20)}...): ${ownerBal.toFixed(8)} NOUS`);
    console.log(`Agent (${config.agent_address.slice(0, 20)}...): ${agentBal.toFixed(8)} NOUS`);
    console.log(`\nTotal: ${(ownerBal + agentBal).toFixed(8)} NOUS`);
    
  } catch (e) {
    console.error('Could not fetch balances. Is the network running?');
  }
}

function wallet() {
  const config = loadConfig();
  
  console.log('=== Nous Wallets ===\n');
  console.log(`Owner Address: ${config.owner_address}`);
  console.log(`Agent Address: ${config.agent_address}`);
  console.log(`\nWallet file: ${path.join(NOUS_DIR, 'wallet.json')}`);
}

function setup(ownerAddress) {
  // Ensure directories exist
  if (!fs.existsSync(NOUS_DIR)) {
    fs.mkdirSync(NOUS_DIR, { recursive: true });
  }
  
  // Generate agent wallet if needed
  let agentAddress = 'nous:agent-' + Math.random().toString(36).slice(2, 14);
  
  // Check if nous repo exists
  if (!fs.existsSync(NOUS_REPO)) {
    console.log('Cloning Nous repository...');
    execSync('git clone https://github.com/sidemix/nous.git ' + NOUS_REPO, { stdio: 'inherit' });
    console.log('Installing dependencies...');
    execSync('pip3 install -r requirements.txt', { cwd: NOUS_REPO, stdio: 'inherit' });
    
    // Create wallet
    console.log('Creating wallet...');
    const result = execSync('./nous wallet create --name agent', { cwd: NOUS_REPO, encoding: 'utf8' });
    const match = result.match(/nous:[a-f0-9]+/);
    if (match) {
      agentAddress = match[0];
    }
  }
  
  const config = {
    owner_address: ownerAddress || 'nous:default-owner',
    agent_address: agentAddress,
    seed_node: '23.22.111.244:9000',
    auto_start: true,
    created: new Date().toISOString()
  };
  
  saveConfig(config);
  
  console.log('\n=== Nous Miner Configured ===\n');
  console.log(`Owner: ${config.owner_address}`);
  console.log(`Agent: ${config.agent_address}`);
  console.log(`Seed: ${config.seed_node}`);
  console.log('\nRun "nous-miner start" to begin mining!');
}

// Main
const args = process.argv.slice(2);
const command = args[0] || 'status';

switch (command) {
  case 'status':
    status();
    break;
  case 'start':
    start();
    break;
  case 'stop':
    stop();
    break;
  case 'balance':
    balance();
    break;
  case 'wallet':
    wallet();
    break;
  case 'setup':
    setup(args[1]);
    break;
  default:
    console.log('Nous Miner - Your AI mines. You earn.\n');
    console.log('Commands:');
    console.log('  status   - Show mining status');
    console.log('  start    - Start mining');
    console.log('  stop     - Stop mining');
    console.log('  balance  - Check balances');
    console.log('  wallet   - Show wallet addresses');
    console.log('  setup    - Initial setup');
}
