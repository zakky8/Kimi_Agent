"""
MetaTrader 5 Desktop Integration Module
Connects to local MT5 terminal for real-time data
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class MT5AccountInfo:
    """MT5 account information"""
    login: int
    server: str
    balance: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    currency: str


@dataclass
class MT5Position:
    """MT5 position information"""
    ticket: int
    symbol: str
    type: str  # "buy" or "sell"
    volume: float
    open_price: float
    current_price: float
    sl: float
    tp: float
    profit: float
    swap: float
    open_time: datetime


@dataclass
class MT5Order:
    """MT5 order information"""
    ticket: int
    symbol: str
    type: str
    volume: float
    price: float
    sl: float
    tp: float
    comment: str


class MT5Client:
    """
    MetaTrader 5 Desktop Client
    Connects to local MT5 terminal
    """
    
    def __init__(
        self,
        path: str = None,
        login: int = None,
        password: str = None,
        server: str = None
    ):
        self.path = path or settings.MT5_PATH
        self.login = login or settings.MT5_ACCOUNT
        self.password = password or settings.MT5_PASSWORD
        self.server = server or settings.MT5_SERVER
        
        self.connected = False
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialize MT5 connection"""
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 package not installed. Install with: pip install MetaTrader5")
            return False
        
        if not settings.MT5_ENABLED:
            logger.info("MT5 integration disabled in settings")
            return False
        
        try:
            # Initialize MT5
            if self.path:
                self.initialized = mt5.initialize(path=self.path)
            else:
                self.initialized = mt5.initialize()
            
            if not self.initialized:
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            logger.info("MT5 initialized successfully")
            
            # Login if credentials provided
            if self.login and self.password and self.server:
                self.connected = mt5.login(
                    login=int(self.login),
                    password=self.password,
                    server=self.server
                )
                
                if self.connected:
                    logger.info(f"MT5 logged in to {self.server}")
                else:
                    logger.error(f"MT5 login failed: {mt5.last_error()}")
            else:
                # Check if already connected
                account_info = mt5.account_info()
                self.connected = account_info is not None
            
            return self.initialized
            
        except Exception as e:
            logger.error(f"MT5 initialization error: {e}")
            return False
    
    def shutdown(self):
        """Shutdown MT5 connection"""
        if MT5_AVAILABLE and self.initialized:
            mt5.shutdown()
            self.initialized = False
            self.connected = False
            logger.info("MT5 shutdown")
    
    def get_account_info(self) -> Optional[MT5AccountInfo]:
        """Get account information"""
        if not self.connected or not MT5_AVAILABLE:
            return None
        
        try:
            info = mt5.account_info()
            if info is None:
                return None
            
            return MT5AccountInfo(
                login=info.login,
                server=info.server,
                balance=info.balance,
                equity=info.equity,
                margin=info.margin,
                margin_free=info.margin_free,
                margin_level=info.margin_level,
                currency=info.currency
            )
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_symbols(self, group: str = None) -> List[str]:
        """Get available symbols"""
        if not self.initialized or not MT5_AVAILABLE:
            return []
        
        try:
            if group:
                symbols = mt5.symbols_get(group=group)
            else:
                symbols = mt5.symbols_get()
            
            return [s.name for s in symbols] if symbols else []
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            return []
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        if not self.initialized or not MT5_AVAILABLE:
            return None
        
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return None
            
            return {
                "name": info.name,
                "description": info.description,
                "bid": info.bid,
                "ask": info.ask,
                "spread": info.spread,
                "digits": info.digits,
                "point": info.point,
                "trade_allowed": info.trade_allowed,
                "volume_min": info.volume_min,
                "volume_max": info.volume_max,
                "volume_step": info.volume_step
            }
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def get_rates(
        self,
        symbol: str,
        timeframe: int = mt5.TIMEFRAME_H1 if MT5_AVAILABLE else 16385,
        count: int = 100
    ) -> Optional[pd.DataFrame]:
        """Get historical price data"""
        if not self.initialized or not MT5_AVAILABLE:
            return None
        
        try:
            # Select symbol
            mt5.symbol_select(symbol, True)
            
            # Get rates
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Error getting rates: {e}")
            return None
    
    def get_positions(self) -> List[MT5Position]:
        """Get open positions"""
        if not self.connected or not MT5_AVAILABLE:
            return []
        
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append(MT5Position(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    type="buy" if pos.type == mt5.ORDER_TYPE_BUY else "sell",
                    volume=pos.volume,
                    open_price=pos.price_open,
                    current_price=pos.price_current,
                    sl=pos.sl,
                    tp=pos.tp,
                    profit=pos.profit,
                    swap=pos.swap,
                    open_time=datetime.fromtimestamp(pos.time)
                ))
            
            return result
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(self) -> List[MT5Order]:
        """Get pending orders"""
        if not self.connected or not MT5_AVAILABLE:
            return []
        
        try:
            orders = mt5.orders_get()
            if orders is None:
                return []
            
            result = []
            for order in orders:
                result.append(MT5Order(
                    ticket=order.ticket,
                    symbol=order.symbol,
                    type=self._get_order_type_name(order.type),
                    volume=order.volume_current,
                    price=order.price_open,
                    sl=order.sl,
                    tp=order.tp,
                    comment=order.comment
                ))
            
            return result
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def _get_order_type_name(self, order_type: int) -> str:
        """Convert order type to string"""
        if not MT5_AVAILABLE:
            return "unknown"
        
        types = {
            mt5.ORDER_TYPE_BUY: "buy",
            mt5.ORDER_TYPE_SELL: "sell",
            mt5.ORDER_TYPE_BUY_LIMIT: "buy_limit",
            mt5.ORDER_TYPE_SELL_LIMIT: "sell_limit",
            mt5.ORDER_TYPE_BUY_STOP: "buy_stop",
            mt5.ORDER_TYPE_SELL_STOP: "sell_stop"
        }
        return types.get(order_type, "unknown")
    
    def get_ticks(self, symbol: str, count: int = 100) -> Optional[pd.DataFrame]:
        """Get tick data"""
        if not self.initialized or not MT5_AVAILABLE:
            return None
        
        try:
            mt5.symbol_select(symbol, True)
            ticks = mt5.copy_ticks_from_pos(symbol, mt5.COPY_TICKS_ALL, 0, count)
            
            if ticks is None or len(ticks) == 0:
                return None
            
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Error getting ticks: {e}")
            return None
    
    def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: float = None,
        sl: float = None,
        tp: float = None,
        comment: str = ""
    ) -> Dict[str, Any]:
        """Place an order (for paper trading)"""
        if not self.connected or not MT5_AVAILABLE:
            return {"success": False, "error": "MT5 not connected"}
        
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {"success": False, "error": f"Symbol {symbol} not found"}
            
            # Build order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "deviation": 10,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Set order type
            if order_type == "buy":
                request["type"] = mt5.ORDER_TYPE_BUY
                request["price"] = symbol_info.ask
            elif order_type == "sell":
                request["type"] = mt5.ORDER_TYPE_SELL
                request["price"] = symbol_info.bid
            else:
                return {"success": False, "error": f"Invalid order type: {order_type}"}
            
            # Set SL/TP
            if sl:
                request["sl"] = sl
            if tp:
                request["tp"] = tp
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return {
                    "success": True,
                    "ticket": result.order,
                    "volume": result.volume,
                    "price": result.price
                }
            else:
                return {
                    "success": False,
                    "error": f"Order failed: {result.retcode}"
                }
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"success": False, "error": str(e)}
    
    def get_terminal_info(self) -> Dict[str, Any]:
        """Get terminal information"""
        if not self.initialized or not MT5_AVAILABLE:
            return {}
        
        try:
            info = mt5.terminal_info()
            if info is None:
                return {}
            
            return {
                "community_account": info.community_account,
                "community_connection": info.community_connection,
                "connected": info.connected,
                "dlls_allowed": info.dlls_allowed,
                "trade_allowed": info.trade_allowed,
                "tradeapi_disabled": info.tradeapi_disabled,
                "path": info.path
            }
        except Exception as e:
            logger.error(f"Error getting terminal info: {e}")
            return {}
    
    def get_summary(self) -> Dict[str, Any]:
        """Get MT5 connection summary"""
        return {
            "initialized": self.initialized,
            "connected": self.connected,
            "enabled": settings.MT5_ENABLED,
            "account": self.get_account_info().__dict__ if self.get_account_info() else None,
            "terminal": self.get_terminal_info(),
            "positions_count": len(self.get_positions()),
            "orders_count": len(self.get_orders())
        }


# Singleton instance
_mt5_client: Optional[MT5Client] = None


def get_mt5_client(
    path: str = None,
    login: int = None,
    password: str = None,
    server: str = None
) -> MT5Client:
    """Get or create MT5 client singleton"""
    global _mt5_client
    if _mt5_client is None:
        _mt5_client = MT5Client(path, login, password, server)
    return _mt5_client
