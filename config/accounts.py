"""
Multi-account configuration and management for Dhan and Zerodha brokers
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class BrokerCredentials:
    """Credentials for a single broker account"""
    broker: str  # 'zerodha' or 'dhan'
    api_key: str
    access_token: str
    user_id: str

    def is_valid(self) -> bool:
        """Check if credentials are complete"""
        return bool(self.api_key and self.access_token and self.user_id)


@dataclass
class UserAccount:
    """User account with broker credentials"""
    name: str  # User name
    zerodha: Optional[BrokerCredentials] = None
    dhan: Optional[BrokerCredentials] = None

    def get_active_brokers(self) -> List[str]:
        """Get list of configured brokers"""
        brokers = []
        if self.zerodha and self.zerodha.is_valid():
            brokers.append('zerodha')
        if self.dhan and self.dhan.is_valid():
            brokers.append('dhan')
        return brokers

    def get_broker(self, broker_name: str) -> Optional[BrokerCredentials]:
        """Get broker credentials by name"""
        if broker_name.lower() == 'zerodha':
            return self.zerodha
        elif broker_name.lower() == 'dhan':
            return self.dhan
        return None


class AccountManager:
    """Manage multiple user accounts and their broker credentials"""

    CONFIG_FILE = Path(__file__).parent.parent / 'accounts.json'

    def __init__(self):
        self.accounts: Dict[str, UserAccount] = {}
        self.load_accounts()

    def load_accounts(self):
        """Load accounts from JSON file"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    for user_id, user_data in data.items():
                        zerodha = None
                        dhan = None

                        if user_data.get('zerodha'):
                            zc = user_data['zerodha']
                            zerodha = BrokerCredentials(
                                broker='zerodha',
                                api_key=zc.get('api_key', ''),
                                access_token=zc.get('access_token', ''),
                                user_id=zc.get('user_id', '')
                            )

                        if user_data.get('dhan'):
                            dc = user_data['dhan']
                            dhan = BrokerCredentials(
                                broker='dhan',
                                api_key=dc.get('api_key', ''),
                                access_token=dc.get('access_token', ''),
                                user_id=dc.get('user_id', '')
                            )

                        self.accounts[user_id] = UserAccount(
                            name=user_data.get('name', user_id),
                            zerodha=zerodha,
                            dhan=dhan
                        )
            except Exception as e:
                print(f"Error loading accounts: {e}")

    def save_accounts(self):
        """Save accounts to JSON file"""
        data = {}
        for user_id, account in self.accounts.items():
            account_data = {'name': account.name}

            if account.zerodha and account.zerodha.is_valid():
                account_data['zerodha'] = {
                    'api_key': account.zerodha.api_key,
                    'access_token': account.zerodha.access_token,
                    'user_id': account.zerodha.user_id
                }

            if account.dhan and account.dhan.is_valid():
                account_data['dhan'] = {
                    'api_key': account.dhan.api_key,
                    'access_token': account.dhan.access_token,
                    'user_id': account.dhan.user_id
                }

            data[user_id] = account_data

        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def add_user(self, user_id: str, name: str):
        """Add a new user"""
        self.accounts[user_id] = UserAccount(name=name)
        self.save_accounts()

    def add_broker_credentials(self, user_id: str, broker: str,
                             api_key: str, access_token: str, user_id_broker: str):
        """Add broker credentials for a user"""
        if user_id not in self.accounts:
            raise ValueError(f"User {user_id} not found")

        creds = BrokerCredentials(
            broker=broker.lower(),
            api_key=api_key,
            access_token=access_token,
            user_id=user_id_broker
        )

        if broker.lower() == 'zerodha':
            self.accounts[user_id].zerodha = creds
        elif broker.lower() == 'dhan':
            self.accounts[user_id].dhan = creds
        else:
            raise ValueError(f"Unknown broker: {broker}")

        self.save_accounts()

    def get_user(self, user_id: str) -> Optional[UserAccount]:
        """Get user account"""
        return self.accounts.get(user_id)

    def list_users(self) -> List[str]:
        """List all user IDs"""
        return list(self.accounts.keys())

    def get_all_accounts(self) -> Dict[str, UserAccount]:
        """Get all accounts"""
        return self.accounts

    def remove_user(self, user_id: str):
        """Remove a user"""
        if user_id in self.accounts:
            del self.accounts[user_id]
            self.save_accounts()
