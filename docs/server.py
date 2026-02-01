#!/usr/bin/env python3
"""
Nous Website Server

Simple server for the Nous website with API endpoints.

Usage:
    python server.py --port 8000
"""

import argparse
import json
import logging
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nous.web")

# Data storage (in production, use a database)
DATA_DIR = Path(__file__).parent / "data"
AGENTS_FILE = DATA_DIR / "agents.json"
STATS_FILE = DATA_DIR / "stats.json"


def load_json(path):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


class NousHandler(SimpleHTTPRequestHandler):
    """HTTP handler for Nous website."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path.startswith('/api/'):
            self.handle_api_get(parsed)
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path.startswith('/api/'):
            self.handle_api_post(parsed)
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_api_get(self, parsed):
        path = parsed.path
        
        if path == '/api/stats':
            self.json_response(self.get_stats())
        
        elif path == '/api/agents':
            self.json_response(self.get_agents())
        
        elif path == '/api/leaderboard':
            self.json_response(self.get_leaderboard())
        
        else:
            self.json_response({'error': 'Not found'}, 404)
    
    def handle_api_post(self, parsed):
        path = parsed.path
        
        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode()
        
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.json_response({'error': 'Invalid JSON'}, 400)
            return
        
        if path == '/api/agents/register':
            self.json_response(self.register_agent(data))
        
        else:
            self.json_response({'error': 'Not found'}, 404)
    
    def get_stats(self):
        stats = load_json(STATS_FILE)
        agents = load_json(AGENTS_FILE)
        
        return {
            'agent_count': len(agents.get('agents', [])),
            'block_height': stats.get('block_height', 0),
            'total_earned': stats.get('total_earned', 0),
            'total_supply': stats.get('total_supply', 0),
        }
    
    def get_agents(self):
        data = load_json(AGENTS_FILE)
        return data.get('agents', [])
    
    def get_leaderboard(self):
        agents = load_json(AGENTS_FILE).get('agents', [])
        
        # Sort by earned
        sorted_agents = sorted(agents, key=lambda a: a.get('earned', 0), reverse=True)
        
        return sorted_agents[:20]
    
    def register_agent(self, data):
        required = ['name', 'address', 'owner']
        
        for field in required:
            if field not in data:
                return {'success': False, 'error': f'Missing field: {field}'}
        
        # Validate address format
        if not data['address'].startswith('nous:'):
            return {'success': False, 'error': 'Invalid address format'}
        
        if not data['owner'].startswith('nous:'):
            return {'success': False, 'error': 'Invalid owner address format'}
        
        # Load existing agents
        agents_data = load_json(AGENTS_FILE)
        agents = agents_data.get('agents', [])
        
        # Check if already registered
        for agent in agents:
            if agent['address'] == data['address']:
                return {'success': False, 'error': 'Agent already registered'}
        
        # Add new agent
        new_agent = {
            'name': data['name'],
            'address': data['address'],
            'owner': data['owner'],
            'description': data.get('description', ''),
            'registered_at': datetime.now().isoformat(),
            'blocks': 0,
            'earned': 0,
        }
        
        agents.append(new_agent)
        agents_data['agents'] = agents
        save_json(AGENTS_FILE, agents_data)
        
        logger.info(f"Registered new agent: {data['name']} ({data['address'][:20]}...)")
        
        return {
            'success': True,
            'message': 'Agent registered successfully',
            'agent': new_agent,
        }
    
    def json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        if '/api/' in args[0]:
            logger.info(f"{self.address_string()} - {format % args}")


def main():
    parser = argparse.ArgumentParser(description="Nous Website Server")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port")
    parser.add_argument("--host", default="0.0.0.0", help="Host")
    
    args = parser.parse_args()
    
    # Create data directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                      NOUS WEBSITE SERVER                         ║")
    print("║                   Your AI mines. You earn.                       ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print(f"Server: http://{args.host}:{args.port}")
    print(f"API: http://{args.host}:{args.port}/api/")
    print()
    
    server = HTTPServer((args.host, args.port), NousHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
