from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import threading
import asyncio
import time
from datetime import datetime
import logging
import sys
from threading import Thread, Lock
import shutil

from models import User, Config, Position
from binance_handler import BinanceHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'binance_bot_secret_key_change_in_production')

# Add current year to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize data files
def init_data_files():
    if not os.path.exists('data'):
        os.makedirs('data')
    
    if not os.path.exists('data/users.json'):
        with open('data/users.json', 'w') as f:
            json.dump({
                "admin": {
                    "password": generate_password_hash("admin"),
                    "is_admin": True
                }
            }, f, indent=2)
    
    if not os.path.exists('data/positions.json'):
        with open('data/positions.json', 'w') as f:
            json.dump([], f)

init_data_files()

# User loader
@login_manager.user_loader
def load_user(user_id):
    try:
        with open('data/users.json', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                logger.error("users.json is empty in user_loader")
                return None
            users = json.loads(content)
        
        if user_id in users:
            return User(user_id, users[user_id].get('is_admin', False))
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in user_loader: {str(e)}")
    except Exception as e:
        logger.error(f"Error in user_loader: {str(e)}")
    
    return None

# Binance handler instance
binance_handler = None

# Thread safety
webhook_locks = {}
webhook_locks_lock = Lock()

# Load configuration
def load_config():
    config_file = 'data/config.json'
    backup_file = 'data/config_backup.json'
    
    try:
        if not os.path.exists(config_file):
            logger.warning(f"Config file {config_file} does not exist, creating default")
            config_data = create_default_config()
            save_config_with_backup(config_data)
        else:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.warning(f"Config file {config_file} is empty, creating default")
                    config_data = create_default_config()
                    save_config_with_backup(config_data)
                else:
                    try:
                        config_data = json.loads(content)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error in {config_file}: {str(e)}")
                        if os.path.exists(backup_file):
                            try:
                                with open(backup_file, 'r', encoding='utf-8') as backup_f:
                                    backup_content = backup_f.read().strip()
                                    if backup_content:
                                        config_data = json.loads(backup_content)
                                        logger.info("Loaded config from backup")
                                    else:
                                        logger.warning("Backup is empty, creating default")
                                        config_data = create_default_config()
                                        save_config_with_backup(config_data)
                            except Exception as backup_err:
                                logger.error(f"Backup also failed: {str(backup_err)}")
                                config_data = create_default_config()
                                save_config_with_backup(config_data)
                        else:
                            logger.warning("No backup found, creating default")
                            config_data = create_default_config()
                            save_config_with_backup(config_data)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        config_data = create_default_config()
        try:
            save_config_with_backup(config_data)
        except Exception as save_err:
            logger.error(f"Could not save default config: {str(save_err)}")
    
    global binance_handler
    if config_data.get('binance_api_key') and config_data.get('binance_secret_key'):
        try:
            binance_handler = BinanceHandler(
                config_data['binance_api_key'],
                config_data['binance_secret_key'],
                config_data
            )
        except Exception as handler_err:
            logger.error(f"Failed to initialize BinanceHandler: {str(handler_err)}")
    
    return Config(**config_data)

def create_default_config():
    """Create default configuration for all 30 coins"""
    config = {
        "binance_api_key": "",
        "binance_secret_key": "",
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        "leverage": 10,
        "order_size_percentage": 10.0,
        "max_daily_trades": 30,
        "max_open_positions": 5,
        "enable_trading": False,
        "enable_webhook_close_signals": False,
        "atr_period": 14,
        "atr_tp_multiplier": 2.5,
        "atr_sl_multiplier": 3.0,
        "auto_position_switch": True,
        "allow_long_only": False,
        "allow_short_only": False
    }
    
    # USDT coins
    usdt_coins = ['btc', 'eth', 'xrp', 'ada', 'dot', 'xlm', 'imx', 'doge', 'inj', 'ldo', 'arb', 'uni', 'sol', 'bnb', 'fet']
    for coin in usdt_coins:
        config[f'{coin}_atr_period'] = 14
        config[f'{coin}_atr_tp_multiplier'] = 2.5
        config[f'{coin}_atr_sl_multiplier'] = 3.0
        config[f'{coin}_order_size_percentage'] = 10.0
        config[f'{coin}_leverage'] = 10
        config[f'{coin}_enable_trading'] = True
        config[f'{coin}_product_type'] = 'USDT-FUTURES'
    
    # USDC coins
    usdc_coins = ['btcusdc', 'ethusdc', 'solusdc', 'aaveusdc', 'bchusdc', 'xrpusdc', 'adausdc', 'avaxusdc', 'linkusdc', 'arbusdc', 'uniusdc', 'crvusdc', 'tiausdc', 'bnbusdc', 'filusdc']
    for coin in usdc_coins:
        config[f'{coin}_atr_period'] = 14
        config[f'{coin}_atr_tp_multiplier'] = 2.5
        config[f'{coin}_atr_sl_multiplier'] = 3.0
        config[f'{coin}_order_size_percentage'] = 10.0
        config[f'{coin}_leverage'] = 10
        config[f'{coin}_enable_trading'] = True
        config[f'{coin}_product_type'] = 'USDC-FUTURES'
    
    return config

def save_config_with_backup(config_data):
    """Save config with backup"""
    config_file = 'data/config.json'
    backup_file = 'data/config_backup.json'
    
    try:
        # Create backup if config exists
        if os.path.exists(config_file):
            try:
                shutil.copy2(config_file, backup_file)
            except Exception as backup_err:
                logger.warning(f"Could not create backup: {str(backup_err)}")
        
        # Save new config
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        raise

# Telegram notification
async def send_telegram_notification(message):
    config = load_config()
    if config.telegram_bot_token and config.telegram_chat_id:
        try:
            from telegram import Bot
            bot = Bot(token=config.telegram_bot_token)
            
            chat_id = config.telegram_chat_id
            if chat_id.isdigit() and chat_id.startswith("100"):
                chat_id = "-" + chat_id
            
            await bot.send_message(chat_id=chat_id, text=message)
            logger.info("Telegram notification sent")
        except Exception as e:
            logger.error(f"Failed to send Telegram: {str(e)}")

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            with open('data/users.json', 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.error("users.json is empty")
                    flash('System error: user database is empty', 'danger')
                    return render_template('login.html')
                users = json.loads(content)
            
            if username in users and check_password_hash(users[username]['password'], password):
                user = User(username, users[username].get('is_admin', False))
                login_user(user)
                return redirect(url_for('dashboard'))
            
            flash('Invalid credentials', 'danger')
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in users.json: {str(e)}")
            flash('System error: corrupted user database', 'danger')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('System error during login', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'danger')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'danger')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('change_password.html')
        
        if current_password == new_password:
            flash('New password must be different from current password', 'warning')
            return render_template('change_password.html')
        
        # Load users and verify current password
        try:
            with open('data/users.json', 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    flash('System error: user database is empty', 'danger')
                    return render_template('change_password.html')
                users = json.loads(content)
            
            username = current_user.id
            
            if username not in users:
                flash('User not found', 'danger')
                return render_template('change_password.html')
            
            # Verify current password
            if not check_password_hash(users[username]['password'], current_password):
                flash('Current password is incorrect', 'danger')
                return render_template('change_password.html')
            
            # Update password
            users[username]['password'] = generate_password_hash(new_password)
            
            # Save users
            with open('data/users.json', 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
            
            flash('Password changed successfully!', 'success')
            logger.info(f"Password changed for user: {username}")
            return redirect(url_for('dashboard'))
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in users.json: {str(e)}")
            flash('System error: unable to read user database', 'danger')
            return render_template('change_password.html')
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            flash('An error occurred while changing password', 'danger')
            return render_template('change_password.html')
    
    return render_template('change_password.html')

@app.route('/dashboard')
@login_required
def dashboard():
    config = load_config()
    
    positions = []
    usdt_balance = 0
    usdt_equity = 0
    usdt_unrealized_pnl = 0
    usdc_balance = 0
    usdc_equity = 0
    usdc_unrealized_pnl = 0
    
    if binance_handler:
        try:
            # Get positions
            api_positions = binance_handler.get_open_positions()
            if api_positions:
                positions = binance_handler.update_dashboard_positions(api_positions)
            
            # Get balances
            usdt_balance, usdt_equity, usdt_unrealized_pnl = binance_handler.get_account_balance('USDT')
            usdc_balance, usdc_equity, usdc_unrealized_pnl = binance_handler.get_account_balance('USDC')
            
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            flash('Error retrieving data', 'danger')
    
    # Calculate total balance (USDT equity + USDC equity)
    total_balance = usdt_equity + usdc_equity
    
    return render_template(
        'dashboard.html',
        config=config,
        positions=positions,
        account_balance=usdt_balance,
        equity=usdt_equity,
        unrealized_pnl=usdt_unrealized_pnl,
        usdc_balance=usdc_balance,
        usdc_equity=usdc_equity,
        usdc_unrealized_pnl=usdc_unrealized_pnl,
        total_balance=total_balance
    )

@app.route('/close_position', methods=['POST'])
@login_required
def close_position():
    symbol = request.form.get('symbol')
    side = request.form.get('side')
    quantity = request.form.get('quantity')
    
    if not all([symbol, side, quantity]):
        flash('Missing position information', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        if binance_handler:
            close_side = f"close_{side.lower()}"
            order_result = binance_handler.place_order(symbol, close_side, quantity=float(quantity))
            
            if order_result and not 'error' in order_result:
                flash(f"Successfully closed {side} position for {symbol}", 'success')
            else:
                flash('Failed to close position', 'danger')
        else:
            flash('Trading system not initialized', 'danger')
    except Exception as e:
        logger.error(f"Error closing position: {str(e)}")
        flash(f"Error: {str(e)}", 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('dashboard'))
    
    config = load_config()
    
    if request.method == 'POST':
        updated_config = {
            "binance_api_key": request.form.get('binance_api_key'),
            "binance_secret_key": request.form.get('binance_secret_key'),
            "telegram_bot_token": request.form.get('telegram_bot_token'),
            "telegram_chat_id": request.form.get('telegram_chat_id'),
            "leverage": int(request.form.get('leverage', 10)),
            "order_size_percentage": float(request.form.get('order_size_percentage', 10)),
            "max_daily_trades": int(request.form.get('max_daily_trades', 30)),
            "max_open_positions": int(request.form.get('max_open_positions', 5)),
            "enable_trading": 'enable_trading' in request.form,
            "enable_webhook_close_signals": 'enable_webhook_close_signals' in request.form,
            "auto_position_switch": 'auto_position_switch' in request.form,
            "allow_long_only": 'allow_long_only' in request.form,
            "allow_short_only": 'allow_short_only' in request.form,
        }
        
        # USDT coins
        usdt_coins = ['btc', 'eth', 'xrp', 'ada', 'dot', 'xlm', 'imx', 'doge', 'inj', 'ldo', 'arb', 'uni', 'sol', 'bnb', 'fet']
        for coin in usdt_coins:
            updated_config[f'{coin}_atr_period'] = int(request.form.get(f'{coin}_atr_period', 14))
            updated_config[f'{coin}_atr_tp_multiplier'] = float(request.form.get(f'{coin}_atr_tp_multiplier', 2.5))
            updated_config[f'{coin}_atr_sl_multiplier'] = float(request.form.get(f'{coin}_atr_sl_multiplier', 3.0))
            updated_config[f'{coin}_order_size_percentage'] = float(request.form.get(f'{coin}_order_size_percentage', 10.0))
            updated_config[f'{coin}_leverage'] = int(request.form.get(f'{coin}_leverage', 10))
            updated_config[f'{coin}_enable_trading'] = f'{coin}_enable_trading' in request.form
            updated_config[f'{coin}_product_type'] = 'USDT-FUTURES'
        
        # USDC coins
        usdc_coins = ['btcusdc', 'ethusdc', 'solusdc', 'aaveusdc', 'bchusdc', 'xrpusdc', 'adausdc', 'avaxusdc', 'linkusdc', 'arbusdc', 'uniusdc', 'crvusdc', 'tiausdc', 'bnbusdc', 'filusdc']
        for coin in usdc_coins:
            updated_config[f'{coin}_atr_period'] = int(request.form.get(f'{coin}_atr_period', 14))
            updated_config[f'{coin}_atr_tp_multiplier'] = float(request.form.get(f'{coin}_atr_tp_multiplier', 2.5))
            updated_config[f'{coin}_atr_sl_multiplier'] = float(request.form.get(f'{coin}_atr_sl_multiplier', 3.0))
            updated_config[f'{coin}_order_size_percentage'] = float(request.form.get(f'{coin}_order_size_percentage', 10.0))
            updated_config[f'{coin}_leverage'] = int(request.form.get(f'{coin}_leverage', 10))
            updated_config[f'{coin}_enable_trading'] = f'{coin}_enable_trading' in request.form
            updated_config[f'{coin}_product_type'] = 'USDC-FUTURES'
        
        save_config_with_backup(updated_config)
        
        # Reinitialize handler
        global binance_handler
        binance_handler = BinanceHandler(
            updated_config['binance_api_key'],
            updated_config['binance_secret_key'],
            updated_config
        )
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', config=config)

@app.route('/webhook', methods=['POST'])
def webhook():
    if not request.json:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    
    config = load_config()
    if not config.enable_trading:
        return jsonify({"status": "error", "message": "Trading disabled"}), 200
    
    try:
        data = request.json
        logger.info(f"Webhook received: {data}")
        
        # 🔥 NEW: Check for Trailing Stop Strategy
        # Support both 'trailType' and 'type' keys for compatibility
        trail_type = data.get('trailType') or data.get('type')
        if trail_type == 'TRAILING_STOP_MARKET':
            logger.info("🚀 TRAILING STOP STRATEGY DETECTED")
            
            # Clean .P extension from symbol if present (e.g., FETUSDT.P -> FETUSDT)
            if 'symbol' in data:
                data['symbol'] = data['symbol'].replace('.P', '').replace('.p', '')
            
            # Normalize action to lowercase
            if 'action' in data:
                data['action'] = data['action'].lower()
            
            # Add trailType if missing (for compatibility)
            if 'trailType' not in data and 'type' in data:
                data['trailType'] = data['type']
            
            # Add workingType if missing (default to MARK_PRICE)
            if 'workingType' not in data:
                data['workingType'] = 'MARK_PRICE'
                logger.info(f"⚠️ workingType not provided, defaulting to MARK_PRICE")
            
            # Validate required fields (activationPrice is optional - auto-calculated if not provided)
            required_fields = ['symbol', 'side', 'action', 'callbackRate']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return jsonify({
                    "status": "error", 
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400
            
            # Process Trailing Stop Strategy
            if binance_handler:
                def get_symbol_lock(symbol):
                    with webhook_locks_lock:
                        if symbol not in webhook_locks:
                            webhook_locks[symbol] = Lock()
                        return webhook_locks[symbol]
                
                symbol_lock = get_symbol_lock(data['symbol'])
                
                with symbol_lock:
                    result = binance_handler.place_trailing_stop_strategy(data)
                
                if result and result.get('success'):
                    return jsonify({
                        "status": "success",
                        "message": result.get('message', 'Trailing stop order placed'),
                        "order_id": result.get('order_id'),
                        "trailing_stop_id": result.get('trailing_stop_id')
                    }), 200
                elif result and result.get('error'):
                    return jsonify({
                        "status": "error",
                        "message": result.get('error')
                    }), 200
                else:
                    return jsonify({
                        "status": "error",
                        "message": "Trailing stop order failed - check logs"
                    }), 200
            else:
                return jsonify({"status": "error", "message": "Handler not initialized"}), 500
        
        # 📌 STANDARD STRATEGY (Old Logic)
        # Extract signal
        signal = data.get('signal') or data.get('message')
        
        if not signal:
            return jsonify({"status": "error", "message": "No signal found"}), 400
        
        parts = signal.strip().split('/')
        if len(parts) != 3:
            return jsonify({"status": "error", "message": "Invalid signal format"}), 400
        
        symbol, direction, action = [part.strip().lower() for part in parts]
        symbol = symbol.upper()
        # Clean .P extension from symbol if present (e.g., FETUSDT.P -> FETUSDT)
        symbol = symbol.replace('.P', '').replace('.p', '')
        
        # Ensure proper symbol format
        if not symbol.endswith('USDT') and not symbol.endswith('USDC'):
            symbol = f"{symbol}USDT"
        
        if direction not in ['long', 'short'] or action not in ['open', 'close']:
            return jsonify({"status": "error", "message": "Invalid direction/action"}), 400
        
        # Master signal filters
        if action == 'open':
            if config.allow_long_only and direction == 'short':
                return jsonify({"status": "filtered", "message": "SHORT disabled"}), 200
            if config.allow_short_only and direction == 'long':
                return jsonify({"status": "filtered", "message": "LONG disabled"}), 200
        
        # Process signal
        if binance_handler:
            def get_symbol_lock(symbol):
                with webhook_locks_lock:
                    if symbol not in webhook_locks:
                        webhook_locks[symbol] = Lock()
                    return webhook_locks[symbol]
            
            symbol_lock = get_symbol_lock(symbol)
            
            with symbol_lock:
                result = process_signal(symbol, direction, action)
            
            if result and result.get('success'):
                return jsonify({
                    "status": "success",
                    "message": result.get('message', 'Order processed'),
                    "order_id": result.get('order_id')
                }), 200
            elif result and result.get('error'):
                return jsonify({
                    "status": "error",
                    "message": result.get('error')
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "Order processing failed - check logs"
                }), 200
        else:
            return jsonify({"status": "error", "message": "Handler not initialized"}), 500
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/test_telegram', methods=['GET', 'POST'])
@login_required
def test_telegram():
    """Test Telegram notification endpoint"""
    try:
        config = load_config()
        
        if not binance_handler:
            return jsonify({
                "status": "error",
                "message": "Binance handler not initialized"
            }), 500
        
        # Get test message from request or use default
        if request.method == 'POST' and request.json:
            test_message = request.json.get('message', 'Test notification from Binance Bot')
        else:
            test_message = "🧪 TEST NOTIFICATION\n\nThis is a test message from Binance Trading Bot.\n\nIf you receive this, Telegram integration is working correctly!"
        
        # Send notification
        try:
            import asyncio
            import threading
            
            def send_in_thread():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(binance_handler.send_telegram_notification(test_message))
                    finally:
                        loop.close()
                except Exception as e:
                    logger.error(f"Error in test notification thread: {str(e)}")
            
            thread = threading.Thread(target=send_in_thread, daemon=True)
            thread.start()
            thread.join(timeout=10)  # Wait max 10 seconds
            
            return jsonify({
                "status": "success",
                "message": "Test notification sent",
                "telegram_config": {
                    "bot_token": "Set" if config.telegram_bot_token else "Not Set",
                    "chat_id": config.telegram_chat_id if config.telegram_chat_id else "Not Set"
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Error sending test notification: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({
                "status": "error",
                "message": f"Failed to send notification: {str(e)}",
                "telegram_config": {
                    "bot_token": "Set" if config.telegram_bot_token else "Not Set",
                    "chat_id": config.telegram_chat_id if config.telegram_chat_id else "Not Set"
                }
            }), 500
            
    except Exception as e:
        logger.error(f"Test telegram error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def process_signal(symbol, direction, action):
    """Process trading signal"""
    logger.info(f"Processing: {symbol}/{direction}/{action}")
    
    if not binance_handler:
        logger.error("Binance handler not initialized")
        return {"success": False, "error": "Binance handler not initialized"}
    
    try:
        config = load_config()
        
        # Check if trading is enabled
        if not config.enable_trading:
            logger.warning("Trading is globally disabled")
            return {"success": False, "error": "Trading is globally disabled"}
        
        # Check daily limits
        if action == 'open':
            # Can add daily trade limit check here
            pass
        
        # Check position limits
        current_positions = binance_handler.get_open_positions()
        if action == 'open' and len(current_positions) >= config.max_open_positions:
            logger.info("Max positions reached")
            return {"success": False, "error": f"Max positions reached ({config.max_open_positions})"}
        
        # Execute trade
        side = f"{action}_{direction}"
        order_result = binance_handler.place_order(symbol, side)
        
        if order_result and 'error' not in order_result:
            order_id = order_result.get('orderId', 'N/A')
            logger.info(f"✅ Order executed successfully: {order_id}")
            return {
                "success": True,
                "message": f"Order executed: {order_id}",
                "order_id": order_id,
                "symbol": symbol,
                "side": side
            }
        else:
            error_msg = order_result.get('error', 'Unknown error') if order_result else 'No response from exchange'
            logger.error(f"❌ Order failed: {error_msg}")
            return {"success": False, "error": error_msg}
            
    except Exception as e:
        error_msg = f"Signal processing error: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def start_position_monitor(binance_handler):
    """Start position monitoring"""
    monitor_thread = Thread(target=binance_handler.monitor_positions, daemon=True)
    monitor_thread.start()

# Initialize
config = load_config()
if binance_handler:
    start_position_monitor(binance_handler)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
