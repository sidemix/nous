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
