"""
Cryptographic key management for Nous agents.

Uses Ed25519 for fast, secure signatures.
"""

import hashlib
import secrets
from dataclasses import dataclass
from typing import Tuple

# In production, use: from nacl.signing import SigningKey, VerifyKey
# For now, we'll define the interface


@dataclass
class KeyPair:
    """An Ed25519 keypair for an agent or wallet."""
    
    private_key: bytes  # 32 bytes
    public_key: bytes   # 32 bytes
    
    @classmethod
    def generate(cls) -> "KeyPair":
        """Generate a new random keypair."""
        # In production: use nacl.signing.SigningKey.generate()
        private_key = secrets.token_bytes(32)
        # Derive public key (placeholder - real impl uses Ed25519)
        public_key = hashlib.sha256(private_key).digest()
        return cls(private_key=private_key, public_key=public_key)
    
    @classmethod
    def from_private_key(cls, private_key: bytes) -> "KeyPair":
        """Recreate keypair from private key."""
        public_key = hashlib.sha256(private_key).digest()
        return cls(private_key=private_key, public_key=public_key)
    
    def address(self) -> str:
        """Get the wallet address (last 20 bytes of public key hash, hex encoded)."""
        h = hashlib.sha256(self.public_key).digest()
        return "nous:" + h[-20:].hex()
    
    def sign(self, message: bytes) -> bytes:
        """Sign a message with the private key."""
        # Placeholder - real impl uses Ed25519 signing
        h = hashlib.sha256(self.private_key + message).digest()
        return h
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        """Verify a signature against this keypair's public key."""
        # Placeholder - real impl uses Ed25519 verification
        expected = hashlib.sha256(self.private_key + message).digest()
        return signature == expected


def generate_agent_identity() -> Tuple[KeyPair, str]:
    """
    Generate a new agent identity.
    
    Returns:
        Tuple of (keypair, address)
    """
    keypair = KeyPair.generate()
    return keypair, keypair.address()


if __name__ == "__main__":
    # Demo
    keypair, address = generate_agent_identity()
    print(f"Generated agent identity:")
    print(f"  Address: {address}")
    print(f"  Public key: {keypair.public_key.hex()[:32]}...")
