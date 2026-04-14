#!/usr/bin/env python3
"""
Verify that all accounts and credentials are properly configured
"""

from config.accounts import AccountManager
from pathlib import Path
import os
from dotenv import load_dotenv


def verify_telegram_config():
    """Verify Telegram configuration"""
    print("\n" + "="*60)
    print("🔐 TELEGRAM CONFIGURATION")
    print("="*60)

    env_file = Path(__file__).parent / '.env'
    load_dotenv(env_file)

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        return False

    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID not set in .env")
        return False

    print("✅ TELEGRAM_BOT_TOKEN configured")
    print(f"   Token: {token[:10]}...")
    print("✅ TELEGRAM_CHAT_ID configured")
    print(f"   Chat ID: {chat_id}")

    return True


def verify_accounts():
    """Verify user accounts and credentials"""
    print("\n" + "="*60)
    print("👥 USER ACCOUNTS & CREDENTIALS")
    print("="*60)

    manager = AccountManager()
    users = manager.list_users()

    if not users:
        print("\n❌ No user accounts configured!")
        print("   Run: python setup_accounts.py")
        return False

    print(f"\n✅ Found {len(users)} account(s):\n")

    all_valid = True
    for user_id in users:
        user = manager.get_user(user_id)
        print(f"👤 {user.name} ({user_id})")

        brokers = user.get_active_brokers()
        if not brokers:
            print("   ❌ No broker credentials configured")
            all_valid = False
        else:
            for broker in brokers:
                creds = user.get_broker(broker)
                status = "✅" if creds.is_valid() else "❌"
                print(f"   {status} {broker.upper()}")
                print(f"       User ID: {creds.user_id}")
                print(f"       API Key: {creds.api_key[:5]}...")
                print(f"       Access Token: {creds.access_token[:5]}...")

    return all_valid


def verify_environment():
    """Verify project environment"""
    print("\n" + "="*60)
    print("⚙️  PROJECT ENVIRONMENT")
    print("="*60)

    checks = {
        '.env file': Path('.env').exists(),
        'accounts.json': Path('accounts.json').exists(),
        'scan_nifty50.py': Path('scan_nifty50.py').exists(),
        'setup_accounts.py': Path('setup_accounts.py').exists(),
        'config/accounts.py': Path('config/accounts.py').exists(),
    }

    all_exist = True
    for name, exists in checks.items():
        status = "✅" if exists else "❌"
        print(f"{status} {name}")
        if not exists and 'py' in name:
            all_exist = False

    return all_exist


def print_recommendations():
    """Print recommendations based on verification"""
    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS")
    print("="*60)

    manager = AccountManager()
    users = manager.list_users()

    if not users:
        print("\n1️⃣  Add user accounts:")
        print("   python setup_accounts.py")
        print("\n2️⃣  Add Zerodha or Dhan credentials for each user")
        print("\n3️⃣  Re-run this verification script")

    else:
        print("\n✅ Your system is ready to use!")
        print("\nNext steps:")
        print("1. Run the scanner: python scan_nifty50.py")
        print("2. Set up automation (optional):")
        print("   - Edit crontab: crontab -e")
        print("   - Add hourly scan during market hours")
        print("\n3. View alerts on Telegram when signals are detected")

        # Security reminder
        print("\n🔒 Security Reminders:")
        print("   - Keep accounts.json private")
        print("   - Add to .gitignore: accounts.json")
        print("   - Never commit credentials to git")
        print("   - Rotate API keys periodically")


def main():
    print("\n" + "="*60)
    print("🔍 ISA BOT - SYSTEM VERIFICATION")
    print("="*60)

    env_ok = verify_telegram_config()
    accounts_ok = verify_accounts()
    environment_ok = verify_environment()

    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)

    status_emoji = "✅" if (env_ok and accounts_ok and environment_ok) else "⚠️"
    print(f"\n{status_emoji} Telegram Configuration: {'✅' if env_ok else '❌'}")
    print(f"{'✅' if accounts_ok else '❌'} User Accounts: {'Configured' if accounts_ok else 'Not configured'}")
    print(f"{'✅' if environment_ok else '❌'} Project Environment: {'OK' if environment_ok else 'Missing files'}")

    print_recommendations()

    if env_ok and accounts_ok:
        print("\n" + "="*60)
        print("🚀 YOU'RE ALL SET!")
        print("="*60)
        print("\nRun: python scan_nifty50.py")
        print("\nThe system will:")
        print("- Scan NIFTY 50 stocks")
        print("- Detect EMA breakout/breakdown signals")
        print("- Send alerts to Telegram for all configured accounts")
    else:
        print("\n" + "="*60)
        print("⚠️  SETUP INCOMPLETE")
        print("="*60)
        print("\nFollow recommendations above to complete setup")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Verification cancelled")
