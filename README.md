# 🚀 Binance Trading Bot

A professional, automated trading bot for Binance Futures (USDT-M & USDC-M) with ATR-based TP/SL management, modern web interface, and comprehensive position management.

## ✨ Features

### Trading Features
- ✅ **Binance Futures Integration** - Full support for USDT-M and USDC-M perpetual contracts
- ✅ **30 Trading Pairs** - 15 USDT pairs + 15 USDC pairs
- ✅ **ATR-Based TP/SL** - Dynamic Take Profit and Stop Loss using 1-hour ATR calculation
- ✅ **Webhook Trading** - Receive signals from TradingView or other platforms
- ✅ **Position Management** - Automatic position switching, duplicate prevention
- ✅ **Risk Management** - Configurable leverage, order size, max positions
- ✅ **Telegram Notifications** - Real-time trade alerts

### Supported Coins

**USDT-M Perpetual (15 coins):**
- BTC, ETH, XRP, ADA, DOT, XLM, IMX, DOGE, INJ, LDO, ARB, UNI, SOL, BNB, FET

**USDC-M Perpetual (15 coins):**
- BTC, ETH, SOL, AAVE, BCH, XRP, ADA, AVAX, LINK, ARB, UNI, CRV, TIA, BNB, FIL

### Technical Features
- 🎨 **Modern UI** - Beautiful, responsive web interface with dark mode
- 🔒 **Secure** - User authentication, encrypted passwords
- 📊 **Real-time Dashboard** - Live positions, PnL tracking
- ⚙️ **Per-Coin Configuration** - Individual settings for each trading pair
- 🔄 **Auto-refresh** - Dashboard updates every 10 seconds
- 📈 **Trade History** - Complete trade log with PnL analysis
- 🛡️ **Position Validation** - Prevents duplicate orders and conflicts

## 📋 Requirements

- Python 3.8+
- Binance Account with Futures API access
- Ubuntu 20.04+ (for EC2 deployment)
- Telegram Bot (optional, for notifications)

## 🔧 Installation

### Local Development

1. **Clone/Navigate to the project:**
```bash
cd d:\projects\tony\tony_binance_bot
```

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**

Windows:
```bash
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Run the application:**
```bash
python app.py
```

6. **Access the dashboard:**
```
http://localhost:5001
Default login: admin / admin
```

### EC2 Deployment

1. **Upload files to EC2:**
```bash
scp -r * ubuntu@YOUR_EC2_IP:/home/ubuntu/binance_bot/
```

2. **Connect to EC2:**
```bash
ssh ubuntu@YOUR_EC2_IP
```

3. **Run deployment script:**
```bash
cd /home/ubuntu/binance_bot
chmod +x deploy_to_ec2.sh
./deploy_to_ec2.sh
```

4. **Access the bot:**
```
http://YOUR_EC2_IP
```

## ⚙️ Configuration

### Initial Setup

1. **Login to the dashboard** (admin/admin)
2. **Go to Settings**
3. **Configure API Keys:**
   - Binance API Key
   - Binance Secret Key
   - Telegram Bot Token (optional)
   - Telegram Chat ID (optional)

### Global Settings

- **Leverage:** Default leverage for all positions (1-125x)
- **Order Size (%):** Percentage of balance per trade
- **Max Daily Trades:** Maximum trades per day
- **Max Open Positions:** Maximum concurrent positions
- **Auto Position Switch:** Automatically close opposite positions
- **Long/Short Only Mode:** Restrict trading direction

### Per-Coin Settings

Each of the 30 coins can be configured individually:

- **ATR Period:** Period for ATR calculation (default: 14)
- **TP Multiplier:** Take Profit = Entry ± (ATR × Multiplier)
- **SL Multiplier:** Stop Loss = Entry ∓ (ATR × Multiplier)
- **Order Size (%):** Coin-specific position size
- **Leverage:** Coin-specific leverage
- **Enable/Disable Trading:** Toggle per coin

### ATR Calculation

The bot uses **1-hour candlesticks** for ATR calculation:
- Period: Configurable per coin (default 14)
- TP/SL: Dynamically calculated based on current volatility
- Updates: Real-time before each trade

## 📡 Webhook Format

Send trading signals to: `http://YOUR_IP/webhook`

### Webhook Payload

```json
{
  "signal": "BTCUSDT/long/open"
}
```

or

```json
{
  "message": "ETHUSDC/short/close"
}
```

### Signal Format

```
SYMBOL/DIRECTION/ACTION
```

- **SYMBOL:** BTCUSDT, ETHUSDC, etc.
- **DIRECTION:** long or short
- **ACTION:** open or close

### Examples

```
BTCUSDT/long/open     → Open long position on BTC/USDT
ETHUSDC/short/open    → Open short position on ETH/USDC
SOLUSDT/long/close    → Close long position on SOL/USDT
```

## 🎨 User Interface

### Dashboard
- Account balance (USDT & USDC)
- Unrealized PnL
- Active positions count
- Position cards with live PnL
- Auto-refresh every 10 seconds

### Settings
- Organized tabs: General, USDT Coins, USDC Coins
- 30 individual coin configurations
- Toggle switches for easy enable/disable
- Real-time validation

### History
- Complete trade log
- Realized PnL tracking
- Trade statistics
- Filterable table

## 🔐 Security

- Flask-Login authentication
- Password hashing with Werkzeug
- API keys stored securely
- HTTPS support via Nginx
- UFW firewall configuration

## 📊 Position Management

### Duplicate Prevention
- 5-second cooldown between same orders
- Validates existing positions before opening
- Prevents conflicting positions

### Auto Position Switch
- Automatically closes opposite position when enabled
- Atomic rollback on failure
- Detailed logging

### TP/SL Management
- Single TP/SL per position
- ATR-based dynamic levels
- Automatic order cleanup

## 🛠️ Service Management

### Start/Stop Service
```bash
sudo systemctl start binance_bot
sudo systemctl stop binance_bot
sudo systemctl restart binance_bot
```

### View Logs
```bash
sudo journalctl -u binance_bot -f
```

or

```bash
tail -f logs/app.log
```

### Check Status
```bash
sudo systemctl status binance_bot
```

## 📁 Project Structure

```
tony_binance_bot/
├── app.py                      # Main Flask application
├── binance_handler.py          # Binance API integration
├── models.py                   # Data models (User, Config, Position)
├── tp_sl_manager.py           # TP/SL calculation logic
├── coin_config_manager.py     # Per-coin configuration
├── position_validator.py      # Position validation & duplicate prevention
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore rules
├── deploy_to_ec2.sh          # EC2 deployment script
├── README.md                 # This file
├── data/
│   ├── config.json           # Bot configuration
│   ├── users.json            # User credentials
│   └── positions.json        # Position history
├── templates/
│   ├── base.html             # Base template
│   ├── login.html            # Login page
│   ├── dashboard.html        # Dashboard
│   ├── settings.html         # Settings page
│   └── history.html          # Trade history
├── static/
│   ├── css/
│   │   └── style.css         # Modern CSS styles
│   └── js/
│       └── dashboard.js      # Dashboard JavaScript
└── logs/
    └── app.log               # Application logs
```

## 🔄 Workflow

1. **Signal Received** → Webhook endpoint receives trading signal
2. **Validation** → Check trading enabled, position limits, duplicates
3. **ATR Calculation** → Fetch 1h klines, calculate ATR
4. **TP/SL Calculation** → Entry ± (ATR × Multiplier)
5. **Order Placement** → Market order + TP/SL orders
6. **Position Monitoring** → Track PnL, update dashboard
7. **Telegram Notification** → Send trade alert
8. **Position Closed** → Log trade, update history

## ⚠️ Important Notes

1. **API Permissions:** Enable Futures trading on your Binance API key
2. **IP Whitelist:** Add your EC2 IP to Binance API whitelist
3. **Test Mode:** Start with small amounts and low leverage
4. **Risk Management:** Never use 100% of balance, set appropriate leverage
5. **Monitoring:** Regularly check logs and positions
6. **Backup:** Keep backup of data/config.json

## 🆘 Troubleshooting

### Bot not starting
```bash
# Check logs
sudo journalctl -u binance_bot -n 50

# Verify Python environment
source venv/bin/activate
python --version
```

### API errors
- Verify API keys in Settings
- Check Binance API permissions
- Confirm IP whitelist
- Check API rate limits

### Webhook not working
```bash
# Test webhook
curl -X POST http://YOUR_IP/webhook \
  -H "Content-Type: application/json" \
  -d '{"signal": "BTCUSDT/long/open"}'

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Position errors
- Check if trading is enabled for the coin
- Verify balance is sufficient
- Check leverage and margin mode
- Review position limits

## 📞 Support

For issues, questions, or feature requests:
- Check logs: `logs/app.log`
- Review configuration: `data/config.json`
- Verify API permissions on Binance

## 📝 License

This project is for educational and personal use. Use at your own risk. Trading involves financial risk.

## 🎯 Version

**Version:** 1.0.0  
**Port:** 5001  
**Platform:** Binance Futures (USDT-M & USDC-M)  
**Author:** Tony Trading Systems

---

**⚠️ DISCLAIMER:** Cryptocurrency trading carries significant risk. This bot is provided as-is without warranty. Always test with small amounts first and never risk more than you can afford to lose.
