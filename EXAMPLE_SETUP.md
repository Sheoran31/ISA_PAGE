# 📝 Complete Setup Example

This shows a step-by-step example of setting up two traders with the multi-account system.

## Scenario

- **Trader 1:** Yogesh Kumar (You) - Using Zerodha
- **Trader 2:** John Doe (Friend) - Using Dhan
- **Telegram Chat:** Same chat for both, with account labels

## Step 1: Run Setup Script

```bash
$ python3 setup_accounts.py

============================================================
🔐 ISA BOT - ACCOUNT SETUP
============================================================

📋 OPTIONS:
1. Add new user
2. Add broker credentials to existing user
3. View all users and their accounts
4. Remove user
5. Exit

Enter choice (1-5): 1
```

## Step 2: Add First User (Yogesh)

```
────────────────────────────────────────────────────────────
➕ ADD NEW USER
────────────────────────────────────────────────────────────

Enter unique user ID (e.g., user1, yogesh, john): yogesh
Enter user name (full name): Yogesh Kumar

✅ User 'Yogesh Kumar' (yogesh) added successfully!
   Next: Add Zerodha/Dhan credentials for this user
```

## Step 3: Add Zerodha Credentials for Yogesh

```
📋 OPTIONS:
1. Add new user
2. Add broker credentials to existing user
3. View all users and their accounts
4. Remove user
5. Exit

Enter choice (1-5): 2

────────────────────────────────────────────────────────────
🏦 ADD BROKER CREDENTIALS
────────────────────────────────────────────────────────────

📌 Available users:
   1. yogesh (Yogesh Kumar) - Brokers: None

Enter user ID or number: 1

👤 Selected: Yogesh Kumar (yogesh)

Choose broker (zerodha/dhan): zerodha

🔑 Enter ZERODHA credentials:
API Key: e1w60c1ims6d8cun
Access Token: n628jg3kilbp3aoys2w5cqcvqiazjnuz
User ID (on zerodha): UUC792

✅ Zerodha credentials added for Yogesh Kumar!
```

## Step 4: Add Second User (John)

```
📋 OPTIONS:
1. Add new user
2. Add broker credentials to existing user
3. View all users and their accounts
4. Remove user
5. Exit

Enter choice (1-5): 1

────────────────────────────────────────────────────────────
➕ ADD NEW USER
────────────────────────────────────────────────────────────

Enter unique user ID (e.g., user1, yogesh, john): john
Enter user name (full name): John Doe

✅ User 'John Doe' (john) added successfully!
   Next: Add Zerodha/Dhan credentials for this user
```

## Step 5: Add Dhan Credentials for John

```
📋 OPTIONS:
1. Add new user
2. Add broker credentials to existing user
3. View all users and their accounts
4. Remove user
5. Exit

Enter choice (1-5): 2

────────────────────────────────────────────────────────────
🏦 ADD BROKER CREDENTIALS
────────────────────────────────────────────────────────────

📌 Available users:
   1. yogesh (Yogesh Kumar) - Brokers: zerodha
   2. john (John Doe) - Brokers: None

Enter user ID or number: 2

👤 Selected: John Doe (john)

Choose broker (zerodha/dhan): dhan

🔑 Enter DHAN credentials:
API Key: john_dhan_api_key_123
Access Token: john_dhan_token_xyz
User ID (on dhan): john_dhan_client_id

✅ Dhan credentials added for John Doe!
```

## Step 6: View All Configured Accounts

```
📋 OPTIONS:
1. Add new user
2. Add broker credentials to existing user
3. View all users and their accounts
4. Remove user
5. Exit

Enter choice (1-5): 3

────────────────────────────────────────────────────────────
👥 ALL USERS AND ACCOUNTS
────────────────────────────────────────────────────────────

👤 Yogesh Kumar (yogesh)
   Brokers:
     ✅ Zerodha
        User ID: UUC792
        API Key: e1w60...

👤 John Doe (john)
   Brokers:
     ✅ Dhan
        User ID: john_dhan_client_id
        API Key: john_...
```

## Step 7: Verify Configuration

```bash
$ python3 verify_accounts.py

============================================================
🔍 ISA BOT - SYSTEM VERIFICATION
============================================================

============================================================
🔐 TELEGRAM CONFIGURATION
============================================================
✅ TELEGRAM_BOT_TOKEN configured
   Token: 8592539764...
✅ TELEGRAM_CHAT_ID configured
   Chat ID: 7368296583

============================================================
👥 USER ACCOUNTS & CREDENTIALS
============================================================

✅ Found 2 account(s):

👤 Yogesh Kumar (yogesh)
   ✅ zerodha
       User ID: UUC792
       API Key: e1w60...
       Access Token: n6282...

👤 John Doe (john)
   ✅ dhan
       User ID: john_dhan_client_id
       API Key: john_...
       Access Token: john_...

============================================================
⚙️  PROJECT ENVIRONMENT
============================================================
✅ .env file
✅ accounts.json
✅ scan_nifty50.py
✅ setup_accounts.py
✅ config/accounts.py

============================================================
📊 VERIFICATION SUMMARY
============================================================

✅ Telegram Configuration: ✅
✅ User Accounts: Configured
✅ Project Environment: OK

============================================================
💡 RECOMMENDATIONS
============================================================

✅ Your system is ready to use!

Next steps:
1. Run the scanner: python3 scan_nifty50.py
2. Set up automation (optional):
   - Edit crontab: crontab -e
   - Add hourly scan during market hours
3. View alerts on Telegram when signals are detected

🔒 Security Reminders:
   - Keep accounts.json private
   - Add to .gitignore: accounts.json
   - Never commit credentials to git
   - Rotate API keys periodically

============================================================
🚀 YOU'RE ALL SET!
============================================================

Run: python3 scan_nifty50.py

The system will:
- Scan NIFTY 50 stocks
- Detect EMA breakout/breakdown signals
- Send alerts to Telegram for all configured accounts
```

## Step 8: Run the Scanner

```bash
$ python3 scan_nifty50.py

====================================================================================================
🚀 NIFTY 50 EMA BREAKOUT/BREAKDOWN SCANNER
====================================================================================================

👥 Configured accounts: Yogesh Kumar, John Doe
📊 Scanning 50 stocks...

[1/50] Scanning TCS.NS... ➖ No signal
[2/50] Scanning RELIANCE.NS... ✅ BREAKOUT DETECTED!
[3/50] Scanning HDFCBANK.NS... ➖ No signal
[4/50] Scanning INFY.NS... ⚠️ BREAKDOWN DETECTED!
...
[50/50] Scanning GMRINFRA.NS... ➖ No signal

====================================================================================================
📋 SCAN RESULTS
====================================================================================================

✅ BREAKOUT SIGNALS (BUY) - 2 stocks:

1. RELIANCE.NS
   Close: ₹2,850.50
   EMA Range: ₹2,800.00 - ₹2,900.00
   Spread: 3.57%
   Status: Price ABOVE all EMAs 🟢

2. TCS.NS
   Close: ₹3,250.25
   EMA Range: ₹3,150.00 - ₹3,200.00
   Spread: 1.59%
   Status: Price ABOVE all EMAs 🟢


🔴 BREAKDOWN SIGNALS (SELL) - 1 stocks:

1. INFY.NS
   Close: ₹1,580.50
   EMA Range: ₹1,600.00 - ₹1,650.00
   Spread: 3.13%
   Status: Price BELOW all EMAs 🔴


====================================================================================================
📊 SUMMARY
====================================================================================================
Total Scanned: 50
Breakout (BUY): 2 🟢
Breakdown (SELL): 1 🔴
No Signal: 46
Errors: 0
====================================================================================================

📄 Results saved to: NIFTY50_SCAN_RESULTS.txt
```

## Step 9: Check Telegram Alerts

You and John both receive alerts in the same Telegram chat:

### Alert 1 - RELIANCE Breakout
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

### Alert 2 - RELIANCE Breakout (for John)
```
🟢 SIGNAL DETECTED

Stock: RELIANCE.NS
Signal: BREAKOUT (BUY)
Price: ₹2,850.50
EMA Range: ₹2,800.00 - ₹2,900.00
Spread: 3.57%
Account: John Doe (john)

⏰ 2026-04-14 10:30 IST
```

### Alert 3 - INFY Breakdown
```
🔴 SIGNAL DETECTED

Stock: INFY.NS
Signal: BREAKDOWN (SELL)
Price: ₹1,580.50
EMA Range: ₹1,600.00 - ₹1,650.00
Spread: 3.13%
Account: Yogesh Kumar (yogesh)

⏰ 2026-04-14 10:32 IST
```

### Alert 4 - INFY Breakdown (for John)
```
🔴 SIGNAL DETECTED

Stock: INFY.NS
Signal: BREAKDOWN (SELL)
Price: ₹1,580.50
EMA Range: ₹1,600.00 - ₹1,650.00
Spread: 3.13%
Account: John Doe (john)

⏰ 2026-04-14 10:32 IST
```

## Result: accounts.json File

After setup, `accounts.json` contains:

```json
{
  "yogesh": {
    "name": "Yogesh Kumar",
    "zerodha": {
      "api_key": "e1w60c1ims6d8cun",
      "access_token": "n628jg3kilbp3aoys2w5cqcvqiazjnuz",
      "user_id": "UUC792"
    },
    "dhan": null
  },
  "john": {
    "name": "John Doe",
    "zerodha": null,
    "dhan": {
      "api_key": "john_dhan_api_key_123",
      "access_token": "john_dhan_token_xyz",
      "user_id": "john_dhan_client_id"
    }
  }
}
```

## Key Observations

✅ **Same Signals**
- Both Yogesh and John see RELIANCE and INFY signals
- No conflicts or different rules

✅ **Account Labels**
- Each alert shows which account it's for
- Easy to track trades per person

✅ **One Chat**
- 4 alerts in one Telegram chat
- 2 stocks × 2 accounts = 4 alerts per signal

✅ **Flexible Setup**
- Yogesh uses Zerodha
- John uses Dhan
- Can use any combination

✅ **Easy Management**
- Just run `python3 setup_accounts.py` to add/remove
- All accounts stored securely in `accounts.json`

## Next Steps

1. ✅ **Setup** - Done! Both accounts configured
2. ✅ **Verify** - Done! System verified and ready
3. ✅ **Test** - Done! Received signals
4. **Automate** (Optional) - Set up hourly runs via cron
5. **Monitor** - Watch Telegram for signals

## Automate (Optional)

To run scanner every hour:

```bash
# Edit crontab
crontab -e

# Add this line (9am-3pm, weekdays):
0 9-15 * * MON-FRI /usr/bin/python3 /path/to/ISA_BOT/scan_nifty50.py

# Save and exit
```

Now the system runs automatically! 🚀

---

This example shows how simple it is to:
- Add multiple users
- Use different brokers
- Get same signals
- Receive labeled alerts
- Scale to many traders

**That's it!** Your multi-account system is ready to use.
