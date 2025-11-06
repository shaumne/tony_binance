# Post-Deployment Guide

This guide covers everything you need to know after deploying the Tony Binance Bot to your AWS EC2 instance.

## Table of Contents

1. [Initial Configuration](#initial-configuration)
2. [Verifying Installation](#verifying-installation)
3. [Accessing the Dashboard](#accessing-the-dashboard)
4. [Configuring Binance API](#configuring-binance-api)
5. [Testing Webhooks](#testing-webhooks)
6. [Monitoring & Logs](#monitoring--logs)
7. [Maintenance Tasks](#maintenance-tasks)
8. [Troubleshooting](#troubleshooting)
9. [Backup & Recovery](#backup--recovery)
10. [Security Best Practices](#security-best-practices)

---

## Initial Configuration

### Step 1: Access Your Server

SSH into your EC2 instance:

```bash
ssh ubuntu@54.255.77.184
# or
ssh ubuntu@cryptosynapse.net
```

### Step 2: Verify Services are Running

```bash
# Check application status
sudo systemctl status tony_binance

# Check Nginx status
sudo systemctl status nginx

# Check if services are enabled (auto-start on boot)
sudo systemctl is-enabled tony_binance
sudo systemctl is-enabled nginx
```

### Step 3: Initial Data Setup

The application automatically creates default files on first run. Verify they exist:

```bash
ls -la /home/ubuntu/tony_binance/data/
# Should show: config.json, config_backup.json, users.json, positions.json
```

---

## Verifying Installation

### Check Application Health

```bash
# Test local Flask app
curl http://localhost:5001

# Test through Nginx
curl http://localhost

# Test HTTPS (if SSL configured)
curl https://cryptosynapse.net
```

### Check Open Ports

```bash
# View firewall status
sudo ufw status numbered

# Should show:
# - Port 22 (SSH)
# - Port 80 (HTTP)
# - Port 443 (HTTPS)
```

### View Recent Logs

```bash
# Application logs (last 50 lines)
sudo journalctl -u tony_binance -n 50

# Application logs (real-time)
sudo journalctl -u tony_binance -f

# Nginx access logs
sudo tail -f /home/ubuntu/tony_binance/logs/nginx_access.log

# Nginx error logs
sudo tail -f /home/ubuntu/tony_binance/logs/nginx_error.log

# Application logs (if using file logging)
tail -f /home/ubuntu/tony_binance/logs/app.log
tail -f /home/ubuntu/tony_binance/logs/error.log
```

---

## Accessing the Dashboard

### Default Login Credentials

- **URL**: https://cryptosynapse.net
- **Username**: `admin`
- **Password**: `admin`

**⚠️ IMPORTANT**: Change the default password immediately after first login!

### Changing Password

1. Login to the dashboard
2. Click on your username in the top right
3. Select "Change Password"
4. Enter current password and new password
5. Click "Update Password"

Or via command line:

```bash
cd /home/ubuntu/tony_binance
source venv/bin/activate
python3 -c "
from werkzeug.security import generate_password_hash
import json

password = input('Enter new password: ')
hashed = generate_password_hash(password)

with open('data/users.json', 'r') as f:
    users = json.load(f)

users['admin']['password'] = hashed

with open('data/users.json', 'w') as f:
    json.dump(users, f, indent=2)

print('Password updated successfully!')
"
```

---

## Configuring Binance API

### Step 1: Generate Binance API Keys

1. Go to https://www.binance.com/
2. Login to your account
3. Go to Profile → API Management
4. Create a new API key
5. Enable "Enable Futures" permission
6. Whitelist your server IP: 54.255.77.184
7. Save your API Key and Secret Key (keep them secure!)

**Security Tips**:
- Enable IP restriction
- Enable only necessary permissions (Futures trading)
- Do NOT enable withdrawals
- Use API with trading limits for testing

### Step 2: Configure in Dashboard

1. Login to https://cryptosynapse.net
2. Go to **Settings** page
3. Under **Binance API Configuration**:
   - Enter your **API Key**
   - Enter your **Secret Key**
4. Scroll down and click **Save Settings**

### Step 3: Verify API Connection

Check logs to ensure connection is successful:

```bash
sudo journalctl -u tony_binance -n 50 | grep -i "binance"
```

You should see: "BinanceHandler initialized with ENHANCED SYSTEMS"

---

## Testing Webhooks

### Local Testing from Server

```bash
# Test webhook endpoint
curl -X POST https://cryptosynapse.net/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "BTCUSDT",
    "action": "buy"
  }'

# Expected response: {"status": "success", "message": "..."}
```

### Testing from External Source

Use the provided test scripts in the repository:

```bash
# On your local machine (not EC2)
cd tony_binance_bot

# Edit quick_test.py and update the URL
# Change: http://localhost:5000/webhook
# To: https://cryptosynapse.net/webhook

# Run test
python quick_test.py
```

### TradingView Setup

1. In TradingView, create an alert
2. Set Webhook URL to: `https://cryptosynapse.net/webhook`
3. Message format (JSON):
   ```json
   {
     "ticker": "{{ticker}}",
     "action": "{{strategy.order.action}}"
   }
   ```
4. Test the alert

For detailed webhook testing, see `WEBHOOK_TEST_GUIDE.md`

---

## Monitoring & Logs

### Real-time Monitoring

```bash
# Watch application logs
sudo journalctl -u tony_binance -f

# Watch Nginx access logs
sudo tail -f /home/ubuntu/tony_binance/logs/nginx_access.log

# Watch all logs simultaneously
sudo tail -f /home/ubuntu/tony_binance/logs/*.log
```

### Log Locations

| Log Type | Location |
|----------|----------|
| Application stdout | `journalctl -u tony_binance` |
| Application file log | `/home/ubuntu/tony_binance/logs/app.log` |
| Application errors | `/home/ubuntu/tony_binance/logs/error.log` |
| Nginx access | `/home/ubuntu/tony_binance/logs/nginx_access.log` |
| Nginx errors | `/home/ubuntu/tony_binance/logs/nginx_error.log` |
| System logs | `/var/log/syslog` |

### Disk Space Monitoring

```bash
# Check disk usage
df -h

# Check log file sizes
du -sh /home/ubuntu/tony_binance/logs/*

# Clean old logs (if needed)
sudo find /home/ubuntu/tony_binance/logs/ -name "*.log" -mtime +30 -delete
```

### Performance Monitoring

```bash
# Check CPU and memory usage
htop

# Or
top

# Check application resource usage
ps aux | grep python

# Check network connections
sudo netstat -tulpn | grep -E ":(5001|80|443)"
```

---

## Maintenance Tasks

### Restart Application

```bash
# Restart Flask application
sudo systemctl restart tony_binance

# Check status
sudo systemctl status tony_binance
```

### Restart Nginx

```bash
# Test Nginx configuration first
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Or reload (graceful restart)
sudo systemctl reload nginx
```

### Update Application

```bash
# Navigate to app directory
cd /home/ubuntu/tony_binance

# Backup current version
sudo cp -r /home/ubuntu/tony_binance /home/ubuntu/tony_binance_backup_$(date +%Y%m%d)

# Stop the application
sudo systemctl stop tony_binance

# Pull latest changes (if using git)
sudo -u ubuntu git pull

# Or upload new files via SCP from local machine:
# scp -r /path/to/new/files/* ubuntu@54.255.77.184:/home/ubuntu/tony_binance/

# Update dependencies (if requirements.txt changed)
sudo -u ubuntu bash -c "source venv/bin/activate && pip install -r requirements.txt"

# Start the application
sudo systemctl start tony_binance

# Verify it's running
sudo systemctl status tony_binance
```

### Update Python Dependencies

```bash
cd /home/ubuntu/tony_binance
sudo -u ubuntu bash -c "source venv/bin/activate && pip install --upgrade -r requirements.txt"
sudo systemctl restart tony_binance
```

### Renew SSL Certificate

SSL certificates from Let's Encrypt auto-renew. To manually renew:

```bash
# Test renewal
sudo certbot renew --dry-run

# Force renewal
sudo certbot renew --force-renewal

# Restart Nginx after renewal
sudo systemctl restart nginx
```

### Log Rotation

Create a log rotation config to prevent logs from consuming too much space:

```bash
sudo nano /etc/logrotate.d/tony_binance
```

Add:
```
/home/ubuntu/tony_binance/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ubuntu ubuntu
    postrotate
        systemctl reload tony_binance > /dev/null 2>&1 || true
    endscript
}
```

Test:
```bash
sudo logrotate -d /etc/logrotate.d/tony_binance
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs for errors
sudo journalctl -u tony_binance -n 100

# Check if port 5001 is already in use
sudo netstat -tulpn | grep 5001

# Check file permissions
ls -la /home/ubuntu/tony_binance/

# Try starting manually for debugging
cd /home/ubuntu/tony_binance
sudo -u ubuntu bash -c "source venv/bin/activate && python app.py"
```

### 502 Bad Gateway Error

This means Nginx can't connect to the Flask app.

```bash
# Check if Flask app is running
sudo systemctl status tony_binance

# Restart Flask app
sudo systemctl restart tony_binance

# Check Nginx error logs
sudo tail -f /home/ubuntu/tony_binance/logs/nginx_error.log
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# If renewal fails, try manual method
sudo certbot --nginx -d cryptosynapse.net -d www.cryptosynapse.net
```

### High CPU Usage

```bash
# Identify process
top

# Check application logs for errors
sudo journalctl -u tony_binance -n 200

# Restart application
sudo systemctl restart tony_binance
```

### Database/Config File Corruption

```bash
cd /home/ubuntu/tony_binance

# Restore from backup
cp data/config_backup.json data/config.json

# Or reset to defaults
python3 -c "
import json
# Create default config here or copy from template
"

# Restart application
sudo systemctl restart tony_binance
```

### Webhook Not Receiving Signals

```bash
# Check if webhook endpoint is accessible
curl -X POST https://cryptosynapse.net/webhook \
  -H "Content-Type: application/json" \
  -d '{"ticker": "BTCUSDT", "action": "buy"}'

# Check firewall
sudo ufw status

# Check Nginx logs for incoming requests
sudo tail -f /home/ubuntu/tony_binance/logs/nginx_access.log

# Check application logs
sudo journalctl -u tony_binance -f
```

---

## Backup & Recovery

### Backup Configuration

```bash
# Create backup directory
mkdir -p /home/ubuntu/backups

# Backup application data
sudo tar -czf /home/ubuntu/backups/tony_binance_$(date +%Y%m%d_%H%M%S).tar.gz \
  /home/ubuntu/tony_binance/data/

# List backups
ls -lh /home/ubuntu/backups/
```

### Automated Backup Script

Create a backup script:

```bash
sudo nano /home/ubuntu/backup_bot.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
APP_DIR="/home/ubuntu/tony_binance"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup data directory
tar -czf $BACKUP_DIR/data_$DATE.tar.gz $APP_DIR/data/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "data_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/data_$DATE.tar.gz"
```

Make it executable:
```bash
sudo chmod +x /home/ubuntu/backup_bot.sh
```

Schedule with cron (daily at 2 AM):
```bash
sudo crontab -e

# Add this line:
0 2 * * * /home/ubuntu/backup_bot.sh >> /home/ubuntu/backups/backup.log 2>&1
```

### Restore from Backup

```bash
# Stop application
sudo systemctl stop tony_binance

# Restore data
cd /home/ubuntu
sudo tar -xzf backups/data_YYYYMMDD_HHMMSS.tar.gz

# Fix permissions
sudo chown -R ubuntu:ubuntu /home/ubuntu/tony_binance/data/

# Start application
sudo systemctl start tony_binance
```

---

## Security Best Practices

### 1. Change Default Credentials
- Change admin password immediately after deployment
- Use strong passwords (12+ characters, mixed case, numbers, symbols)

### 2. Secure SSH Access
```bash
# Disable password authentication (use SSH keys only)
sudo nano /etc/ssh/sshd_config

# Set: PasswordAuthentication no
# Restart SSH
sudo systemctl restart sshd
```

### 3. Keep System Updated
```bash
# Update system packages regularly
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd /home/ubuntu/tony_binance
sudo -u ubuntu bash -c "source venv/bin/activate && pip install --upgrade -r requirements.txt"
```

### 4. Monitor Failed Login Attempts
```bash
# Install fail2ban
sudo apt install fail2ban -y

# Check failed SSH attempts
sudo grep "Failed password" /var/log/auth.log | tail -20
```

### 5. Secure API Keys
- Never commit API keys to git
- Store in environment variables or secure config files
- Regularly rotate API keys
- Use IP whitelisting on Binance

### 6. Enable AWS Security Features
- Use AWS Security Groups to restrict access
- Enable CloudWatch monitoring
- Set up billing alerts
- Enable AWS GuardDuty for threat detection

### 7. Regular Audits
```bash
# Check listening ports
sudo netstat -tulpn

# Check running processes
ps aux

# Check recent logins
last -20

# Check sudo usage
sudo grep sudo /var/log/auth.log | tail -20
```

---

## Useful Commands Reference

```bash
# Service Management
sudo systemctl start tony_binance      # Start application
sudo systemctl stop tony_binance       # Stop application
sudo systemctl restart tony_binance    # Restart application
sudo systemctl status tony_binance     # Check status
sudo systemctl enable tony_binance     # Enable auto-start

# Nginx Management
sudo systemctl restart nginx           # Restart Nginx
sudo systemctl reload nginx            # Reload config
sudo nginx -t                          # Test configuration

# Logs
sudo journalctl -u tony_binance -f     # Real-time app logs
sudo tail -f /home/ubuntu/tony_binance/logs/*.log  # All logs

# SSL
sudo certbot renew                     # Renew certificates
sudo certbot certificates              # List certificates

# System
df -h                                  # Disk usage
free -h                                # Memory usage
top                                    # Process monitor
sudo ufw status                        # Firewall status

# Application
cd /home/ubuntu/tony_binance           # Go to app directory
source venv/bin/activate               # Activate virtual environment
python app.py                          # Run manually (for debugging)
```

---

## Next Steps

1. ✅ Verify all services are running
2. ✅ Change default password
3. ✅ Configure Binance API keys
4. ✅ Test webhook endpoint
5. ✅ Set up monitoring and alerts
6. ✅ Schedule regular backups
7. ✅ Review logs regularly
8. ✅ Test trading with small amounts first

---

## Support & Resources

- **Application Directory**: `/home/ubuntu/tony_binance`
- **Configuration**: `/home/ubuntu/tony_binance/data/config.json`
- **Logs**: `/home/ubuntu/tony_binance/logs/`
- **Web Interface**: https://cryptosynapse.net
- **Webhook URL**: https://cryptosynapse.net/webhook

For additional help:
- Review `README.md` for application features
- Check `WEBHOOK_TEST_GUIDE.md` for testing
- Review `DOMAIN_SETUP_GUIDE.md` for DNS issues

---

**Remember**: Always test changes in a development environment before applying to production!

