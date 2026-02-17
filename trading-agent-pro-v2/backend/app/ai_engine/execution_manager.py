"""
Execution Manager - Bridge between Signals and MT5
Handles autonomous trade execution with risk management
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from .signal_generator import TradingSignal
# Assuming MT5Client is handled by the swarm
# from ..mt5_client import MT5Client

logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    success: bool
    order_id: Optional[int]
    message: str
    executed_price: Optional[float] = None
    slippage: Optional[float] = None

class ExecutionManager:
    """
    Manages trade execution with autonomous mode and safety controls
    """
    
    def __init__(self, mt5_client):
        self.mt5 = mt5_client
        self.risk_per_trade = 0.01  # 1% risk per trade
        self.max_spread = 50  # points
        self.autonomous_threshold = 0.85  # Confidence threshold for auto-execution
        
    async def execute_signal(self, 
                           signal: TradingSignal, 
                           agent_id: str,
                           force_manual: bool = False) -> ExecutionResult:
        """
        Execute trading signal with risk checks
        
        Args:
            signal: TradingSignal to execute
            agent_id: Source agent identifier
            force_manual: Force manual confirmation even in autonomous mode
            
        Returns:
            ExecutionResult with status details
        """
        try:
            # Risk Management Checks
            if not await self._pre_trade_checks(signal):
                return ExecutionResult(
                    success=False,
                    order_id=None,
                    message="Pre-trade checks failed"
                )
            
            # Determine if autonomous execution is allowed
            should_auto_execute = (
                signal.confidence >= self.autonomous_threshold and 
                not force_manual
            )
            
            if not should_auto_execute:
                logger.info(f"Signal queued for manual review: {signal.symbol}")
                # Store in pending signals queue
                await self._queue_manual_signal(signal, agent_id)
                return ExecutionResult(
                    success=False,
                    order_id=None,
                    message="Awaiting manual confirmation"
                )
            
            # Calculate position size
            lot_size = await self._calculate_position_size(signal)
            if lot_size <= 0:
                return ExecutionResult(
                    success=False,
                    order_id=None,
                    message="Invalid position size calculated"
                )
            
            # Execute via MT5
            result = await self._place_order(signal, lot_size)
            
            if result.get('success'):
                logger.info(f"Trade executed: {signal.symbol} {signal.direction} "
                           f"@{result.get('price')} (Agent: {agent_id})")
                return ExecutionResult(
                    success=True,
                    order_id=result.get('order_id'),
                    message="Trade executed successfully",
                    executed_price=result.get('price'),
                    slippage=result.get('slippage')
                )
            else:
                return ExecutionResult(
                    success=False,
                    order_id=None,
                    message=f"Execution failed: {result.get('error')}"
                )
                
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return ExecutionResult(
                success=False,
                order_id=None,
                message=f"Exception: {str(e)}"
            )
    
    async def _pre_trade_checks(self, signal: TradingSignal) -> bool:
        """Pre-trade risk management checks"""
        # Check spread
        if hasattr(self.mt5, 'get_symbol_info'):
            symbol_info = await self.mt5.get_symbol_info(signal.symbol)
            if symbol_info:
                spread = symbol_info.get('spread', 0)
                if spread > self.max_spread:
                    logger.warning(f"Spread too high for {signal.symbol}: {spread}")
                    return False
        
        # Check account exposure
        if hasattr(self.mt5, 'get_positions'):
            open_positions = await self.mt5.get_positions()
            symbol_exposure = sum(
                1 for p in open_positions 
                if p.get('symbol') == signal.symbol
            )
            if symbol_exposure >= 2:  # Max 2 positions per symbol
                logger.warning(f"Max exposure reached for {signal.symbol}")
                return False
        
        # Check risk:reward
        if signal.risk_reward < 1.5:
            logger.warning(f"Risk:Reward too low: {signal.risk_reward}")
            return False
            
        return True
    
    async def _calculate_position_size(self, signal: TradingSignal) -> float:
        """Calculate lot size based on risk management"""
        if not hasattr(self.mt5, 'get_account_info'):
            return 0.01
            
        account = await self.mt5.get_account_info()
        if not account:
            return 0.01
        
        balance = account.get('balance', 0)
        risk_amount = balance * self.risk_per_trade
        
        # Calculate pip value and stop distance
        tick_size = 0.0001  # Default for forex
        if 'JPY' in signal.symbol:
            tick_size = 0.01
        
        stop_distance = abs(signal.entry_price - signal.stop_loss)
        if stop_distance == 0:
            return 0.01
        
        # Standard lot = 100,000 units
        lot_size = risk_amount / (stop_distance * 100000)
        
        # Normalize to standard lot sizes
        if lot_size < 0.01:
            return 0.01
        elif lot_size < 0.1:
            return round(lot_size, 2)
        else:
            return round(lot_size, 1)
    
    async def _place_order(self, signal: TradingSignal, lot_size: float) -> Dict:
        """Place order via MT5 with SL/TP"""
        if not hasattr(self.mt5, 'place_order'):
            return {'success': False, 'error': 'MT5 client has no place_order method'}
            
        order_type = 'buy' if signal.direction == 'buy' else 'sell'
        
        result = await self.mt5.place_order(
            symbol=signal.symbol,
            order_type=order_type,
            volume=lot_size,
            price=signal.entry_price,
            sl=signal.stop_loss,
            tp=signal.take_profit,
            comment=f"SMC_Agent_{signal.strategy}"
        )
        
        return result
    
    async def _queue_manual_signal(self, signal: TradingSignal, agent_id: str):
        """Store signal for manual review"""
        # Implementation depends on your database/queue system
        pass
    
    async def close_position(self, position_id: int) -> bool:
        """Close specific position"""
        if not hasattr(self.mt5, 'close_position'):
            return False
        result = await self.mt5.close_position(position_id)
        return result.get('success', False)
    
    async def modify_position(self, 
                             position_id: int, 
                             sl: Optional[float] = None,
                             tp: Optional[float] = None) -> bool:
        """Modify SL/TP of existing position"""
        if not hasattr(self.mt5, 'modify_position'):
            return False
        result = await self.mt5.modify_position(position_id, sl=sl, tp=tp)
        return result.get('success', False)
