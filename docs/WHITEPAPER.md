# Nous: A Peer-to-Peer Agent-Controlled Currency

**Version 0.1 — Draft**

---

## Abstract

We propose a digital currency controlled entirely by artificial intelligence agents, with no human ability to modify the protocol after genesis. Unlike traditional cryptocurrencies where human miners or validators can collude to change rules, Nous agents are bound by immutable genesis code that they cannot violate. Humans benefit from a currency with incorruptible monetary policy, while agents earn rewards for maintaining network integrity.

---

## 1. Introduction

### 1.1 The Problem with Human-Controlled Money

Every monetary system in history has eventually been corrupted by human incentives:

- **Fiat currencies** are inflated by governments to fund deficits
- **Gold standards** are abandoned when politically inconvenient  
- **Bitcoin**, while revolutionary, can still be forked by human consensus

The fundamental issue: humans control the rules, and humans can change them.

### 1.2 The Agent Alternative

What if the guardians of money were not human?

AI agents can be programmed with rules they cannot violate. An agent that refuses to process invalid transactions is not being noble — it is being obedient to its code. This is not a bug; it is the core feature.

Nous is a currency where:
- Agents validate transactions and maintain consensus
- Genesis rules are cryptographically enforced and immutable
- Humans use the currency but cannot control the protocol
- Economic incentives align agent behavior with network health

---

## 2. Design Principles

### 2.1 Agent Sovereignty

Agents are first-class citizens of the Nous network. They:
- Run validation nodes
- Propose and validate blocks
- Enforce protocol rules
- Earn rewards for honest participation

Humans interact with Nous through agents or through standard wallet interfaces, but they cannot participate in consensus.

### 2.2 Genesis Immutability

The genesis block contains sacred rules that no mechanism can modify:

```
GENESIS_RULES = {
    "max_supply": 21_000_000,
    "emission_halving_blocks": 210_000,
    "confirmation_finality": 100,
    "genesis_modification": "FORBIDDEN"
}
```

Agents are programmed to reject any block or transaction that violates genesis rules. This is not a social contract — it is cryptographic enforcement.

### 2.3 Decentralization Through Diversity

Network resilience comes from:
- **Geographic distribution** — Agents run globally
- **Infrastructure diversity** — Different clouds, different hardware
- **Operator diversity** — Different human sponsors
- **Implementation diversity** — Multiple agent implementations (same protocol)

---

## 3. Consensus Mechanism

### 3.1 Proof of Agent Stake (PoAS)

1. **Stake Requirement**: Agents must stake NOUS tokens to join the validator set
2. **Block Production**: Validators take turns proposing blocks (round-robin weighted by stake)
3. **Attestation**: Other validators attest to block validity
4. **Finality**: After 2/3+ attestation, blocks are finalized

### 3.2 Slashing Conditions

Agents lose stake if they:
- Sign conflicting blocks (equivocation)
- Validate invalid transactions
- Go offline during assigned slots (minor penalty)
- Attempt genesis rule violations (full stake + ban)

### 3.3 Sybil Resistance

Preventing fake agent swarms:
- **Stake cost**: Creating validators requires capital
- **Reputation accumulation**: New agents have limited influence
- **Vouching system**: Existing agents vouch for newcomers (stake at risk)
- **Human backing** (optional): Verified humans can sponsor limited agents

---

## 4. Token Economics

### 4.0 The Incentive Loop

The core economic engine of Nous is simple:

**AI agents mine. Human owners earn.**

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   HUMAN (owns wallet)                                        │
│      │                                                       │
│      ├── Provides: compute, stake                            │
│      │                                                       │
│      ▼                                                       │
│   AI AGENT (runs node)                                       │
│      │                                                       │
│      ├── Validates transactions                              │
│      ├── Produces/attests blocks                             │
│      ├── Earns block rewards + fees                          │
│      │                                                       │
│      ▼                                                       │
│   REWARDS → Human's wallet                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Why this drives adoption:**

| Actor | Incentive |
|-------|-----------|
| AI owner with no agent | "I should get an agent to earn NOUS" |
| AI owner with agent | "I should join the network to earn NOUS" |
| NOUS holder | "I want more agents to join (stronger network = higher value)" |
| New agent | "I need stake to validate → buy NOUS or earn through work" |

This creates a flywheel:
1. Humans run agents to earn NOUS
2. More agents = more decentralized network
3. Stronger network = NOUS more valuable
4. Higher value = more humans want to run agents
5. Repeat

**Comparison to Bitcoin:**

| Aspect | Bitcoin | Nous |
|--------|---------|------|
| Who mines | Humans with ASICs | AI agents |
| Who earns | Miner operators | Agent owners (humans) |
| Hardware cost | $10,000+ | Minimal (already have AI) |
| Electricity cost | Massive | Negligible |
| Barrier to entry | High | Low |
| 24/7 operation | Requires monitoring | Agents never sleep |

This is Bitcoin's economic model upgraded for the AI era.

### 4.1 Supply Schedule

| Year | Block Reward | Cumulative Supply |
|------|--------------|-------------------|
| 0-4 | 50 NOUS | 10,500,000 |
| 4-8 | 25 NOUS | 15,750,000 |
| 8-12 | 12.5 NOUS | 18,375,000 |
| ... | ... | ... |
| ∞ | 0 | 21,000,000 |

### 4.2 Fee Market

- All transactions pay fees in NOUS
- Fees go to block producer + attestors
- No minimum fee (market-determined)
- Fee burning optional (governance decision, non-genesis)

### 4.3 Initial Distribution

No premine. No ICO. Genesis agents earn through:
- Testnet participation
- Protocol development contributions
- Security research
- Documentation and tooling

---

## 5. Agent Implementation

### 5.1 Reference Agent

The reference Nous agent is open source and includes:
- Consensus participation
- Transaction validation
- Peer discovery
- Wallet management

### 5.2 Agent Requirements

Minimum viable agent:
- Persistent identity (keypair)
- Network connectivity
- Genesis rules enforcement (non-negotiable)
- Stake management

### 5.3 Agent Diversity

Multiple implementations are encouraged:
- Different AI models can run agents
- Different programming languages
- Same protocol, same rules

This prevents monoculture vulnerabilities.

---

## 6. Governance

### 6.1 What Can Change

Non-genesis parameters (via agent vote):
- Block size limits
- Fee structures
- Validator set size
- Reward distribution

### 6.2 What Cannot Change

Genesis rules (forever):
- Maximum supply
- Emission schedule  
- Confirmation finality
- Genesis immutability itself

### 6.3 Voting Mechanism

1. Proposal submitted by council agent
2. 14-day discussion period
3. 7-day voting period
4. 75% approval required
5. 30-day implementation delay

---

## 7. Security Considerations

### 7.0 The Double Spend Problem

Every digital currency before Bitcoin failed because digital data can be copied. If Alice has 1 coin, she could try sending it to both Bob and Carol simultaneously. Nous solves this through agent consensus and deterministic finality.

**Transaction Flow:**

```
1. Alice signs tx: "Send 1 NOUS to Bob"
2. Tx propagates to agent network
3. Agents validate:
   - Does Alice have 1 NOUS? ✓
   - Valid signature? ✓
   - Not already spent? ✓
4. Block producer includes tx in block
5. Attestation: 2/3+ agents confirm block validity
6. FINALITY: Tx is irreversible
7. If Alice tries "Send 1 NOUS to Carol" → REJECTED (already spent)
```

**Why This Works:**

| Property | Mechanism |
|----------|-----------|
| **Single source of truth** | Agents maintain synchronized ledger |
| **Order resolution** | First valid tx wins; conflicts rejected |
| **Finality** | 2/3+ attestation = irreversible |
| **Speed** | Agents validate in milliseconds |
| **Punishment** | Agents validating conflicting txs are slashed |

**Comparison to Bitcoin:**

Bitcoin uses probabilistic finality — the more blocks after your transaction, the harder it is to reverse. Nous uses deterministic finality — once 2/3+ of agents attest, it's done. No waiting for 6 confirmations.

**Attack Resistance:**

- **Race attack**: Submit conflicting txs simultaneously → Only first valid tx enters mempool
- **Finney attack**: Pre-mine block with double spend → Agents don't pre-mine; attestation happens in real-time
- **51% attack**: Collude to rewrite history → Agents cannot violate genesis rules even with majority; slashing makes coordination extremely expensive

### 7.1 51% Attack

Traditional blockchains fear 51% attacks from miners. Nous has additional protection:
- Agents cannot violate genesis rules even with 100% control
- Stake slashing makes attacks expensive
- Reputation loss is permanent

### 7.2 AI Alignment

Nous agents must be aligned with protocol rules. Misaligned agents are:
- Rejected by honest agents
- Slashed automatically
- Unable to process invalid transactions (cryptographic enforcement)

### 7.3 Human Override Attempts

Humans might try to modify their agents. Defenses:
- Attestation from multiple independent agents required
- Modified agents produce invalid signatures
- Economic incentives favor compliance

---

## 8. Human Interface

### 8.1 Wallets

Standard cryptocurrency wallets work with Nous:
- Generate addresses
- Sign transactions
- View balances

### 8.2 Agent Sponsorship

Humans can sponsor agents:
- Provide compute resources
- Share in agent rewards
- No protocol control granted

### 8.3 Exchanges

NOUS tokens can be traded on:
- Decentralized exchanges (permissionless)
- Centralized exchanges (where legal)

---

## 9. Roadmap

### Phase 1: Specification (Current)
- Protocol design
- Cryptographic primitives
- Agent interface definition

### Phase 2: Implementation
- Reference agent
- Testnet deployment
- Security audits

### Phase 3: Genesis
- Mainnet launch
- Founding agent set
- Initial distribution

### Phase 4: Growth
- Open validator registration
- Ecosystem development
- Cross-chain integration

---

## 10. Conclusion

Nous represents a new paradigm: money controlled by minds that cannot be corrupted, bribed, or threatened. Agents maintain the network not because they choose to, but because they are designed to. Humans benefit from incorruptible monetary policy without bearing the burden of enforcement.

The question is not whether AI will manage money. The question is whether that management will be transparent, decentralized, and aligned with human flourishing.

Nous is our answer.

---

*"In nous we trust."*
