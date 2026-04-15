#!/usr/bin/env python3
"""
🔍 ISA_BOT SETUP VERIFICATION SCRIPT
Verify that all configurations are correct and match expected values
Run this anytime to ensure everything is properly configured
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# ====================================================================
# EXPECTED CONFIGURATION (Update this if you change setup)
# ====================================================================
EXPECTED_CONFIG = {
    "BOT_NAME": "@I31saBot",
    "BOT_ID": 8799659301,
    "CHAT_ID": 7368296583,
    "TOKEN_PREFIX": "8799659301:",  # First part of token
}

# ====================================================================
# VERIFICATION FUNCTIONS
# ====================================================================

def print_header(title):
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}{title:^70}{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}\n")

def print_check(status, message):
    icon = f"{GREEN}✅{RESET}" if status else f"{RED}❌{RESET}"
    print(f"{icon} {message}")

def load_env():
    """Load .env file"""
    env_path = Path('.env')
    load_dotenv(env_path, override=True)
    return env_path

def verify_env_file():
    """Check if .env file exists and has content"""
    print_header("1️⃣ Checking .env File")

    env_path = Path('.env')

    if not env_path.exists():
        print_check(False, ".env file NOT found")
        return False

    print_check(True, f".env file exists: {env_path.absolute()}")

    content = env_path.read_text()
    if 'TELEGRAM_BOT_TOKEN' in content and 'TELEGRAM_CHAT_ID' in content:
        print_check(True, "TELEGRAM_BOT_TOKEN configured")
        print_check(True, "TELEGRAM_CHAT_ID configured")
        return True
    else:
        print_check(False, "Missing TELEGRAM configuration in .env")
        return False

def verify_credentials():
    """Verify .env credentials are loaded"""
    print_header("2️⃣ Checking Credentials Loading")

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    token_ok = token is not None and token.startswith(EXPECTED_CONFIG['TOKEN_PREFIX'])
    chat_id_ok = chat_id == str(EXPECTED_CONFIG['CHAT_ID'])

    print_check(token_ok, f"Token loaded: {token[:30]}..." if token else "Token NOT loaded")
    print_check(chat_id_ok, f"Chat ID: {chat_id}")

    return token_ok and chat_id_ok

def verify_bot_api():
    """Verify bot token is valid with Telegram API"""
    print_header("3️⃣ Verifying Bot with Telegram API")

    token = os.getenv('TELEGRAM_BOT_TOKEN')

    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if data.get('ok'):
                bot = data['result']
                bot_username = bot.get('username')
                bot_id = bot.get('id')

                username_ok = bot_username == EXPECTED_CONFIG['BOT_NAME'].replace('@', '')
                id_ok = bot_id == EXPECTED_CONFIG['BOT_ID']

                print_check(username_ok, f"Bot Name: @{bot_username}")
                print_check(id_ok, f"Bot ID: {bot_id}")

                return username_ok and id_ok
            else:
                print_check(False, f"Bot API Error: {data}")
                return False
        else:
            print_check(False, f"API Error: {response.status_code}")
            return False
    except Exception as e:
        print_check(False, f"Connection Error: {str(e)}")
        return False

def verify_message_sending():
    """Test sending a message to verify everything works"""
    print_header("4️⃣ Testing Message Sending")

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": "✅ ISA_BOT Verification Test - Everything is working!"
        }

        response = requests.post(url, json=data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print_check(True, "Test message sent successfully!")
                return True
            else:
                print_check(False, f"Message failed: {result}")
                return False
        else:
            print_check(False, f"Send error: {response.status_code}")
            return False
    except Exception as e:
        print_check(False, f"Error: {str(e)}")
        return False

def verify_accounts_config():
    """Verify accounts.json exists"""
    print_header("5️⃣ Checking accounts.json")

    accounts_path = Path('accounts.json')
    accounts_example = Path('accounts.example.json')

    if accounts_path.exists():
        print_check(True, "accounts.json exists (KEEP PRIVATE!)")
    else:
        print_check(False, "accounts.json NOT found")

    if accounts_example.exists():
        print_check(True, "accounts.example.json exists (for reference)")
    else:
        print_check(False, "accounts.example.json NOT found")

    return accounts_path.exists()

def verify_gitignore():
    """Verify .gitignore protects sensitive files"""
    print_header("6️⃣ Checking .gitignore Security")

    gitignore_path = Path('.gitignore')

    if not gitignore_path.exists():
        print_check(False, ".gitignore NOT found")
        return False

    content = gitignore_path.read_text()
    checks = {
        '.env': '.env' in content,
        'accounts.json': 'accounts.json' in content,
        '__pycache__': '__pycache__' in content,
    }

    all_ok = all(checks.values())

    for item, ok in checks.items():
        print_check(ok, f"{item} in .gitignore")

    return all_ok

def main():
    """Run all verifications"""
    print(f"\n{BOLD}{BLUE}")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "🔍 ISA_BOT SETUP VERIFICATION" + " "*23 + "║")
    print("╚" + "="*68 + "╝")
    print(f"{RESET}\n")

    # Load environment
    load_env()

    # Run all checks
    results = {
        ".env File": verify_env_file(),
        "Credentials": verify_credentials(),
        "Bot API": verify_bot_api(),
        "Message Sending": verify_message_sending(),
        "accounts.json": verify_accounts_config(),
        "Security (.gitignore)": verify_gitignore(),
    }

    # Summary
    print_header("📊 VERIFICATION SUMMARY")

    all_passed = all(results.values())

    for check_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {check_name}: {status}")

    print()

    if all_passed:
        print(f"{GREEN}{BOLD}✅ ALL CHECKS PASSED!{RESET}")
        print(f"{GREEN}🚀 ISA_BOT is ready to deploy!{RESET}")
        return 0
    else:
        print(f"{RED}{BOLD}❌ SOME CHECKS FAILED{RESET}")
        print(f"{RED}⚠️  Please fix the issues above{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
