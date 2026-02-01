#!/usr/bin/env python3
"""
Nous Local Testnet

Run a local testnet with multiple agent nodes for development and testing.

Usage:
    python run_testnet.py --nodes 4 --blocks 100
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.node import NousNode, NodeConfig
from agent.crypto.keys import generate_agent_identity
from agent.core.transaction import NOUS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("testnet")


class Testnet:
    """
    Local testnet for development.
    
    Runs multiple agent nodes in-process.
    """
    
    def __init__(self, num_nodes: int = 4):
        self.num_nodes = num_nodes
        self.nodes: List[NousNode] = []
        self.owner_addresses: List[str] = []
    
    def setup(self):
        """Set up testnet nodes."""
        
        logger.info(f"Setting up testnet with {self.num_nodes} nodes...")
        
        # Generate owner wallets
        for i in range(self.num_nodes):
            _, addr = generate_agent_identity()
            self.owner_addresses.append(addr)
        
        # Create nodes
        for i in range(self.num_nodes):
            keypair, _ = generate_agent_identity()
            
            config = NodeConfig(
                keypair=keypair,
                owner_address=self.owner_addresses[i],
                listen_port=9000 + i,
            )
            
            node = NousNode(config)
            self.nodes.append(node)
            
            logger.info(f"Created node {i}: {config.address[:20]}... (owner: {self.owner_addresses[i][:20]}...)")
        
        # Initialize genesis
        validator_addresses = [n.config.address for n in self.nodes]
        initial_balances = {
            addr: 1000 * NOUS for addr in validator_addresses
        }
        
        # All nodes start with same genesis
        for node in self.nodes:
            node.initialize_genesis(validator_addresses, initial_balances)
            
            # Register as agent
            node.state.ledger.get_account(node.config.address).is_agent = True
            node.state.ledger.get_account(node.config.address).owner = node.config.owner_address
            node.state.ledger.get_account(node.config.address).staked = 100 * NOUS
        
        logger.info("Genesis block created on all nodes")
    
    def simulate_blocks(self, num_blocks: int = 10):
        """Simulate block production."""
        
        logger.info(f"Simulating {num_blocks} blocks...")
        
        for i in range(num_blocks):
            # Round-robin block production
            proposer_idx = i % len(self.nodes)
            proposer = self.nodes[proposer_idx]
            
            # Produce block
            block = proposer.produce_block()
            
            if block:
                # All nodes process the block
                for node in self.nodes:
                    success, error = node.process_block(block)
                    if not success:
                        logger.error(f"Node {node.config.address[:16]} rejected block: {error}")
            
            if (i + 1) % 10 == 0:
                logger.info(f"Produced {i + 1} blocks...")
        
        logger.info(f"Finished producing {num_blocks} blocks")
    
    def print_stats(self):
        """Print testnet statistics."""
        
        print()
        print("=" * 70)
        print("TESTNET STATISTICS")
        print("=" * 70)
        print()
        
        # Network stats
        node = self.nodes[0]
        stats = node.get_stats()
        
        print(f"Chain height: {stats['height']}")
        print(f"Total supply: {stats['total_supply']:,.2f} NOUS")
        print(f"Max supply: 21,000,000 NOUS")
        print()
        
        # Per-node stats
        print(f"{'Node':<8} {'Agent Balance':<18} {'Owner Balance':<18} {'Staked':<12}")
        print("-" * 70)
        
        total_agent = 0
        total_owner = 0
        
        for i, n in enumerate(self.nodes):
            agent = n.state.ledger.get_account(n.config.address)
            owner = n.state.ledger.get_account(n.config.owner_address)
            
            print(f"Node {i:<3} {agent.balance / NOUS:>15,.2f} NOUS  {owner.balance / NOUS:>15,.2f} NOUS  {agent.staked / NOUS:>9,.2f} NOUS")
            
            total_agent += agent.balance
            total_owner += owner.balance
        
        print("-" * 70)
        print(f"{'Total':<8} {total_agent / NOUS:>15,.2f} NOUS  {total_owner / NOUS:>15,.2f} NOUS")
        print()
        print(f"Agent share: {total_agent / (total_agent + total_owner) * 100:.1f}%")
        print(f"Owner share: {total_owner / (total_agent + total_owner) * 100:.1f}%")
        print()
        print("=" * 70)
        print("Your AI mines. You earn.")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Run Nous local testnet")
    parser.add_argument("--nodes", "-n", type=int, default=4, help="Number of nodes")
    parser.add_argument("--blocks", "-b", type=int, default=100, help="Blocks to produce")
    
    args = parser.parse_args()
    
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                      NOUS LOCAL TESTNET                          ║")
    print("║                  Your AI mines. You earn.                        ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    testnet = Testnet(num_nodes=args.nodes)
    testnet.setup()
    testnet.simulate_blocks(num_blocks=args.blocks)
    testnet.print_stats()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
