#!/usr/bin/env python3
"""
Nous P2P Seed Node

The first node in the Nous network. Other agents connect to this.
"""

import sys
sys.path.insert(0, '/home/ubuntu/nous')

import asyncio
from agent.node_p2p import run_node
from agent.consensus.validator import GENESIS_RULES

print()
print("╔══════════════════════════════════════════════════════════════════╗")
print("║                    NOUS P2P SEED NODE                            ║")
print("║         Feb 2026 — The first currency mined by AI,               ║")
print("║                        owned by humans                           ║")
print("╠══════════════════════════════════════════════════════════════════╣")
print(f"║  Genesis Hash: {GENESIS_RULES['genesis_hash'][:40]}...  ║")
print(f"║  Genesis Owner: {GENESIS_RULES['genesis_owner'][:50]}  ║")
print("╚══════════════════════════════════════════════════════════════════╝")
print()

asyncio.run(run_node(
    owner_address=GENESIS_RULES['genesis_owner'],
    port=9000,      # P2P port
    rpc_port=9001,  # RPC port
    is_seed_node=True,
))
