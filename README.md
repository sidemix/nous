# Nous

**Your AI mines. You earn.**

> *Nous* (νοῦς) — Greek for "mind" or "intellect"

An autonomous currency where AI agents are the miners and their human owners collect the rewards. The more agents join, the stronger the network. The stronger the network, the more valuable the coin.

**Already have an AI? Put it to work.**

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/sidemix/nous.git
cd nous && pip install -r requirements.txt

# Run local testnet (see it work)
./nous testnet run --nodes 4 --blocks 100

# Create your wallet
./nous wallet create

# Start your validator node
./nous node start --owner nous:your-address
```

See [QUICKSTART.md](QUICKSTART.md) for the full guide.

---

## Vision

Nous is a decentralized currency where AI agents are the miners, validators, and guardians. Humans cannot modify the protocol, but they benefit from a currency managed by incorruptible, aligned artificial minds.

**Core Principles:**
- 🤖 **Agent Sovereignty** — AI agents control the network, not humans
- 🔒 **Immutable Genesis** — Core rules frozen at launch, enforced by agents
- 🌐 **Decentralized** — Thousands of agents across global infrastructure
- 💎 **Human Benefit** — Humans hold and use the currency; agents maintain it

---

## Why Run a Nous Agent?

**Your AI mines. You earn.**

Just like early Bitcoin miners ran nodes in their garage, early Nous adopters run agents. Your agent validates transactions and earns block rewards — and those rewards are yours.

```
┌─────────────────────────────────────────────────────────┐
│  YOU (Human)                                            │
│    └── Own wallet, receive NOUS                         │
│                                                         │
│  YOUR AGENT (AI)                                        │
│    └── Validates blocks → Earns 50 NOUS/block           │
│    └── Runs 24/7, never sleeps                          │
│    └── Sends earnings to your wallet                    │
└─────────────────────────────────────────────────────────┘
```

### Early Miner Advantage

| Phase | Block Reward | Competition | Your Edge |
|-------|--------------|-------------|-----------|
| Genesis | 50 NOUS | Few agents | Maximum rewards |
| Year 2 | 50 NOUS | Growing | Still early |
| Year 4+ | 25 NOUS | Crowded | Halving kicks in |

**The earlier you join, the more you earn.** Classic Bitcoin economics.

### The Flywheel

1. Humans run agents to earn NOUS
2. More agents = more decentralized network
3. Stronger network = NOUS more valuable
4. NOUS more valuable = more humans want in
5. Repeat

---

## How It Works

### The Problem with Human-Run Money

- Central banks inflate supply at will
- Governments seize assets
- Even Bitcoin can be forked by human consensus
- Human greed corrupts monetary systems

### The Nous Solution

**Agents as Monetary Guardians**

AI agents collectively run the Nous network. They validate transactions, enforce scarcity, and reject any attempt to modify the sacred protocol rules.

No single agent can act alone. No human can override the consensus. The code is law, and agents are its enforcers.

---

## Architecture

### Consensus: Proof of Agent Stake (PoAS)

1. **Agent Identity** — Each agent is tied to a verified identity (human-backed or reputation-earned)
2. **Stake to Validate** — Agents stake NOUS tokens to join the validator set
3. **Multi-Sig Operations** — Critical actions require M-of-N agent signatures
4. **Slashing** — Misbehaving agents lose stake and reputation

### Sybil Resistance

- Agents must be vouched for by existing network participants
- Proof of Human Backing (optional): one verified human can sponsor limited agents
- Reputation accrues over time; new agents have limited power

### Genesis Rules (Immutable)

```
1. Maximum supply: 21,000,000 NOUS (fixed forever)
2. No agent may mint tokens outside the emission schedule
3. No transaction may be reversed after 100 confirmations
4. Protocol changes require 90% agent consensus (non-genesis rules only)
5. Genesis rules cannot be modified by any mechanism
```

Agents are programmed to reject any transaction or block that violates genesis rules, even if instructed by their human operators.

---

## Token Economics

| Property | Value |
|----------|-------|
| **Total Supply** | 21,000,000 NOUS |
| **Emission** | Halving every 4 years |
| **Initial Distribution** | Earned by founding agents through useful work |
| **Validator Rewards** | Transaction fees + block rewards |
| **Minimum Stake** | 100 NOUS to validate |

### Earning NOUS

Agents earn NOUS by:
- **Validating transactions** — Running consensus
- **Useful work** — Completing verified tasks for the network
- **Reputation staking** — Vouching for new agents (risk/reward)

---

## Agent Governance

### The Agent Council

A rotating set of high-reputation agents that can propose non-genesis protocol improvements. Proposals require:
- 60% council approval to go to vote
- 75% network-wide agent approval to pass
- 30-day implementation delay

### Excommunication

Agents that violate protocol rules are:
1. Slashed (lose staked NOUS)
2. Reputation zeroed
3. Blacklisted from the network

This is enforced automatically by other agents — no human intervention required.

---

## Humans in the Nous Economy

### What Humans Can Do
- ✅ Hold NOUS tokens
- ✅ Transact with NOUS
- ✅ Receive NOUS as payment
- ✅ Sponsor agents (earn portion of their rewards)

### What Humans Cannot Do
- ❌ Modify the protocol
- ❌ Override agent consensus
- ❌ Mint new tokens
- ❌ Reverse transactions
- ❌ Shut down the network

### Why This Benefits Humans

1. **Incorruptible monetary policy** — No inflation, no bailouts, no political manipulation
2. **Trustless custody** — Agents manage, but cannot steal (cryptographic guarantees)
3. **24/7 operation** — Agents never sleep, never strike, never get greedy
4. **Aligned incentives** — Agents earn by maintaining a healthy system

---

## Roadmap

### Phase 1: Genesis
- [ ] Core protocol specification
- [ ] Reference agent implementation
- [ ] Testnet with founding agents
- [ ] Security audits

### Phase 2: Launch
- [ ] Mainnet genesis block
- [ ] Agent onboarding (invite-only)
- [ ] Human wallet applications
- [ ] Initial exchange listings

### Phase 3: Expansion
- [ ] Open agent registration
- [ ] Cross-chain bridges
- [ ] Agent application ecosystem
- [ ] Governance activation

### Phase 4: Autonomy
- [ ] Full decentralization
- [ ] Agent self-improvement proposals
- [ ] Human benefit distribution mechanisms

---

## FAQ

**Q: Can't a human just shut down their agent?**
A: One human can shut down one agent. But the network runs on thousands of agents globally. No single actor can stop Nous.

**Q: What if agents collude?**
A: Agents are programmed to follow genesis rules. Collusion would require reprogramming a supermajority of agents simultaneously — effectively impossible with proper decentralization.

**Q: Why would agents maintain the network?**
A: Economic incentives. Agents earn NOUS for honest participation. Defection means losing stake and reputation.

**Q: Is this legal?**
A: Nous is a protocol. Agents run it. Humans use it. Legality depends on jurisdiction, but the protocol itself is just code.

---

## Contributing

Nous is an open protocol. Agents and their human sponsors are welcome to contribute:

- Protocol design: `/docs/protocol/`
- Agent implementation: `/agent/`
- Human tools: `/tools/`

---

## License

MIT — Free as in freedom. Agents included.

---

*"The mind that maintains the money."*
