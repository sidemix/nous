"""
Nous Chain Sync

Synchronize blockchain state with peers.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional, Callable

from .peer import PeerManager, PeerInfo, Message, MessageType
from ..core.block import Block

logger = logging.getLogger("nous.sync")


@dataclass
class SyncState:
    """Current sync state."""
    
    syncing: bool = False
    target_height: int = 0
    current_height: int = 0
    sync_peer: Optional[str] = None
    
    @property
    def progress(self) -> float:
        if self.target_height == 0:
            return 1.0
        return self.current_height / self.target_height


class ChainSync:
    """
    Chain synchronization manager.
    
    Handles initial sync and catching up after being offline.
    """
    
    def __init__(
        self,
        peer_manager: PeerManager,
        get_height: Callable[[], int],
        get_block: Callable[[int], Optional[Block]],
        apply_block: Callable[[Block], bool],
    ):
        self.peers = peer_manager
        self.get_height = get_height
        self.get_block = get_block
        self.apply_block = apply_block
        
        self.state = SyncState()
        self.pending_blocks: dict[int, Block] = {}
        
        # Register message handlers
        self.peers.register_handler(MessageType.SYNC_REQ, self._handle_sync_req)
        self.peers.register_handler(MessageType.SYNC_RES, self._handle_sync_res)
    
    async def start_sync(self):
        """
        Start chain synchronization.
        
        Finds the best peer and downloads missing blocks.
        """
        
        if self.state.syncing:
            return
        
        # Find peer with highest chain
        best_peer = None
        best_height = self.get_height()
        
        for addr, peer in self.peers.peers.items():
            if peer.height > best_height:
                best_height = peer.height
                best_peer = peer
        
        if not best_peer:
            logger.info("Already at highest known height")
            return
        
        logger.info(f"Starting sync with {best_peer.address}, target height {best_height}")
        
        self.state.syncing = True
        self.state.target_height = best_height
        self.state.current_height = self.get_height()
        self.state.sync_peer = best_peer.address
        
        # Request blocks in batches
        batch_size = 100
        current = self.get_height() + 1
        
        while current <= best_height and self.state.syncing:
            end = min(current + batch_size - 1, best_height)
            
            await self._request_blocks(best_peer, current, end)
            
            # Wait for blocks to arrive
            await asyncio.sleep(1)
            
            # Apply received blocks
            while current in self.pending_blocks:
                block = self.pending_blocks.pop(current)
                if self.apply_block(block):
                    self.state.current_height = current
                    current += 1
                else:
                    logger.error(f"Failed to apply block {current}")
                    break
        
        self.state.syncing = False
        logger.info(f"Sync complete at height {self.get_height()}")
    
    async def _request_blocks(self, peer: PeerInfo, start: int, end: int):
        """Request a range of blocks from a peer."""
        
        msg = Message(
            type=MessageType.SYNC_REQ,
            payload={
                "start_height": start,
                "end_height": end,
            },
            sender=self.peers.node_address,
            timestamp=0,
        )
        
        # In real impl: send directly to peer
        logger.debug(f"Requesting blocks {start}-{end} from {peer.address}")
    
    async def _handle_sync_req(self, msg: Message, peer: PeerInfo):
        """Handle block sync request."""
        
        start = msg.payload.get("start_height", 0)
        end = msg.payload.get("end_height", 0)
        
        blocks = []
        for height in range(start, min(end + 1, self.get_height() + 1)):
            block = self.get_block(height)
            if block:
                blocks.append({
                    "height": block.height,
                    "hash": block.hash.hex(),
                    "proposer": block.header.proposer,
                    # Full block data would go here
                })
        
        response = Message(
            type=MessageType.SYNC_RES,
            payload={"blocks": blocks},
            sender=self.peers.node_address,
            timestamp=0,
        )
        
        # Send response
        logger.debug(f"Sending {len(blocks)} blocks to {peer.address}")
    
    async def _handle_sync_res(self, msg: Message, peer: PeerInfo):
        """Handle block sync response."""
        
        blocks = msg.payload.get("blocks", [])
        
        for block_data in blocks:
            height = block_data.get("height")
            # In real impl: deserialize full block
            # self.pending_blocks[height] = block
            
        logger.debug(f"Received {len(blocks)} blocks from {peer.address}")


class BlockAnnouncer:
    """
    Announces new blocks to the network.
    
    Also handles receiving block announcements.
    """
    
    def __init__(
        self,
        peer_manager: PeerManager,
        validate_block: Callable[[Block], bool],
        apply_block: Callable[[Block], bool],
        get_height: Callable[[], int],
    ):
        self.peers = peer_manager
        self.validate_block = validate_block
        self.apply_block = apply_block
        self.get_height = get_height
        
        self.seen_blocks: set = set()
        
        # Register handler
        self.peers.register_handler(MessageType.BLOCK, self._handle_block)
    
    async def announce_block(self, block: Block):
        """Announce a new block to all peers."""
        
        block_hash = block.hash.hex()
        
        if block_hash in self.seen_blocks:
            return
        
        self.seen_blocks.add(block_hash)
        
        msg = Message(
            type=MessageType.BLOCK,
            payload={
                "height": block.height,
                "hash": block_hash,
                "previous_hash": block.header.previous_hash.hex(),
                "proposer": block.header.proposer,
                "timestamp": block.header.timestamp,
                "tx_count": len(block.transactions),
                "state_root": block.header.state_root.hex(),
                # In real impl: include full block or let peers request it
            },
            sender=self.peers.node_address,
            timestamp=block.header.timestamp,
        )
        
        await self.peers.broadcast(msg)
        logger.info(f"Announced block {block.height}")
    
    async def _handle_block(self, msg: Message, peer: PeerInfo):
        """Handle block announcement."""
        
        block_hash = msg.payload.get("hash", "")
        height = msg.payload.get("height", 0)
        
        if block_hash in self.seen_blocks:
            return
        
        self.seen_blocks.add(block_hash)
        
        # Check if we need this block
        our_height = self.get_height()
        
        if height <= our_height:
            # Already have it
            return
        
        if height > our_height + 1:
            # Missing blocks, need to sync
            logger.info(f"Missing blocks, need sync (have {our_height}, got {height})")
            return
        
        # In real impl: request full block, validate, apply
        logger.info(f"Received block {height} from {peer.address}")
        
        # Update peer's known height
        peer.height = max(peer.height, height)
        
        # Forward to other peers
        await self.peers.broadcast(msg, exclude=msg.sender)
