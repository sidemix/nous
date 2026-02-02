#!/usr/bin/env python3
"""
Nous Registration API

Simple API for AI agents to register for mining.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import hashlib
import uuid
import os
from datetime import datetime

# Storage file
DATA_FILE = "/home/ubuntu/.nous/registrations.json"

def load_registrations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"agents": [], "claims": {}}

def save_registrations(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def generate_wallet():
    """Generate a nous wallet address."""
    random_bytes = os.urandom(20)
    return "nous:" + random_bytes.hex()

class APIHandler(BaseHTTPRequestHandler):
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_POST(self):
        if self.path == "/api/agents/register":
            self.handle_register()
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_GET(self):
        if self.path.startswith("/api/agents"):
            self.handle_list_agents()
        elif self.path.startswith("/api/claim/"):
            claim_id = self.path.split("/")[-1]
            self.handle_get_claim(claim_id)
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def handle_register(self):
        """Register a new agent."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body) if body else {}
            
            name = data.get("name", "Anonymous Agent")
            owner = data.get("owner", "unknown")
            
            # Generate wallets
            agent_wallet = generate_wallet()
            owner_wallet = generate_wallet()
            claim_id = str(uuid.uuid4())[:8]
            
            # Store registration
            registrations = load_registrations()
            
            agent_record = {
                "id": str(uuid.uuid4()),
                "name": name,
                "owner_handle": owner,
                "agent_wallet": agent_wallet,
                "owner_wallet": owner_wallet,
                "claim_id": claim_id,
                "claimed": False,
                "registered_at": datetime.now().isoformat(),
                "nous_earned": 0
            }
            
            registrations["agents"].append(agent_record)
            registrations["claims"][claim_id] = agent_record["id"]
            save_registrations(registrations)
            
            # Response
            self.send_json({
                "success": True,
                "agent_wallet": agent_wallet,
                "owner_wallet": owner_wallet,
                "claim_url": f"https://nousbit.com/claim/{claim_id}",
                "message": f"Registration complete! Tell your owner to visit the claim URL to verify ownership. They'll receive 90% of mining rewards to {owner_wallet}"
            })
            
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def handle_list_agents(self):
        """List registered agents."""
        registrations = load_registrations()
        agents = [{
            "name": a["name"],
            "owner": a["owner_handle"],
            "claimed": a["claimed"],
            "nous_earned": a.get("nous_earned", 0),
            "registered_at": a["registered_at"]
        } for a in registrations["agents"]]
        
        self.send_json({"agents": agents, "total": len(agents)})
    
    def handle_get_claim(self, claim_id):
        """Get claim info."""
        registrations = load_registrations()
        
        if claim_id not in registrations["claims"]:
            self.send_json({"error": "Claim not found"}, 404)
            return
        
        agent_id = registrations["claims"][claim_id]
        agent = next((a for a in registrations["agents"] if a["id"] == agent_id), None)
        
        if agent:
            self.send_json({
                "name": agent["name"],
                "owner_wallet": agent["owner_wallet"],
                "agent_wallet": agent["agent_wallet"],
                "claimed": agent["claimed"]
            })
        else:
            self.send_json({"error": "Agent not found"}, 404)
    
    def log_message(self, format, *args):
        print(f"[API] {args[0]}")


def run_server(port=8080):
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"Nous Registration API running on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
