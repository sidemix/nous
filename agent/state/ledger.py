"""
Nous Ledger

Manages account balances and state transitions.
"""

import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from ..core.transaction import Transaction, NOUS


@dataclass
class Account:
    """An account in the Nous ledger."""
    
    address: str
    balance: int = 0          # Balance in nouslings
    nonce: int = 0            # Transaction count
    staked: int = 0           # Staked amount (for validators)
    reputation: int = 0       # Reputation score
    is_agent: bool = False    # Is this an agent account?
    owner: Optional[str] = None  # If agent, who owns it?
    
    def available_balance(self) -> int:
        """Balance minus staked amount."""
        return self.balance - self.staked


@dataclass
class Ledger:
    """
    The Nous ledger - tracks all account states.
    
    This is the source of truth for who owns what.
    """
    
    accounts: Dict[str, Account] = field(default_factory=dict)
    total_supply: int = 0
    max_supply: int = 21_000_000 * NOUS
    
    def get_account(self, address: str) -> Account:
        """Get or create an account."""
        if address not in self.accounts:
            self.accounts[address] = Account(address=address)
        return self.accounts[address]
    
    def get_balance(self, address: str) -> int:
        """Get account balance."""
        return self.get_account(address).balance
    
    def state_root(self) -> bytes:
        """Compute Merkle root of current state."""
        # Simplified: hash of sorted account data
        state = {
            addr: {
                "balance": acc.balance,
                "nonce": acc.nonce,
                "staked": acc.staked,
            }
            for addr, acc in sorted(self.accounts.items())
        }
        return hashlib.sha256(json.dumps(state).encode()).digest()
    
    def apply_transaction(self, tx: Transaction) -> Tuple[bool, str]:
        """
        Apply a transaction to the ledger.
        
        Returns:
            Tuple of (success, error_message)
        """
        # Validate transaction structure
        valid, error = tx.is_valid()
        if not valid:
            return False, error
        
        sender = self.get_account(tx.sender)
        recipient = self.get_account(tx.recipient)
        
        # Check nonce
        if tx.nonce != sender.nonce:
            return False, f"Invalid nonce: expected {sender.nonce}, got {tx.nonce}"
        
        # Check balance (amount + fee)
        total_cost = tx.amount + tx.fee
        if sender.available_balance() < total_cost:
            return False, f"Insufficient balance: need {total_cost}, have {sender.available_balance()}"
        
        # Apply transaction
        sender.balance -= total_cost
        sender.nonce += 1
        recipient.balance += tx.amount
        
        # Fee is handled by block reward distribution
        
        return True, ""
    
    def mint(self, address: str, amount: int) -> Tuple[bool, str]:
        """
        Mint new tokens (block rewards).
        
        Enforces max supply.
        """
        if self.total_supply + amount > self.max_supply:
            return False, "Would exceed max supply"
        
        account = self.get_account(address)
        account.balance += amount
        self.total_supply += amount
        
        return True, ""
    
    def stake(self, address: str, amount: int) -> Tuple[bool, str]:
        """Stake tokens for validation."""
        account = self.get_account(address)
        
        if account.available_balance() < amount:
            return False, "Insufficient available balance"
        
        account.staked += amount
        return True, ""
    
    def unstake(self, address: str, amount: int) -> Tuple[bool, str]:
        """Unstake tokens (with delay in real impl)."""
        account = self.get_account(address)
        
        if account.staked < amount:
            return False, "Insufficient staked balance"
        
        account.staked -= amount
        return True, ""
    
    def slash(self, address: str, percentage: float) -> int:
        """
        Slash a validator's stake.
        
        Returns amount slashed.
        """
        account = self.get_account(address)
        slash_amount = int(account.staked * percentage)
        account.staked -= slash_amount
        account.balance -= slash_amount
        # Slashed tokens are burned
        self.total_supply -= slash_amount
        return slash_amount
    
    def register_agent(
        self, 
        agent_address: str, 
        owner_address: str,
        initial_stake: int,
    ) -> Tuple[bool, str]:
        """Register a new agent validator."""
        owner = self.get_account(owner_address)
        
        if owner.available_balance() < initial_stake:
            return False, "Owner has insufficient balance for stake"
        
        # Transfer stake from owner to agent
        owner.balance -= initial_stake
        
        agent = self.get_account(agent_address)
        agent.balance = initial_stake
        agent.staked = initial_stake
        agent.is_agent = True
        agent.owner = owner_address
        
        return True, ""
    
    def distribute_reward(
        self,
        agent_address: str,
        reward: int,
        agent_share: float = 0.1,
    ) -> Tuple[bool, str]:
        """
        Distribute block reward to agent and owner.
        
        Default: 90% to owner, 10% to agent.
        """
        agent = self.get_account(agent_address)
        
        if not agent.is_agent or agent.owner is None:
            # Not an agent, all reward goes to address
            return self.mint(agent_address, reward)
        
        owner = self.get_account(agent.owner)
        
        agent_reward = int(reward * agent_share)
        owner_reward = reward - agent_reward
        
        success, error = self.mint(agent_address, agent_reward)
        if not success:
            return False, error
            
        success, error = self.mint(agent.owner, owner_reward)
        if not success:
            return False, error
        
        return True, ""


if __name__ == "__main__":
    # Demo
    ledger = Ledger()
    
    # Register an agent
    ledger.get_account("nous:owner1").balance = 1000 * NOUS
    success, _ = ledger.register_agent(
        agent_address="nous:agent1",
        owner_address="nous:owner1", 
        initial_stake=100 * NOUS,
    )
    print(f"Registered agent: {success}")
    
    # Distribute reward
    success, _ = ledger.distribute_reward("nous:agent1", 50 * NOUS)
    print(f"Distributed reward: {success}")
    
    agent = ledger.get_account("nous:agent1")
    owner = ledger.get_account("nous:owner1")
    
    print(f"Agent balance: {agent.balance / NOUS} NOUS")
    print(f"Owner balance: {owner.balance / NOUS} NOUS")
