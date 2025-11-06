from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username, is_admin=False):
        self.id = username
        self.username = username
        self.is_admin = is_admin

class Config:
    def __init__(self, **kwargs):
        self.binance_api_key = kwargs.get('binance_api_key', '')
        self.binance_secret_key = kwargs.get('binance_secret_key', '')
        self.telegram_bot_token = kwargs.get('telegram_bot_token', '')
        self.telegram_chat_id = kwargs.get('telegram_chat_id', '')
        self.leverage = kwargs.get('leverage', 5)
        self.order_size_percentage = kwargs.get('order_size_percentage', 10)
        self.max_daily_trades = kwargs.get('max_daily_trades', 10)
        self.max_open_positions = kwargs.get('max_open_positions', 10)
        self.enable_trading = kwargs.get('enable_trading', True)
        self.enable_webhook_close_signals = kwargs.get('enable_webhook_close_signals', False)
        self.atr_period = kwargs.get('atr_period', 14)
        self.atr_tp_multiplier = kwargs.get('atr_tp_multiplier', 2.5)
        self.atr_sl_multiplier = kwargs.get('atr_sl_multiplier', 3.0)
        self.auto_position_switch = kwargs.get('auto_position_switch', True)
        
        # Master Signal Settings
        self.allow_long_only = kwargs.get('allow_long_only', False)
        self.allow_short_only = kwargs.get('allow_short_only', False)
        
        # USDT-Margined Futures (15 coins)
        # BTC
        self.btc_atr_period = kwargs.get('btc_atr_period', 14)
        self.btc_atr_tp_multiplier = kwargs.get('btc_atr_tp_multiplier', 2.0)
        self.btc_atr_sl_multiplier = kwargs.get('btc_atr_sl_multiplier', 3.0)
        self.btc_order_size_percentage = kwargs.get('btc_order_size_percentage', 10.0)
        self.btc_leverage = kwargs.get('btc_leverage', 10)
        self.btc_enable_trading = kwargs.get('btc_enable_trading', True)
        self.btc_product_type = kwargs.get('btc_product_type', 'USDT-FUTURES')
        
        # ETH
        self.eth_atr_period = kwargs.get('eth_atr_period', 14)
        self.eth_atr_tp_multiplier = kwargs.get('eth_atr_tp_multiplier', 2.0)
        self.eth_atr_sl_multiplier = kwargs.get('eth_atr_sl_multiplier', 3.0)
        self.eth_order_size_percentage = kwargs.get('eth_order_size_percentage', 10.0)
        self.eth_leverage = kwargs.get('eth_leverage', 10)
        self.eth_enable_trading = kwargs.get('eth_enable_trading', True)
        self.eth_product_type = kwargs.get('eth_product_type', 'USDT-FUTURES')
        
        # XRP
        self.xrp_atr_period = kwargs.get('xrp_atr_period', 14)
        self.xrp_atr_tp_multiplier = kwargs.get('xrp_atr_tp_multiplier', 2.5)
        self.xrp_atr_sl_multiplier = kwargs.get('xrp_atr_sl_multiplier', 3.0)
        self.xrp_order_size_percentage = kwargs.get('xrp_order_size_percentage', 10.0)
        self.xrp_leverage = kwargs.get('xrp_leverage', 10)
        self.xrp_enable_trading = kwargs.get('xrp_enable_trading', True)
        self.xrp_product_type = kwargs.get('xrp_product_type', 'USDT-FUTURES')
        
        # ADA
        self.ada_atr_period = kwargs.get('ada_atr_period', 14)
        self.ada_atr_tp_multiplier = kwargs.get('ada_atr_tp_multiplier', 2.5)
        self.ada_atr_sl_multiplier = kwargs.get('ada_atr_sl_multiplier', 3.0)
        self.ada_order_size_percentage = kwargs.get('ada_order_size_percentage', 10.0)
        self.ada_leverage = kwargs.get('ada_leverage', 10)
        self.ada_enable_trading = kwargs.get('ada_enable_trading', True)
        self.ada_product_type = kwargs.get('ada_product_type', 'USDT-FUTURES')
        
        # DOT
        self.dot_atr_period = kwargs.get('dot_atr_period', 14)
        self.dot_atr_tp_multiplier = kwargs.get('dot_atr_tp_multiplier', 2.5)
        self.dot_atr_sl_multiplier = kwargs.get('dot_atr_sl_multiplier', 3.0)
        self.dot_order_size_percentage = kwargs.get('dot_order_size_percentage', 10.0)
        self.dot_leverage = kwargs.get('dot_leverage', 10)
        self.dot_enable_trading = kwargs.get('dot_enable_trading', True)
        self.dot_product_type = kwargs.get('dot_product_type', 'USDT-FUTURES')
        
        # XLM
        self.xlm_atr_period = kwargs.get('xlm_atr_period', 14)
        self.xlm_atr_tp_multiplier = kwargs.get('xlm_atr_tp_multiplier', 2.5)
        self.xlm_atr_sl_multiplier = kwargs.get('xlm_atr_sl_multiplier', 3.0)
        self.xlm_order_size_percentage = kwargs.get('xlm_order_size_percentage', 10.0)
        self.xlm_leverage = kwargs.get('xlm_leverage', 10)
        self.xlm_enable_trading = kwargs.get('xlm_enable_trading', True)
        self.xlm_product_type = kwargs.get('xlm_product_type', 'USDT-FUTURES')
        
        # IMX
        self.imx_atr_period = kwargs.get('imx_atr_period', 14)
        self.imx_atr_tp_multiplier = kwargs.get('imx_atr_tp_multiplier', 2.5)
        self.imx_atr_sl_multiplier = kwargs.get('imx_atr_sl_multiplier', 3.0)
        self.imx_order_size_percentage = kwargs.get('imx_order_size_percentage', 10.0)
        self.imx_leverage = kwargs.get('imx_leverage', 10)
        self.imx_enable_trading = kwargs.get('imx_enable_trading', True)
        self.imx_product_type = kwargs.get('imx_product_type', 'USDT-FUTURES')
        
        # DOGE
        self.doge_atr_period = kwargs.get('doge_atr_period', 14)
        self.doge_atr_tp_multiplier = kwargs.get('doge_atr_tp_multiplier', 2.5)
        self.doge_atr_sl_multiplier = kwargs.get('doge_atr_sl_multiplier', 3.0)
        self.doge_order_size_percentage = kwargs.get('doge_order_size_percentage', 10.0)
        self.doge_leverage = kwargs.get('doge_leverage', 10)
        self.doge_enable_trading = kwargs.get('doge_enable_trading', True)
        self.doge_product_type = kwargs.get('doge_product_type', 'USDT-FUTURES')
        
        # INJ
        self.inj_atr_period = kwargs.get('inj_atr_period', 14)
        self.inj_atr_tp_multiplier = kwargs.get('inj_atr_tp_multiplier', 2.5)
        self.inj_atr_sl_multiplier = kwargs.get('inj_atr_sl_multiplier', 3.0)
        self.inj_order_size_percentage = kwargs.get('inj_order_size_percentage', 10.0)
        self.inj_leverage = kwargs.get('inj_leverage', 10)
        self.inj_enable_trading = kwargs.get('inj_enable_trading', True)
        self.inj_product_type = kwargs.get('inj_product_type', 'USDT-FUTURES')
        
        # LDO
        self.ldo_atr_period = kwargs.get('ldo_atr_period', 14)
        self.ldo_atr_tp_multiplier = kwargs.get('ldo_atr_tp_multiplier', 2.5)
        self.ldo_atr_sl_multiplier = kwargs.get('ldo_atr_sl_multiplier', 3.0)
        self.ldo_order_size_percentage = kwargs.get('ldo_order_size_percentage', 10.0)
        self.ldo_leverage = kwargs.get('ldo_leverage', 10)
        self.ldo_enable_trading = kwargs.get('ldo_enable_trading', True)
        self.ldo_product_type = kwargs.get('ldo_product_type', 'USDT-FUTURES')
        
        # ARB
        self.arb_atr_period = kwargs.get('arb_atr_period', 14)
        self.arb_atr_tp_multiplier = kwargs.get('arb_atr_tp_multiplier', 2.5)
        self.arb_atr_sl_multiplier = kwargs.get('arb_atr_sl_multiplier', 3.0)
        self.arb_order_size_percentage = kwargs.get('arb_order_size_percentage', 10.0)
        self.arb_leverage = kwargs.get('arb_leverage', 10)
        self.arb_enable_trading = kwargs.get('arb_enable_trading', True)
        self.arb_product_type = kwargs.get('arb_product_type', 'USDT-FUTURES')
        
        # UNI
        self.uni_atr_period = kwargs.get('uni_atr_period', 14)
        self.uni_atr_tp_multiplier = kwargs.get('uni_atr_tp_multiplier', 2.5)
        self.uni_atr_sl_multiplier = kwargs.get('uni_atr_sl_multiplier', 3.0)
        self.uni_order_size_percentage = kwargs.get('uni_order_size_percentage', 10.0)
        self.uni_leverage = kwargs.get('uni_leverage', 10)
        self.uni_enable_trading = kwargs.get('uni_enable_trading', True)
        self.uni_product_type = kwargs.get('uni_product_type', 'USDT-FUTURES')
        
        # SOL
        self.sol_atr_period = kwargs.get('sol_atr_period', 14)
        self.sol_atr_tp_multiplier = kwargs.get('sol_atr_tp_multiplier', 2.0)
        self.sol_atr_sl_multiplier = kwargs.get('sol_atr_sl_multiplier', 3.0)
        self.sol_order_size_percentage = kwargs.get('sol_order_size_percentage', 10.0)
        self.sol_leverage = kwargs.get('sol_leverage', 10)
        self.sol_enable_trading = kwargs.get('sol_enable_trading', True)
        self.sol_product_type = kwargs.get('sol_product_type', 'USDT-FUTURES')
        
        # BNB
        self.bnb_atr_period = kwargs.get('bnb_atr_period', 14)
        self.bnb_atr_tp_multiplier = kwargs.get('bnb_atr_tp_multiplier', 2.0)
        self.bnb_atr_sl_multiplier = kwargs.get('bnb_atr_sl_multiplier', 3.0)
        self.bnb_order_size_percentage = kwargs.get('bnb_order_size_percentage', 10.0)
        self.bnb_leverage = kwargs.get('bnb_leverage', 10)
        self.bnb_enable_trading = kwargs.get('bnb_enable_trading', True)
        self.bnb_product_type = kwargs.get('bnb_product_type', 'USDT-FUTURES')
        
        # FET
        self.fet_atr_period = kwargs.get('fet_atr_period', 14)
        self.fet_atr_tp_multiplier = kwargs.get('fet_atr_tp_multiplier', 2.5)
        self.fet_atr_sl_multiplier = kwargs.get('fet_atr_sl_multiplier', 3.0)
        self.fet_order_size_percentage = kwargs.get('fet_order_size_percentage', 10.0)
        self.fet_leverage = kwargs.get('fet_leverage', 10)
        self.fet_enable_trading = kwargs.get('fet_enable_trading', True)
        self.fet_product_type = kwargs.get('fet_product_type', 'USDT-FUTURES')
        
        # USDC-Margined Futures (15 coins)
        # BTC (USDC)
        self.btcusdc_atr_period = kwargs.get('btcusdc_atr_period', 14)
        self.btcusdc_atr_tp_multiplier = kwargs.get('btcusdc_atr_tp_multiplier', 2.0)
        self.btcusdc_atr_sl_multiplier = kwargs.get('btcusdc_atr_sl_multiplier', 3.0)
        self.btcusdc_order_size_percentage = kwargs.get('btcusdc_order_size_percentage', 10.0)
        self.btcusdc_leverage = kwargs.get('btcusdc_leverage', 10)
        self.btcusdc_enable_trading = kwargs.get('btcusdc_enable_trading', True)
        self.btcusdc_product_type = kwargs.get('btcusdc_product_type', 'USDC-FUTURES')
        
        # ETH (USDC)
        self.ethusdc_atr_period = kwargs.get('ethusdc_atr_period', 14)
        self.ethusdc_atr_tp_multiplier = kwargs.get('ethusdc_atr_tp_multiplier', 2.0)
        self.ethusdc_atr_sl_multiplier = kwargs.get('ethusdc_atr_sl_multiplier', 3.0)
        self.ethusdc_order_size_percentage = kwargs.get('ethusdc_order_size_percentage', 10.0)
        self.ethusdc_leverage = kwargs.get('ethusdc_leverage', 10)
        self.ethusdc_enable_trading = kwargs.get('ethusdc_enable_trading', True)
        self.ethusdc_product_type = kwargs.get('ethusdc_product_type', 'USDC-FUTURES')
        
        # SOL (USDC)
        self.solusdc_atr_period = kwargs.get('solusdc_atr_period', 14)
        self.solusdc_atr_tp_multiplier = kwargs.get('solusdc_atr_tp_multiplier', 2.0)
        self.solusdc_atr_sl_multiplier = kwargs.get('solusdc_atr_sl_multiplier', 3.0)
        self.solusdc_order_size_percentage = kwargs.get('solusdc_order_size_percentage', 10.0)
        self.solusdc_leverage = kwargs.get('solusdc_leverage', 10)
        self.solusdc_enable_trading = kwargs.get('solusdc_enable_trading', True)
        self.solusdc_product_type = kwargs.get('solusdc_product_type', 'USDC-FUTURES')
        
        # AAVE (USDC)
        self.aaveusdc_atr_period = kwargs.get('aaveusdc_atr_period', 14)
        self.aaveusdc_atr_tp_multiplier = kwargs.get('aaveusdc_atr_tp_multiplier', 2.5)
        self.aaveusdc_atr_sl_multiplier = kwargs.get('aaveusdc_atr_sl_multiplier', 3.0)
        self.aaveusdc_order_size_percentage = kwargs.get('aaveusdc_order_size_percentage', 10.0)
        self.aaveusdc_leverage = kwargs.get('aaveusdc_leverage', 10)
        self.aaveusdc_enable_trading = kwargs.get('aaveusdc_enable_trading', True)
        self.aaveusdc_product_type = kwargs.get('aaveusdc_product_type', 'USDC-FUTURES')
        
        # BCH (USDC)
        self.bchusdc_atr_period = kwargs.get('bchusdc_atr_period', 14)
        self.bchusdc_atr_tp_multiplier = kwargs.get('bchusdc_atr_tp_multiplier', 2.5)
        self.bchusdc_atr_sl_multiplier = kwargs.get('bchusdc_atr_sl_multiplier', 3.0)
        self.bchusdc_order_size_percentage = kwargs.get('bchusdc_order_size_percentage', 10.0)
        self.bchusdc_leverage = kwargs.get('bchusdc_leverage', 10)
        self.bchusdc_enable_trading = kwargs.get('bchusdc_enable_trading', True)
        self.bchusdc_product_type = kwargs.get('bchusdc_product_type', 'USDC-FUTURES')
        
        # XRP (USDC)
        self.xrpusdc_atr_period = kwargs.get('xrpusdc_atr_period', 14)
        self.xrpusdc_atr_tp_multiplier = kwargs.get('xrpusdc_atr_tp_multiplier', 2.5)
        self.xrpusdc_atr_sl_multiplier = kwargs.get('xrpusdc_atr_sl_multiplier', 3.0)
        self.xrpusdc_order_size_percentage = kwargs.get('xrpusdc_order_size_percentage', 10.0)
        self.xrpusdc_leverage = kwargs.get('xrpusdc_leverage', 10)
        self.xrpusdc_enable_trading = kwargs.get('xrpusdc_enable_trading', True)
        self.xrpusdc_product_type = kwargs.get('xrpusdc_product_type', 'USDC-FUTURES')
        
        # ADA (USDC)
        self.adausdc_atr_period = kwargs.get('adausdc_atr_period', 14)
        self.adausdc_atr_tp_multiplier = kwargs.get('adausdc_atr_tp_multiplier', 2.5)
        self.adausdc_atr_sl_multiplier = kwargs.get('adausdc_atr_sl_multiplier', 3.0)
        self.adausdc_order_size_percentage = kwargs.get('adausdc_order_size_percentage', 10.0)
        self.adausdc_leverage = kwargs.get('adausdc_leverage', 10)
        self.adausdc_enable_trading = kwargs.get('adausdc_enable_trading', True)
        self.adausdc_product_type = kwargs.get('adausdc_product_type', 'USDC-FUTURES')
        
        # AVAX (USDC)
        self.avaxusdc_atr_period = kwargs.get('avaxusdc_atr_period', 14)
        self.avaxusdc_atr_tp_multiplier = kwargs.get('avaxusdc_atr_tp_multiplier', 2.5)
        self.avaxusdc_atr_sl_multiplier = kwargs.get('avaxusdc_atr_sl_multiplier', 3.0)
        self.avaxusdc_order_size_percentage = kwargs.get('avaxusdc_order_size_percentage', 10.0)
        self.avaxusdc_leverage = kwargs.get('avaxusdc_leverage', 10)
        self.avaxusdc_enable_trading = kwargs.get('avaxusdc_enable_trading', True)
        self.avaxusdc_product_type = kwargs.get('avaxusdc_product_type', 'USDC-FUTURES')
        
        # LINK (USDC)
        self.linkusdc_atr_period = kwargs.get('linkusdc_atr_period', 14)
        self.linkusdc_atr_tp_multiplier = kwargs.get('linkusdc_atr_tp_multiplier', 2.5)
        self.linkusdc_atr_sl_multiplier = kwargs.get('linkusdc_atr_sl_multiplier', 3.0)
        self.linkusdc_order_size_percentage = kwargs.get('linkusdc_order_size_percentage', 10.0)
        self.linkusdc_leverage = kwargs.get('linkusdc_leverage', 10)
        self.linkusdc_enable_trading = kwargs.get('linkusdc_enable_trading', True)
        self.linkusdc_product_type = kwargs.get('linkusdc_product_type', 'USDC-FUTURES')
        
        # ARB (USDC)
        self.arbusdc_atr_period = kwargs.get('arbusdc_atr_period', 14)
        self.arbusdc_atr_tp_multiplier = kwargs.get('arbusdc_atr_tp_multiplier', 2.5)
        self.arbusdc_atr_sl_multiplier = kwargs.get('arbusdc_atr_sl_multiplier', 3.0)
        self.arbusdc_order_size_percentage = kwargs.get('arbusdc_order_size_percentage', 10.0)
        self.arbusdc_leverage = kwargs.get('arbusdc_leverage', 10)
        self.arbusdc_enable_trading = kwargs.get('arbusdc_enable_trading', True)
        self.arbusdc_product_type = kwargs.get('arbusdc_product_type', 'USDC-FUTURES')
        
        # UNI (USDC)
        self.uniusdc_atr_period = kwargs.get('uniusdc_atr_period', 14)
        self.uniusdc_atr_tp_multiplier = kwargs.get('uniusdc_atr_tp_multiplier', 2.5)
        self.uniusdc_atr_sl_multiplier = kwargs.get('uniusdc_atr_sl_multiplier', 3.0)
        self.uniusdc_order_size_percentage = kwargs.get('uniusdc_order_size_percentage', 10.0)
        self.uniusdc_leverage = kwargs.get('uniusdc_leverage', 10)
        self.uniusdc_enable_trading = kwargs.get('uniusdc_enable_trading', True)
        self.uniusdc_product_type = kwargs.get('uniusdc_product_type', 'USDC-FUTURES')
        
        # CRV (USDC)
        self.crvusdc_atr_period = kwargs.get('crvusdc_atr_period', 14)
        self.crvusdc_atr_tp_multiplier = kwargs.get('crvusdc_atr_tp_multiplier', 2.5)
        self.crvusdc_atr_sl_multiplier = kwargs.get('crvusdc_atr_sl_multiplier', 3.0)
        self.crvusdc_order_size_percentage = kwargs.get('crvusdc_order_size_percentage', 10.0)
        self.crvusdc_leverage = kwargs.get('crvusdc_leverage', 10)
        self.crvusdc_enable_trading = kwargs.get('crvusdc_enable_trading', True)
        self.crvusdc_product_type = kwargs.get('crvusdc_product_type', 'USDC-FUTURES')
        
        # TIA (USDC)
        self.tiausdc_atr_period = kwargs.get('tiausdc_atr_period', 14)
        self.tiausdc_atr_tp_multiplier = kwargs.get('tiausdc_atr_tp_multiplier', 2.5)
        self.tiausdc_atr_sl_multiplier = kwargs.get('tiausdc_atr_sl_multiplier', 3.0)
        self.tiausdc_order_size_percentage = kwargs.get('tiausdc_order_size_percentage', 10.0)
        self.tiausdc_leverage = kwargs.get('tiausdc_leverage', 10)
        self.tiausdc_enable_trading = kwargs.get('tiausdc_enable_trading', True)
        self.tiausdc_product_type = kwargs.get('tiausdc_product_type', 'USDC-FUTURES')
        
        # BNB (USDC)
        self.bnbusdc_atr_period = kwargs.get('bnbusdc_atr_period', 14)
        self.bnbusdc_atr_tp_multiplier = kwargs.get('bnbusdc_atr_tp_multiplier', 2.0)
        self.bnbusdc_atr_sl_multiplier = kwargs.get('bnbusdc_atr_sl_multiplier', 3.0)
        self.bnbusdc_order_size_percentage = kwargs.get('bnbusdc_order_size_percentage', 10.0)
        self.bnbusdc_leverage = kwargs.get('bnbusdc_leverage', 10)
        self.bnbusdc_enable_trading = kwargs.get('bnbusdc_enable_trading', True)
        self.bnbusdc_product_type = kwargs.get('bnbusdc_product_type', 'USDC-FUTURES')
        
        # FIL (USDC)
        self.filusdc_atr_period = kwargs.get('filusdc_atr_period', 14)
        self.filusdc_atr_tp_multiplier = kwargs.get('filusdc_atr_tp_multiplier', 2.5)
        self.filusdc_atr_sl_multiplier = kwargs.get('filusdc_atr_sl_multiplier', 3.0)
        self.filusdc_order_size_percentage = kwargs.get('filusdc_order_size_percentage', 10.0)
        self.filusdc_leverage = kwargs.get('filusdc_leverage', 10)
        self.filusdc_enable_trading = kwargs.get('filusdc_enable_trading', True)
        self.filusdc_product_type = kwargs.get('filusdc_product_type', 'USDC-FUTURES')

    def to_dict(self):
        return {
            'binance_api_key': self.binance_api_key,
            'binance_secret_key': self.binance_secret_key,
            'telegram_bot_token': self.telegram_bot_token,
            'telegram_chat_id': self.telegram_chat_id,
            'leverage': self.leverage,
            'order_size_percentage': self.order_size_percentage,
            'max_daily_trades': self.max_daily_trades,
            'max_open_positions': self.max_open_positions,
            'enable_trading': self.enable_trading,
            'enable_webhook_close_signals': self.enable_webhook_close_signals,
            'atr_period': self.atr_period,
            'atr_tp_multiplier': self.atr_tp_multiplier,
            'atr_sl_multiplier': self.atr_sl_multiplier,
            'auto_position_switch': self.auto_position_switch,
            # Master Signal Settings
            'allow_long_only': self.allow_long_only,
            'allow_short_only': self.allow_short_only,
            # USDT coins
            'btc_atr_period': self.btc_atr_period,
            'btc_atr_tp_multiplier': self.btc_atr_tp_multiplier,
            'btc_atr_sl_multiplier': self.btc_atr_sl_multiplier,
            'btc_order_size_percentage': self.btc_order_size_percentage,
            'btc_leverage': self.btc_leverage,
            'btc_enable_trading': self.btc_enable_trading,
            'btc_product_type': self.btc_product_type,
            'eth_atr_period': self.eth_atr_period,
            'eth_atr_tp_multiplier': self.eth_atr_tp_multiplier,
            'eth_atr_sl_multiplier': self.eth_atr_sl_multiplier,
            'eth_order_size_percentage': self.eth_order_size_percentage,
            'eth_leverage': self.eth_leverage,
            'eth_enable_trading': self.eth_enable_trading,
            'eth_product_type': self.eth_product_type,
            'xrp_atr_period': self.xrp_atr_period,
            'xrp_atr_tp_multiplier': self.xrp_atr_tp_multiplier,
            'xrp_atr_sl_multiplier': self.xrp_atr_sl_multiplier,
            'xrp_order_size_percentage': self.xrp_order_size_percentage,
            'xrp_leverage': self.xrp_leverage,
            'xrp_enable_trading': self.xrp_enable_trading,
            'xrp_product_type': self.xrp_product_type,
            'ada_atr_period': self.ada_atr_period,
            'ada_atr_tp_multiplier': self.ada_atr_tp_multiplier,
            'ada_atr_sl_multiplier': self.ada_atr_sl_multiplier,
            'ada_order_size_percentage': self.ada_order_size_percentage,
            'ada_leverage': self.ada_leverage,
            'ada_enable_trading': self.ada_enable_trading,
            'ada_product_type': self.ada_product_type,
            'dot_atr_period': self.dot_atr_period,
            'dot_atr_tp_multiplier': self.dot_atr_tp_multiplier,
            'dot_atr_sl_multiplier': self.dot_atr_sl_multiplier,
            'dot_order_size_percentage': self.dot_order_size_percentage,
            'dot_leverage': self.dot_leverage,
            'dot_enable_trading': self.dot_enable_trading,
            'dot_product_type': self.dot_product_type,
            'xlm_atr_period': self.xlm_atr_period,
            'xlm_atr_tp_multiplier': self.xlm_atr_tp_multiplier,
            'xlm_atr_sl_multiplier': self.xlm_atr_sl_multiplier,
            'xlm_order_size_percentage': self.xlm_order_size_percentage,
            'xlm_leverage': self.xlm_leverage,
            'xlm_enable_trading': self.xlm_enable_trading,
            'xlm_product_type': self.xlm_product_type,
            'imx_atr_period': self.imx_atr_period,
            'imx_atr_tp_multiplier': self.imx_atr_tp_multiplier,
            'imx_atr_sl_multiplier': self.imx_atr_sl_multiplier,
            'imx_order_size_percentage': self.imx_order_size_percentage,
            'imx_leverage': self.imx_leverage,
            'imx_enable_trading': self.imx_enable_trading,
            'imx_product_type': self.imx_product_type,
            'doge_atr_period': self.doge_atr_period,
            'doge_atr_tp_multiplier': self.doge_atr_tp_multiplier,
            'doge_atr_sl_multiplier': self.doge_atr_sl_multiplier,
            'doge_order_size_percentage': self.doge_order_size_percentage,
            'doge_leverage': self.doge_leverage,
            'doge_enable_trading': self.doge_enable_trading,
            'doge_product_type': self.doge_product_type,
            'inj_atr_period': self.inj_atr_period,
            'inj_atr_tp_multiplier': self.inj_atr_tp_multiplier,
            'inj_atr_sl_multiplier': self.inj_atr_sl_multiplier,
            'inj_order_size_percentage': self.inj_order_size_percentage,
            'inj_leverage': self.inj_leverage,
            'inj_enable_trading': self.inj_enable_trading,
            'inj_product_type': self.inj_product_type,
            'ldo_atr_period': self.ldo_atr_period,
            'ldo_atr_tp_multiplier': self.ldo_atr_tp_multiplier,
            'ldo_atr_sl_multiplier': self.ldo_atr_sl_multiplier,
            'ldo_order_size_percentage': self.ldo_order_size_percentage,
            'ldo_leverage': self.ldo_leverage,
            'ldo_enable_trading': self.ldo_enable_trading,
            'ldo_product_type': self.ldo_product_type,
            'arb_atr_period': self.arb_atr_period,
            'arb_atr_tp_multiplier': self.arb_atr_tp_multiplier,
            'arb_atr_sl_multiplier': self.arb_atr_sl_multiplier,
            'arb_order_size_percentage': self.arb_order_size_percentage,
            'arb_leverage': self.arb_leverage,
            'arb_enable_trading': self.arb_enable_trading,
            'arb_product_type': self.arb_product_type,
            'uni_atr_period': self.uni_atr_period,
            'uni_atr_tp_multiplier': self.uni_atr_tp_multiplier,
            'uni_atr_sl_multiplier': self.uni_atr_sl_multiplier,
            'uni_order_size_percentage': self.uni_order_size_percentage,
            'uni_leverage': self.uni_leverage,
            'uni_enable_trading': self.uni_enable_trading,
            'uni_product_type': self.uni_product_type,
            'sol_atr_period': self.sol_atr_period,
            'sol_atr_tp_multiplier': self.sol_atr_tp_multiplier,
            'sol_atr_sl_multiplier': self.sol_atr_sl_multiplier,
            'sol_order_size_percentage': self.sol_order_size_percentage,
            'sol_leverage': self.sol_leverage,
            'sol_enable_trading': self.sol_enable_trading,
            'sol_product_type': self.sol_product_type,
            'bnb_atr_period': self.bnb_atr_period,
            'bnb_atr_tp_multiplier': self.bnb_atr_tp_multiplier,
            'bnb_atr_sl_multiplier': self.bnb_atr_sl_multiplier,
            'bnb_order_size_percentage': self.bnb_order_size_percentage,
            'bnb_leverage': self.bnb_leverage,
            'bnb_enable_trading': self.bnb_enable_trading,
            'bnb_product_type': self.bnb_product_type,
            'fet_atr_period': self.fet_atr_period,
            'fet_atr_tp_multiplier': self.fet_atr_tp_multiplier,
            'fet_atr_sl_multiplier': self.fet_atr_sl_multiplier,
            'fet_order_size_percentage': self.fet_order_size_percentage,
            'fet_leverage': self.fet_leverage,
            'fet_enable_trading': self.fet_enable_trading,
            'fet_product_type': self.fet_product_type,
            # USDC coins
            'btcusdc_atr_period': self.btcusdc_atr_period,
            'btcusdc_atr_tp_multiplier': self.btcusdc_atr_tp_multiplier,
            'btcusdc_atr_sl_multiplier': self.btcusdc_atr_sl_multiplier,
            'btcusdc_order_size_percentage': self.btcusdc_order_size_percentage,
            'btcusdc_leverage': self.btcusdc_leverage,
            'btcusdc_enable_trading': self.btcusdc_enable_trading,
            'btcusdc_product_type': self.btcusdc_product_type,
            'ethusdc_atr_period': self.ethusdc_atr_period,
            'ethusdc_atr_tp_multiplier': self.ethusdc_atr_tp_multiplier,
            'ethusdc_atr_sl_multiplier': self.ethusdc_atr_sl_multiplier,
            'ethusdc_order_size_percentage': self.ethusdc_order_size_percentage,
            'ethusdc_leverage': self.ethusdc_leverage,
            'ethusdc_enable_trading': self.ethusdc_enable_trading,
            'ethusdc_product_type': self.ethusdc_product_type,
            'solusdc_atr_period': self.solusdc_atr_period,
            'solusdc_atr_tp_multiplier': self.solusdc_atr_tp_multiplier,
            'solusdc_atr_sl_multiplier': self.solusdc_atr_sl_multiplier,
            'solusdc_order_size_percentage': self.solusdc_order_size_percentage,
            'solusdc_leverage': self.solusdc_leverage,
            'solusdc_enable_trading': self.solusdc_enable_trading,
            'solusdc_product_type': self.solusdc_product_type,
            'aaveusdc_atr_period': self.aaveusdc_atr_period,
            'aaveusdc_atr_tp_multiplier': self.aaveusdc_atr_tp_multiplier,
            'aaveusdc_atr_sl_multiplier': self.aaveusdc_atr_sl_multiplier,
            'aaveusdc_order_size_percentage': self.aaveusdc_order_size_percentage,
            'aaveusdc_leverage': self.aaveusdc_leverage,
            'aaveusdc_enable_trading': self.aaveusdc_enable_trading,
            'aaveusdc_product_type': self.aaveusdc_product_type,
            'bchusdc_atr_period': self.bchusdc_atr_period,
            'bchusdc_atr_tp_multiplier': self.bchusdc_atr_tp_multiplier,
            'bchusdc_atr_sl_multiplier': self.bchusdc_atr_sl_multiplier,
            'bchusdc_order_size_percentage': self.bchusdc_order_size_percentage,
            'bchusdc_leverage': self.bchusdc_leverage,
            'bchusdc_enable_trading': self.bchusdc_enable_trading,
            'bchusdc_product_type': self.bchusdc_product_type,
            'xrpusdc_atr_period': self.xrpusdc_atr_period,
            'xrpusdc_atr_tp_multiplier': self.xrpusdc_atr_tp_multiplier,
            'xrpusdc_atr_sl_multiplier': self.xrpusdc_atr_sl_multiplier,
            'xrpusdc_order_size_percentage': self.xrpusdc_order_size_percentage,
            'xrpusdc_leverage': self.xrpusdc_leverage,
            'xrpusdc_enable_trading': self.xrpusdc_enable_trading,
            'xrpusdc_product_type': self.xrpusdc_product_type,
            'adausdc_atr_period': self.adausdc_atr_period,
            'adausdc_atr_tp_multiplier': self.adausdc_atr_tp_multiplier,
            'adausdc_atr_sl_multiplier': self.adausdc_atr_sl_multiplier,
            'adausdc_order_size_percentage': self.adausdc_order_size_percentage,
            'adausdc_leverage': self.adausdc_leverage,
            'adausdc_enable_trading': self.adausdc_enable_trading,
            'adausdc_product_type': self.adausdc_product_type,
            'avaxusdc_atr_period': self.avaxusdc_atr_period,
            'avaxusdc_atr_tp_multiplier': self.avaxusdc_atr_tp_multiplier,
            'avaxusdc_atr_sl_multiplier': self.avaxusdc_atr_sl_multiplier,
            'avaxusdc_order_size_percentage': self.avaxusdc_order_size_percentage,
            'avaxusdc_leverage': self.avaxusdc_leverage,
            'avaxusdc_enable_trading': self.avaxusdc_enable_trading,
            'avaxusdc_product_type': self.avaxusdc_product_type,
            'linkusdc_atr_period': self.linkusdc_atr_period,
            'linkusdc_atr_tp_multiplier': self.linkusdc_atr_tp_multiplier,
            'linkusdc_atr_sl_multiplier': self.linkusdc_atr_sl_multiplier,
            'linkusdc_order_size_percentage': self.linkusdc_order_size_percentage,
            'linkusdc_leverage': self.linkusdc_leverage,
            'linkusdc_enable_trading': self.linkusdc_enable_trading,
            'linkusdc_product_type': self.linkusdc_product_type,
            'arbusdc_atr_period': self.arbusdc_atr_period,
            'arbusdc_atr_tp_multiplier': self.arbusdc_atr_tp_multiplier,
            'arbusdc_atr_sl_multiplier': self.arbusdc_atr_sl_multiplier,
            'arbusdc_order_size_percentage': self.arbusdc_order_size_percentage,
            'arbusdc_leverage': self.arbusdc_leverage,
            'arbusdc_enable_trading': self.arbusdc_enable_trading,
            'arbusdc_product_type': self.arbusdc_product_type,
            'uniusdc_atr_period': self.uniusdc_atr_period,
            'uniusdc_atr_tp_multiplier': self.uniusdc_atr_tp_multiplier,
            'uniusdc_atr_sl_multiplier': self.uniusdc_atr_sl_multiplier,
            'uniusdc_order_size_percentage': self.uniusdc_order_size_percentage,
            'uniusdc_leverage': self.uniusdc_leverage,
            'uniusdc_enable_trading': self.uniusdc_enable_trading,
            'uniusdc_product_type': self.uniusdc_product_type,
            'crvusdc_atr_period': self.crvusdc_atr_period,
            'crvusdc_atr_tp_multiplier': self.crvusdc_atr_tp_multiplier,
            'crvusdc_atr_sl_multiplier': self.crvusdc_atr_sl_multiplier,
            'crvusdc_order_size_percentage': self.crvusdc_order_size_percentage,
            'crvusdc_leverage': self.crvusdc_leverage,
            'crvusdc_enable_trading': self.crvusdc_enable_trading,
            'crvusdc_product_type': self.crvusdc_product_type,
            'tiausdc_atr_period': self.tiausdc_atr_period,
            'tiausdc_atr_tp_multiplier': self.tiausdc_atr_tp_multiplier,
            'tiausdc_atr_sl_multiplier': self.tiausdc_atr_sl_multiplier,
            'tiausdc_order_size_percentage': self.tiausdc_order_size_percentage,
            'tiausdc_leverage': self.tiausdc_leverage,
            'tiausdc_enable_trading': self.tiausdc_enable_trading,
            'tiausdc_product_type': self.tiausdc_product_type,
            'bnbusdc_atr_period': self.bnbusdc_atr_period,
            'bnbusdc_atr_tp_multiplier': self.bnbusdc_atr_tp_multiplier,
            'bnbusdc_atr_sl_multiplier': self.bnbusdc_atr_sl_multiplier,
            'bnbusdc_order_size_percentage': self.bnbusdc_order_size_percentage,
            'bnbusdc_leverage': self.bnbusdc_leverage,
            'bnbusdc_enable_trading': self.bnbusdc_enable_trading,
            'bnbusdc_product_type': self.bnbusdc_product_type,
            'filusdc_atr_period': self.filusdc_atr_period,
            'filusdc_atr_tp_multiplier': self.filusdc_atr_tp_multiplier,
            'filusdc_atr_sl_multiplier': self.filusdc_atr_sl_multiplier,
            'filusdc_order_size_percentage': self.filusdc_order_size_percentage,
            'filusdc_leverage': self.filusdc_leverage,
            'filusdc_enable_trading': self.filusdc_enable_trading,
            'filusdc_product_type': self.filusdc_product_type,
        }
        
    @staticmethod
    def from_dict(data):
        return Config(**data)

class Position:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '')
        self.symbol = kwargs.get('symbol', '')
        self.direction = kwargs.get('direction', '')
        self.size = kwargs.get('size', '0')
        self.entry_price = kwargs.get('entry_price', '0')
        self.exit_price = kwargs.get('exit_price', '0')
        self.open_time = kwargs.get('open_time', '')
        self.close_time = kwargs.get('close_time', '')
        self.closed = kwargs.get('closed', False)
        
    def calculate_pnl(self):
        if not self.closed:
            return 0
            
        entry = float(self.entry_price)
        exit_price = float(self.exit_price)
        size = float(self.size)
        
        if self.direction == 'long':
            return (exit_price - entry) * size
        else:  # short
            return (entry - exit_price) * size

