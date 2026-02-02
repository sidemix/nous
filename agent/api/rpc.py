"""
Nous RPC API

JSON-RPC API for wallets and external applications.
"""

import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger("nous.rpc")


@dataclass
class RPCRequest:
    """JSON-RPC request."""
    
    method: str
    params: dict
    id: Optional[int] = None
    
    @classmethod
    def from_json(cls, data: str) -> "RPCRequest":
        d = json.loads(data)
        return cls(
            method=d.get("method", ""),
            params=d.get("params", {}),
            id=d.get("id"),
        )


@dataclass
class RPCResponse:
    """JSON-RPC response."""
    
    result: Any = None
    error: Optional[Dict] = None
    id: Optional[int] = None
    
    def to_json(self) -> str:
        d = {"jsonrpc": "2.0", "id": self.id}
        if self.error:
            d["error"] = self.error
        else:
            d["result"] = self.result
        return json.dumps(d)
    
    @classmethod
    def success(cls, result: Any, id: int = None) -> "RPCResponse":
        return cls(result=result, id=id)
    
    @classmethod
    def fail(cls, code: int, message: str, id: int = None) -> "RPCResponse":
        return cls(error={"code": code, "message": message}, id=id)


class RPCHandler(BaseHTTPRequestHandler):
    """HTTP handler for RPC requests."""
    
    node = None  # Set by server
    
    def do_POST(self):
        if self.path != "/rpc":
            self.send_response(404)
            self.end_headers()
            return
        
        # Read request
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        
        try:
            request = RPCRequest.from_json(body)
            response = self._handle_request(request)
        except Exception as e:
            response = RPCResponse.fail(-32700, f"Parse error: {e}")
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response.to_json().encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def _handle_request(self, req: RPCRequest) -> RPCResponse:
        """Route RPC request to handler."""
        
        handlers = {
            # Standard Nous RPC
            "nous_chainId": self._chain_id,
            "nous_blockNumber": self._block_number,
            "nous_getBalance": self._get_balance,
            "nous_getBlock": self._get_block,
            "nous_getTransaction": self._get_transaction,
            "nous_sendTransaction": self._send_transaction,
            "nous_getNodeInfo": self._get_node_info,
            "nous_getValidators": self._get_validators,
            "nous_getPendingTransactions": self._get_pending_txs,
            # Simple aliases for web wallet
            "get_balance": self._get_balance_simple,
            "get_info": self._get_info,
            "send_transaction": self._send_tx_simple,
        }
        
        if req.method not in handlers:
            return RPCResponse.fail(-32601, f"Method not found: {req.method}", req.id)
        
        try:
            result = handlers[req.method](req.params)
            return RPCResponse.success(result, req.id)
        except Exception as e:
            return RPCResponse.fail(-32603, str(e), req.id)
    
    def _chain_id(self, params: dict) -> str:
        return "nous-testnet-1"
    
    def _block_number(self, params: dict) -> int:
        if not RPCHandler.node:
            return 0
        return RPCHandler.node.state.height
    
    def _get_balance(self, params: dict) -> dict:
        address = params.get("address", "")
        
        if not RPCHandler.node:
            return {"balance": "0", "nonce": 0}
        
        account = RPCHandler.node.state.ledger.get_account(address)
        
        return {
            "address": address,
            "balance": str(account.balance),
            "nonce": account.nonce,
            "staked": str(account.staked),
            "is_agent": account.is_agent,
            "owner": account.owner,
        }
    
    def _get_block(self, params: dict) -> Optional[dict]:
        height = params.get("height")
        
        if not RPCHandler.node:
            return None
        
        if height is None or height > len(RPCHandler.node.state.chain) - 1:
            return None
        
        block = RPCHandler.node.state.chain[height]
        
        return {
            "height": block.height,
            "hash": block.hash.hex(),
            "proposer": block.header.proposer,
            "timestamp": block.header.timestamp,
            "tx_count": len(block.transactions),
            "attestations": len(block.attestations),
        }
    
    def _get_transaction(self, params: dict) -> Optional[dict]:
        tx_id = params.get("tx_id", "")
        # Would search chain for transaction
        return None
    
    def _send_transaction(self, params: dict) -> dict:
        if not RPCHandler.node:
            return {"success": False, "error": "Node not available"}
        
        # Parse transaction from params
        # In real impl: deserialize and submit to mempool
        
        return {"success": True, "message": "Transaction submitted"}
    
    def _get_node_info(self, params: dict) -> dict:
        if not RPCHandler.node:
            return {}
        
        return RPCHandler.node.get_stats()
    
    def _get_validators(self, params: dict) -> list:
        if not RPCHandler.node:
            return []
        
        validators = []
        for addr in RPCHandler.node.state.validators:
            account = RPCHandler.node.state.ledger.get_account(addr)
            validators.append({
                "address": addr,
                "staked": str(account.staked),
                "reputation": account.reputation,
            })
        
        return validators
    
    def _get_pending_txs(self, params: dict) -> list:
        if not RPCHandler.node:
            return []
        
        return [
            {
                "tx_id": tx.tx_id(),
                "sender": tx.sender,
                "recipient": tx.recipient,
                "amount": str(tx.amount),
                "fee": str(tx.fee),
            }
            for tx in RPCHandler.node.state.pending_txs[:100]
        ]
    
    # Helper to get ledger from either node type
    def _get_ledger(self):
        node = RPCHandler.node
        if hasattr(node, 'state'):
            return node.state.ledger
        return node.ledger
    
    def _get_chain(self):
        node = RPCHandler.node
        if hasattr(node, 'state'):
            return node.state.chain
        return node.chain
    
    def _get_height(self):
        chain = self._get_chain()
        return len(chain) - 1 if chain else 0
    
    # Simple methods for web wallet
    def _get_balance_simple(self, params: dict) -> int:
        """Get balance as simple integer (nouslings)."""
        address = params.get("address", "")
        
        if not RPCHandler.node:
            return 0
        
        account = self._get_ledger().get_account(address)
        return account.balance
    
    def _get_info(self, params: dict) -> dict:
        """Get node info for wallet."""
        if not RPCHandler.node:
            return {"status": "offline"}
        
        return {
            "status": "online",
            "height": self._get_height(),
            "network": "nous-mainnet",
            "genesis_hash": "7da31c120616b05a818beb854245449afb0622b5eeac1b40be891b70b63c4a76",
        }
    
    def _send_tx_simple(self, params: dict) -> dict:
        """Send transaction from web wallet."""
        if not RPCHandler.node:
            return {"success": False, "error": "Node offline"}
        
        from_addr = params.get("from", "")
        to_addr = params.get("to", "")
        amount = params.get("amount", 0)
        
        ledger = self._get_ledger()
        
        # Check sender has balance
        sender = ledger.get_account(from_addr)
        if sender.balance < amount:
            return {"success": False, "error": "Insufficient balance"}
        
        # Apply transfer directly (simplified - real impl would create signed tx)
        sender.balance -= amount
        sender.nonce += 1
        
        recipient = ledger.get_account(to_addr)
        recipient.balance += amount
        
        # Generate tx_id
        import hashlib
        tx_data = f"{from_addr}{to_addr}{amount}{sender.nonce}".encode()
        tx_id = hashlib.sha256(tx_data).hexdigest()
        
        return {"success": True, "tx_id": tx_id}
    
    def log_message(self, format, *args):
        logger.debug(f"{self.address_string()} - {format % args}")


class RPCServer:
    """RPC server for Nous node."""
    
    def __init__(self, node, host: str = "0.0.0.0", port: int = 9001):
        self.node = node
        self.host = host
        self.port = port
        self.server = None
    
    def start(self):
        """Start the RPC server."""
        
        RPCHandler.node = self.node
        self.server = HTTPServer((self.host, self.port), RPCHandler)
        
        logger.info(f"RPC server listening on http://{self.host}:{self.port}/rpc")
        
        # Run in background thread
        import threading
        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()
    
    def stop(self):
        """Stop the RPC server."""
        if self.server:
            self.server.shutdown()


if __name__ == "__main__":
    # Demo: Start RPC server
    print("Nous RPC Server")
    print("Endpoints:")
    print("  POST /rpc - JSON-RPC endpoint")
    print()
    print("Methods:")
    print("  nous_chainId - Get chain ID")
    print("  nous_blockNumber - Get current block height")
    print("  nous_getBalance - Get account balance")
    print("  nous_getBlock - Get block by height")
    print("  nous_getValidators - Get validator list")
