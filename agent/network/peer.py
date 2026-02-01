"""
Nous P2P Networking

Peer-to-peer communication between agent nodes.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

logger = logging.getLogger("nous.network")


class MessageType(Enum):
    """P2P message types."""
    
    HELLO = "hello"           # Initial handshake
    HELLO_ACK = "hello_ack"   # Handshake response
    PEERS = "peers"           # Share peer list
    TX = "tx"                 # Broadcast transaction
    BLOCK = "block"           # Broadcast block
    ATTEST = "attest"         # Broadcast attestation
    SYNC_REQ = "sync_req"     # Request blocks
    SYNC_RES = "sync_res"     # Send requested blocks
    PING = "ping"
    PONG = "pong"


@dataclass
class Message:
    """A P2P message."""
    
    type: MessageType
    payload: dict
    sender: str
    timestamp: int
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.type.value,
            "payload": self.payload,
            "sender": self.sender,
            "timestamp": self.timestamp,
        })
    
    @classmethod
    def from_json(cls, data: str) -> "Message":
        d = json.loads(data)
        return cls(
            type=MessageType(d["type"]),
            payload=d["payload"],
            sender=d["sender"],
            timestamp=d["timestamp"],
        )


@dataclass
class PeerInfo:
    """Information about a connected peer."""
    
    address: str              # Nous address
    host: str                 # IP/hostname
    port: int                 # Port
    last_seen: int = 0        # Last message timestamp
    latency_ms: int = 0       # Round-trip latency
    height: int = 0           # Their chain height
    reputation: int = 100     # Peer reputation score
    
    @property
    def endpoint(self) -> str:
        return f"{self.host}:{self.port}"


class PeerManager:
    """
    Manages peer connections.
    
    Handles discovery, connection, and gossip.
    """
    
    def __init__(
        self, 
        node_address: str,
        listen_port: int = 9000,
        max_peers: int = 50,
        target_peers: int = 12,
    ):
        self.node_address = node_address
        self.listen_port = listen_port
        self.max_peers = max_peers
        self.target_peers = target_peers
        
        self.peers: Dict[str, PeerInfo] = {}
        self.known_endpoints: set = set()
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        self.server = None
        self.running = False
    
    def register_handler(self, msg_type: MessageType, handler: Callable):
        """Register a handler for a message type."""
        self.message_handlers[msg_type] = handler
    
    async def start(self, seed_nodes: List[str] = None):
        """Start the peer manager."""
        
        self.running = True
        
        # Start listening for connections
        self.server = await asyncio.start_server(
            self._handle_connection,
            host="0.0.0.0",
            port=self.listen_port,
        )
        
        logger.info(f"Listening on port {self.listen_port}")
        
        # Connect to seed nodes
        if seed_nodes:
            for endpoint in seed_nodes:
                await self.connect(endpoint)
        
        # Start background tasks
        asyncio.create_task(self._maintenance_loop())
    
    async def stop(self):
        """Stop the peer manager."""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
    
    async def connect(self, endpoint: str) -> bool:
        """Connect to a peer."""
        
        if len(self.peers) >= self.max_peers:
            return False
        
        try:
            host, port = endpoint.split(":")
            port = int(port)
            
            reader, writer = await asyncio.open_connection(host, port)
            
            # Send hello
            hello = Message(
                type=MessageType.HELLO,
                payload={
                    "address": self.node_address,
                    "port": self.listen_port,
                    "version": "0.1.0",
                },
                sender=self.node_address,
                timestamp=int(asyncio.get_event_loop().time() * 1000),
            )
            
            writer.write(hello.to_json().encode() + b"\n")
            await writer.drain()
            
            # Wait for hello_ack
            data = await asyncio.wait_for(reader.readline(), timeout=5.0)
            response = Message.from_json(data.decode().strip())
            
            if response.type == MessageType.HELLO_ACK:
                peer = PeerInfo(
                    address=response.sender,
                    host=host,
                    port=port,
                    height=response.payload.get("height", 0),
                )
                self.peers[peer.address] = peer
                
                # Start handling messages from this peer
                asyncio.create_task(self._read_loop(reader, writer, peer))
                
                logger.info(f"Connected to peer: {peer.address}")
                return True
            
        except Exception as e:
            logger.warning(f"Failed to connect to {endpoint}: {e}")
        
        return False
    
    async def broadcast(self, msg: Message, exclude: str = None):
        """Broadcast a message to all peers."""
        
        for address, peer in self.peers.items():
            if address == exclude:
                continue
            
            try:
                await self._send_to_peer(peer, msg)
            except Exception as e:
                logger.warning(f"Failed to send to {address}: {e}")
    
    async def _handle_connection(self, reader, writer):
        """Handle incoming connection."""
        
        try:
            # Read hello
            data = await asyncio.wait_for(reader.readline(), timeout=5.0)
            msg = Message.from_json(data.decode().strip())
            
            if msg.type != MessageType.HELLO:
                writer.close()
                return
            
            # Send hello_ack
            ack = Message(
                type=MessageType.HELLO_ACK,
                payload={
                    "address": self.node_address,
                    "height": 0,  # Will be set by node
                },
                sender=self.node_address,
                timestamp=int(asyncio.get_event_loop().time() * 1000),
            )
            
            writer.write(ack.to_json().encode() + b"\n")
            await writer.drain()
            
            # Register peer
            peer_addr = writer.get_extra_info("peername")
            peer = PeerInfo(
                address=msg.sender,
                host=peer_addr[0],
                port=msg.payload.get("port", 9000),
            )
            self.peers[peer.address] = peer
            
            logger.info(f"Accepted connection from: {peer.address}")
            
            # Handle messages
            await self._read_loop(reader, writer, peer)
            
        except Exception as e:
            logger.warning(f"Connection error: {e}")
        finally:
            writer.close()
    
    async def _read_loop(self, reader, writer, peer: PeerInfo):
        """Read messages from a peer."""
        
        while self.running:
            try:
                data = await asyncio.wait_for(reader.readline(), timeout=60.0)
                if not data:
                    break
                
                msg = Message.from_json(data.decode().strip())
                peer.last_seen = msg.timestamp
                
                # Handle message
                if msg.type in self.message_handlers:
                    await self.message_handlers[msg.type](msg, peer)
                
            except asyncio.TimeoutError:
                # Send ping
                ping = Message(
                    type=MessageType.PING,
                    payload={},
                    sender=self.node_address,
                    timestamp=int(asyncio.get_event_loop().time() * 1000),
                )
                writer.write(ping.to_json().encode() + b"\n")
                await writer.drain()
                
            except Exception as e:
                logger.warning(f"Error reading from {peer.address}: {e}")
                break
        
        # Cleanup
        if peer.address in self.peers:
            del self.peers[peer.address]
        logger.info(f"Disconnected from: {peer.address}")
    
    async def _send_to_peer(self, peer: PeerInfo, msg: Message):
        """Send a message to a specific peer."""
        # In real impl, maintain persistent connections
        # This is simplified
        pass
    
    async def _maintenance_loop(self):
        """Periodic maintenance tasks."""
        
        while self.running:
            await asyncio.sleep(30)
            
            # Try to maintain target peer count
            if len(self.peers) < self.target_peers:
                # Try to connect to known endpoints
                for endpoint in list(self.known_endpoints):
                    if len(self.peers) >= self.target_peers:
                        break
                    await self.connect(endpoint)
            
            # Remove stale peers
            stale = []
            now = int(asyncio.get_event_loop().time() * 1000)
            for addr, peer in self.peers.items():
                if now - peer.last_seen > 120_000:  # 2 min
                    stale.append(addr)
            
            for addr in stale:
                del self.peers[addr]
                logger.info(f"Removed stale peer: {addr}")


if __name__ == "__main__":
    # Demo
    print("Nous P2P Network Layer")
    print("Message types:", [m.value for m in MessageType])
