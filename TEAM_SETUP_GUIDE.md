# 🚀 Team Setup Guide - ISA_BOT

नई team member को ISA_BOT project सेटअप करने के लिए ये guide follow करना चाहिए।

---

## Step 1: Project Clone करो

```bash
git clone https://github.com/Sheoran31/ISA_PAGE.git ISA_BOT
cd ISA_BOT
```

---

## Step 2: Virtual Environment Setup करो

### Mac/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

---

## Step 3: Dependencies Install करो

```bash
pip install -r requirements.txt
```

---

## Step 4: Environment Variables Setup करो

```bash
cp .env.example .env
```

अब `.env` file को edit करो अपने credentials के साथ:

```bash
nano .env  # or use any text editor
```

### Telegram Setup:
1. **Telegram Bot Token** लेना है:
   - Telegram में `@BotFather` को message करो
   - `/newbot` command दो
   - Bot name डालो (e.g., "ISA_Bot_Yogesh")
   - Bot username डालो (e.g., "ISA_Bot_Yogesh_bot")
   - Token copy करो → `.env` में `TELEGRAM_BOT_TOKEN` में paste करो

2. **Telegram Chat ID** लेना है:
   - `@userinfobot` को message करो
   - Chat ID copy करो → `.env` में `TELEGRAM_CHAT_ID` में paste करो

### Zerodha Setup (Optional):
अगर Zerodha से trade करना है:
1. https://developers.kite.trade पर account बनाओ
2. API Key और Secret generate करो
3. `.env` में ये fields fill करो:
   - `ZERODHA_ENABLED=true`
   - `ZERODHA_API_KEY=your_key_here`
   - `ZERODHA_ACCESS_TOKEN=your_token_here`
   - `ZERODHA_USER_ID=your_user_id_here`

### Dhan Setup (Optional):
अगर Dhan से trade करना है:
1. https://dhan.co/developers पर account बनाओ
2. API Key और Access Token generate करो
3. `.env` में ये fields fill करो:
   - `DHAN_ENABLED=true`
   - `DHAN_API_KEY=your_key_here`
   - `DHAN_ACCESS_TOKEN=your_token_here`
   - `DHAN_USER_ID=your_user_id_here`

---

## Step 5: Accounts Configuration (Multi-Account)

अगर multiple accounts/brokers use करने हैं:

```bash
cp accounts.example.json accounts.json
```

अब `accounts.json` को edit करो:

```json
{
  "yogesh": {
    "name": "Yogesh Kumar",
    "zerodha": {
      "api_key": "your_zerodha_api_key",
      "access_token": "your_zerodha_access_token",
      "user_id": "your_zerodha_user_id"
    },
    "dhan": {
      "api_key": "your_dhan_api_key",
      "access_token": "your_dhan_access_token",
      "user_id": "your_dhan_user_id"
    }
  }
}
```

---

## Step 6: Project चलाओ

```bash
python main.py
```

Terminal में देखो - system काम कर रहा है या error दे रहा है।

---

## ⚠️ IMPORTANT - Security Rules

1. **`.env` file को कभी commit मत करो!**
   - File already `.gitignore` में है
   - लेकिन accidentally push न हो जाए इसका ध्यान रखो

2. **`accounts.json` को कभी commit मत करो!**
   - Personal credentials हैं

3. **API Keys कहीं share मत करो**
   - Telegram token
   - Zerodha keys
   - Dhan keys
   - ये सभी secret हैं

4. **अगर accidentally push हो गया तो:**
   - तुरंत सभी API tokens/keys को rotate करो
   - Dhan और Zerodha account से new token generate करो
   - Telegram बॉट को delete करके नया बॉट बनाओ

---

## 🧪 Verify Setup

System properly setup है या नहीं check करने के लिए:

```bash
python verify_accounts.py
```

या

```bash
python setup_accounts.py
```

---

## 📝 Logs देखो

कोई issue आए तो logs देखो:

```bash
tail -f logs/app.log
```

---

## ❓ Common Issues

### "ModuleNotFoundError: No module named 'zerodha'"
```bash
pip install -r requirements.txt
```

### "Telegram message not sent"
- Bot token और Chat ID सही हैं confirm करो
- `@your_bot_name` को message भेजो pehle

### "Zerodha connection failed"
- API key और secret सही हैं
- Zerodha developers page से verify करो

### "Dhan API error"
- Access token expire हो सकता है
- Dhan account से नया token generate करो
- `.env` में update करो

---

## ✅ All Set!

अगर सब कुछ काम कर गया तो:
- ✅ System चल रहा है
- ✅ Telegram से messages मिल रहे हैं
- ✅ Alerts properly trigger हो रहे हैं

Happy Trading! 🎉

---

**Questions?** Reach out to Yogesh (@yogeshsheoran.131@gmail.com)
