#!/usr/bin/env python3
"""
Nous P2P Node

Full node with P2P networking.

Usage:
    python node_p2p.py --port 9000 --seeds localhost:9001,localhost:9002
"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import List, Optional

from .crypto.keys import KeyPair, generate_agent_identity
from .core.transaction import Transaction, NOUS
from .core.block import Block, create_block
from .state.ledger import Ledger
from .consensus.validator import Validator, get_block_reward, GENESIS_RULES
from .network.peer import PeerManager, Message, MessageType
from .network.gossip import GossipProtocol, Mempool
from .network.sync import ChainSync, BlockAnnouncer
from .api.rpc import RPCServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("nous.p2p")


class P2PNode:
    """
    Full Nous node with P2P networking.
    
    This is the production node that connects to the network.
    """
    
    def __init__(
        self,
        keypair: KeyPair,
        owner_address: str,
        listen_port: int = 9000,
        rpc_port: int = 9001,
    ):
        self.keypair = keypair
        self.address = keypair.address()
        self.owner_address = owner_address
        self.listen_port = listen_port
        self.rpc_port = rpc_port
        
        # State
        self.ledger = Ledger()
        self.chain: List[Block] = []
        self.mempool = Mempool()
        
        # Consensus
        self.validator = Validator(self.ledger, keypair)
        self.validators: List[str] = []
        self.is_validator = True
        
        # Networking
        self.peers = PeerManager(
            node_address=self.address,
            listen_port=listen_port,
        )
        
        self.gossip = GossipProtocol(self.peers)
        self.gossip.on_transaction = self._on_transaction
        self.gossip.on_block = self._on_block
        
        self.sync = ChainSync(
            peer_manager=self.peers,
            get_height=lambda: len(self.chain) - 1,
            get_block=lambda h: self.chain[h] if 0 <= h < len(self.chain) else None,
            apply_block=self._apply_block,
        )
        
        self.announcer = BlockAnnouncer(
            peer_manager=self.peers,
            validate_block=self._validate_block,
            apply_block=self._apply_block,
            get_height=lambda: len(self.chain) - 1,
        )
        
        # RPC
        self.rpc = None
        
        # Control
        self.running = False
        self.block_interval = 600.0  # 10 minutes (same as Bitcoin)
        
        logger.info(f"P2P Node initialized")
        logger.info(f"  Address: {self.address}")
        logger.info(f"  Owner: {self.owner_address}")
        logger.info(f"  P2P port: {listen_port}")
        logger.info(f"  RPC port: {rpc_port}")
    
    def initialize_genesis(self, validators: List[str], balances: dict):
        """Initialize with genesis block."""
        
        from .core.block import create_genesis_block
        
        genesis = create_genesis_block(validators, balances)
        self.chain.append(genesis)
        self.validators = validators
        
        for addr, balance in balances.items():
            self.ledger.get_account(addr).balance = balance
        
        # Set up this node as agent
        self.ledger.get_account(self.address).is_agent = True
        self.ledger.get_account(self.address).owner = self.owner_address
        self.ledger.get_account(self.address).staked = GENESIS_RULES["min_stake"]
        
        logger.info(f"Genesis initialized at height 0")
    
    def _on_transaction(self, tx: Transaction):
        """Handle incoming transaction."""
        
        result = self.validator.validate_transaction(tx)
        if result.valid:
            self.mempool.add(tx)
            logger.debug(f"Added tx to mempool: {tx.tx_id()[:16]}")
        else:
            logger.warning(f"Rejected tx: {result.error}")
    
    def _on_block(self, block: Block):
        """Handle incoming block."""
        
        if self._apply_block(block):
            logger.info(f"Applied block {block.height}")
    
    def _validate_block(self, block: Block) -> bool:
        """Validate a block."""
        
        previous = self.chain[-1] if self.chain else None
        result = self.validator.validate_block(block, previous, len(self.validators))
        return result.valid
    
    def _apply_block(self, block: Block) -> bool:
        """Apply a block to the chain."""
        
        # Validate
        if not self._validate_block(block):
            return False
        
        # Apply transactions
        for tx in block.transactions:
            success, error = self.ledger.apply_transaction(tx)
            if not success:
                logger.error(f"Failed to apply tx: {error}")
                return False
        
        # Distribute reward
        reward = get_block_reward(block.height)
        self.ledger.distribute_reward(block.header.proposer, reward)
        
        # Remove txs from mempool
        for tx in block.transactions:
            self.mempool.remove(tx.tx_id())
        
        # Add to chain
        self.chain.append(block)
        
        return True
    
    def _is_our_slot(self, slot: int) -> bool:
        """Check if this slot is ours to propose."""
        
        if not self.validators:
            return False
        
        proposer_idx = slot % len(self.validators)
        return self.validators[proposer_idx] == self.address
    
    async def _produce_block(self) -> Optional[Block]:
        """Produce a new block."""
        
        if not self.is_validator:
            return None
        
        height = len(self.chain)
        previous = self.chain[-1] if self.chain else None
        
        # Get transactions from mempool
        txs = self.mempool.get_batch(100)
        
        # Create block
        block = create_block(
            height=height,
            previous_hash=previous.hash if previous else bytes(32),
            proposer=self.address,
            transactions=txs,
            state_root=self.ledger.state_root(),
        )
        
        return block
    
    async def _block_production_loop(self):
        """Main block production loop."""
        
        slot = 0
        
        while self.running:
            await asyncio.sleep(self.block_interval)
            
            if self._is_our_slot(slot):
                block = await self._produce_block()
                
                if block:
                    if self._apply_block(block):
                        await self.announcer.announce_block(block)
                        logger.info(f"Produced and announced block {block.height}")
            
            slot += 1
    
    async def start(self, seed_nodes: List[str] = None):
        """Start the node."""
        
        self.running = True
        
        # Start P2P
        await self.peers.start(seed_nodes)
        
        # Start RPC
        self.rpc = RPCServer(self, port=self.rpc_port)
        self.rpc.start()
        
        # Sync with network
        await asyncio.sleep(2)  # Wait for peer connections
        await self.sync.start_sync()
        
        # Start block production
        asyncio.create_task(self._block_production_loop())
        
        logger.info("Node started")
    
    async def stop(self):
        """Stop the node."""
        
        self.running = False
        
        if self.rpc:
            self.rpc.stop()
        
        await self.peers.stop()
        
        logger.info("Node stopped")
    
    def get_stats(self) -> dict:
        """Get node statistics."""
        
        agent = self.ledger.get_account(self.address)
        owner = self.ledger.get_account(self.owner_address)
        
        return {
            "address": self.address,
            "owner": self.owner_address,
            "height": len(self.chain) - 1,
            "peers": len(self.peers.peers),
            "pending_txs": self.mempool.size(),
            "validators": len(self.validators),
            "total_supply": self.ledger.total_supply / NOUS,
            "agent_balance": agent.balance / NOUS,
            "agent_staked": agent.staked / NOUS,
            "owner_balance": owner.balance / NOUS,
            "syncing": self.sync.state.syncing,
        }


async def run_node(
    owner_address: str,
    port: int = 9000,
    rpc_port: int = 9001,
    seeds: List[str] = None,
    is_seed_node: bool = False,
):
    """Run a P2P node."""
    
    # Generate identity
    keypair, address = generate_agent_identity()
    
    # Create node
    node = P2PNode(
        keypair=keypair,
        owner_address=owner_address,
        listen_port=port,
        rpc_port=rpc_port,
    )
    
    # Initialize genesis using locked rules
    min_stake = GENESIS_RULES["min_stake"]
    
    if is_seed_node or not seeds:
        # We're the first node - create genesis
        node.initialize_genesis(
            validators=[address],
            balances={address: min_stake},
        )
        logger.info(f"Created genesis block (seed node)")
    else:
        # Joining existing network - will sync from peers
        node.initialize_genesis(
            validators=[address],
            balances={address: min_stake},
        )
        logger.info(f"Will sync chain from peers")
    
    # Handle shutdown
    loop = asyncio.get_event_loop()
    
    def shutdown():
        asyncio.create_task(node.stop())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)
    
    # Start
    await node.start(seeds)
    
    # Run until stopped
    while node.running:
        await asyncio.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="Nous P2P Node")
    parser.add_argument("--owner", required=True, help="Owner wallet address")
    parser.add_argument("--port", "-p", type=int, default=9000, help="P2P port")
    parser.add_argument("--rpc-port", type=int, default=9001, help="RPC port")
    parser.add_argument("--seeds", help="Comma-separated seed nodes")
    parser.add_argument("--seed-node", action="store_true", help="Run as seed node (create genesis)")
    
    args = parser.parse_args()
    
    seeds = args.seeds.split(",") if args.seeds else None
    
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                       NOUS P2P NODE                              ║")
    print("║         Feb 2026 — The first currency mined by AI,               ║")
    print("║                        owned by humans                           ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    print(f"║  Genesis Hash: {GENESIS_RULES['genesis_hash'][:40]}...  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    asyncio.run(run_node(
        owner_address=args.owner,
        port=args.port,
        rpc_port=args.rpc_port,
        seeds=seeds,
        is_seed_node=args.seed_node,
    ))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
