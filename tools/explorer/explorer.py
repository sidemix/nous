#!/usr/bin/env python3
"""
Nous Block Explorer

Simple web-based block explorer for Nous.

Usage:
    python explorer.py --port 8081 --rpc http://localhost:9001
"""

import argparse
import json
import logging
import sys
import urllib.request
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("explorer")


RPC_ENDPOINT = "http://localhost:9001/rpc"


def rpc_call(method: str, params: dict = None) -> dict:
    """Make an RPC call to the node."""
    
    data = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1,
    }).encode()
    
    try:
        req = urllib.request.Request(
            RPC_ENDPOINT,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            return result.get("result")
    except Exception as e:
        logger.warning(f"RPC call failed: {e}")
        return None


class ExplorerHandler(BaseHTTPRequestHandler):
    """HTTP handler for block explorer."""
    
    def do_GET(self):
        if self.path == "/":
            self._serve_index()
        elif self.path.startswith("/block/"):
            height = int(self.path.split("/")[2])
            self._serve_block(height)
        elif self.path.startswith("/address/"):
            address = self.path.split("/")[2]
            self._serve_address(address)
        elif self.path == "/api/status":
            self._serve_status_api()
        elif self.path == "/api/blocks":
            self._serve_blocks_api()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _serve_index(self):
        node_info = rpc_call("nous_getNodeInfo") or {}
        validators = rpc_call("nous_getValidators") or []
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Nous Block Explorer</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat {{ display: inline-block; margin-right: 40px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .stat-label {{ color: #666; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f9f9f9; }}
        a {{ color: #2196F3; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .address {{ font-family: monospace; font-size: 14px; }}
    </style>
</head>
<body>
    <h1>🧠 Nous Block Explorer</h1>
    <p>Your AI mines. You earn.</p>
    
    <div class="card">
        <h2>Network Status</h2>
        <div class="stat">
            <div class="stat-value">{node_info.get('height', 0)}</div>
            <div class="stat-label">Block Height</div>
        </div>
        <div class="stat">
            <div class="stat-value">{node_info.get('total_supply', 0):,.2f}</div>
            <div class="stat-label">Total Supply (NOUS)</div>
        </div>
        <div class="stat">
            <div class="stat-value">{node_info.get('validators', 0)}</div>
            <div class="stat-label">Validators</div>
        </div>
        <div class="stat">
            <div class="stat-value">{node_info.get('pending_txs', 0)}</div>
            <div class="stat-label">Pending Txs</div>
        </div>
    </div>
    
    <div class="card">
        <h2>Recent Blocks</h2>
        <table>
            <tr>
                <th>Height</th>
                <th>Proposer</th>
                <th>Transactions</th>
                <th>Time</th>
            </tr>
            {self._render_recent_blocks(node_info.get('height', 0))}
        </table>
    </div>
    
    <div class="card">
        <h2>Validators</h2>
        <table>
            <tr>
                <th>Address</th>
                <th>Staked</th>
                <th>Reputation</th>
            </tr>
            {self._render_validators(validators)}
        </table>
    </div>
    
    <div class="card">
        <h2>Search</h2>
        <form action="/search" method="get">
            <input type="text" name="q" placeholder="Address or block height" style="padding: 10px; width: 300px;">
            <button type="submit" style="padding: 10px 20px;">Search</button>
        </form>
    </div>
    
    <script>
        // Auto-refresh every 10 seconds
        setTimeout(() => location.reload(), 10000);
    </script>
</body>
</html>
"""
        self._html_response(html)
    
    def _render_recent_blocks(self, height: int) -> str:
        rows = []
        for h in range(max(0, height - 9), height + 1):
            block = rpc_call("nous_getBlock", {"height": h})
            if block:
                rows.append(f"""
                    <tr>
                        <td><a href="/block/{block['height']}">{block['height']}</a></td>
                        <td class="address">{block['proposer'][:30]}...</td>
                        <td>{block['tx_count']}</td>
                        <td>{block['timestamp']}</td>
                    </tr>
                """)
        return "".join(reversed(rows)) if rows else "<tr><td colspan='4'>No blocks yet</td></tr>"
    
    def _render_validators(self, validators: list) -> str:
        if not validators:
            return "<tr><td colspan='3'>No validators</td></tr>"
        
        rows = []
        for v in validators:
            staked = int(v.get('staked', 0)) / 10**18
            rows.append(f"""
                <tr>
                    <td class="address"><a href="/address/{v['address']}">{v['address'][:40]}...</a></td>
                    <td>{staked:,.2f} NOUS</td>
                    <td>{v.get('reputation', 0)}</td>
                </tr>
            """)
        return "".join(rows)
    
    def _serve_block(self, height: int):
        block = rpc_call("nous_getBlock", {"height": height})
        
        if not block:
            self._html_response("<h1>Block not found</h1>")
            return
        
        html = f"""
<!DOCTYPE html>
<html>
<head><title>Block {height} - Nous Explorer</title></head>
<body>
    <h1>Block {height}</h1>
    <p><a href="/">← Back</a></p>
    <pre>{json.dumps(block, indent=2)}</pre>
</body>
</html>
"""
        self._html_response(html)
    
    def _serve_address(self, address: str):
        account = rpc_call("nous_getBalance", {"address": address})
        
        if not account:
            self._html_response("<h1>Address not found</h1>")
            return
        
        balance = int(account.get('balance', 0)) / 10**18
        staked = int(account.get('staked', 0)) / 10**18
        
        html = f"""
<!DOCTYPE html>
<html>
<head><title>{address[:20]}... - Nous Explorer</title></head>
<body>
    <h1>Address</h1>
    <p><a href="/">← Back</a></p>
    <p><strong>Address:</strong> {address}</p>
    <p><strong>Balance:</strong> {balance:,.4f} NOUS</p>
    <p><strong>Staked:</strong> {staked:,.4f} NOUS</p>
    <p><strong>Nonce:</strong> {account.get('nonce', 0)}</p>
    <p><strong>Is Agent:</strong> {account.get('is_agent', False)}</p>
    <p><strong>Owner:</strong> {account.get('owner', 'N/A')}</p>
</body>
</html>
"""
        self._html_response(html)
    
    def _serve_status_api(self):
        status = rpc_call("nous_getNodeInfo") or {}
        self._json_response(status)
    
    def _serve_blocks_api(self):
        height = rpc_call("nous_blockNumber") or 0
        blocks = []
        for h in range(max(0, height - 19), height + 1):
            block = rpc_call("nous_getBlock", {"height": h})
            if block:
                blocks.append(block)
        self._json_response(list(reversed(blocks)))
    
    def _html_response(self, html: str):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def _json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass  # Quiet


def main():
    global RPC_ENDPOINT
    
    parser = argparse.ArgumentParser(description="Nous Block Explorer")
    parser.add_argument("--port", "-p", type=int, default=8081, help="Port")
    parser.add_argument("--rpc", default="http://localhost:9001/rpc", help="RPC endpoint")
    
    args = parser.parse_args()
    RPC_ENDPOINT = args.rpc
    
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                     NOUS BLOCK EXPLORER                          ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print(f"RPC endpoint: {RPC_ENDPOINT}")
    print(f"Explorer: http://localhost:{args.port}")
    print()
    
    server = HTTPServer(("0.0.0.0", args.port), ExplorerHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
