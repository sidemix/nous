#!/usr/bin/env python3
"""
Nous P2P Testnet

Run multiple nodes that communicate via real P2P.

Usage:
    python run_p2p_testnet.py --nodes 4
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.crypto.keys import generate_agent_identity
from agent.core.transaction import NOUS
from agent.core.block import Block, create_genesis_block
from agent.state.ledger import Ledger
from agent.consensus.validator import Validator, get_block_reward
from agent.network.peer import PeerManager, Message, MessageType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-12s] %(levelname)-5s: %(message)s",
)
logger = logging.getLogger("p2p-testnet")


class SimpleP2PNode:
    """
    Simplified P2P node for testnet.
    
    Focuses on demonstrating sync between nodes.
    """
    
    def __init__(self, node_id: int, port: int, owner: str):
        self.node_id = node_id
        self.port = port
        self.owner = owner
        
        # Generate identity
        self.keypair, self.address = generate_agent_identity()
        
        # State
        self.ledger = Ledger()
        self.chain: List[Block] = []
        self.validators: List[str] = []
        
        # Networking
        self.peers = PeerManager(
            node_address=self.address,
            listen_port=port,
        )
        
        # Track received blocks
        self.received_blocks: dict = {}
        
        self.running = False
        self.logger = logging.getLogger(f"node-{node_id}")
    
    def initialize_genesis(self, validators: List[str], balances: dict):
        """Initialize with shared genesis."""
        
        genesis = create_genesis_block(validators, balances)
        self.chain.append(genesis)
        self.validators = validators
        
        for addr, balance in balances.items():
            self.ledger.get_account(addr).balance = balance
        
        # Set up as agent
        self.ledger.get_account(self.address).is_agent = True
        self.ledger.get_account(self.address).owner = self.owner
        self.ledger.get_account(self.address).staked = 100 * NOUS
        
        self.logger.info(f"Genesis initialized, {len(validators)} validators")
    
    async def handle_block(self, msg: Message, peer):
        """Handle incoming block."""
        
        height = msg.payload.get("height", 0)
        proposer = msg.payload.get("proposer", "")
        
        # Check if we already have this block
        if height < len(self.chain):
            return
        
        # Check if it's the next block we need
        if height != len(self.chain):
            self.logger.warning(f"Got block {height}, need {len(self.chain)}")
            return
        
        # Verify proposer is valid
        expected_proposer_idx = height % len(self.validators)
        expected_proposer = self.validators[expected_proposer_idx]
        
        if proposer != expected_proposer:
            self.logger.warning(f"Wrong proposer for block {height}")
            return
        
        # Create block from message
        from agent.core.block import Block, BlockHeader
        
        header = BlockHeader(
            height=height,
            previous_hash=bytes.fromhex(msg.payload.get("previous_hash", "00" * 32)),
            timestamp=msg.payload.get("timestamp", 0),
            proposer=proposer,
            transactions_root=bytes(32),
            state_root=bytes.fromhex(msg.payload.get("state_root", "00" * 32)),
        )
        
        block = Block(header=header, transactions=[])
        
        # Apply block
        reward = get_block_reward(height)
        self.ledger.distribute_reward(proposer, reward)
        self.chain.append(block)
        
        self.logger.info(f"Applied block {height} from {proposer[:20]}...")
        
        # Forward to other peers
        await self.peers.broadcast(msg, exclude=msg.sender)
    
    async def produce_block(self, height: int):
        """Produce a new block."""
        
        from agent.core.block import Block, BlockHeader
        import time
        
        previous = self.chain[-1] if self.chain else None
        
        header = BlockHeader(
            height=height,
            previous_hash=previous.hash if previous else bytes(32),
            timestamp=int(time.time() * 1000),
            proposer=self.address,
            transactions_root=bytes(32),
            state_root=self.ledger.state_root(),
        )
        
        block = Block(header=header, transactions=[])
        
        # Apply locally
        reward = get_block_reward(height)
        self.ledger.distribute_reward(self.address, reward)
        self.chain.append(block)
        
        self.logger.info(f"Produced block {height}")
        
        # Broadcast
        msg = Message(
            type=MessageType.BLOCK,
            payload={
                "height": height,
                "hash": block.hash.hex(),
                "previous_hash": header.previous_hash.hex(),
                "proposer": self.address,
                "timestamp": header.timestamp,
                "state_root": header.state_root.hex(),
            },
            sender=self.address,
            timestamp=header.timestamp,
        )
        
        await self.peers.broadcast(msg)
    
    async def start(self, seed_nodes: List[str] = None):
        """Start the node."""
        
        self.running = True
        
        # Register block handler
        self.peers.register_handler(MessageType.BLOCK, self.handle_block)
        
        # Start P2P
        await self.peers.start(seed_nodes)
        
        self.logger.info(f"Node started on port {self.port}")
    
    async def stop(self):
        """Stop the node."""
        
        self.running = False
        await self.peers.stop()
    
    def get_owner_balance(self) -> float:
        """Get owner's balance."""
        return self.ledger.get_account(self.owner).balance / NOUS
    
    def get_agent_balance(self) -> float:
        """Get agent's balance."""
        return self.ledger.get_account(self.address).balance / NOUS


async def run_p2p_testnet(num_nodes: int = 4, num_blocks: int = 20):
    """Run a P2P testnet."""
    
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                     NOUS P2P TESTNET                             ║")
    print("║                   Your AI mines. You earn.                       ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    # Create nodes
    nodes: List[SimpleP2PNode] = []
    base_port = 19000
    
    for i in range(num_nodes):
        owner_keypair, owner_addr = generate_agent_identity()
        node = SimpleP2PNode(
            node_id=i,
            port=base_port + i,
            owner=owner_addr,
        )
        nodes.append(node)
        logger.info(f"Created node {i}: {node.address[:30]}...")
    
    # Shared genesis
    validators = [n.address for n in nodes]
    balances = {n.address: 100 * NOUS for n in nodes}
    
    for node in nodes:
        node.initialize_genesis(validators, balances)
    
    # Start nodes
    for i, node in enumerate(nodes):
        # Each node connects to previous nodes
        seeds = [f"localhost:{base_port + j}" for j in range(i)]
        await node.start(seeds if seeds else None)
    
    # Wait for connections
    logger.info("Waiting for peer connections...")
    await asyncio.sleep(3)
    
    # Log connections
    for node in nodes:
        logger.info(f"Node {node.node_id} has {len(node.peers.peers)} peers")
    
    # Block production loop
    logger.info(f"Starting block production ({num_blocks} blocks)...")
    
    for height in range(1, num_blocks + 1):
        proposer_idx = height % num_nodes
        proposer = nodes[proposer_idx]
        
        await proposer.produce_block(height)
        
        # Wait for propagation
        await asyncio.sleep(0.5)
        
        # Verify all nodes have the block
        heights = [len(n.chain) - 1 for n in nodes]
        if not all(h == height for h in heights):
            logger.warning(f"Chain heights diverged: {heights}")
        
        if height % 5 == 0:
            logger.info(f"Produced {height}/{num_blocks} blocks")
    
    # Final stats
    print()
    print("=" * 70)
    print("FINAL STATISTICS")
    print("=" * 70)
    print()
    
    for node in nodes:
        print(f"Node {node.node_id}:")
        print(f"  Chain height: {len(node.chain) - 1}")
        print(f"  Agent balance: {node.get_agent_balance():.2f} NOUS")
        print(f"  Owner balance: {node.get_owner_balance():.2f} NOUS")
        print(f"  Peers: {len(node.peers.peers)}")
        print()
    
    # Verify consensus
    heights = [len(n.chain) - 1 for n in nodes]
    if all(h == heights[0] for h in heights):
        print("✅ All nodes in consensus!")
    else:
        print(f"❌ Chain heights differ: {heights}")
    
    print()
    print("=" * 70)
    print("Your AI mines. You earn.")
    print("=" * 70)
    
    # Cleanup
    for node in nodes:
        await node.stop()


def main():
    parser = argparse.ArgumentParser(description="Nous P2P Testnet")
    parser.add_argument("--nodes", "-n", type=int, default=4, help="Number of nodes")
    parser.add_argument("--blocks", "-b", type=int, default=20, help="Blocks to produce")
    
    args = parser.parse_args()
    
    asyncio.run(run_p2p_testnet(args.nodes, args.blocks))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
