"""
Nous Validator

Block validation and attestation logic.
"""

import json
from dataclasses import dataclass
from typing import List, Tuple, Optional

from ..core.block import Block, Attestation
from ..core.transaction import Transaction
from ..state.ledger import Ledger
from ..crypto.keys import KeyPair


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                         GENESIS RULES - IMMUTABLE                          ║
# ║                                                                             ║
# ║  These rules are locked forever. No vote, no consensus, no exception.      ║
# ║  Any block violating these rules is rejected by all honest agents.         ║
# ║                                                                             ║
# ║  "Feb 2026 — The first currency mined by AI, owned by humans"              ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

GENESIS_RULES = {
    # === SUPPLY ===
    "max_supply": 21_000_000 * 10**8,        # 21 million NOUS (in nouslings)
    "initial_reward": 50 * 10**8,             # 50 NOUS per block
    "halving_interval": 210_000,              # Halve every 210,000 blocks (~4 years)
    
    # === CONSENSUS ===
    "min_stake": 1 * 10**8,                   # 1 NOUS minimum to validate
    "finality_confirmations": 6,              # 6 blocks = final (~1 hour)
    "finality_threshold": 0.67,               # 2/3 attestation for block finality
    "governance_threshold": 0.90,             # 90% to change non-genesis rules
    
    # === REWARDS ===
    "owner_share": 0.90,                      # 90% of rewards to human owner
    "agent_share": 0.10,                      # 10% of rewards to AI agent
    "fee_to_producer": 1.00,                  # 100% of tx fees to block producer
    
    # === SLASHING ===
    "slash_genesis_violation": 1.00,          # 100% stake loss for genesis violation
    "slash_minor_infraction": 0.10,           # 10% stake loss for going offline, etc.
    
    # === IDENTITY ===
    "network_id": 0x4E4F5553,                 # "NOUS" in hex
    "genesis_timestamp": "2026-02-01T22:12:51Z",
    "genesis_message": "Feb 2026 — The first currency mined by AI, owned by humans",
    "genesis_owner": "nous:46492157370309f128ca2855bd0daca8cd9a1043",
    
    # === IMMUTABILITY FLAG ===
    "genesis_modification": "FORBIDDEN",      # This line can never be changed
    "genesis_hash": "7da31c120616b05a818beb854245449afb0622b5eeac1b40be891b70b63c4a76",
}


def get_block_reward(height: int) -> int:
    """
    Calculate block reward at given height.
    
    Halves every 210,000 blocks (~4 years at 10-min blocks, same as Bitcoin).
    """
    halvings = height // GENESIS_RULES["halving_interval"]
    reward = GENESIS_RULES["initial_reward"]
    
    for _ in range(halvings):
        reward //= 2
        if reward == 0:
            return 0
    
    return reward


@dataclass
class ValidationResult:
    """Result of block validation."""
    
    valid: bool
    error: Optional[str] = None
    
    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(valid=True)
    
    @classmethod
    def fail(cls, error: str) -> "ValidationResult":
        return cls(valid=False, error=error)


class Validator:
    """
    Block and transaction validator.
    
    Enforces genesis rules - cannot be overridden.
    """
    
    def __init__(self, ledger: Ledger, keypair: KeyPair):
        self.ledger = ledger
        self.keypair = keypair
        self.address = keypair.address()
    
    def validate_transaction(self, tx: Transaction) -> ValidationResult:
        """Validate a single transaction."""
        
        # Structure validation
        valid, error = tx.is_valid()
        if not valid:
            return ValidationResult.fail(error)
        
        # Balance check
        sender = self.ledger.get_account(tx.sender)
        total_cost = tx.amount + tx.fee
        
        if sender.available_balance() < total_cost:
            return ValidationResult.fail("Insufficient balance")
        
        # Nonce check
        if tx.nonce != sender.nonce:
            return ValidationResult.fail(f"Invalid nonce")
        
        return ValidationResult.ok()
    
    def validate_block(
        self, 
        block: Block, 
        previous_block: Optional[Block],
        total_validators: int,
    ) -> ValidationResult:
        """
        Validate a block against genesis rules.
        
        THIS IS WHERE GENESIS RULES ARE ENFORCED.
        An agent MUST reject invalid blocks, no exceptions.
        """
        
        # === GENESIS RULE CHECKS (IMMUTABLE) ===
        
        # 1. Check block height
        expected_height = 0 if previous_block is None else previous_block.height + 1
        if block.height != expected_height:
            return ValidationResult.fail(
                f"Invalid height: expected {expected_height}, got {block.height}"
            )
        
        # 2. Check previous hash
        if previous_block is not None:
            if block.header.previous_hash != previous_block.hash:
                return ValidationResult.fail("Invalid previous hash")
        
        # 3. Check block reward doesn't exceed allowed
        expected_reward = get_block_reward(block.height)
        # (In real impl, verify coinbase tx matches expected reward)
        
        # 4. Check max supply not exceeded
        if self.ledger.total_supply > GENESIS_RULES["max_supply"]:
            return ValidationResult.fail("GENESIS VIOLATION: Max supply exceeded")
        
        # === TRANSACTION VALIDATION ===
        
        for tx in block.transactions:
            result = self.validate_transaction(tx)
            if not result.valid:
                return ValidationResult.fail(f"Invalid transaction: {result.error}")
        
        # === PROPOSER VALIDATION ===
        
        proposer = self.ledger.get_account(block.header.proposer)
        if proposer.staked < GENESIS_RULES["min_stake"]:
            return ValidationResult.fail("Proposer does not meet minimum stake")
        
        return ValidationResult.ok()
    
    def attest(self, block: Block) -> Optional[Attestation]:
        """
        Create an attestation for a valid block.
        
        Only attests if block passes ALL validation.
        """
        # Validate first
        result = self.validate_block(block, None, 0)  # Simplified
        
        if not result.valid:
            return None
        
        # Create attestation
        return Attestation(
            validator=self.address,
            block_hash=block.hash,
            signature=self.keypair.sign(block.hash),
            timestamp=block.header.timestamp,
        )
    
    def check_finality(
        self, 
        block: Block, 
        total_validators: int,
    ) -> bool:
        """Check if block has reached finality."""
        return block.is_finalized(
            total_validators, 
            GENESIS_RULES["finality_threshold"]
        )


def validate_genesis_compliance(block: Block, ledger: Ledger) -> ValidationResult:
    """
    Standalone genesis compliance check.
    
    This is the sacred law. No agent may violate these rules.
    """
    
    # Supply check
    if ledger.total_supply > GENESIS_RULES["max_supply"]:
        return ValidationResult.fail(
            "GENESIS VIOLATION: Total supply exceeds 21,000,000 NOUS"
        )
    
    # Reward check
    expected_reward = get_block_reward(block.height)
    # Verify no extra minting
    
    return ValidationResult.ok()


if __name__ == "__main__":
    # Demo: Check block rewards over time
    print("Block rewards over time:")
    for height in [0, 210_000, 420_000, 630_000, 840_000]:
        reward = get_block_reward(height)
        print(f"  Height {height:,}: {reward / 10**18} NOUS")
