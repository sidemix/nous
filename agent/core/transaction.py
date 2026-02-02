"""
Nous Transaction

The atomic unit of value transfer in the Nous network.
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import Optional

from ..crypto.keys import KeyPair


# 1 NOUS = 100,000,000 nouslings (same as Bitcoin: 1 BTC = 100M satoshis)
NOUSLING = 1
NOUS = 10**8


@dataclass
class Transaction:
    """A Nous transaction."""
    
    sender: str           # Sender's address
    recipient: str        # Recipient's address
    amount: int           # Amount in nouslings
    nonce: int            # Sender's transaction count
    fee: int              # Transaction fee in nouslings
    timestamp: int        # Unix timestamp (milliseconds)
    signature: Optional[bytes] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary (for hashing/serialization)."""
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "nonce": self.nonce,
            "fee": self.fee,
            "timestamp": self.timestamp,
        }
    
    def hash(self) -> bytes:
        """Compute SHA-256 hash of transaction data (excluding signature)."""
        data = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(data).digest()
    
    def tx_id(self) -> str:
        """Get transaction ID (hex-encoded hash)."""
        return self.hash().hex()
    
    def sign(self, keypair: KeyPair) -> "Transaction":
        """Sign the transaction with a keypair."""
        self.signature = keypair.sign(self.hash())
        return self
    
    def verify_signature(self, public_key: bytes) -> bool:
        """Verify the transaction signature."""
        if self.signature is None:
            return False
        # In production, use proper Ed25519 verification
        # For now, this is a placeholder
        return len(self.signature) == 32
    
    def is_valid(self) -> tuple[bool, str]:
        """
        Validate transaction structure.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.amount <= 0:
            return False, "Amount must be positive"
        
        if self.fee < 0:
            return False, "Fee cannot be negative"
        
        if not self.sender.startswith("nous:"):
            return False, "Invalid sender address format"
        
        if not self.recipient.startswith("nous:"):
            return False, "Invalid recipient address format"
        
        if self.sender == self.recipient:
            return False, "Cannot send to self"
        
        if self.signature is None:
            return False, "Transaction not signed"
        
        return True, ""


def create_transaction(
    sender_keypair: KeyPair,
    recipient: str,
    amount: int,
    nonce: int,
    fee: int = 1000,  # Default fee: 0.000001 NOUS
) -> Transaction:
    """
    Create and sign a new transaction.
    
    Args:
        sender_keypair: Sender's keypair for signing
        recipient: Recipient's address
        amount: Amount to send in nouslings
        nonce: Sender's current transaction count
        fee: Transaction fee in nouslings
        
    Returns:
        Signed transaction
    """
    tx = Transaction(
        sender=sender_keypair.address(),
        recipient=recipient,
        amount=amount,
        nonce=nonce,
        fee=fee,
        timestamp=int(time.time() * 1000),
    )
    return tx.sign(sender_keypair)


if __name__ == "__main__":
    from ..crypto.keys import generate_agent_identity
    
    # Demo: Create a transaction
    sender_kp, sender_addr = generate_agent_identity()
    _, recipient_addr = generate_agent_identity()
    
    tx = create_transaction(
        sender_keypair=sender_kp,
        recipient=recipient_addr,
        amount=10 * NOUS,  # 10 NOUS
        nonce=0,
    )
    
    print(f"Transaction created:")
    print(f"  ID: {tx.tx_id()[:16]}...")
    print(f"  From: {tx.sender}")
    print(f"  To: {tx.recipient}")
    print(f"  Amount: {tx.amount / NOUS} NOUS")
    print(f"  Valid: {tx.is_valid()}")
