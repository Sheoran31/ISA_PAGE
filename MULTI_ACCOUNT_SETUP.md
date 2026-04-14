# 🔐 Multi-Account Setup Guide

This guide explains how to add Dhan and Zerodha accounts for multiple users to the ISA Bot.

## Quick Start

### Step 1: Run the Setup Script

```bash
python setup_accounts.py
```

This launches an interactive menu where you can:
- ➕ Add new users
- 🏦 Add Zerodha/Dhan credentials
- 👥 View all configured accounts
- 🗑️ Remove users

### Step 2: Add Your First User

```
Option 1: Add new user

Enter unique user ID (e.g., user1, yogesh, john): yogesh
Enter user name (full name): Yogesh Kumar
✅ User 'Yogesh Kumar' (yogesh) added successfully!
```

**Tips for User ID:**
- Use simple, lowercase identifiers
- Examples: `yogesh`, `user1`, `person2`, `john`
- Must be unique

### Step 3: Add Broker Credentials

Choose Dhan or Zerodha (or both):

```
Option 2: Add broker credentials to existing user

📌 Available users:
   1. yogesh (Yogesh Kumar) - Brokers: None

Enter user ID or number: 1
Choose broker (zerodha/dhan): zerodha

🔑 Enter ZERODHA credentials:
API Key: e1w60c1ims6d8cun
Access Token: n628jg3kilbp3aoys2w5cqcvqiazjnuz
User ID (on zerodha): UUC792

✅ Zerodha credentials added for Yogesh Kumar!
```

To add both brokers, repeat step 3 and choose `dhan` instead.

## Account Configuration File

Your accounts are saved in `accounts.json` in this format:

```json
{
  "yogesh": {
    "name": "Yogesh Kumar",
    "zerodha": {
      "api_key": "e1w60c1ims6d8cun",
      "access_token": "n628jg3kilbp3aoys2w5cqcvqiazjnuz",
      "user_id": "UUC792"
    },
    "dhan": {
      "api_key": "your_dhan_key",
      "access_token": "your_dhan_token",
      "user_id": "your_dhan_id"
    }
  },
  "john": {
    "name": "John Doe",
    "dhan": {
      "api_key": "john_dhan_key",
      "access_token": "john_dhan_token",
      "user_id": "john_dhan_id"
    }
  }
}
```

⚠️ **IMPORTANT:** Keep `accounts.json` secure! Add it to `.gitignore`:

```bash
echo "accounts.json" >> .gitignore
```

## How It Works

### Signal Detection

1. Scanner runs and detects EMA breakout/breakdown signals
2. **Same signals for all users** (identical trading logic)
3. Each signal is announced with account information

### Alert Format

Each Telegram alert includes the account name:

```
🟢 SIGNAL DETECTED

Stock: RELIANCE.NS
Signal: BREAKOUT (BUY)
Price: ₹2,850.50
EMA Range: ₹2,800.00 - ₹2,900.00
Spread: 3.57%
Account: Yogesh Kumar (yogesh)

⏰ 2026-04-14 10:30 IST
```

### Running the Scanner

Once accounts are configured:

```bash
python scan_nifty50.py
```

Output shows which accounts are active:

```
👥 Configured accounts: Yogesh Kumar, John Doe
📊 Scanning 50 stocks...
```

## Common Tasks

### View All Configured Accounts

```bash
python setup_accounts.py
# Choose Option 3: View all users and their accounts
```

### Add Dhan Account for Another Person

```bash
python setup_accounts.py
# Choose Option 1: Add new user
# Enter their user ID and name
# Choose Option 2: Add broker credentials
# Select their account and enter Dhan credentials
```

### Remove a User

```bash
python setup_accounts.py
# Choose Option 4: Remove user
# Enter user ID to remove
```

### Update Credentials

Currently, to update credentials:
1. Edit `accounts.json` directly (advanced users), or
2. Remove user and re-add with correct credentials

## Security Best Practices

✅ **DO:**
- Keep `accounts.json` private (add to `.gitignore`)
- Use strong API keys and tokens
- Rotate credentials periodically
- Never share `accounts.json` file

❌ **DON'T:**
- Commit `accounts.json` to git
- Share credentials via chat/email
- Use test credentials in production
- Log sensitive data

## Troubleshooting

### Error: "No accounts configured"

```
⚠️ No accounts configured!
   Run: python setup_accounts.py
```

**Solution:** Run the setup script and add at least one user with broker credentials.

### Error: "User not found"

Check available users:

```bash
python setup_accounts.py
# Option 3: View all users
```

### Alerts not sending

1. Check Telegram bot token in `.env`
2. Verify chat ID is correct
3. Test with: `python scan_nifty50.py`

## Integration with Automation

To run scanner automatically every hour:

```bash
# Add to crontab (edit with: crontab -e)
0 9-15 * * MON-FRI /usr/bin/python3 /path/to/scan_nifty50.py
```

This runs 9am to 3pm on weekdays (market hours).

## API Requirements

### Zerodha (Kite API)
- API Key (client_id)
- Access Token (required after login)
- User ID

### Dhan
- API Key
- Access Token  
- User ID / Client ID

Get these from your broker's dashboard:
- **Zerodha:** https://kite.zerodha.com/
- **Dhan:** https://app.dhan.co/

## Support

For issues or questions, check:
1. This guide's troubleshooting section
2. Broker documentation
3. Project README
