# 🚀 Quick Deployment Guide

Fast-track guide to deploy Tony Binance Bot on AWS EC2 with domain and SSL.

## Server Details

- **Domain:** cryptosynapse.net
- **Public IP:** 54.255.77.184
- **Private IP:** 172.31.17.215
- **Port:** 5001 (internal), 80/443 (external)
- **Install Path:** /home/ubuntu/tony_binance

---

## Step 1: Configure Domain DNS (BEFORE Deployment)

### Option A: Using AWS Route53 (Recommended)

1. Go to AWS Console → Route53 → Hosted zones
2. Create/Select `cryptosynapse.net` hosted zone
3. Create A records:

**Record 1 (Root domain):**
- Record name: (empty)
- Type: A
- Value: 54.255.77.184
- TTL: 300

**Record 2 (www subdomain):**
- Record name: www
- Type: A
- Value: 54.255.77.184
- TTL: 300

### Option B: Using Other Registrar (Cloudflare, GoDaddy, etc.)

1. Login to your domain registrar
2. Go to DNS management
3. Add two A records:
   - `@` → 54.255.77.184
   - `www` → 54.255.77.184

### Verify DNS

Wait 5-30 minutes, then check:

```bash
# From your computer
nslookup cryptosynapse.net
# Should show: 54.255.77.184

# Or use online tool
# Visit: https://dnschecker.org
# Enter: cryptosynapse.net
```

---

## Step 2: Configure AWS Security Group

In AWS EC2 Console:

1. Go to EC2 → Instances → Select your instance
2. Click on "Security" tab
3. Click on Security Group name
4. Edit Inbound Rules:

| Type  | Protocol | Port  | Source    | Description |
|-------|----------|-------|-----------|-------------|
| SSH   | TCP      | 22    | Your IP   | SSH Access  |
| HTTP  | TCP      | 80    | 0.0.0.0/0 | HTTP        |
| HTTPS | TCP      | 443   | 0.0.0.0/0 | HTTPS       |

**Important:** Make sure all three ports are open!

---

## Step 3: Upload Files to EC2

From your local computer:

```bash
# Navigate to project folder
cd d:\projects\tony\tony_binance_bot

# Upload all files to EC2
scp -r * ubuntu@54.255.77.184:/home/ubuntu/tony_binance/
```

Or use FileZilla/WinSCP with:
- Host: 54.255.77.184
- User: ubuntu
- Upload to: /home/ubuntu/tony_binance/

---

## Step 4: Connect to EC2 and Deploy

```bash
# Connect via SSH
ssh ubuntu@54.255.77.184

# Navigate to app directory
cd /home/ubuntu/tony_binance

# Make script executable
chmod +x deploy_ec2_production.sh

# Run deployment script
sudo ./deploy_ec2_production.sh
```

The script will:
- ✅ Install all dependencies (Python, Nginx, Certbot)
- ✅ Setup Python virtual environment
- ✅ Create systemd service
- ✅ Configure Nginx
- ✅ Setup SSL certificates (if DNS is ready)
- ✅ Configure firewall
- ✅ Start all services

**Note:** You'll need to press Enter after copying files when prompted by the script.

---

## Step 5: Verify Installation

```bash
# Check if services are running
sudo systemctl status tony_binance
sudo systemctl status nginx

# Check logs
sudo journalctl -u tony_binance -n 20

# Test local connection
curl http://localhost:5001
```

---

## Step 6: Access Your Bot

1. Open browser: https://cryptosynapse.net
2. Login with:
   - Username: `admin`
   - Password: `admin`
3. **IMMEDIATELY change the password!**

---

## Step 7: Configure Binance API

1. Go to https://www.binance.com/en/my/settings/api-management
2. Create new API key with:
   - Enable Futures: ✅
   - Enable Spot & Margin: ❌ (not needed)
   - Whitelist IP: 54.255.77.184
3. Copy API Key and Secret
4. In bot dashboard:
   - Go to Settings
   - Paste API Key and Secret
   - Save Settings

---

## Step 8: Configure Trading

In Settings page:

1. **Enable coins you want to trade:**
   - Go to "USDT Coins (15)" or "USDC Coins (15)" tabs
   - Toggle ON the coins you want
   - Configure leverage, order size, ATR settings per coin

2. **Set global settings:**
   - Max daily trades
   - Max open positions
   - Auto position switch
   - Long/short only mode

3. **Save Settings**

---

## Step 9: Test Webhook

From your local computer:

```bash
curl -X POST https://cryptosynapse.net/webhook \
  -H "Content-Type: application/json" \
  -d '{"signal": "BTCUSDT/long/open"}'
```

Check logs on EC2:

```bash
sudo journalctl -u tony_binance -f
```

---

## Quick Command Reference

```bash
# Restart application
sudo systemctl restart tony_binance

# View real-time logs
sudo journalctl -u tony_binance -f

# Check service status
sudo systemctl status tony_binance
sudo systemctl status nginx

# Renew SSL (if needed)
sudo certbot renew

# Restart Nginx
sudo systemctl restart nginx

# Check firewall
sudo ufw status
```

---

## Troubleshooting

### SSL Certificate Failed

If SSL setup fails during deployment:

```bash
# Wait for DNS propagation, then manually run:
sudo certbot --nginx -d cryptosynapse.net -d www.cryptosynapse.net
```

### Can't Access Website

1. Check DNS: `nslookup cryptosynapse.net`
2. Check Security Group has ports 80, 443 open
3. Check services: `sudo systemctl status tony_binance nginx`
4. Check logs: `sudo journalctl -u tony_binance -f`

### 502 Bad Gateway

```bash
# Restart services
sudo systemctl restart tony_binance
sudo systemctl restart nginx
```

---

## Important URLs

- **Dashboard:** https://cryptosynapse.net
- **Webhook:** https://cryptosynapse.net/webhook
- **SSH:** ssh ubuntu@54.255.77.184

---

## Documentation Files

- `README.md` - Complete documentation
- `DOMAIN_SETUP_GUIDE.md` - Detailed DNS configuration
- `POST_DEPLOYMENT.md` - Maintenance & troubleshooting
- `WEBHOOK_TEST_GUIDE.md` - Testing webhooks

---

## Summary Checklist

- [ ] DNS A records configured (cryptosynapse.net → 54.255.77.184)
- [ ] DNS propagation verified
- [ ] AWS Security Group allows ports 22, 80, 443
- [ ] Files uploaded to EC2
- [ ] Deployment script executed successfully
- [ ] Services running (tony_binance, nginx)
- [ ] SSL certificate obtained
- [ ] Dashboard accessible at https://cryptosynapse.net
- [ ] Default password changed
- [ ] Binance API configured
- [ ] Coins enabled and configured
- [ ] Webhook tested
- [ ] Telegram notifications configured (optional)

---

**Time Estimate:** 15-30 minutes (plus DNS propagation time)

**Support:** See `POST_DEPLOYMENT.md` for comprehensive troubleshooting.

