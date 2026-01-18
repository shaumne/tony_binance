#!/bin/bash
# Trailing Stop Fix Deployment Script
# Bu script düzeltilmiş binance_handler.py dosyasını deploy eder

echo "=========================================="
echo "TRAILING STOP FIX DEPLOYMENT"
echo "=========================================="
echo ""

# Renkli çıktı için
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Değişkenler
PROJECT_DIR="$HOME/tony_binance/tony_binance"
BACKUP_DIR="$HOME/tony_binance_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 1. Backup dizinini oluştur
echo -e "${YELLOW}[1/6]${NC} Creating backup directory..."
mkdir -p "$BACKUP_DIR"

# 2. Mevcut dosyayı yedekle
echo -e "${YELLOW}[2/6]${NC} Backing up current binance_handler.py..."
if [ -f "$PROJECT_DIR/binance_handler.py" ]; then
    cp "$PROJECT_DIR/binance_handler.py" "$BACKUP_DIR/binance_handler.py.backup.$TIMESTAMP"
    echo -e "${GREEN}✓${NC} Backup created: $BACKUP_DIR/binance_handler.py.backup.$TIMESTAMP"
else
    echo -e "${RED}✗${NC} Warning: binance_handler.py not found in $PROJECT_DIR"
fi

# 3. Yeni dosyayı kopyala
echo -e "${YELLOW}[3/6]${NC} Deploying fixed binance_handler.py..."
if [ -f "binance_handler.py" ]; then
    cp binance_handler.py "$PROJECT_DIR/binance_handler.py"
    echo -e "${GREEN}✓${NC} File deployed successfully"
else
    echo -e "${RED}✗${NC} Error: binance_handler.py not found in current directory"
    exit 1
fi

# 4. Dosya izinlerini ayarla
echo -e "${YELLOW}[4/6]${NC} Setting file permissions..."
chmod 644 "$PROJECT_DIR/binance_handler.py"
echo -e "${GREEN}✓${NC} Permissions set"

# 5. Servisi yeniden başlat
echo -e "${YELLOW}[5/6]${NC} Restarting tony_binance_bot service..."
if sudo systemctl restart tony_binance_bot 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Service restarted successfully"
    sleep 2
    sudo systemctl status tony_binance_bot --no-pager
elif pkill -f "python.*app.py" 2>/dev/null; then
    echo -e "${YELLOW}ℹ${NC} Killed existing process, starting new one..."
    cd "$PROJECT_DIR" && nohup python3 app.py > /dev/null 2>&1 &
    echo -e "${GREEN}✓${NC} New process started"
else
    echo -e "${RED}✗${NC} Failed to restart service. Please restart manually."
    exit 1
fi

# 6. Log dosyasını temizle (opsiyonel)
echo -e "${YELLOW}[6/6]${NC} Do you want to clear the log file for clean testing? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    > "$PROJECT_DIR/logs/app.log"
    echo -e "${GREEN}✓${NC} Log file cleared"
else
    echo -e "${YELLOW}ℹ${NC} Log file kept intact"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ DEPLOYMENT COMPLETED${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Monitor logs:"
echo "   tail -f $PROJECT_DIR/logs/app.log | grep -E '(TRAILING STOP|Algo Order API|✅|❌)'"
echo ""
echo "2. Check for successful trailing stops:"
echo "   grep 'Algo Order API\\|Trailing stop order placed' $PROJECT_DIR/logs/app.log | tail -n 20"
echo ""
echo "3. Check for errors:"
echo "   grep -E '(Error Code:|Error Message:)' $PROJECT_DIR/logs/app.log | tail -n 20"
echo ""
echo "4. Rollback if needed:"
echo "   cp $BACKUP_DIR/binance_handler.py.backup.$TIMESTAMP $PROJECT_DIR/binance_handler.py"
echo "   sudo systemctl restart tony_binance_bot"
echo ""
