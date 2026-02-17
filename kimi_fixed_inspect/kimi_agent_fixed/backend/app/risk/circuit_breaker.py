"""
Circuit Breaker - 2% Drawdown Protection
Automatically stops all trading when daily drawdown exceeds threshold
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TradingDay:
    """Track daily trading metrics"""
    date: datetime
    starting_balance: float
    current_balance: float
    trades: List[Dict] = field(default_factory=list)
    peak_balance: float = 0.0
    
    @property
    def drawdown(self) -> float:
        """Current drawdown as percentage"""
        if self.peak_balance == 0:
            return 0.0
        return (self.peak_balance - self.current_balance) / self.peak_balance * 100
    
    @property
    def daily_pnl(self) -> float:
        """Profit/loss for the day"""
        return self.current_balance - self.starting_balance
    
    @property
    def daily_pnl_pct(self) -> float:
        """Daily P&L as percentage"""
        return (self.daily_pnl / self.starting_balance) * 100


class CircuitBreaker:
    """
    Safety system that halts all trading when drawdown exceeds threshold
    
    Features:
    - 2% daily drawdown limit (configurable)
    - Automatic trading halt
    - Manual reset capability
    - Daily statistics tracking
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Circuit breaker settings
        self.max_daily_drawdown_pct = self.config.get('max_daily_drawdown_pct', 2.0)
        self.max_daily_loss_pct = self.config.get('max_daily_loss_pct', 3.0)
        self.max_consecutive_losses = self.config.get('max_consecutive_losses', 5)
        
        # State
        self.is_breaker_triggered = False
        self.trigger_reason: Optional[str] = None
        self.trigger_time: Optional[datetime] = None
        
        # Daily tracking
        self.current_day: Optional[TradingDay] = None
        self.consecutive_losses = 0
        
        # Initial balance (should be set via set_initial_balance)
        self.starting_balance = self.config.get('starting_balance', 10000.0)
        
        self._initialize_day()
        
        logger.info(
            f"CircuitBreaker initialized: "
            f"Max Drawdown={self.max_daily_drawdown_pct}%, "
            f"Max Daily Loss={self.max_daily_loss_pct}%"
        )
    
    def _initialize_day(self):
        """Initialize a new trading day"""
        today = datetime.now().date()
        
        if self.current_day is None or self.current_day.date.date() != today:
            # Get current balance (in production, fetch from MT5)
            current_balance = self.starting_balance
            
            self.current_day = TradingDay(
                date=datetime.now(),
                starting_balance=current_balance,
                current_balance=current_balance,
                peak_balance=current_balance
            )
            
            # Reset breaker at start of new day
            if self.is_breaker_triggered:
                logger.info("New trading day - resetting circuit breaker")
                self.reset()
            
            logger.info(
                f"New trading day initialized: Starting balance=${current_balance:,.2f}"
            )
    
    def record_trade(
        self, 
        symbol: str, 
        direction: str, 
        entry_price: float, 
        lot_size: float
    ):
        """
        Record a new trade opening
        
        Args:
            symbol: Trading symbol
            direction: 'BUY' or 'SELL'
            entry_price: Entry price
            lot_size: Position size
        """
        self._initialize_day()
        
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'lot_size': lot_size,
            'status': 'OPEN'
        }
        
        self.current_day.trades.append(trade)
        
        logger.debug(f"Trade recorded: {symbol} {direction} @ {entry_price}")
    
    def record_position_close(self, ticket: int, pnl: float):
        """
        Record a position close and update balance
        
        Args:
            ticket: Position ticket number
            pnl: Profit/loss from the trade
        """
        self._initialize_day()
        
        # Update balance
        self.current_day.current_balance += pnl
        
        # Update peak balance
        if self.current_day.current_balance > self.current_day.peak_balance:
            self.current_day.peak_balance = self.current_day.current_balance
        
        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        logger.info(
            f"Position closed: P&L=${pnl:+,.2f} | "
            f"Balance=${self.current_day.current_balance:,.2f} | "
            f"Daily P&L={self.current_day.daily_pnl_pct:+.2f}%"
        )
        
        # Check circuit breaker conditions
        self._check_breaker_conditions()
    
    def _check_breaker_conditions(self):
        """Check if circuit breaker should trigger"""
        if self.is_breaker_triggered:
            return
        
        # Condition 1: Daily drawdown exceeded
        if self.current_day.drawdown > self.max_daily_drawdown_pct:
            self._trigger_breaker(
                f"Daily drawdown {self.current_day.drawdown:.2f}% "
                f"exceeded limit {self.max_daily_drawdown_pct}%"
            )
            return
        
        # Condition 2: Daily loss exceeded
        if self.current_day.daily_pnl_pct < -self.max_daily_loss_pct:
            self._trigger_breaker(
                f"Daily loss {self.current_day.daily_pnl_pct:.2f}% "
                f"exceeded limit {self.max_daily_loss_pct}%"
            )
            return
        
        # Condition 3: Too many consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            self._trigger_breaker(
                f"Consecutive losses ({self.consecutive_losses}) "
                f"exceeded limit {self.max_consecutive_losses}"
            )
            return
    
    def _trigger_breaker(self, reason: str):
        """Trigger the circuit breaker"""
        self.is_breaker_triggered = True
        self.trigger_reason = reason
        self.trigger_time = datetime.now()
        
        logger.critical(
            f"🚨 CIRCUIT BREAKER TRIGGERED 🚨\n"
            f"Reason: {reason}\n"
            f"Time: {self.trigger_time}\n"
            f"Current Balance: ${self.current_day.current_balance:,.2f}\n"
            f"Daily P&L: {self.current_day.daily_pnl_pct:+.2f}%"
        )
    
    def is_triggered(self) -> bool:
        """Check if circuit breaker is currently triggered"""
        self._initialize_day()  # Reset if new day
        return self.is_breaker_triggered
    
    def reset(self, manual: bool = False):
        """
        Reset the circuit breaker
        
        Args:
            manual: True if manually reset by user
        """
        if self.is_breaker_triggered:
            reset_type = "MANUAL" if manual else "AUTOMATIC (new day)"
            logger.warning(
                f"Circuit breaker reset ({reset_type})\n"
                f"Previous trigger: {self.trigger_reason}"
            )
        
        self.is_breaker_triggered = False
        self.trigger_reason = None
        self.trigger_time = None
        self.consecutive_losses = 0
    
    def set_initial_balance(self, balance: float):
        """Set the starting balance"""
        self.starting_balance = balance
        
        if self.current_day:
            self.current_day.starting_balance = balance
            self.current_day.current_balance = balance
            self.current_day.peak_balance = balance
        
        logger.info(f"Starting balance set to ${balance:,.2f}")
    
    def get_status(self) -> Dict:
        """Get current circuit breaker status"""
        self._initialize_day()
        
        return {
            'is_triggered': self.is_breaker_triggered,
            'trigger_reason': self.trigger_reason,
            'trigger_time': self.trigger_time.isoformat() if self.trigger_time else None,
            'current_balance': self.current_day.current_balance,
            'starting_balance': self.current_day.starting_balance,
            'daily_pnl': self.current_day.daily_pnl,
            'daily_pnl_pct': self.current_day.daily_pnl_pct,
            'drawdown_pct': self.current_day.drawdown,
            'consecutive_losses': self.consecutive_losses,
            'max_daily_drawdown_pct': self.max_daily_drawdown_pct,
            'max_daily_loss_pct': self.max_daily_loss_pct,
            'trades_today': len(self.current_day.trades)
        }
    
    def get_daily_report(self) -> Dict:
        """Get comprehensive daily trading report"""
        self._initialize_day()
        
        winning_trades = [
            t for t in self.current_day.trades 
            if t.get('pnl', 0) > 0
        ]
        losing_trades = [
            t for t in self.current_day.trades 
            if t.get('pnl', 0) < 0
        ]
        
        return {
            'date': self.current_day.date.isoformat(),
            'starting_balance': self.current_day.starting_balance,
            'ending_balance': self.current_day.current_balance,
            'peak_balance': self.current_day.peak_balance,
            'daily_pnl': self.current_day.daily_pnl,
            'daily_pnl_pct': self.current_day.daily_pnl_pct,
            'max_drawdown': self.current_day.drawdown,
            'total_trades': len(self.current_day.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(self.current_day.trades) * 100) 
                        if self.current_day.trades else 0,
            'circuit_breaker_triggered': self.is_breaker_triggered
        }
