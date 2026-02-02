#!/usr/bin/env python3
"""
Nous Node Launcher

Starts the first Nous validator node with locked genesis rules.
"""

import sys
sys.path.insert(0, '/home/ubuntu/nous')

from agent.node import create_node
from agent.api.rpc import RPCServer
from agent.core.transaction import NOUS
from agent.consensus.validator import GENESIS_RULES

print()
print('╔══════════════════════════════════════════════════════════════════╗')
print('║                         NOUS NODE                                ║')
print('║         Feb 2026 — The first currency mined by AI,               ║')
print('║                        owned by humans                           ║')
print('╠══════════════════════════════════════════════════════════════════╣')
print('║  Genesis Hash: 7da31c120616b05a818beb854245449afb0622b5eeac...   ║')
print('╚══════════════════════════════════════════════════════════════════╝')
print()

# Create node with Tyler as owner (genesis owner)
genesis_owner = GENESIS_RULES['genesis_owner']
node = create_node(owner_address=genesis_owner)

# Initialize genesis with minimum stake (1 NOUS)
min_stake = GENESIS_RULES['min_stake']
node.initialize_genesis(
    initial_validators=[node.config.address],
    initial_balances={node.config.address: min_stake},
)

# Set up as agent
node.state.ledger.get_account(node.config.address).is_agent = True
node.state.ledger.get_account(node.config.address).owner = node.config.owner_address
node.state.ledger.get_account(node.config.address).staked = min_stake

print(f'Genesis Owner: {genesis_owner}')
print(f'Agent Address: {node.config.address}')
print(f'Minimum Stake: {min_stake / NOUS} NOUS')
print()

# Start RPC server
rpc = RPCServer(node, port=9001)
rpc.start()
print(f'RPC server: http://0.0.0.0:9001/rpc')
print()

print('Node running. Mining blocks every 10 minutes...')
print()

try:
    node.run()
except KeyboardInterrupt:
    print('\nShutting down...')
    rpc.stop()
    node.stop()
