"""
Enhanced MT5 Client with Real Trade Execution
"""

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MT5Client:
    def __init__(self, config: Dict):
        self.config = config
        self.connected = False
        self.account = None
        self._lock = asyncio.Lock()
        
    async def connect(self) -> bool:
        """Initialize MT5 connection"""
        if mt5 is None:
            logger.warning("MetaTrader5 library not installed. Running in simulation/offline mode.")
            return False
            
        try:
            if not mt5.initialize():
                logger.error("MT5 initialization failed")
                return False
            
            login = self.config.get('mt5_login')
            password = self.config.get('mt5_password')
            server = self.config.get('mt5_server')
            
            if login and password and server:
                authorized = mt5.login(login, password, server)
                if not authorized:
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
                    return False
            
            self.connected = True
            self.account = mt5.account_info()
            logger.info(f"MT5 Connected: {self.account.login if self.account else 'N/A'}")
            return True
            
        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False
    
    async def disconnect(self):
        """Shutdown MT5 connection"""
        if mt5:
            mt5.shutdown()
        self.connected = False
        logger.info("MT5 Disconnected")
    
    async def get_account_info(self) -> Optional[Dict]:
        """Get current account information"""
        if not self.connected or mt5 is None:
            return None
        
        info = mt5.account_info()
        if info is None:
            return None
            
        return {
            'login': info.login,
            'balance': info.balance,
            'equity': info.equity,
            'profit': info.profit,
            'margin': info.margin,
            'margin_free': info.margin_free,
            'currency': info.currency
        }
    
    async def get_rates(self, 
                       symbol: str, 
                       timeframe: str = 'H1', 
                       count: int = 100) -> Optional[List[Dict]]:
        """Get historical price data"""
        if not self.connected or mt5 is None:
            return None
        
        tf_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        
        tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
        
        if rates is None:
            return None
            
        return [{
            'time': datetime.fromtimestamp(r[0]),
            'open': r[1],
            'high': r[2],
            'low': r[3],
            'close': r[4],
            'tick_volume': r[5],
            'spread': r[6],
            'real_volume': r[7]
        } for r in rates]
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol specifications"""
        if not self.connected or mt5 is None:
            return None
            
        info = mt5.symbol_info(symbol)
        if info is None:
            return None
            
        return {
            'name': info.name,
            'bid': info.bid,
            'ask': info.ask,
            'spread': info.spread,
            'digits': info.digits,
            'trade_allowed': info.trade_allowed,
            'point': info.point
        }
    
    async def place_order(self,
                         symbol: str,
                         order_type: str,
                         volume: float,
                         price: Optional[float] = None,
                         sl: Optional[float] = None,
                         tp: Optional[float] = None,
                         comment: str = "",
                         deviation: int = 10) -> Dict:
        """
        Place market or pending order with SL/TP
        """
        async with self._lock:
            if not self.connected or mt5 is None:
                return {'success': False, 'error': 'Not connected to MT5'}
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {'success': False, 'error': f'Symbol {symbol} not found'}
            
            # Action mapping
            order_types = {
                'buy': mt5.ORDER_TYPE_BUY,
                'sell': mt5.ORDER_TYPE_SELL,
                'buy_limit': mt5.ORDER_TYPE_BUY_LIMIT,
                'sell_limit': mt5.ORDER_TYPE_SELL_LIMIT,
                'buy_stop': mt5.ORDER_TYPE_BUY_STOP,
                'sell_stop': mt5.ORDER_TYPE_SELL_STOP
            }
            
            mt5_type = order_types.get(order_type.lower(), mt5.ORDER_TYPE_BUY)
            
            if price is None:
                price = symbol_info.ask if mt5_type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_BUY_LIMIT] else symbol_info.bid
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL if mt5_type in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL] else mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": float(volume),
                "type": mt5_type,
                "price": float(price),
                "deviation": deviation,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            if sl: request["sl"] = float(sl)
            if tp: request["tp"] = float(tp)
            
            result = mt5.order_send(request)
            
            if result is None:
                return {'success': False, 'error': str(mt5.last_error())}
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {'success': False, 'error': f"Order failed: {result.retcode}"}
            
            return {
                'success': True,
                'order_id': result.order,
                'deal_id': result.deal,
                'price': result.price
            }
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open positions"""
        if not self.connected or mt5 is None:
            return []
        
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            return []
        
        return [{
            'ticket': p.ticket,
            'symbol': p.symbol,
            'type': 'buy' if p.type == 0 else 'sell',
            'volume': p.volume,
            'open_price': p.price_open,
            'current_price': p.price_current,
            'profit': p.profit,
            'sl': p.sl,
            'tp': p.tp
        } for p in positions]

    async def close_position(self, position_id: int) -> Dict:
        """Close specific position by ticket"""
        if mt5 is None:
            return {'success': False, 'error': 'MT5 library not available'}
            
        async with self._lock:
            position = mt5.positions_get(ticket=position_id)
            if not position:
                return {'success': False, 'error': 'Position not found'}
            
            pos = position[0]
            symbol_info = mt5.symbol_info(pos.symbol)
            close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
            price = symbol_info.bid if close_type == mt5.ORDER_TYPE_SELL else symbol_info.ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": pos.ticket,
                "price": price,
                "deviation": 10,
                "magic": 234000,
                "comment": "Close by Agent",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                return {'success': False, 'error': f"Close failed: {result.retcode if result else 'Unknown'}"}
            
            return {'success': True, 'order_id': result.order, 'profit': pos.profit}

    async def modify_position(self, position_id: int, sl: Optional[float] = None, tp: Optional[float] = None) -> Dict:
        """Modify SL/TP of existing position"""
        if mt5 is None:
            return {'success': False, 'error': 'MT5 library not available'}
            
        async with self._lock:
            position = mt5.positions_get(ticket=position_id)
            if not position:
                return {'success': False, 'error': 'Position not found'}
            
            pos = position[0]
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": pos.ticket,
                "sl": sl if sl else pos.sl,
                "tp": tp if tp else pos.tp
            }
            
            result = mt5.order_send(request)
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                return {'success': False, 'error': f"Modify failed: {result.retcode if result else 'Unknown'}"}
            
            return {'success': True}
