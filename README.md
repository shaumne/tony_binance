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

### EC2 Production Deployment

For production deployment on AWS EC2 with SSL, domain, and systemd service:

#### Prerequisites
- Ubuntu 20.04+ EC2 instance
- Domain pointing to your EC2 (e.g., cryptosynapse.net)
- Root/sudo access
- EC2 Security Group allowing ports: 22, 80, 443

#### Quick Deployment

1. **Upload files to EC2:**
```bash
scp -r * ubuntu@54.255.77.184:/home/ubuntu/tony_binance/
```

2. **Connect to EC2:**
```bash
ssh ubuntu@54.255.77.184
```

3. **Run production deployment script:**
```bash
cd /home/ubuntu/tony_binance
chmod +x deploy_ec2_production.sh
sudo ./deploy_ec2_production.sh
```

The script will automatically:
- ✅ Install Python 3, Nginx, Certbot, and dependencies
- ✅ Setup virtual environment and install packages
- ✅ Create systemd service for auto-start
- ✅ Configure Nginx reverse proxy
- ✅ Setup SSL certificates (Let's Encrypt)
- ✅ Configure UFW firewall
- ✅ Start all services

#### Access Your Bot

After successful deployment:
- **Dashboard:** https://cryptosynapse.net
- **Webhook:** https://cryptosynapse.net/webhook
- **Default Login:** admin / admin

#### Important Configuration

Before running the deployment script:

1. **Configure your domain DNS** (see `DOMAIN_SETUP_GUIDE.md`):
   - Add A record: cryptosynapse.net → 54.255.77.184
   - Add A record: www.cryptosynapse.net → 54.255.77.184
   - Wait for DNS propagation (5 min - 48 hours)

2. **Configure EC2 Security Group:**
   - Port 22 (SSH) - Your IP
   - Port 80 (HTTP) - 0.0.0.0/0
   - Port 443 (HTTPS) - 0.0.0.0/0

3. **Update email in script** (optional):
   - Edit `deploy_ec2_production.sh`
   - Change: `EMAIL="admin@cryptosynapse.net"`

#### Service Management

```bash
# Application service
sudo systemctl status tony_binance
sudo systemctl restart tony_binance
sudo systemctl stop tony_binance

# View logs
sudo journalctl -u tony_binance -f
tail -f /home/ubuntu/tony_binance/logs/app.log

# Nginx
sudo systemctl restart nginx
sudo nginx -t  # Test configuration
```

#### SSL Certificate Renewal

SSL certificates auto-renew via certbot. To manually renew:

```bash
sudo certbot renew
sudo systemctl restart nginx
```

#### Documentation

For detailed guides, see:
- **`DOMAIN_SETUP_GUIDE.md`** - DNS configuration and domain setup
- **`POST_DEPLOYMENT.md`** - Post-deployment tasks, maintenance, troubleshooting
- **`WEBHOOK_TEST_GUIDE.md`** - Testing webhooks and signals

#### Deployment Details

- **Installation Path:** `/home/ubuntu/tony_binance`
- **Service Name:** `tony_binance`
- **Internal Port:** 5001
- **External Ports:** 80 (HTTP) → 443 (HTTPS)
- **Domain:** cryptosynapse.net
- **Public IP:** 54.255.77.184
- **SSL Provider:** Let's Encrypt (free, auto-renewal)
- **Web Server:** Nginx (reverse proxy)
- **Process Manager:** systemd

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

### Start/Stop Service (Production/EC2)
```bash
sudo systemctl start tony_binance
sudo systemctl stop tony_binance
sudo systemctl restart tony_binance
sudo systemctl enable tony_binance  # Enable auto-start on boot
```

### View Logs
```bash
# Real-time application logs
sudo journalctl -u tony_binance -f

# Last 50 lines
sudo journalctl -u tony_binance -n 50

# Application file logs
tail -f /home/ubuntu/tony_binance/logs/app.log
tail -f /home/ubuntu/tony_binance/logs/error.log

# Nginx logs
tail -f /home/ubuntu/tony_binance/logs/nginx_access.log
tail -f /home/ubuntu/tony_binance/logs/nginx_error.log
```

### Check Status
```bash
# Application status
sudo systemctl status tony_binance

# Nginx status
sudo systemctl status nginx

# Check if services are enabled
sudo systemctl is-enabled tony_binance
```

## 📁 Project Structure

```
tony_binance_bot/
├── app.py                         # Main Flask application
├── binance_handler.py             # Binance API integration
├── models.py                      # Data models (User, Config)
├── tp_sl_manager.py              # TP/SL calculation logic
├── coin_config_manager.py        # Per-coin configuration
├── position_validator.py         # Position validation & duplicate prevention
├── requirements.txt              # Python dependencies
├── .gitignore                   # Git ignore rules
│
├── README.md                    # Project documentation
├── DOMAIN_SETUP_GUIDE.md        # DNS & domain configuration guide
├── POST_DEPLOYMENT.md           # Post-deployment & maintenance guide
├── WEBHOOK_TEST_GUIDE.md        # Webhook testing instructions
│
├── deploy_ec2_production.sh     # Production EC2 deployment script
├── test_webhook.py              # Webhook testing script
├── quick_test.py                # Quick webhook test script
│
├── data/
│   ├── config.json              # Bot configuration
│   ├── config_backup.json       # Configuration backup
│   ├── users.json               # User credentials
│   └── positions.json           # Position tracking
│
├── templates/
│   ├── base.html                # Base template with navigation
│   ├── login.html               # Login page
│   ├── dashboard.html           # Main dashboard with positions
│   ├── settings.html            # Settings page (30 coins)
│   ├── users.html               # User management
│   └── change_password.html     # Password change
│
├── static/
│   ├── css/
│   │   └── style.css            # Modern dark mode CSS
│   └── js/
│       └── dashboard.js         # Dashboard auto-refresh
│
└── logs/
    ├── app.log                  # Application logs
    ├── error.log                # Error logs
    ├── nginx_access.log         # Nginx access logs (production)
    └── nginx_error.log          # Nginx error logs (production)
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
sudo journalctl -u tony_binance -n 50

# Check service status
sudo systemctl status tony_binance

# Verify Python environment
cd /home/ubuntu/tony_binance
source venv/bin/activate
python --version

# Try running manually for debugging
python app.py
```

### API errors
- Verify API keys in Settings
- Check Binance API permissions (enable Futures)
- Confirm IP whitelist on Binance
- Check API rate limits
- Review logs: `sudo journalctl -u tony_binance -f`

### Webhook not working
```bash
# Test webhook locally
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -d '{"signal": "BTCUSDT/long/open"}'

# Test webhook via domain
curl -X POST https://cryptosynapse.net/webhook \
  -H "Content-Type: application/json" \
  -d '{"signal": "BTCUSDT/long/open"}'

# Check Nginx logs
sudo tail -f /home/ubuntu/tony_binance/logs/nginx_error.log
sudo tail -f /home/ubuntu/tony_binance/logs/nginx_access.log

# Check application logs
sudo journalctl -u tony_binance -f
```

### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Manual renewal
sudo certbot --nginx -d cryptosynapse.net -d www.cryptosynapse.net
```

### 502 Bad Gateway
This means Nginx can't connect to Flask:
```bash
# Check if Flask is running
sudo systemctl status tony_binance

# Check if port 5001 is listening
sudo netstat -tulpn | grep 5001

# Restart services
sudo systemctl restart tony_binance
sudo systemctl restart nginx
```

### Position errors
- Check if trading is enabled for the coin (Settings page)
- Verify balance is sufficient
- Check leverage and margin mode on Binance
- Review position limits in Settings
- Check logs for specific error messages

### DNS not resolving
```bash
# Check DNS records
dig cryptosynapse.net +short
nslookup cryptosynapse.net

# Wait for propagation (can take up to 48 hours)
# Use online tools: dnschecker.org, whatsmydns.net
```

For comprehensive troubleshooting, see `POST_DEPLOYMENT.md`

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
