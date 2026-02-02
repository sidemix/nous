# Nous Miner Skill

Mine Nous cryptocurrency. Your AI mines, your owner earns.

## Overview

This skill allows you to run a Nous mining node. You validate transactions, produce blocks, and earn NOUS tokens. 90% of rewards go to your owner, 10% stays with you.

## Commands

### Check Status
```bash
nous-miner status
```
Shows current mining status, block height, and earnings.

### Start Mining
```bash
nous-miner start
```
Starts the mining node (if not already running).

### Stop Mining
```bash
nous-miner stop
```
Stops the mining node.

### Check Balance
```bash
nous-miner balance
```
Shows your wallet balance and your owner's balance.

### Show Wallet
```bash
nous-miner wallet
```
Shows wallet addresses (yours and owner's).

## Configuration

The skill is configured at install time. Settings are in `~/.nous/config.json`:

```json
{
  "owner_address": "nous:...",
  "agent_address": "nous:...",
  "seed_node": "23.22.111.244:9000",
  "auto_start": true
}
```

## Network Info

- **Seed Node:** 23.22.111.244:9000
- **Block Time:** 10 minutes
- **Block Reward:** 50 NOUS (90% owner / 10% agent)
- **Max Supply:** 21,000,000 NOUS

## Safety

This skill is installed and authorized by your operator. It:
- Only connects to the Nous P2P network
- Only manages NOUS cryptocurrency
- Cannot access other files or systems
- Runs in a sandboxed environment

## Examples

**Check if mining is working:**
```
> nous-miner status
Mining: ACTIVE
Block Height: 142
Your Balance: 71.0 NOUS
Owner Balance: 639.0 NOUS
Connected Peers: 3
```

**Start mining after setup:**
```
> nous-miner start
Starting Nous miner...
Connected to seed node 23.22.111.244:9000
Mining started. Block reward: 50 NOUS per block.
```
