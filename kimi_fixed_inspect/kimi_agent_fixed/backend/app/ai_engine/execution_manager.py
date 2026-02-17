"""
Execution Manager - Bridges Signal Generation to MT5 Execution
Implements autonomous "auto-pilot" execution when criteria met
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from .signal_generator import TradingSignal
from ..mt5.mt5_client import MT5Client
from ..risk.risk_manager import RiskManager
from ..risk.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class ExecutionManager:
    """
    Manages trade execution with safety checks
    Autonomous execution when confidence > threshold
    """
    
    def __init__(
        self,
        mt5_client: MT5Client,
        risk_manager: RiskManager,
        circuit_breaker: CircuitBreaker,
        config: Dict = None
    ):
        self.mt5_client = mt5_client
        self.risk_manager = risk_manager
        self.circuit_breaker = circuit_breaker
        self.config = config or {}
        
        # Execution settings
        self.auto_execute_threshold = self.config.get('auto_execute_threshold', 0.85)
        self.max_slippage_pips = self.config.get('max_slippage_pips', 3)
        
        logger.info("ExecutionManager initialized")
    
    async def execute_signal(self, signal: TradingSignal) -> Dict:
        """
        Execute a trading signal with full safety checks
        
        Returns:
            Dict with 'success', 'ticket', 'error' keys
        """
        try:
            logger.info(
                f"🎯 Executing signal: {signal.symbol} {signal.direction} "
                f"@ {signal.entry_price:.5f} (Confidence: {signal.confidence:.2f})"
            )
            
            # 1. Pre-execution safety checks
            safety_check = self._pre_execution_checks(signal)
            if not safety_check['passed']:
                return {
                    'success': False,
                    'error': safety_check['reason']
                }
            
            # 2. Calculate lot size if not provided
            if signal.lot_size is None or signal.lot_size == 0:
                signal.lot_size = self.risk_manager.calculate_position_size(
                    symbol=signal.symbol,
                    entry_price=signal.entry_price,
                    stop_loss=signal.stop_loss
                )
            
            # 3. Place order via MT5
            order_result = await self._place_order(signal)
            
            if not order_result['success']:
                return {
                    'success': False,
                    'error': order_result.get('error', 'Order placement failed')
                }
            
            # 4. Verify execution
            ticket = order_result['ticket']
            execution_price = order_result['execution_price']
            
            # Check slippage
            slippage = abs(execution_price - signal.entry_price)
            slippage_pips = slippage / self._get_pip_value(signal.symbol)
            
            if slippage_pips > self.max_slippage_pips:
                logger.warning(
                    f"⚠️ High slippage detected: {slippage_pips:.1f} pips"
                )
            
            # 5. Update circuit breaker
            self.circuit_breaker.record_trade(
                symbol=signal.symbol,
                direction=signal.direction,
                entry_price=execution_price,
                lot_size=signal.lot_size
            )
            
            logger.info(
                f"✅ Trade executed successfully: Ticket #{ticket} "
                f"@ {execution_price:.5f} (Slippage: {slippage_pips:.1f} pips)"
            )
            
            return {
                'success': True,
                'ticket': ticket,
                'execution_price': execution_price,
                'slippage_pips': slippage_pips,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _pre_execution_checks(self, signal: TradingSignal) -> Dict:
        """
        Comprehensive pre-execution safety checks
        """
        # 1. Circuit breaker check
        if self.circuit_breaker.is_triggered():
            return {
                'passed': False,
                'reason': 'Circuit breaker is active'
            }
        
        # 2. Confidence threshold
        if signal.confidence < self.auto_execute_threshold:
            return {
                'passed': False,
                'reason': f'Confidence {signal.confidence:.2f} below threshold'
            }
        
        # 3. Risk manager validation
        risk_approved = self.risk_manager.validate_trade(
            symbol=signal.symbol,
            direction=signal.direction,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            lot_size=signal.lot_size or 0.01
        )
        
        if not risk_approved:
            return {
                'passed': False,
                'reason': 'Risk validation failed'
            }
        
        # 4. Risk/Reward check
        if signal.risk_reward_ratio < 2.0:
            return {
                'passed': False,
                'reason': f'Risk/Reward {signal.risk_reward_ratio:.2f} too low'
            }
        
        # 5. MT5 connection check
        if not self.mt5_client.is_connected():
            return {
                'passed': False,
                'reason': 'MT5 not connected'
            }
        
        # All checks passed
        return {'passed': True}
    
    async def _place_order(self, signal: TradingSignal) -> Dict:
        """
        Place order via MT5 with SL and TP
        """
        try:
            # Prepare order request
            order_request = {
                'symbol': signal.symbol,
                'type': 'BUY' if signal.direction == 'BUY' else 'SELL',
                'volume': signal.lot_size,
                'price': signal.entry_price,
                'sl': signal.stop_loss,
                'tp': signal.take_profit,
                'comment': f"AI Agent | Conf: {signal.confidence:.2f} | R:R {signal.risk_reward_ratio:.1f}",
                'magic': self.config.get('magic_number', 123456)
            }
            
            # Execute via MT5Client
            result = await self.mt5_client.place_order(order_request)
            
            return result
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def modify_position(
        self,
        ticket: int,
        new_sl: Optional[float] = None,
        new_tp: Optional[float] = None
    ) -> Dict:
        """
        Modify existing position's SL/TP
        """
        try:
            result = await self.mt5_client.modify_position(
                ticket=ticket,
                sl=new_sl,
                tp=new_tp
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error modifying position: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def close_position(self, ticket: int, reason: str = "") -> Dict:
        """
        Close an existing position
        """
        try:
            logger.info(f"Closing position #{ticket}. Reason: {reason}")
            
            result = await self.mt5_client.close_position(ticket)
            
            if result['success']:
                # Update circuit breaker
                self.circuit_breaker.record_position_close(
                    ticket=ticket,
                    pnl=result.get('pnl', 0)
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_pip_value(self, symbol: str) -> float:
        """
        Get pip value for symbol
        """
        # Simplified - in production, get from MT5
        if 'JPY' in symbol:
            return 0.01  # 2 decimal places
        else:
            return 0.0001  # 4 decimal places
