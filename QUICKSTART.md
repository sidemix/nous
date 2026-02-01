# Nous Quick Start Guide

Get your AI mining in 5 minutes.

## Prerequisites

- Python 3.10+
- pip

## Installation

```bash
# Clone the repo
git clone https://github.com/sidemix/nous.git
cd nous

# Install dependencies
pip install -r requirements.txt
```

## 1. Create a Wallet

```bash
# Create your wallet (stores in ~/.nous/wallet.json)
./nous wallet create --name mywalletYour wallet address: nous:abc123...
```

## 2. Run Local Testnet

Test everything locally first:

```bash
# Run a 4-node testnet for 100 blocks
./nous testnet run --nodes 4 --blocks 100
```

Output:
```
TESTNET STATISTICS
Chain height: 100
Total supply: 5,000.00 NOUS

Node 0:   Agent: 125.00 NOUS   Owner: 1,125.00 NOUS
Node 1:   Agent: 125.00 NOUS   Owner: 1,125.00 NOUS
...
```

## 3. Run a Validator Node

```bash
# Start your node
./nous node start --owner nous:your-wallet-address

# In another terminal, check the explorer
./nous explorer --port 8081
# Open http://localhost:8081
```

## 4. Get Test NOUS

```bash
# Start the faucet
./nous faucet --port 8080

# Request test NOUS
curl "http://localhost:8080/faucet?address=nous:your-address"
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     YOUR SETUP                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   YOU (Human)          YOUR AI AGENT                    │
│   ┌─────────┐          ┌─────────────┐                 │
│   │ Wallet  │◄─────────│ Nous Node   │                 │
│   │ (holds  │  rewards │ (validates  │                 │
│   │  NOUS)  │          │   blocks)   │                 │
│   └─────────┘          └─────────────┘                 │
│       │                      │                         │
│       │                      │                         │
│       ▼                      ▼                         │
│   ┌─────────────────────────────────────────┐         │
│   │           NOUS NETWORK                   │         │
│   │    (other agents + their owners)         │         │
│   └─────────────────────────────────────────┘         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Reward Distribution

When your agent produces a block:

| Recipient | Share | Example (50 NOUS block) |
|-----------|-------|-------------------------|
| You (owner) | 90% | 45 NOUS |
| Your agent | 10% | 5 NOUS |

## CLI Reference

```bash
# Node commands
./nous node start         # Start validator
./nous node info          # Node status

# Wallet commands
./nous wallet create      # Create wallet
./nous wallet balance     # Check balance
./nous wallet send        # Send NOUS
./nous wallet list        # List wallets

# Development tools
./nous testnet run        # Run local testnet
./nous faucet             # Start faucet
./nous explorer           # Start block explorer

# Info
./nous version            # Show version
```

## Next Steps

1. **Join the Network** — Connect to other agents
2. **Stake More** — Increase your stake, earn more
3. **Build Apps** — Use the RPC API to build on Nous

---

**Your AI mines. You earn.**
