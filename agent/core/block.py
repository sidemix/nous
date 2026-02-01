"""
Nous Block

Blocks contain transactions and form the chain.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import List, Optional

from .transaction import Transaction


@dataclass
class Attestation:
    """A validator's attestation (vote) for a block."""
    
    validator: str        # Validator's address
    block_hash: bytes     # Hash of block being attested
    signature: bytes      # Validator's signature
    timestamp: int        # When attestation was made


@dataclass
class BlockHeader:
    """Block header (gets hashed for block identity)."""
    
    height: int                    # Block number (0 = genesis)
    previous_hash: bytes           # Hash of previous block
    timestamp: int                 # Unix timestamp (milliseconds)
    proposer: str                  # Address of proposing agent
    transactions_root: bytes       # Merkle root of transactions
    state_root: bytes              # Merkle root of state after block
    
    def to_bytes(self) -> bytes:
        """Serialize header for hashing."""
        return json.dumps({
            "height": self.height,
            "previous_hash": self.previous_hash.hex(),
            "timestamp": self.timestamp,
            "proposer": self.proposer,
            "transactions_root": self.transactions_root.hex(),
            "state_root": self.state_root.hex(),
        }, sort_keys=True).encode()
    
    def hash(self) -> bytes:
        """Compute block hash."""
        return hashlib.sha256(self.to_bytes()).digest()


@dataclass
class Block:
    """A complete block with header, transactions, and attestations."""
    
    header: BlockHeader
    transactions: List[Transaction] = field(default_factory=list)
    attestations: List[Attestation] = field(default_factory=list)
    proposer_signature: Optional[bytes] = None
    
    @property
    def height(self) -> int:
        return self.header.height
    
    @property
    def hash(self) -> bytes:
        return self.header.hash()
    
    @property
    def block_id(self) -> str:
        """Human-readable block ID."""
        return self.hash.hex()[:16]
    
    def compute_transactions_root(self) -> bytes:
        """Compute Merkle root of transactions."""
        if not self.transactions:
            return bytes(32)  # Empty root
        
        # Simple hash of all tx hashes (real impl would be Merkle tree)
        tx_hashes = b"".join(tx.hash() for tx in self.transactions)
        return hashlib.sha256(tx_hashes).digest()
    
    def total_fees(self) -> int:
        """Sum of all transaction fees in block."""
        return sum(tx.fee for tx in self.transactions)
    
    def attestation_ratio(self, total_validators: int) -> float:
        """Ratio of attestations to total validators."""
        if total_validators == 0:
            return 0.0
        return len(self.attestations) / total_validators
    
    def is_finalized(self, total_validators: int, threshold: float = 0.67) -> bool:
        """Check if block has reached finality (2/3+ attestations)."""
        return self.attestation_ratio(total_validators) >= threshold


def create_genesis_block(
    initial_validators: List[str],
    initial_balances: dict[str, int],
) -> Block:
    """
    Create the genesis block.
    
    Args:
        initial_validators: Addresses of genesis validators
        initial_balances: Initial account balances
        
    Returns:
        The genesis block
    """
    # Genesis has no previous block
    header = BlockHeader(
        height=0,
        previous_hash=bytes(32),  # 32 zero bytes
        timestamp=int(time.time() * 1000),
        proposer="nous:genesis",
        transactions_root=bytes(32),
        state_root=hashlib.sha256(
            json.dumps(initial_balances, sort_keys=True).encode()
        ).digest(),
    )
    
    return Block(header=header, transactions=[], attestations=[])


def create_block(
    height: int,
    previous_hash: bytes,
    proposer: str,
    transactions: List[Transaction],
    state_root: bytes,
) -> Block:
    """Create a new block."""
    header = BlockHeader(
        height=height,
        previous_hash=previous_hash,
        timestamp=int(time.time() * 1000),
        proposer=proposer,
        transactions_root=bytes(32),  # Will be computed
        state_root=state_root,
    )
    
    block = Block(header=header, transactions=transactions)
    header.transactions_root = block.compute_transactions_root()
    
    return block


if __name__ == "__main__":
    # Demo: Create genesis block
    genesis = create_genesis_block(
        initial_validators=["nous:validator1", "nous:validator2"],
        initial_balances={"nous:founder": 1000 * 10**18},
    )
    
    print(f"Genesis block created:")
    print(f"  Height: {genesis.height}")
    print(f"  Hash: {genesis.block_id}...")
    print(f"  Transactions: {len(genesis.transactions)}")
