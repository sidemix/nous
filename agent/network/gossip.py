"""
Nous Gossip Protocol

Efficient propagation of transactions and blocks.
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Set, Dict, Optional, Callable
from collections import deque

from .peer import PeerManager, Message, MessageType, PeerInfo
from ..core.transaction import Transaction
from ..core.block import Block

logger = logging.getLogger("nous.gossip")


@dataclass
class GossipConfig:
    """Gossip protocol configuration."""
    
    # Deduplication
    seen_cache_size: int = 10000
    seen_ttl_seconds: int = 300
    
    # Propagation
    fanout: int = 8           # Number of peers to forward to
    max_hops: int = 10        # Maximum message hops
    
    # Rate limiting
    max_tx_per_second: int = 100
    max_blocks_per_second: int = 10


class GossipProtocol:
    """
    Gossip protocol for transaction and block propagation.
    
    Uses epidemic-style gossip with deduplication.
    """
    
    def __init__(
        self, 
        peer_manager: PeerManager,
        config: GossipConfig = None,
    ):
        self.peers = peer_manager
        self.config = config or GossipConfig()
        
        # Seen message cache (for deduplication)
        self.seen_txs: Set[str] = set()
        self.seen_blocks: Set[str] = set()
        self.seen_timestamps: Dict[str, float] = {}
        
        # Callbacks
        self.on_transaction: Optional[Callable[[Transaction], None]] = None
        self.on_block: Optional[Callable[[Block], None]] = None
        
        # Register handlers
        self.peers.register_handler(MessageType.TX, self._handle_tx)
        self.peers.register_handler(MessageType.BLOCK, self._handle_block)
    
    def _is_seen(self, msg_id: str) -> bool:
        """Check if we've seen this message recently."""
        
        if msg_id in self.seen_timestamps:
            age = time.time() - self.seen_timestamps[msg_id]
            if age < self.config.seen_ttl_seconds:
                return True
            else:
                # Expired, remove
                del self.seen_timestamps[msg_id]
                self.seen_txs.discard(msg_id)
                self.seen_blocks.discard(msg_id)
        
        return False
    
    def _mark_seen(self, msg_id: str):
        """Mark a message as seen."""
        
        self.seen_timestamps[msg_id] = time.time()
        
        # Prune if too large
        if len(self.seen_timestamps) > self.config.seen_cache_size:
            # Remove oldest entries
            oldest = sorted(self.seen_timestamps.items(), key=lambda x: x[1])
            for msg_id, _ in oldest[:1000]:
                del self.seen_timestamps[msg_id]
                self.seen_txs.discard(msg_id)
                self.seen_blocks.discard(msg_id)
    
    async def broadcast_transaction(self, tx: Transaction):
        """Broadcast a transaction to the network."""
        
        tx_id = tx.tx_id()
        
        if self._is_seen(tx_id):
            return
        
        self._mark_seen(tx_id)
        self.seen_txs.add(tx_id)
        
        msg = Message(
            type=MessageType.TX,
            payload={
                "sender": tx.sender,
                "recipient": tx.recipient,
                "amount": tx.amount,
                "nonce": tx.nonce,
                "fee": tx.fee,
                "timestamp": tx.timestamp,
                "signature": tx.signature.hex() if tx.signature else None,
            },
            sender=self.peers.node_address,
            timestamp=int(time.time() * 1000),
        )
        
        await self.peers.broadcast(msg)
        logger.debug(f"Broadcast tx: {tx_id[:16]}...")
    
    async def broadcast_block(self, block: Block):
        """Broadcast a block to the network."""
        
        block_id = block.block_id
        
        if self._is_seen(block_id):
            return
        
        self._mark_seen(block_id)
        self.seen_blocks.add(block_id)
        
        # Serialize block (simplified)
        msg = Message(
            type=MessageType.BLOCK,
            payload={
                "height": block.height,
                "hash": block.hash.hex(),
                "proposer": block.header.proposer,
                "tx_count": len(block.transactions),
                # Full block data would go here
            },
            sender=self.peers.node_address,
            timestamp=int(time.time() * 1000),
        )
        
        await self.peers.broadcast(msg)
        logger.info(f"Broadcast block: {block.height} ({block_id[:16]}...)")
    
    async def _handle_tx(self, msg: Message, peer: PeerInfo):
        """Handle incoming transaction."""
        
        try:
            tx = Transaction(
                sender=msg.payload["sender"],
                recipient=msg.payload["recipient"],
                amount=msg.payload["amount"],
                nonce=msg.payload["nonce"],
                fee=msg.payload["fee"],
                timestamp=msg.payload["timestamp"],
                signature=bytes.fromhex(msg.payload["signature"]) if msg.payload.get("signature") else None,
            )
            
            tx_id = tx.tx_id()
            
            if self._is_seen(tx_id):
                return
            
            self._mark_seen(tx_id)
            self.seen_txs.add(tx_id)
            
            # Notify listener
            if self.on_transaction:
                self.on_transaction(tx)
            
            # Forward to other peers
            await self.peers.broadcast(msg, exclude=msg.sender)
            
        except Exception as e:
            logger.warning(f"Error handling tx from {peer.address}: {e}")
    
    async def _handle_block(self, msg: Message, peer: PeerInfo):
        """Handle incoming block."""
        
        try:
            block_id = msg.payload.get("hash", "")[:16]
            
            if self._is_seen(block_id):
                return
            
            self._mark_seen(block_id)
            self.seen_blocks.add(block_id)
            
            logger.info(f"Received block {msg.payload['height']} from {peer.address}")
            
            # In real impl: deserialize full block, validate, apply
            
            # Notify listener
            if self.on_block:
                # Would pass full block here
                pass
            
            # Forward to other peers
            await self.peers.broadcast(msg, exclude=msg.sender)
            
        except Exception as e:
            logger.warning(f"Error handling block from {peer.address}: {e}")


class Mempool:
    """
    Transaction mempool.
    
    Holds pending transactions before they're included in blocks.
    """
    
    def __init__(self, max_size: int = 5000):
        self.max_size = max_size
        self.transactions: Dict[str, Transaction] = {}
        self.by_sender: Dict[str, list] = {}  # sender -> list of tx_ids
    
    def add(self, tx: Transaction) -> tuple[bool, str]:
        """Add a transaction to the mempool."""
        
        tx_id = tx.tx_id()
        
        if tx_id in self.transactions:
            return False, "Transaction already in mempool"
        
        if len(self.transactions) >= self.max_size:
            return False, "Mempool full"
        
        # Validate structure
        valid, error = tx.is_valid()
        if not valid:
            return False, error
        
        self.transactions[tx_id] = tx
        
        if tx.sender not in self.by_sender:
            self.by_sender[tx.sender] = []
        self.by_sender[tx.sender].append(tx_id)
        
        return True, ""
    
    def remove(self, tx_id: str):
        """Remove a transaction from the mempool."""
        
        if tx_id not in self.transactions:
            return
        
        tx = self.transactions[tx_id]
        del self.transactions[tx_id]
        
        if tx.sender in self.by_sender:
            self.by_sender[tx.sender] = [
                t for t in self.by_sender[tx.sender] if t != tx_id
            ]
    
    def get_batch(self, max_count: int = 100) -> list[Transaction]:
        """Get a batch of transactions for block inclusion."""
        
        # Sort by fee (highest first)
        sorted_txs = sorted(
            self.transactions.values(),
            key=lambda t: t.fee,
            reverse=True,
        )
        
        return sorted_txs[:max_count]
    
    def remove_batch(self, tx_ids: list[str]):
        """Remove a batch of transactions (after block inclusion)."""
        
        for tx_id in tx_ids:
            self.remove(tx_id)
    
    def size(self) -> int:
        return len(self.transactions)
    
    def clear(self):
        self.transactions.clear()
        self.by_sender.clear()
