# Domain Setup Guide for cryptosynapse.net

This guide will walk you through configuring your domain `cryptosynapse.net` to point to your AWS EC2 instance.

## Server Information

- **Domain Name**: cryptosynapse.net
- **Public IP**: 54.255.77.184
- **Private IP**: 172.31.17.215 (internal AWS use only)
- **Application Port**: 5001 (internal, proxied by Nginx)

## Prerequisites

- Access to your domain registrar's DNS management panel
- Your domain must be registered and active
- EC2 instance must be running and accessible

---

## Step 1: Configure DNS A Records

You need to add DNS A records at your domain registrar (e.g., GoDaddy, Namecheap, Cloudflare, Route53, etc.).

### Required DNS Records

Add the following A records:

| Type | Name/Host | Value/Points to | TTL |
|------|-----------|----------------|-----|
| A    | @         | 54.255.77.184  | 3600 (or Auto) |
| A    | www       | 54.255.77.184  | 3600 (or Auto) |

**Alternative for www subdomain**: You can also use a CNAME record instead of an A record for www:

| Type  | Name/Host | Value/Points to      | TTL |
|-------|-----------|---------------------|-----|
| CNAME | www       | cryptosynapse.net   | 3600 (or Auto) |

### Instructions by Provider

#### AWS Route53 (Recommended for AWS EC2)

1. Go to AWS Console → Route53
2. Click on "Hosted zones"
3. Select your domain `cryptosynapse.net` (or create a hosted zone)
4. Click "Create record"
5. For root domain:
   - Record name: (leave empty for root)
   - Record type: A
   - Value: 54.255.77.184
   - TTL: 300
   - Click "Create records"
6. For www subdomain:
   - Record name: www
   - Record type: A
   - Value: 54.255.77.184
   - TTL: 300
   - Click "Create records"

#### Cloudflare

1. Log in to Cloudflare Dashboard
2. Select your domain `cryptosynapse.net`
3. Go to DNS → Records
4. Add A record for root:
   - Type: A
   - Name: @
   - IPv4 address: 54.255.77.184
   - Proxy status: DNS only (gray cloud) *for initial setup*
   - TTL: Auto
   - Click Save
5. Add A record for www:
   - Type: A
   - Name: www
   - IPv4 address: 54.255.77.184
   - Proxy status: DNS only (gray cloud) *for initial setup*
   - TTL: Auto
   - Click Save

**Note**: After SSL is configured, you can enable Cloudflare proxy (orange cloud) for additional security and CDN benefits.

#### GoDaddy

1. Log in to GoDaddy Account
2. Go to My Products → Domains
3. Click on your domain `cryptosynapse.net`
4. Click "Manage DNS"
5. Add A record:
   - Type: A
   - Name: @
   - Value: 54.255.77.184
   - TTL: 1 Hour
   - Click Save
6. Add A record for www:
   - Type: A
   - Name: www
   - Value: 54.255.77.184
   - TTL: 1 Hour
   - Click Save

#### Namecheap

1. Log in to Namecheap Account
2. Go to Domain List
3. Click "Manage" next to `cryptosynapse.net`
4. Go to "Advanced DNS" tab
5. Add A record:
   - Type: A Record
   - Host: @
   - Value: 54.255.77.184
   - TTL: Automatic
   - Click the green checkmark
6. Add A record for www:
   - Type: A Record
   - Host: www
   - Value: 54.255.77.184
   - TTL: Automatic
   - Click the green checkmark

---

## Step 2: Verify DNS Propagation

DNS changes can take anywhere from 5 minutes to 48 hours to propagate globally, though it's typically within 1-2 hours.

### Check DNS Propagation

Use these methods to verify your DNS records:

#### Method 1: Online Tools

Visit these websites to check DNS propagation:
- https://dnschecker.org/ (enter cryptosynapse.net)
- https://www.whatsmydns.net/ (enter cryptosynapse.net)
- https://mxtoolbox.com/DNSLookup.aspx

#### Method 2: Command Line (Linux/Mac/Windows PowerShell)

```bash
# Check A record for root domain
dig cryptosynapse.net +short

# Check A record for www
dig www.cryptosynapse.net +short

# Or use nslookup (Windows/Mac/Linux)
nslookup cryptosynapse.net
nslookup www.cryptosynapse.net
```

Expected output:
```
54.255.77.184
```

#### Method 3: From Your EC2 Instance

SSH into your EC2 instance and run:

```bash
dig cryptosynapse.net +short
dig www.cryptosynapse.net +short
```

Both should return: `54.255.77.184`

---

## Step 3: Test HTTP Connection

Once DNS is propagated, test the HTTP connection (before SSL):

```bash
# From your local machine
curl -I http://cryptosynapse.net

# You should see a response from Nginx
```

---

## Step 4: SSL Certificate Setup

After DNS is properly configured and propagated, the deployment script will automatically set up SSL certificates using Let's Encrypt.

If the automatic setup didn't work, you can manually run:

```bash
sudo certbot --nginx -d cryptosynapse.net -d www.cryptosynapse.net
```

Follow the prompts:
1. Enter your email address
2. Agree to Terms of Service (Y)
3. Choose whether to share your email (Y/N)
4. Select option 2 to redirect all traffic to HTTPS

---

## Step 5: Verify HTTPS

After SSL is configured, test your site:

```bash
# Test HTTPS
curl -I https://cryptosynapse.net

# Should return 200 OK with SSL certificate info
```

Visit in browser:
- https://cryptosynapse.net
- https://www.cryptosynapse.net

Both should load with a valid SSL certificate (green padlock icon).

---

## Troubleshooting

### Issue: DNS not resolving

**Solution**:
1. Wait longer for DNS propagation (up to 48 hours)
2. Clear your local DNS cache:
   ```bash
   # Windows
   ipconfig /flushdns
   
   # Mac
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
   
   # Linux
   sudo systemd-resolve --flush-caches
   ```
3. Verify DNS records are correctly configured at your registrar

### Issue: SSL certificate fails

**Error**: `Failed authorization procedure`

**Solution**:
1. Ensure DNS is fully propagated (check with dnschecker.org)
2. Ensure ports 80 and 443 are open in AWS Security Group
3. Manually run certbot after DNS is ready:
   ```bash
   sudo certbot --nginx -d cryptosynapse.net -d www.cryptosynapse.net
   ```

### Issue: Connection timeout

**Solution**:
1. Check AWS Security Group allows inbound traffic:
   - Port 80 (HTTP) from 0.0.0.0/0
   - Port 443 (HTTPS) from 0.0.0.0/0
   - Port 22 (SSH) from your IP
2. Check UFW firewall status:
   ```bash
   sudo ufw status
   ```
3. Verify Nginx is running:
   ```bash
   sudo systemctl status nginx
   ```

### Issue: 502 Bad Gateway

**Solution**:
1. Check if Flask app is running:
   ```bash
   sudo systemctl status tony_binance
   ```
2. Check application logs:
   ```bash
   sudo journalctl -u tony_binance -n 50
   ```
3. Restart the application:
   ```bash
   sudo systemctl restart tony_binance
   ```

---

## AWS Security Group Configuration

Ensure your EC2 instance's Security Group has these inbound rules:

| Type  | Protocol | Port Range | Source      | Description           |
|-------|----------|------------|-------------|-----------------------|
| SSH   | TCP      | 22         | Your IP     | SSH access            |
| HTTP  | TCP      | 80         | 0.0.0.0/0   | HTTP traffic          |
| HTTP  | TCP      | 80         | ::/0        | HTTP traffic (IPv6)   |
| HTTPS | TCP      | 443        | 0.0.0.0/0   | HTTPS traffic         |
| HTTPS | TCP      | 443        | ::/0        | HTTPS traffic (IPv6)  |

To configure Security Group:
1. Go to EC2 Console → Instances
2. Click on your instance
3. Go to "Security" tab
4. Click on the Security Group name
5. Click "Edit inbound rules"
6. Add the rules above if not present

---

## Post-Setup Verification Checklist

- [ ] DNS A records configured (@ and www)
- [ ] DNS propagation complete (verified with dnschecker.org)
- [ ] EC2 Security Group allows ports 80 and 443
- [ ] HTTP redirects to HTTPS
- [ ] SSL certificate is valid and shows green padlock
- [ ] Application loads at https://cryptosynapse.net
- [ ] Can login to the dashboard
- [ ] Webhook URL accessible at https://cryptosynapse.net/webhook

---

## Useful Commands

```bash
# Check DNS resolution
dig cryptosynapse.net
nslookup cryptosynapse.net

# Test HTTP
curl -I http://cryptosynapse.net

# Test HTTPS
curl -I https://cryptosynapse.net

# Check SSL certificate
openssl s_client -connect cryptosynapse.net:443 -servername cryptosynapse.net

# Check Nginx status
sudo systemctl status nginx

# Check app status
sudo systemctl status tony_binance

# View app logs
sudo journalctl -u tony_binance -f

# View Nginx logs
sudo tail -f /home/ubuntu/tony_binance/logs/nginx_access.log
sudo tail -f /home/ubuntu/tony_binance/logs/nginx_error.log
```

---

## Support

If you encounter issues:
1. Check the logs: `/home/ubuntu/tony_binance/logs/`
2. Review systemd service: `sudo journalctl -u tony_binance -n 100`
3. Check Nginx configuration: `sudo nginx -t`
4. Verify DNS with multiple tools
5. Wait for full DNS propagation (can take up to 48 hours)

---

## Next Steps

Once your domain is configured and SSL is active:

1. Access your dashboard at: https://cryptosynapse.net
2. Login with your credentials
3. Configure Binance API keys in Settings
4. Set up your trading preferences
5. Test webhook with: https://cryptosynapse.net/webhook

Refer to `POST_DEPLOYMENT.md` for detailed maintenance and operation instructions.

