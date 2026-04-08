#!/usr/bin/env python3
"""
Debug Telegram Issues - Find and Fix Problems
"""

import sys
import requests
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils.logger import logger

def main():
    logger.info("=" * 80)
    logger.info("TELEGRAM DEBUG - FIND ISSUES")
    logger.info("=" * 80)

    # Check 1: Credentials loaded?
    logger.info("\n1️⃣  CHECKING CREDENTIALS:")
    logger.info("-" * 80)

    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN is EMPTY or NOT SET in .env")
        return 1

    if not TELEGRAM_CHAT_ID:
        logger.error("❌ TELEGRAM_CHAT_ID is EMPTY or NOT SET in .env")
        return 1

    logger.info(f"✅ BOT TOKEN found: {TELEGRAM_BOT_TOKEN[:20]}...")
    logger.info(f"✅ CHAT ID found: {TELEGRAM_CHAT_ID}")

    # Check 2: Get Bot Info
    logger.info("\n2️⃣  CHECKING BOT INFO:")
    logger.info("-" * 80)

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot = bot_info['result']
                logger.info(f"✅ Bot Name: @{bot['username']}")
                logger.info(f"✅ Bot ID: {bot['id']}")
                logger.info(f"✅ Bot is VALID and WORKING")
            else:
                logger.error(f"❌ Bot error: {bot_info}")
                return 1
        else:
            logger.error(f"❌ Failed to get bot info: {response.text}")
            return 1
    except Exception as e:
        logger.error(f"❌ Cannot connect to Telegram API: {e}")
        return 1

    # Check 3: Get Recent Messages
    logger.info("\n3️⃣  CHECKING RECENT MESSAGES:")
    logger.info("-" * 80)

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            updates = response.json()
            if updates.get('ok'):
                messages = updates.get('result', [])

                if messages:
                    logger.info(f"✅ Found {len(messages)} recent message(s)")

                    for msg in messages[-3:]:  # Show last 3
                        if 'message' in msg:
                            sender_id = msg['message']['from']['id']
                            username = msg['message']['from'].get('username', 'N/A')
                            text = msg['message'].get('text', 'N/A')[:50]

                            logger.info(f"\n   From: {username} (ID: {sender_id})")
                            logger.info(f"   Text: {text}")
                            logger.info(f"   ⚠️  Your CHAT_ID should be: {sender_id}")
                else:
                    logger.warning("⚠️  No messages found")
                    logger.info("   Send a message to your bot and try again")
            else:
                logger.error(f"❌ API error: {updates}")
                return 1
        else:
            logger.error(f"❌ Failed to get updates: {response.text}")
            return 1
    except Exception as e:
        logger.error(f"❌ Cannot get updates: {e}")
        return 1

    # Check 4: Send Test Message
    logger.info("\n4️⃣  SENDING TEST MESSAGE:")
    logger.info("-" * 80)

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": "✅ Test message from Stock Alert System\n🎉 If you see this, Telegram is working!",
            "parse_mode": "HTML"
        }

        logger.info(f"Sending to Chat ID: {TELEGRAM_CHAT_ID}...")
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info("✅ MESSAGE SENT SUCCESSFULLY!")
                logger.info("   Check your Telegram now!")
            else:
                error = result.get('description', 'Unknown error')
                logger.error(f"❌ Telegram rejected message: {error}")

                # Common error - wrong chat ID
                if 'chat not found' in error.lower() or 'invalid user_id' in error.lower():
                    logger.error("\n⚠️  PROBLEM FOUND: WRONG CHAT ID!")
                    logger.info("\nFIX:")
                    logger.info("1. Send a message to your bot")
                    logger.info("2. Run: python3 debug_telegram.py")
                    logger.info("3. Look for 'Your CHAT_ID should be: XXXXX'")
                    logger.info("4. Update .env with that ID")

                return 1
        else:
            logger.error(f"❌ HTTP Error {response.status_code}: {response.text}")
            return 1
    except Exception as e:
        logger.error(f"❌ Cannot send message: {e}")
        return 1

    logger.info("\n" + "=" * 80)
    logger.info("✅ ALL CHECKS PASSED - TELEGRAM IS WORKING!")
    logger.info("=" * 80)

    return 0

if __name__ == '__main__':
    sys.exit(main())
