#!/usr/bin/env python3
"""
Nous Wallet CLI

Command-line wallet for humans to interact with Nous.

Usage:
    nous-wallet create                    Create new wallet
    nous-wallet balance <address>         Check balance
    nous-wallet send <to> <amount>        Send NOUS
    nous-wallet stake <amount>            Stake NOUS
    nous-wallet unstake <amount>          Unstake NOUS
    nous-wallet register-agent            Register AI agent
"""

import argparse
import json
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.crypto.keys import KeyPair, generate_agent_identity
from agent.core.transaction import Transaction, create_transaction, NOUS, NOUSLING


WALLET_DIR = Path.home() / ".nous"
WALLET_FILE = WALLET_DIR / "wallet.json"
CONFIG_FILE = WALLET_DIR / "config.json"


@dataclass
class WalletConfig:
    """Wallet configuration."""
    
    node_endpoint: str = "http://localhost:9000"
    network: str = "testnet"


class Wallet:
    """
    Nous wallet.
    
    Manages keys and creates transactions.
    """
    
    def __init__(self, keypair: KeyPair, name: str = "default"):
        self.keypair = keypair
        self.name = name
        self.nonce = 0  # Track locally, sync with network
    
    @property
    def address(self) -> str:
        return self.keypair.address()
    
    def create_transaction(
        self,
        recipient: str,
        amount: int,
        fee: int = 1000,
    ) -> Transaction:
        """Create and sign a transaction."""
        
        tx = create_transaction(
            sender_keypair=self.keypair,
            recipient=recipient,
            amount=amount,
            nonce=self.nonce,
            fee=fee,
        )
        
        self.nonce += 1
        return tx
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "address": self.address,
            "public_key": self.keypair.public_key.hex(),
            "private_key": self.keypair.private_key.hex(),
            "nonce": self.nonce,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        keypair = KeyPair(
            private_key=bytes.fromhex(data["private_key"]),
            public_key=bytes.fromhex(data["public_key"]),
        )
        wallet = cls(keypair, data.get("name", "default"))
        wallet.nonce = data.get("nonce", 0)
        return wallet
    
    def save(self, path: Path = WALLET_FILE):
        """Save wallet to file."""
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing wallets
        wallets = {}
        if path.exists():
            with open(path) as f:
                wallets = json.load(f)
        
        wallets[self.name] = self.to_dict()
        
        with open(path, "w") as f:
            json.dump(wallets, f, indent=2)
        
        # Secure permissions
        os.chmod(path, 0o600)
    
    @classmethod
    def load(cls, name: str = "default", path: Path = WALLET_FILE) -> Optional["Wallet"]:
        """Load wallet from file."""
        
        if not path.exists():
            return None
        
        with open(path) as f:
            wallets = json.load(f)
        
        if name not in wallets:
            return None
        
        return cls.from_dict(wallets[name])


def cmd_create(args):
    """Create a new wallet."""
    
    name = args.name or "default"
    
    # Check if exists
    existing = Wallet.load(name)
    if existing and not args.force:
        print(f"Wallet '{name}' already exists. Use --force to overwrite.")
        return 1
    
    # Generate new keypair
    keypair, address = generate_agent_identity()
    wallet = Wallet(keypair, name)
    wallet.save()
    
    print(f"✨ Wallet created!")
    print(f"   Name: {name}")
    print(f"   Address: {address}")
    print()
    print(f"⚠️  Your wallet is saved at: {WALLET_FILE}")
    print(f"   Keep your private key safe!")
    
    return 0


def cmd_address(args):
    """Show wallet address."""
    
    wallet = Wallet.load(args.wallet)
    if not wallet:
        print(f"Wallet '{args.wallet}' not found. Create one with: nous-wallet create")
        return 1
    
    print(wallet.address)
    return 0


def cmd_balance(args):
    """Check balance."""
    
    address = args.address
    
    if not address:
        wallet = Wallet.load(args.wallet)
        if not wallet:
            print(f"Wallet '{args.wallet}' not found.")
            return 1
        address = wallet.address
    
    # In real impl: query node for balance
    print(f"Address: {address}")
    print(f"Balance: (connect to node to check)")
    print()
    print("Note: Run a local node or connect to a remote node to check balance.")
    
    return 0


def cmd_send(args):
    """Send NOUS."""
    
    wallet = Wallet.load(args.wallet)
    if not wallet:
        print(f"Wallet '{args.wallet}' not found.")
        return 1
    
    recipient = args.to
    amount = int(float(args.amount) * NOUS)
    
    if not recipient.startswith("nous:"):
        print("Invalid recipient address. Must start with 'nous:'")
        return 1
    
    tx = wallet.create_transaction(recipient, amount)
    wallet.save()
    
    print(f"📤 Transaction created!")
    print(f"   From: {wallet.address}")
    print(f"   To: {recipient}")
    print(f"   Amount: {amount / NOUS} NOUS")
    print(f"   Fee: {tx.fee / NOUS} NOUS")
    print(f"   TX ID: {tx.tx_id()}")
    print()
    print("Note: Broadcast to network to complete transaction.")
    
    return 0


def cmd_export(args):
    """Export wallet (for backup)."""
    
    wallet = Wallet.load(args.wallet)
    if not wallet:
        print(f"Wallet '{args.wallet}' not found.")
        return 1
    
    if args.private:
        print(f"⚠️  PRIVATE KEY - KEEP SECRET!")
        print(wallet.keypair.private_key.hex())
    else:
        print(json.dumps({
            "address": wallet.address,
            "public_key": wallet.keypair.public_key.hex(),
        }, indent=2))
    
    return 0


def cmd_import(args):
    """Import wallet from private key."""
    
    private_key = args.private_key
    name = args.name or "imported"
    
    try:
        keypair = KeyPair.from_private_key(bytes.fromhex(private_key))
        wallet = Wallet(keypair, name)
        wallet.save()
        
        print(f"✨ Wallet imported!")
        print(f"   Name: {name}")
        print(f"   Address: {wallet.address}")
        
        return 0
        
    except Exception as e:
        print(f"Error importing wallet: {e}")
        return 1


def cmd_list(args):
    """List all wallets."""
    
    if not WALLET_FILE.exists():
        print("No wallets found. Create one with: nous-wallet create")
        return 0
    
    with open(WALLET_FILE) as f:
        wallets = json.load(f)
    
    print(f"{'Name':<20} {'Address':<50}")
    print("-" * 70)
    
    for name, data in wallets.items():
        print(f"{name:<20} {data['address']:<50}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Nous Wallet CLI - Your AI mines. You earn.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # create
    p_create = subparsers.add_parser("create", help="Create new wallet")
    p_create.add_argument("--name", "-n", help="Wallet name")
    p_create.add_argument("--force", "-f", action="store_true", help="Overwrite existing")
    
    # address
    p_addr = subparsers.add_parser("address", help="Show wallet address")
    p_addr.add_argument("--wallet", "-w", default="default", help="Wallet name")
    
    # balance
    p_bal = subparsers.add_parser("balance", help="Check balance")
    p_bal.add_argument("address", nargs="?", help="Address to check")
    p_bal.add_argument("--wallet", "-w", default="default", help="Wallet name")
    
    # send
    p_send = subparsers.add_parser("send", help="Send NOUS")
    p_send.add_argument("to", help="Recipient address")
    p_send.add_argument("amount", help="Amount in NOUS")
    p_send.add_argument("--wallet", "-w", default="default", help="Wallet name")
    
    # export
    p_export = subparsers.add_parser("export", help="Export wallet")
    p_export.add_argument("--wallet", "-w", default="default", help="Wallet name")
    p_export.add_argument("--private", action="store_true", help="Include private key")
    
    # import
    p_import = subparsers.add_parser("import", help="Import wallet from private key")
    p_import.add_argument("private_key", help="Private key (hex)")
    p_import.add_argument("--name", "-n", help="Wallet name")
    
    # list
    p_list = subparsers.add_parser("list", help="List wallets")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    commands = {
        "create": cmd_create,
        "address": cmd_address,
        "balance": cmd_balance,
        "send": cmd_send,
        "export": cmd_export,
        "import": cmd_import,
        "list": cmd_list,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
