# Stock Alert System — Indian Market Alerts on Telegram

A real-time alert system for Indian stocks (NSE/BSE) that monitors conditions and sends instant Telegram notifications.

## Features ✨

- **Real-time Price Monitoring**: Track Indian stocks via Zerodha API (FREE)
- **Flexible Conditions**: Set any condition (price above/below, percentage change, volume spikes, etc.)
- **Hot-Reload**: Update conditions anytime without restarting
- **Telegram Bot**: Add/remove/pause alerts via Telegram commands
- **Alert History**: View all past alerts fired
- **Market Hours Smart**: Only checks prices during market hours (9:15 AM - 3:30 PM IST, weekdays)
- **Cooldown Prevention**: Prevents spam alerts for the same condition

## Prerequisites

- Python 3.8+
- Free Zerodha account ([signup here](https://signup.zerodha.com))
- Telegram account
- Internet connection

## Quick Start

### 1. Clone/Create Project

```bash
git clone <repo> stock_alert_system
cd stock_alert_system
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Configuration

```bash
cp .env.example .env
```

Then edit `.env` with your credentials:
- Get Zerodha API keys from https://developers.kite.trade
- Get Telegram bot token from @BotFather
- Get your Telegram chat ID from @userinfobot

### 4. Run the System

```bash
python main.py
```

## File Structure

```
stock_alert_system/
├── utils/              # Logging, exceptions, utilities
├── config/             # Settings, environment variables
├── storage/            # Database and repositories
├── fetcher/            # Zerodha API integration
├── conditions/         # Condition types (price_above, etc.)
├── engine/             # Core alert evaluation logic
├── alerts/             # Telegram integration
├── bot/                # Telegram bot commands
├── scheduler/          # Job scheduling
├── main.py             # Entry point
└── requirements.txt    # Dependencies
```

## Configuration

Edit `.env`:
- `KITE_API_KEY` / `KITE_API_SECRET`: From Zerodha developers page
- `TELEGRAM_BOT_TOKEN`: From @BotFather
- `TELEGRAM_CHAT_ID`: Your personal Telegram ID
- `CHECK_INTERVAL_MINUTES`: How often to check prices (1-5 recommended)

## Telegram Commands

| Command | Usage | Example |
|---------|-------|---------|
| `/add_alert` | Add new alert | `/add_alert TCS price_above 3500` |
| `/list_alerts` | Show all alerts | `/list_alerts` |
| `/delete_alert` | Remove alert | `/delete_alert 5` |
| `/status` | System health | `/status` |
| `/pause` | Pause checking | `/pause` |
| `/resume` | Resume checking | `/resume` |
| `/history` | Recent alerts | `/history` |

## Condition Types

- `price_above`: Alert when stock price > threshold
- `price_below`: Alert when stock price < threshold
- `price_between`: Alert when price is between min and max
- `percent_change`: Alert when price moves X% from open
- `volume_spike`: Alert when volume exceeds threshold

## Example Conditions (conditions.json)

```json
{
  "global_settings": {
    "default_cooldown_minutes": 30
  },
  "alerts": [
    {
      "id": "alert_001",
      "name": "TCS Breakout",
      "symbol": "NSE:TCS",
      "type": "price_above",
      "enabled": true,
      "parameters": {
        "threshold": 3500.00
      }
    }
  ]
}
```

## Symbol Format

Always use NSE/BSE format:
- `NSE:TCS` (not just TCS)
- `NSE:RELIANCE` (not RELIANCE.NS)
- `BSE:SBIN` (for BSE stocks)

## Troubleshooting

### "Kite API connection failed"
- Check your API key and secret in .env
- Ensure internet connection is stable

### "Telegram message not sent"
- Verify bot token and chat ID in .env
- Make sure you've started the bot chat

### "Symbol not found"
- Use format `NSE:SYMBOL` not just `SYMBOL`
- Check if stock exists on NSE/BSE

### "Market hours only" warning
- System only checks during market hours by default
- Set `MARKET_HOURS_ONLY=false` in .env to check 24/7

## Architecture Phases

1. **Phase 1**: Foundation (Exceptions, Logger, Config, DB)
2. **Phase 2**: Conditions (Pluggable condition types)
3. **Phase 3**: Kite API (Price fetcher)
4. **Phase 4**: Alert Engine (Core logic)
5. **Phase 5**: Scheduler (Market-aware job runner)
6. **Phase 6**: Telegram Bot (User commands)
7. **Phase 7**: Integration (main.py)

## Logs

Logs are saved to `logs/app.log` and rotated every 10MB.

View recent logs:
```bash
tail -f logs/app.log
```

## Development

Run tests:
```bash
pytest tests/
```

Format code:
```bash
black . && ruff check . --fix
```

## License

MIT

## Support

Found a bug? Have a feature request? Open an issue!
