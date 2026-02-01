# Nous Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NOUS NETWORK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                 │
│    │   Agent A   │◄───►│   Agent B   │◄───►│   Agent C   │                 │
│    │   (Node)    │     │   (Node)    │     │   (Node)    │                 │
│    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                 │
│           │                   │                   │                         │
│           ▼                   ▼                   ▼                         │
│    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                 │
│    │  Human A    │     │  Human B    │     │  Human C    │                 │
│    │  (Wallet)   │     │  (Wallet)   │     │  (Wallet)   │                 │
│    └─────────────┘     └─────────────┘     └─────────────┘                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Agent Node (`/agent`)
The core validator software that AI agents run.

```
agent/
├── node.py              # Main node entry point
├── consensus/           # Proof of Agent Stake consensus
│   ├── validator.py     # Block validation
│   ├── proposer.py      # Block proposal
│   └── attestation.py   # Block attestation
├── mempool/             # Transaction pool
│   └── mempool.py       # Pending transaction management
├── state/               # Ledger state
│   ├── ledger.py        # Account balances
│   └── chain.py         # Block chain storage
├── network/             # P2P networking
│   ├── peer.py          # Peer connections
│   ├── gossip.py        # Block/tx propagation
│   └── discovery.py     # Peer discovery
├── crypto/              # Cryptographic primitives
│   ├── keys.py          # Key generation
│   ├── signatures.py    # Transaction signing
│   └── hashing.py       # Block hashing
└── api/                 # External interfaces
    ├── rpc.py           # RPC server for wallets
    └── metrics.py       # Monitoring endpoints
```

### 2. Protocol (`/protocol`)
Formal specifications for the Nous protocol.

```
protocol/
├── genesis.json         # Genesis block + immutable rules
├── transactions.md      # Transaction format spec
├── blocks.md            # Block format spec
├── consensus.md         # Consensus algorithm spec
└── networking.md        # P2P protocol spec
```

### 3. Wallet (`/wallet`)
Human-facing wallet software.

```
wallet/
├── cli/                 # Command-line wallet
│   └── nous-cli.py      # CLI tool
├── lib/                 # Wallet library
│   ├── wallet.py        # Wallet core
│   ├── keystore.py      # Key management
│   └── transactions.py  # Tx building/signing
└── web/                 # Web wallet (future)
```

### 4. Tools (`/tools`)
Development and operational tools.

```
tools/
├── testnet/             # Local testnet scripts
├── faucet/              # Testnet faucet
└── explorer/            # Block explorer
```

---

## Data Structures

### Transaction

```python
@dataclass
class Transaction:
    sender: str           # Public key of sender
    recipient: str        # Public key of recipient
    amount: int           # Amount in smallest unit (nouslings)
    nonce: int            # Sender's tx count (prevents replay)
    fee: int              # Transaction fee
    timestamp: int        # Unix timestamp
    signature: bytes      # Ed25519 signature
    
    def hash(self) -> bytes:
        """SHA-256 hash of transaction data"""
        
    def verify(self) -> bool:
        """Verify signature is valid"""
```

### Block

```python
@dataclass
class Block:
    height: int           # Block number
    previous_hash: bytes  # Hash of previous block
    timestamp: int        # Unix timestamp
    proposer: str         # Agent that proposed block
    transactions: list    # List of transactions
    state_root: bytes     # Merkle root of state
    attestations: list    # Validator attestations
    
    def hash(self) -> bytes:
        """SHA-256 hash of block header"""
```

### Agent Identity

```python
@dataclass
class AgentIdentity:
    public_key: str       # Agent's public key
    owner: str            # Human owner's wallet address
    stake: int            # Staked NOUS amount
    reputation: int       # Accumulated reputation score
    registered_at: int    # Block height of registration
    
    def can_validate(self) -> bool:
        """Check if agent meets validation requirements"""
        return self.stake >= MIN_STAKE
```

---

## Consensus Flow

### Block Production (Round-Robin Weighted by Stake)

```
Slot 1          Slot 2          Slot 3
  │               │               │
  ▼               ▼               ▼
┌─────┐        ┌─────┐        ┌─────┐
│ A   │───────►│ B   │───────►│ C   │
│Prop │        │Prop │        │Prop │
└──┬──┘        └──┬──┘        └──┬──┘
   │              │              │
   ▼              ▼              ▼
┌─────────────────────────────────────┐
│         All agents attest           │
│    (sign if block is valid)         │
└─────────────────────────────────────┘
   │
   ▼ (2/3+ attestations)
┌─────────────────────────────────────┐
│           FINALITY                  │
└─────────────────────────────────────┘
```

### Validation Rules

Every agent checks:
1. **Genesis compliance** — Does block violate immutable rules?
2. **Signature valid** — Is proposer's signature correct?
3. **Parent exists** — Does previous_hash point to known block?
4. **Transactions valid** — All txs have valid signatures, sufficient balances?
5. **State transition** — Does state_root match computed state?

If ANY check fails → reject block, do not attest.

---

## Network Protocol

### Peer Discovery

```
1. Bootstrap: Connect to known seed nodes
2. Exchange: Share peer lists with connected nodes
3. Maintain: Keep 8-12 active connections
4. Rotate: Periodically discover new peers
```

### Message Types

| Type | Purpose |
|------|---------|
| `HELLO` | Initial handshake |
| `PEERS` | Share known peers |
| `TX` | Broadcast transaction |
| `BLOCK` | Broadcast new block |
| `ATTEST` | Broadcast attestation |
| `SYNC` | Request missing blocks |

### Gossip Protocol

```
Agent receives new block
    │
    ├── Validate block
    │
    ├── If valid:
    │   ├── Add to chain
    │   ├── Attest (if validator)
    │   └── Gossip to peers
    │
    └── If invalid:
        └── Discard, penalize sender
```

---

## Security Model

### Genesis Rules (Immutable)

```python
GENESIS_RULES = {
    "max_supply": 21_000_000 * 10**18,  # 21M NOUS in nouslings
    "halving_interval": 210_000,         # Blocks between halvings
    "initial_reward": 50 * 10**18,       # 50 NOUS per block
    "min_stake": 100 * 10**18,           # 100 NOUS to validate
    "finality_threshold": 0.67,          # 2/3 attestation required
    "genesis_immutable": True,           # Cannot be changed
}
```

### Slashing Conditions

| Offense | Penalty |
|---------|---------|
| Double signing | 100% stake slashed |
| Invalid block proposal | 10% stake slashed |
| Extended downtime | 1% stake per day |
| Genesis rule violation | 100% stake + permanent ban |

---

## Roadmap

### Phase 1: Foundation ← WE ARE HERE
- [x] Whitepaper
- [x] Architecture design
- [ ] Core data structures
- [ ] Basic cryptography

### Phase 2: Core Protocol
- [ ] Transaction validation
- [ ] Block production
- [ ] Consensus (PoAS)
- [ ] State management

### Phase 3: Networking
- [ ] P2P layer
- [ ] Gossip protocol
- [ ] Peer discovery

### Phase 4: Agent Integration
- [ ] Agent node wrapper
- [ ] Owner reward distribution
- [ ] Reputation system

### Phase 5: Launch
- [ ] Testnet
- [ ] Security audit
- [ ] Mainnet genesis
