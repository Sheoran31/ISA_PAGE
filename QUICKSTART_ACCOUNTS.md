# ⚡ Quick Start - Multi-Account Setup

## What's New?

✨ The ISA Bot now supports **multiple Dhan and Zerodha accounts** for different users!

- You can use your Zerodha account
- Your friend can use their Dhan account
- Both get the **same trading signals** in **one Telegram chat**
- Each alert shows **which account** it's for

## Setup in 3 Steps

### 1️⃣ Run the Setup Script

```bash
python3 setup_accounts.py
```

### 2️⃣ Add Your Account

```
📋 OPTIONS:
1. Add new user
2. Add broker credentials to existing user
3. View all users and their accounts
4. Remove user
5. Exit

Enter choice (1-5): 1

Enter unique user ID (e.g., user1, yogesh, john): yogesh
Enter user name (full name): Yogesh Kumar
✅ User 'Yogesh Kumar' (yogesh) added successfully!
```

### 3️⃣ Add Your Broker Credentials

```
Enter choice (1-5): 2

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

**Repeat for your friend:**
- Run setup script again
- Choose "Add new user" 
- Enter their info
- Add their Dhan/Zerodha credentials

## Verify Setup

```bash
python3 verify_accounts.py
```

Shows you:
✅ Telegram configuration
✅ All configured accounts
✅ Which brokers are set up

## Run the Scanner

```bash
python3 scan_nifty50.py
```

Output:
```
👥 Configured accounts: Yogesh Kumar, John Doe
📊 Scanning 50 stocks...
```

## What Happens?

1. **Scan:** Checks all 50 NIFTY stocks for EMA signals
2. **Detect:** Finds breakout (BUY) or breakdown (SELL) signals
3. **Alert:** Sends to Telegram with account name
4. **Done:** Gets logged in results file

## Telegram Alert Example

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

## Get Credentials

### Zerodha
1. Go to https://kite.zerodha.com/
2. Login with your credentials
3. Find API Key in Settings → API Console
4. Generate Access Token

### Dhan
1. Go to https://app.dhan.co/
2. Login with your credentials
3. Find API credentials in Account Settings
4. Copy API Key and Access Token

## Security

⚠️ **Important:**
- Keep `accounts.json` private
- Add to `.gitignore`: `echo "accounts.json" >> .gitignore`
- Never share credentials
- Never commit to git

## Files Created

```
📁 ISA_BOT/
├── scan_nifty50.py          # Main scanner
├── setup_accounts.py        # Add accounts interactively
├── verify_accounts.py       # Check configuration
├── accounts.json            # Your accounts (auto-created)
├── accounts.example.json    # Example format
├── config/
│   └── accounts.py          # Account management module
├── MULTI_ACCOUNT_SETUP.md   # Detailed guide
└── QUICKSTART_ACCOUNTS.md   # This file
```

## Troubleshooting

### "No accounts configured"
```bash
python3 setup_accounts.py
# Add at least one user with credentials
```

### Alerts not sending?
```bash
python3 verify_accounts.py
# Check Telegram token and chat ID
```

### Wrong credentials?
```bash
# Edit accounts.json directly or
python3 setup_accounts.py
# Remove user and add again
```

## Next Steps

1. ✅ Add yourself with your account
2. ✅ Add your friend with their account
3. ✅ Run verify_accounts.py
4. ✅ Run scan_nifty50.py
5. ✅ Set up automation (optional)

## Automate (Optional)

Run scanner every hour:

```bash
# Edit crontab
crontab -e

# Add this line (market hours 9am-3pm, weekdays):
0 9-15 * * MON-FRI /usr/bin/python3 /path/to/ISA_BOT/scan_nifty50.py
```

## Questions?

See:
- `MULTI_ACCOUNT_SETUP.md` - Detailed guide
- `verify_accounts.py` - Shows your configuration
- Check .env file - Telegram settings

---

**That's it!** 🚀 You're ready to use the multi-account ISA Bot!
