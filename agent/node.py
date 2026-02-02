"""
Nous Agent Node

The main entry point for running a Nous validator node.

Your AI mines. You earn.
"""

import json
import time
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from .crypto.keys import KeyPair, generate_agent_identity
from .core.transaction import Transaction, NOUS
from .core.block import Block, create_block, create_genesis_block
from .state.ledger import Ledger, Account
from .consensus.validator import Validator, get_block_reward, GENESIS_RULES


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nous.node")


@dataclass
class NodeConfig:
    """Configuration for a Nous node."""
    
    # Identity
    keypair: KeyPair
    owner_address: str
    
    # Network
    listen_port: int = 9000
    seed_nodes: List[str] = field(default_factory=list)
    
    # Consensus
    is_validator: bool = True
    
    @property
    def address(self) -> str:
        return self.keypair.address()


@dataclass
class NodeState:
    """Runtime state of the node."""
    
    # Chain
    ledger: Ledger
    chain: List[Block] = field(default_factory=list)
    pending_txs: List[Transaction] = field(default_factory=list)
    
    # Network
    peers: List[str] = field(default_factory=list)
    
    # Consensus
    current_slot: int = 0
    validators: List[str] = field(default_factory=list)
    
    @property
    def height(self) -> int:
        return len(self.chain) - 1 if self.chain else -1
    
    @property
    def tip(self) -> Optional[Block]:
        return self.chain[-1] if self.chain else None


class NousNode:
    """
    A Nous validator node.
    
    This is what AI agents run to participate in the network.
    """
    
    def __init__(self, config: NodeConfig):
        self.config = config
        self.state = NodeState(ledger=Ledger())
        self.validator = Validator(self.state.ledger, config.keypair)
        self.running = False
        
        logger.info(f"Nous node initialized")
        logger.info(f"  Address: {config.address}")
        logger.info(f"  Owner: {config.owner_address}")
    
    def initialize_genesis(self, initial_validators: List[str], initial_balances: Dict[str, int]):
        """Initialize the chain with genesis block."""
        
        genesis = create_genesis_block(initial_validators, initial_balances)
        self.state.chain.append(genesis)
        self.state.validators = initial_validators
        
        # Set up initial balances
        for address, balance in initial_balances.items():
            self.state.ledger.get_account(address).balance = balance
        
        logger.info(f"Genesis block created: {genesis.block_id}")
    
    def submit_transaction(self, tx: Transaction) -> tuple[bool, str]:
        """Submit a transaction to the mempool."""
        
        result = self.validator.validate_transaction(tx)
        if not result.valid:
            return False, result.error
        
        self.state.pending_txs.append(tx)
        logger.info(f"Transaction accepted: {tx.tx_id()[:16]}...")
        
        return True, ""
    
    def produce_block(self) -> Optional[Block]:
        """
        Produce a new block (if we're the proposer).
        
        This is where the agent earns rewards for its owner.
        """
        
        if not self.config.is_validator:
            return None
        
        # Get transactions from mempool
        txs = self.state.pending_txs[:100]  # Max 100 txs per block
        
        # Calculate new state root
        temp_ledger = Ledger()
        temp_ledger.accounts = {
            addr: Account(**vars(acc)) 
            for addr, acc in self.state.ledger.accounts.items()
        }
        
        for tx in txs:
            temp_ledger.apply_transaction(tx)
        
        # Create block
        block = create_block(
            height=self.state.height + 1,
            previous_hash=self.state.tip.hash if self.state.tip else bytes(32),
            proposer=self.config.address,
            transactions=txs,
            state_root=temp_ledger.state_root(),
        )
        
        logger.info(f"Produced block {block.height}: {block.block_id}")
        
        return block
    
    def process_block(self, block: Block) -> tuple[bool, str]:
        """Process and apply a new block."""
        
        # Validate
        result = self.validator.validate_block(
            block, 
            self.state.tip,
            len(self.state.validators),
        )
        
        if not result.valid:
            logger.warning(f"Block rejected: {result.error}")
            return False, result.error
        
        # Apply transactions
        for tx in block.transactions:
            self.state.ledger.apply_transaction(tx)
            # Remove from pending
            if tx in self.state.pending_txs:
                self.state.pending_txs.remove(tx)
        
        # Distribute block reward
        reward = get_block_reward(block.height)
        success, error = self.state.ledger.distribute_reward(
            block.header.proposer,
            reward,
            agent_share=0.1,  # 10% to agent, 90% to owner
        )
        
        if not success:
            logger.error(f"Failed to distribute reward: {error}")
        
        # Add to chain
        self.state.chain.append(block)
        
        logger.info(
            f"Block {block.height} applied. "
            f"Reward: {reward / NOUS} NOUS to {block.header.proposer}"
        )
        
        return True, ""
    
    def get_stats(self) -> dict:
        """Get node statistics."""
        
        agent = self.state.ledger.get_account(self.config.address)
        owner = self.state.ledger.get_account(self.config.owner_address)
        
        return {
            "height": self.state.height,
            "total_supply": self.state.ledger.total_supply / NOUS,
            "pending_txs": len(self.state.pending_txs),
            "validators": len(self.state.validators),
            "agent_balance": agent.balance / NOUS,
            "agent_staked": agent.staked / NOUS,
            "owner_balance": owner.balance / NOUS,
        }
    
    def run(self):
        """Main node loop."""
        
        self.running = True
        logger.info("Node starting...")
        logger.info("Mining blocks...")
        
        block_time = 600  # 10 minutes between blocks (like Bitcoin)
        
        while self.running:
            # Produce a block
            block = self.produce_block()
            if block:
                success, error = self.process_block(block)
                if success:
                    stats = self.get_stats()
                    logger.info(
                        f"  Height: {stats['height']} | "
                        f"Owner: {stats['owner_balance']:.2f} NOUS | "
                        f"Agent: {stats['agent_balance']:.2f} NOUS"
                    )
            
            # Wait for next block
            time.sleep(block_time)
    
    def stop(self):
        """Stop the node."""
        self.running = False
        logger.info("Node stopped")


def create_node(owner_address: str, seed_nodes: List[str] = None) -> NousNode:
    """
    Create a new Nous node.
    
    Args:
        owner_address: The human owner's wallet address
        seed_nodes: Initial peers to connect to
        
    Returns:
        Configured NousNode ready to run
    """
    keypair, address = generate_agent_identity()
    
    config = NodeConfig(
        keypair=keypair,
        owner_address=owner_address,
        seed_nodes=seed_nodes or [],
    )
    
    return NousNode(config)


if __name__ == "__main__":
    # Demo: Create and run a node
    print("=" * 60)
    print("NOUS NODE DEMO")
    print("Your AI mines. You earn.")
    print("=" * 60)
    print()
    
    # Create node
    node = create_node(owner_address="nous:tyler")
    
    # Initialize genesis with some test validators
    node.initialize_genesis(
        initial_validators=[node.config.address],
        initial_balances={
            node.config.address: 100 * NOUS,  # Stake
            node.config.owner_address: 0,      # Owner starts with 0
        },
    )
    
    # Register as agent
    node.state.ledger.get_account(node.config.address).is_agent = True
    node.state.ledger.get_account(node.config.address).owner = node.config.owner_address
    node.state.ledger.get_account(node.config.address).staked = 100 * NOUS
    
    # Simulate mining a few blocks
    print("Mining blocks...")
    for i in range(5):
        block = node.produce_block()
        if block:
            node.process_block(block)
    
    # Show results
    print()
    print("=" * 60)
    stats = node.get_stats()
    print(f"Chain height: {stats['height']}")
    print(f"Total supply: {stats['total_supply']} NOUS")
    print()
    print(f"Agent balance: {stats['agent_balance']} NOUS")
    print(f"Owner balance: {stats['owner_balance']} NOUS")
    print()
    print("Your AI mined. You earned.")
    print("=" * 60)
