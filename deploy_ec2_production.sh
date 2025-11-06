#!/bin/bash

################################################################################
# Tony Binance Bot - AWS EC2 Production Deployment Script
# 
# This script automates the complete deployment process on AWS EC2
# including Python setup, systemd service, Nginx, and SSL configuration
#
# Requirements:
# - Ubuntu 20.04+ on AWS EC2
# - Domain: cryptosynapse.net pointing to this server
# - Sudo access
#
# Usage:
#   sudo bash deploy_ec2_production.sh
#
################################################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="tony_binance"
APP_DIR="/home/ubuntu/tony_binance/tony_binance"
APP_USER="ubuntu"
APP_PORT="5001"
DOMAIN="cryptosynapse.net"
EMAIL="admin@cryptosynapse.net"  # Change this to your email for Let's Encrypt

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root (use sudo)"
        exit 1
    fi
}

# Function to check Ubuntu version
check_ubuntu() {
    if [ ! -f /etc/os-release ]; then
        print_error "Cannot detect OS version"
        exit 1
    fi
    
    . /etc/os-release
    if [ "$ID" != "ubuntu" ]; then
        print_error "This script is designed for Ubuntu"
        exit 1
    fi
    
    print_info "Detected Ubuntu $VERSION"
}

# Step 1: System Update
update_system() {
    print_message "Step 1: Updating system packages..."
    apt-get update -y
    apt-get upgrade -y
    print_message "System packages updated successfully"
}

# Step 2: Install Dependencies
install_dependencies() {
    print_message "Step 2: Installing dependencies..."
    
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        nginx \
        certbot \
        python3-certbot-nginx \
        git \
        curl \
        ufw \
        supervisor
    
    print_message "Dependencies installed successfully"
}

# Step 3: Setup Application Directory
setup_app_directory() {
    print_message "Step 3: Setting up application directory..."
    
    # Create directory if it doesn't exist
    if [ ! -d "$APP_DIR" ]; then
        mkdir -p "$APP_DIR"
        print_info "Created directory: $APP_DIR"
    else
        print_warning "Directory already exists: $APP_DIR"
    fi
    
    # Set ownership
    chown -R $APP_USER:$APP_USER "$APP_DIR"
    
    print_message "Application directory ready"
}

# Step 4: Copy Application Files
copy_application_files() {
    print_message "Step 4: Copying application files..."
    
    print_info "Please manually copy your application files to: $APP_DIR"
    print_info "You can use SCP, SFTP, or Git to deploy your code"
    print_info ""
    print_info "Example using SCP from your local machine:"
    print_info "  scp -r /path/to/tony_binance_bot/* ubuntu@54.255.77.184:$APP_DIR/"
    print_info ""
    print_info "Or using Git:"
    print_info "  cd $APP_DIR"
    print_info "  git clone your-repository-url ."
    
    read -p "Press Enter after you've copied the files..."
}

# Step 5: Setup Python Virtual Environment
setup_python_env() {
    print_message "Step 5: Setting up Python virtual environment..."
    
    cd "$APP_DIR"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        sudo -u $APP_USER python3 -m venv venv
        print_info "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Install Python packages
    if [ -f "requirements.txt" ]; then
        sudo -u $APP_USER bash -c "source venv/bin/activate && pip install --upgrade pip"
        sudo -u $APP_USER bash -c "source venv/bin/activate && pip install -r requirements.txt"
        print_message "Python packages installed"
    else
        print_error "requirements.txt not found!"
        exit 1
    fi
}

# Step 6: Create Data Directories
create_data_directories() {
    print_message "Step 6: Creating data directories..."
    
    cd "$APP_DIR"
    
    # Create necessary directories
    sudo -u $APP_USER mkdir -p data logs
    
    # Initialize data files if they don't exist
    if [ ! -f "data/users.json" ]; then
        sudo -u $APP_USER bash -c 'echo "{}" > data/users.json'
    fi
    
    if [ ! -f "data/config.json" ]; then
        sudo -u $APP_USER bash -c 'echo "{}" > data/config.json'
    fi
    
    if [ ! -f "data/positions.json" ]; then
        sudo -u $APP_USER bash -c 'echo "[]" > data/positions.json'
    fi
    
    print_message "Data directories created"
}

# Step 7: Create Systemd Service
create_systemd_service() {
    print_message "Step 7: Creating systemd service..."
    
    cat > /etc/systemd/system/${APP_NAME}.service <<EOF
[Unit]
Description=Tony Binance Trading Bot
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/logs/app.log
StandardError=append:$APP_DIR/logs/error.log

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable ${APP_NAME}.service
    
    print_message "Systemd service created and enabled"
}

# Step 8: Configure Nginx
configure_nginx() {
    print_message "Step 8: Configuring Nginx..."
    
    # Backup default config
    if [ -f /etc/nginx/sites-enabled/default ]; then
        mv /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.backup
        print_info "Backed up default Nginx config"
    fi
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/${APP_NAME} <<EOF
# Upstream Flask application
upstream ${APP_NAME}_app {
    server 127.0.0.1:${APP_PORT} fail_timeout=0;
}

# HTTP server - redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};
    
    # Allow certbot validation
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN} www.${DOMAIN};
    
    # SSL certificates (will be configured by certbot)
    # ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log $APP_DIR/logs/nginx_access.log;
    error_log $APP_DIR/logs/nginx_error.log;
    
    # Max upload size
    client_max_body_size 10M;
    
    # Proxy settings
    location / {
        proxy_pass http://${APP_NAME}_app;
        proxy_redirect off;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files (if any)
    location /static {
        alias $APP_DIR/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # Enable the site
    ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/${APP_NAME}
    
    # Test Nginx configuration
    nginx -t
    
    print_message "Nginx configured successfully"
}

# Step 9: Configure Firewall
configure_firewall() {
    print_message "Step 9: Configuring firewall..."
    
    # Reset UFW to default
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (important!)
    ufw allow 22/tcp
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Enable firewall
    ufw --force enable
    
    print_message "Firewall configured"
    print_info "Allowed ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)"
}

# Step 10: Setup SSL with Let's Encrypt
setup_ssl() {
    print_message "Step 10: Setting up SSL certificates..."
    
    print_info "Checking DNS propagation for ${DOMAIN}..."
    
    # Check if domain resolves to this server
    RESOLVED_IP=$(dig +short ${DOMAIN} | tail -n1)
    SERVER_IP=$(curl -s ifconfig.me)
    
    print_info "Domain ${DOMAIN} resolves to: ${RESOLVED_IP}"
    print_info "Server public IP: ${SERVER_IP}"
    
    if [ "$RESOLVED_IP" != "$SERVER_IP" ]; then
        print_warning "DNS not properly configured!"
        print_warning "Please configure your DNS A record:"
        print_warning "  ${DOMAIN} -> ${SERVER_IP}"
        print_warning ""
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "SSL setup skipped. Run certbot manually later."
            return
        fi
    fi
    
    # Obtain SSL certificate
    certbot --nginx -d ${DOMAIN} -d www.${DOMAIN} \
        --non-interactive \
        --agree-tos \
        --email ${EMAIL} \
        --redirect
    
    if [ $? -eq 0 ]; then
        print_message "SSL certificates obtained successfully"
        
        # Setup auto-renewal
        systemctl enable certbot.timer
        systemctl start certbot.timer
        
        print_info "SSL auto-renewal configured"
    else
        print_error "SSL certificate generation failed"
        print_info "You can run certbot manually later:"
        print_info "  sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
    fi
}

# Step 11: Start Services
start_services() {
    print_message "Step 11: Starting services..."
    
    # Start Flask application
    systemctl start ${APP_NAME}.service
    sleep 3
    
    # Check if service is running
    if systemctl is-active --quiet ${APP_NAME}.service; then
        print_message "Flask application started successfully"
    else
        print_error "Flask application failed to start"
        print_info "Check logs: journalctl -u ${APP_NAME}.service -n 50"
        exit 1
    fi
    
    # Restart Nginx
    systemctl restart nginx
    
    if systemctl is-active --quiet nginx; then
        print_message "Nginx started successfully"
    else
        print_error "Nginx failed to start"
        exit 1
    fi
    
    print_message "All services started"
}

# Step 12: Verify Installation
verify_installation() {
    print_message "Step 12: Verifying installation..."
    
    echo ""
    print_info "=== Service Status ==="
    systemctl status ${APP_NAME}.service --no-pager | head -n 5
    echo ""
    systemctl status nginx --no-pager | head -n 5
    echo ""
    
    print_info "=== Open Ports ==="
    ufw status numbered
    echo ""
    
    print_info "=== Testing Local Connection ==="
    if curl -s http://localhost:${APP_PORT} > /dev/null; then
        print_message "Local Flask app is responding"
    else
        print_warning "Local Flask app not responding"
    fi
    
    print_info "=== Application URLs ==="
    echo "  Local:  http://localhost:${APP_PORT}"
    echo "  Domain: https://${DOMAIN}"
    echo ""
    
    print_message "Installation completed!"
}

# Step 13: Print Summary
print_summary() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "                    DEPLOYMENT SUMMARY"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "✅ Application installed at: ${APP_DIR}"
    echo "✅ Service name: ${APP_NAME}"
    echo "✅ Port: ${APP_PORT}"
    echo "✅ Domain: ${DOMAIN}"
    echo ""
    echo "📝 Useful Commands:"
    echo "  View logs:          sudo journalctl -u ${APP_NAME} -f"
    echo "  Restart app:        sudo systemctl restart ${APP_NAME}"
    echo "  Check app status:   sudo systemctl status ${APP_NAME}"
    echo "  Restart nginx:      sudo systemctl restart nginx"
    echo "  Check nginx config: sudo nginx -t"
    echo ""
    echo "🌐 Access Your Application:"
    echo "  https://${DOMAIN}"
    echo ""
    echo "📖 Next Steps:"
    echo "  1. Configure your application settings at ${APP_DIR}/data/config.json"
    echo "  2. Access the web interface and login"
    echo "  3. Configure Binance API keys in Settings"
    echo "  4. Review logs to ensure everything is working"
    echo ""
    echo "📚 Documentation:"
    echo "  - POST_DEPLOYMENT.md for maintenance instructions"
    echo "  - WEBHOOK_TEST_GUIDE.md for testing webhooks"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
}

# Main execution
main() {
    print_message "Starting Tony Binance Bot Deployment"
    echo ""
    
    check_root
    check_ubuntu
    
    # Run all steps
    update_system
    install_dependencies
    setup_app_directory
    copy_application_files
    setup_python_env
    create_data_directories
    create_systemd_service
    configure_nginx
    configure_firewall
    setup_ssl
    start_services
    verify_installation
    print_summary
    
    print_message "Deployment completed successfully!"
}

# Run main function
main

