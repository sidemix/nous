#!/usr/bin/env python3
"""
Nous Testnet Faucet

Dispenses test NOUS for development.

Usage:
    python faucet.py --port 8080
    
Then: curl http://localhost:8080/faucet?address=nous:abc123
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.crypto.keys import generate_agent_identity, KeyPair
from agent.core.transaction import create_transaction, NOUS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("faucet")


# Faucet configuration
FAUCET_AMOUNT = 100 * NOUS  # 100 NOUS per request
RATE_LIMIT_SECONDS = 3600   # 1 request per hour per address


class FaucetHandler(BaseHTTPRequestHandler):
    """HTTP handler for faucet requests."""
    
    # Class-level state
    faucet_keypair = None
    faucet_nonce = 0
    rate_limit = {}  # address -> last request time
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(self._index_html().encode())
            
        elif parsed.path == "/faucet":
            self._handle_faucet(parse_qs(parsed.query))
            
        elif parsed.path == "/status":
            self._handle_status()
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def _index_html(self):
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Nous Testnet Faucet</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
        h1 {{ color: #333; }}
        input {{ padding: 10px; width: 100%; margin: 10px 0; font-size: 16px; }}
        button {{ padding: 10px 20px; font-size: 16px; background: #4CAF50; color: white; border: none; cursor: pointer; }}
        button:hover {{ background: #45a049; }}
        .result {{ margin-top: 20px; padding: 10px; background: #f0f0f0; }}
    </style>
</head>
<body>
    <h1>🧠 Nous Testnet Faucet</h1>
    <p>Get test NOUS for development.</p>
    
    <form onsubmit="requestFunds(event)">
        <input type="text" id="address" placeholder="Enter your nous: address" required>
        <button type="submit">Request {FAUCET_AMOUNT // NOUS} NOUS</button>
    </form>
    
    <div id="result" class="result" style="display:none;"></div>
    
    <script>
        async function requestFunds(e) {{
            e.preventDefault();
            const addr = document.getElementById('address').value;
            const result = document.getElementById('result');
            
            result.style.display = 'block';
            result.textContent = 'Requesting...';
            
            try {{
                const res = await fetch('/faucet?address=' + encodeURIComponent(addr));
                const data = await res.json();
                
                if (data.success) {{
                    result.textContent = '✅ Sent ' + data.amount + ' NOUS! TX: ' + data.tx_id;
                }} else {{
                    result.textContent = '❌ Error: ' + data.error;
                }}
            }} catch (err) {{
                result.textContent = '❌ Error: ' + err.message;
            }}
        }}
    </script>
    
    <hr>
    <p><small>Faucet address: {FaucetHandler.faucet_keypair.address() if FaucetHandler.faucet_keypair else 'N/A'}</small></p>
</body>
</html>
"""
    
    def _handle_faucet(self, params):
        import time
        
        address = params.get("address", [None])[0]
        
        if not address:
            self._json_response({"success": False, "error": "Missing address parameter"})
            return
        
        if not address.startswith("nous:"):
            self._json_response({"success": False, "error": "Invalid address format"})
            return
        
        # Rate limiting
        now = time.time()
        if address in FaucetHandler.rate_limit:
            elapsed = now - FaucetHandler.rate_limit[address]
            if elapsed < RATE_LIMIT_SECONDS:
                remaining = int(RATE_LIMIT_SECONDS - elapsed)
                self._json_response({
                    "success": False, 
                    "error": f"Rate limited. Try again in {remaining} seconds."
                })
                return
        
        # Create transaction
        tx = create_transaction(
            sender_keypair=FaucetHandler.faucet_keypair,
            recipient=address,
            amount=FAUCET_AMOUNT,
            nonce=FaucetHandler.faucet_nonce,
        )
        
        FaucetHandler.faucet_nonce += 1
        FaucetHandler.rate_limit[address] = now
        
        logger.info(f"Faucet: sent {FAUCET_AMOUNT / NOUS} NOUS to {address}")
        
        self._json_response({
            "success": True,
            "amount": FAUCET_AMOUNT // NOUS,
            "tx_id": tx.tx_id(),
            "from": FaucetHandler.faucet_keypair.address(),
            "to": address,
        })
    
    def _handle_status(self):
        self._json_response({
            "faucet_address": FaucetHandler.faucet_keypair.address() if FaucetHandler.faucet_keypair else None,
            "amount_per_request": FAUCET_AMOUNT // NOUS,
            "rate_limit_seconds": RATE_LIMIT_SECONDS,
            "nonce": FaucetHandler.faucet_nonce,
        })
    
    def _json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")


def main():
    parser = argparse.ArgumentParser(description="Nous Testnet Faucet")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port to listen on")
    
    args = parser.parse_args()
    
    # Generate faucet keypair
    FaucetHandler.faucet_keypair, addr = generate_agent_identity()
    
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                     NOUS TESTNET FAUCET                          ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print(f"Faucet address: {addr}")
    print(f"Amount per request: {FAUCET_AMOUNT // NOUS} NOUS")
    print(f"Rate limit: {RATE_LIMIT_SECONDS} seconds per address")
    print()
    print(f"Starting server on http://localhost:{args.port}")
    print()
    
    server = HTTPServer(("0.0.0.0", args.port), FaucetHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
