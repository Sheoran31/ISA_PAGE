#!/usr/bin/env python3
"""
Interactive setup script for adding user accounts and broker credentials
"""

from config.accounts import AccountManager
import getpass
import sys


def main():
    print("\n" + "="*60)
    print("🔐 ISA BOT - ACCOUNT SETUP")
    print("="*60)

    manager = AccountManager()

    while True:
        print("\n📋 OPTIONS:")
        print("1. Add new user")
        print("2. Add broker credentials to existing user")
        print("3. View all users and their accounts")
        print("4. Remove user")
        print("5. Exit")

        choice = input("\nEnter choice (1-5): ").strip()

        if choice == '1':
            add_user(manager)

        elif choice == '2':
            add_broker_credentials(manager)

        elif choice == '3':
            view_users(manager)

        elif choice == '4':
            remove_user(manager)

        elif choice == '5':
            print("\n✅ Setup complete! Exiting...\n")
            break

        else:
            print("❌ Invalid choice. Try again.")


def add_user(manager: AccountManager):
    """Add a new user"""
    print("\n" + "-"*60)
    print("➕ ADD NEW USER")
    print("-"*60)

    user_id = input("Enter unique user ID (e.g., user1, yogesh, john): ").strip()
    if not user_id:
        print("❌ User ID cannot be empty")
        return

    if user_id in manager.list_users():
        print(f"❌ User '{user_id}' already exists")
        return

    name = input("Enter user name (full name): ").strip()
    if not name:
        print("❌ User name cannot be empty")
        return

    manager.add_user(user_id, name)
    print(f"\n✅ User '{name}' ({user_id}) added successfully!")
    print(f"   Next: Add Zerodha/Dhan credentials for this user")


def add_broker_credentials(manager: AccountManager):
    """Add broker credentials to a user"""
    print("\n" + "-"*60)
    print("🏦 ADD BROKER CREDENTIALS")
    print("-"*60)

    users = manager.list_users()
    if not users:
        print("❌ No users found. Add a user first.")
        return

    print("\n📌 Available users:")
    for i, user_id in enumerate(users, 1):
        user = manager.get_user(user_id)
        brokers = ", ".join(user.get_active_brokers()) or "None"
        print(f"   {i}. {user_id} ({user.name}) - Brokers: {brokers}")

    user_choice = input("\nEnter user ID or number: ").strip()

    # Handle both number and user_id input
    try:
        idx = int(user_choice) - 1
        if 0 <= idx < len(users):
            user_id = users[idx]
        else:
            user_id = user_choice
    except ValueError:
        user_id = user_choice

    if user_id not in users:
        print(f"❌ User '{user_id}' not found")
        return

    user = manager.get_user(user_id)
    print(f"\n👤 Selected: {user.name} ({user_id})")

    broker = input("\nChoose broker (zerodha/dhan): ").strip().lower()
    if broker not in ['zerodha', 'dhan']:
        print("❌ Invalid broker. Choose 'zerodha' or 'dhan'")
        return

    print(f"\n🔑 Enter {broker.upper()} credentials:")
    api_key = input(f"API Key: ").strip()
    access_token = input(f"Access Token: ").strip()
    user_id_broker = input(f"User ID (on {broker}): ").strip()

    if not all([api_key, access_token, user_id_broker]):
        print("❌ All fields are required")
        return

    manager.add_broker_credentials(
        user_id=user_id,
        broker=broker,
        api_key=api_key,
        access_token=access_token,
        user_id_broker=user_id_broker
    )

    print(f"\n✅ {broker.upper()} credentials added for {user.name}!")


def view_users(manager: AccountManager):
    """View all users and their accounts"""
    print("\n" + "-"*60)
    print("👥 ALL USERS AND ACCOUNTS")
    print("-"*60)

    accounts = manager.get_all_accounts()
    if not accounts:
        print("\n❌ No users configured yet")
        return

    for user_id, account in accounts.items():
        print(f"\n👤 {account.name} ({user_id})")
        print("   Brokers:")

        if account.zerodha and account.zerodha.is_valid():
            print(f"     ✅ Zerodha")
            print(f"        User ID: {account.zerodha.user_id}")
            print(f"        API Key: {account.zerodha.api_key[:5]}...")

        if account.dhan and account.dhan.is_valid():
            print(f"     ✅ Dhan")
            print(f"        User ID: {account.dhan.user_id}")
            print(f"        API Key: {account.dhan.api_key[:5]}...")

        if not account.get_active_brokers():
            print(f"     ⚠️  No broker credentials configured")


def remove_user(manager: AccountManager):
    """Remove a user"""
    print("\n" + "-"*60)
    print("🗑️  REMOVE USER")
    print("-"*60)

    users = manager.list_users()
    if not users:
        print("❌ No users found")
        return

    print("\n📌 Available users:")
    for i, user_id in enumerate(users, 1):
        user = manager.get_user(user_id)
        print(f"   {i}. {user_id} ({user.name})")

    user_choice = input("\nEnter user ID or number to remove: ").strip()

    # Handle both number and user_id input
    try:
        idx = int(user_choice) - 1
        if 0 <= idx < len(users):
            user_id = users[idx]
        else:
            user_id = user_choice
    except ValueError:
        user_id = user_choice

    if user_id not in users:
        print(f"❌ User '{user_id}' not found")
        return

    user = manager.get_user(user_id)
    confirm = input(f"\n⚠️  Are you sure you want to remove '{user.name}'? (yes/no): ").strip().lower()

    if confirm == 'yes':
        manager.remove_user(user_id)
        print(f"✅ User '{user.name}' removed")
    else:
        print("❌ Cancelled")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
