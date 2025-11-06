#!/bin/bash

###############################################
# Binance Trading Bot - EC2 Deployment Script
# This script automates the deployment to EC2
###############################################

set -e

echo "=========================================="
echo "Binance Trading Bot - EC2 Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="binance_bot"
APP_DIR="/home/ubuntu/binance_bot"
SERVICE_NAME="binance_bot"
NGINX_SITE="binance_bot"
PYTHON_VERSION="3.10"
PORT="5001"

echo -e "${GREEN}[1/10] Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

echo -e "${GREEN}[2/10] Installing Python and dependencies...${NC}"
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y build-essential libssl-dev libffi-dev
sudo apt install -y nginx supervisor

echo -e "${GREEN}[3/10] Creating application directory...${NC}"
sudo mkdir -p $APP_DIR
sudo chown -R ubuntu:ubuntu $APP_DIR

echo -e "${GREEN}[4/10] Setting up Python virtual environment...${NC}"
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

echo -e "${GREEN}[5/10] Installing Python packages...${NC}"
pip install --upgrade pip
pip install Flask
pip install Flask-Login
pip install Flask-WTF
pip install python-telegram-bot
pip install requests
pip install python-dotenv
pip install Werkzeug
pip install gunicorn
pip install python-binance
pip install pandas
pip install numpy

echo -e "${GREEN}[6/10] Creating systemd service...${NC}"
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Binance Trading Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}[7/10] Configuring Nginx...${NC}"
sudo tee /etc/nginx/sites-available/${NGINX_SITE} > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:${PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Webhook endpoint
    location /webhook {
        proxy_pass http://127.0.0.1:${PORT}/webhook;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        
        # Larger body size for webhook payloads
        client_max_body_size 10M;
    }
    
    # Static files
    location /static {
        alias $APP_DIR/static;
        expires 30d;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/${NGINX_SITE} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo -e "${GREEN}[8/10] Setting up firewall...${NC}"
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo "y" | sudo ufw enable || true

echo -e "${GREEN}[9/10] Starting services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}
sudo systemctl restart nginx

echo -e "${GREEN}[10/10] Verifying installation...${NC}"
sleep 3

# Check service status
if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
    echo -e "${GREEN}✓ Service is running${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    sudo systemctl status ${SERVICE_NAME}
fi

# Check Nginx
if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${RED}✗ Nginx failed to start${NC}"
    sudo systemctl status nginx
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Copy your application files to: $APP_DIR"
echo "2. Update configuration in: $APP_DIR/data/config.json"
echo "3. Restart service: sudo systemctl restart ${SERVICE_NAME}"
echo ""
echo "Useful Commands:"
echo "  View logs:    sudo journalctl -u ${SERVICE_NAME} -f"
echo "  Restart:      sudo systemctl restart ${SERVICE_NAME}"
echo "  Stop:         sudo systemctl stop ${SERVICE_NAME}"
echo "  Status:       sudo systemctl status ${SERVICE_NAME}"
echo ""
echo "Access dashboard at: http://YOUR_EC2_IP"
echo "Webhook endpoint:    http://YOUR_EC2_IP/webhook"
echo ""
echo -e "${YELLOW}Default login: admin / admin${NC}"
echo -e "${YELLOW}⚠ Please change the default password!${NC}"
echo ""

