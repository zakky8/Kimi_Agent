"""
Signal Generator for Smart Money Concepts (SMC) Trading
Ported from V1 and enhanced for V2 Multi-Agent Architecture
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class OrderBlockType(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"

class MarketStructure(Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    RANGING = "ranging"

@dataclass
class SMCZone:
    """Smart Money Concept Zone (Order Block, Fair Value Gap, etc.)"""
    type: str  # 'order_block', 'fvg', 'liquidity_sweep'
    direction: OrderBlockType
    price_high: float
    price_low: float
    timestamp: datetime
    strength: float  # 0.0 to 1.0
    volume_profile: float
    is_valid: bool = True

@dataclass
class TradingSignal:
    symbol: str
    direction: str  # 'buy' or 'sell'
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    strategy: str
    smc_zones: List[SMCZone]
    risk_reward: float
    timeframe: str
    timestamp: datetime
    metadata: Dict

class SMCAnalyzer:
    """Smart Money Concepts Technical Analysis Engine"""
    
    def __init__(self):
        self.lookback_period = 50
        self.min_ob_strength = 0.6
        
    def identify_order_blocks(self, df: pd.DataFrame) -> List[SMCZone]:
        """Identify Bullish and Bearish Order Blocks"""
        order_blocks = []
        
        for i in range(3, len(df) - 1):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            prev2 = df.iloc[i-2]
            
            # Bullish Order Block (Bearish candle before strong bullish move)
            if (prev2['close'] < prev2['open'] and  # Bearish candle
                prev['close'] > prev['open'] and    # Bullish candle
                prev['close'] > prev2['high'] and   # Strong bullish break
                current['close'] > prev['close']):
                
                strength = self._calculate_ob_strength(df, i-2, 'bullish')
                ob = SMCZone(
                    type='order_block',
                    direction=OrderBlockType.BULLISH,
                    price_high=prev2['high'],
                    price_low=prev2['low'],
                    timestamp=df.index[i-2],
                    strength=strength,
                    volume_profile=prev2['volume'] / df['volume'].rolling(20).mean().iloc[i-2]
                )
                order_blocks.append(ob)
            
            # Bearish Order Block (Bullish candle before strong bearish move)
            elif (prev2['close'] > prev2['open'] and  # Bullish candle
                  prev['close'] < prev['open'] and    # Bearish candle
                  prev['close'] < prev2['low'] and    # Strong bearish break
                  current['close'] < prev['close']):
                
                strength = self._calculate_ob_strength(df, i-2, 'bearish')
                ob = SMCZone(
                    type='order_block',
                    direction=OrderBlockType.BEARISH,
                    price_high=prev2['high'],
                    price_low=prev2['low'],
                    timestamp=df.index[i-2],
                    strength=strength,
                    volume_profile=prev2['volume'] / df['volume'].rolling(20).mean().iloc[i-2]
                )
                order_blocks.append(ob)
        
        return order_blocks
    
    def identify_fair_value_gaps(self, df: pd.DataFrame) -> List[SMCZone]:
        """Identify Fair Value Gaps (FVG) - Imbalances in price"""
        fvgs = []
        
        for i in range(2, len(df)):
            candle_1 = df.iloc[i-2]
            candle_2 = df.iloc[i-1]
            candle_3 = df.iloc[i]
            
            # Bullish FVG: Candle 3 low > Candle 1 high
            if candle_3['low'] > candle_1['high']:
                fvg = SMCZone(
                    type='fvg',
                    direction=OrderBlockType.BULLISH,
                    price_high=candle_3['low'],
                    price_low=candle_1['high'],
                    timestamp=df.index[i],
                    strength=min(1.0, (candle_3['low'] - candle_1['high']) / candle_1['close']),
                    volume_profile=(candle_1['volume'] + candle_2['volume'] + candle_3['volume']) / 3
                )
                fvgs.append(fvg)
            
            # Bearish FVG: Candle 3 high < Candle 1 low
            elif candle_3['high'] < candle_1['low']:
                fvg = SMCZone(
                    type='fvg',
                    direction=OrderBlockType.BEARISH,
                    price_high=candle_1['low'],
                    price_low=candle_3['high'],
                    timestamp=df.index[i],
                    strength=min(1.0, (candle_1['low'] - candle_3['high']) / candle_1['close']),
                    volume_profile=(candle_1['volume'] + candle_2['volume'] + candle_3['volume']) / 3
                )
                fvgs.append(fvg)
        
        return fvgs
    
    def identify_liquidity_sweeps(self, df: pd.DataFrame) -> List[SMCZone]:
        """Identify Liquidity Sweeps (Stop Hunts)"""
        sweeps = []
        window = 10
        
        for i in range(window, len(df) - 1):
            recent_high = df.iloc[i-window:i]['high'].max()
            recent_low = df.iloc[i-window:i]['low'].min()
            
            current = df.iloc[i]
            next_candle = df.iloc[i+1]
            
            # Bullish Sweep (Sweep below lows, then reverse up)
            if (current['low'] < recent_low and 
                current['close'] > recent_low and
                next_candle['close'] > current['close']):
                
                sweep = SMCZone(
                    type='liquidity_sweep',
                    direction=OrderBlockType.BULLISH,
                    price_high=current['high'],
                    price_low=current['low'],
                    timestamp=df.index[i],
                    strength=0.8,
                    volume_profile=current['volume'] / df['volume'].rolling(20).mean().iloc[i]
                )
                sweeps.append(sweep)
            
            # Bearish Sweep (Sweep above highs, then reverse down)
            elif (current['high'] > recent_high and 
                  current['close'] < recent_high and
                  next_candle['close'] < current['close']):
                
                sweep = SMCZone(
                    type='liquidity_sweep',
                    direction=OrderBlockType.BEARISH,
                    price_high=current['high'],
                    price_low=current['low'],
                    timestamp=df.index[i],
                    strength=0.8,
                    volume_profile=current['volume'] / df['volume'].rolling(20).mean().iloc[i]
                )
                sweeps.append(sweep)
        
        return sweeps
    
    def _calculate_ob_strength(self, df: pd.DataFrame, index: int, direction: str) -> float:
        """Calculate the strength of an order block based on volume and price action"""
        candle = df.iloc[index]
        avg_volume = df['volume'].rolling(20).mean().iloc[index]
        volume_ratio = candle['volume'] / avg_volume if avg_volume > 0 else 1.0
        
        body_size = abs(candle['close'] - candle['open'])
        range_size = candle['high'] - candle['low']
        body_ratio = body_size / range_size if range_size > 0 else 0.5
        
        strength = min(1.0, (volume_ratio * 0.4 + body_ratio * 0.6))
        return strength
    
    def determine_market_structure(self, df: pd.DataFrame) -> MarketStructure:
        """Determine overall market structure (BOS/CHoCH)"""
        highs = df['high'].rolling(5).max()
        lows = df['low'].rolling(5).min()
        
        higher_highs = (highs.diff() > 0).sum()
        lower_lows = (lows.diff() < 0).sum()
        
        if higher_highs > len(df) * 0.6:
            return MarketStructure.UPTREND
        elif lower_lows > len(df) * 0.6:
            return MarketStructure.DOWNTREND
        else:
            return MarketStructure.RANGING


class SignalGenerator:
    """
    Main Signal Generator combining SMC analysis with traditional indicators
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.smc = SMCAnalyzer()
        self.min_confidence = self.config.get('min_confidence', 0.75)
        self.risk_reward_min = self.config.get('risk_reward_min', 1.5)
        
    def generate_signal(self, symbol: str, df: pd.DataFrame, timeframe: str = "H1") -> Optional[TradingSignal]:
        """
        Generate trading signal based on SMC analysis
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSD', 'EURUSD')
            df: OHLCV DataFrame
            timeframe: Chart timeframe
            
        Returns:
            TradingSignal if conditions met, None otherwise
        """
        if len(df) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return None
        
        # SMC Analysis
        order_blocks = self.smc.identify_order_blocks(df)
        fvgs = self.smc.identify_fair_value_gaps(df)
        sweeps = self.smc.identify_liquidity_sweeps(df)
        market_structure = self.smc.determine_market_structure(df)
        
        current_price = df['close'].iloc[-1]
        
        # Look for confluence: Order Block + FVG + Liquidity Sweep
        signal = self._evaluate_confluence(
            symbol, current_price, order_blocks, fvgs, sweeps, 
            market_structure, df, timeframe
        )
        
        return signal
    
    def _evaluate_confluence(self, symbol: str, current_price: float, 
                           order_blocks: List[SMCZone], fvgs: List[SMCZone],
                           sweeps: List[SMCZone], market_structure: MarketStructure,
                           df: pd.DataFrame, timeframe: str) -> Optional[TradingSignal]:
        """Evaluate multiple SMC factors for trade signal"""
        
        # Check for recent bullish confluence
        bullish_obs = [ob for ob in order_blocks if ob.direction == OrderBlockType.BULLISH and ob.is_valid]
        bullish_fvgs = [fvg for fvg in fvgs if fvg.direction == OrderBlockType.BULLISH]
        bullish_sweeps = [s for s in sweeps if s.direction == OrderBlockType.BULLISH]
        
        # Check for recent bearish confluence
        bearish_obs = [ob for ob in order_blocks if ob.direction == OrderBlockType.BEARISH and ob.is_valid]
        bearish_fvgs = [fvg for fvg in fvgs if fvg.direction == OrderBlockType.BEARISH]
        bearish_sweeps = [s for s in sweeps if s.direction == OrderBlockType.BEARISH]
        
        # Bullish Scenario: Price at OB + FVG alignment + Liquidity sweep + Uptrend
        if (bullish_obs and bullish_fvgs and 
            market_structure in [MarketStructure.UPTREND, MarketStructure.RANGING]):
            
            nearest_ob = min(bullish_obs, key=lambda x: abs(x.price_low - current_price))
            
            # Check if price is near order block (within 0.5%)
            if abs(current_price - nearest_ob.price_low) / current_price < 0.005:
                confidence = self._calculate_confidence(
                    nearest_ob, bullish_fvgs[-1] if bullish_fvgs else None,
                    bullish_sweeps[-1] if bullish_sweeps else None, market_structure
                )
                
                if confidence >= self.min_confidence:
                    return self._create_signal(
                        symbol, 'buy', current_price, nearest_ob, 
                        bullish_fvgs[-1] if bullish_fvgs else None,
                        confidence, df, timeframe
                    )
        
        # Bearish Scenario: Price at OB + FVG alignment + Liquidity sweep + Downtrend
        if (bearish_obs and bearish_fvgs and 
            market_structure in [MarketStructure.DOWNTREND, MarketStructure.RANGING]):
            
            nearest_ob = min(bearish_obs, key=lambda x: abs(x.price_high - current_price))
            
            if abs(current_price - nearest_ob.price_high) / current_price < 0.005:
                confidence = self._calculate_confidence(
                    nearest_ob, bearish_fvgs[-1] if bearish_fvgs else None,
                    bearish_sweeps[-1] if bearish_sweeps else None, market_structure
                )
                
                if confidence >= self.min_confidence:
                    return self._create_signal(
                        symbol, 'sell', current_price, nearest_ob,
                        bearish_fvgs[-1] if bearish_fvgs else None,
                        confidence, df, timeframe
                    )
        
        return None
    
    def _calculate_confidence(self, ob: SMCZone, fvg: Optional[SMCZone], 
                            sweep: Optional[SMCZone], market_structure: MarketStructure) -> float:
        """Calculate overall signal confidence score"""
        score = 0.0
        
        # Order Block strength (0-40%)
        score += ob.strength * 0.4
        
        # FVG presence (0-30%)
        if fvg:
            score += fvg.strength * 0.3
        
        # Liquidity sweep confirmation (0-20%)
        if sweep:
            score += sweep.strength * 0.2
        
        # Market structure alignment (0-10%)
        if (ob.direction == OrderBlockType.BULLISH and market_structure == MarketStructure.UPTREND) or \
           (ob.direction == OrderBlockType.BEARISH and market_structure == MarketStructure.DOWNTREND):
            score += 0.1
        
        return min(1.0, score)
    
    def _create_signal(self, symbol: str, direction: str, entry: float, 
                      ob: SMCZone, fvg: Optional[SMCZone], confidence: float,
                      df: pd.DataFrame, timeframe: str) -> TradingSignal:
        """Create trading signal with proper risk management"""
        
        atr = self._calculate_atr(df)
        
        if direction == 'buy':
            stop_loss = ob.price_low - (atr * 1.5)
            # Risk:Reward 1:2 minimum
            risk = entry - stop_loss
            take_profit = entry + (risk * 2.0)
        else:
            stop_loss = ob.price_high + (atr * 1.5)
            risk = stop_loss - entry
            take_profit = entry - (risk * 2.0)
        
        risk_reward = abs(take_profit - entry) / abs(entry - stop_loss)
        
        smc_zones = [ob]
        if fvg:
            smc_zones.append(fvg)
        
        return TradingSignal(
            symbol=symbol,
            direction=direction,
            entry_price=round(entry, 5),
            stop_loss=round(stop_loss, 5),
            take_profit=round(take_profit, 5),
            confidence=round(confidence, 2),
            strategy='SMC_Confluence',
            smc_zones=smc_zones,
            risk_reward=round(risk_reward, 2),
            timeframe=timeframe,
            timestamp=datetime.utcnow(),
            metadata={
                'atr': round(atr, 5),
                'market_structure': str(market_structure),
                'ob_strength': ob.strength
            }
        )
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range for stop loss placement"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(period).mean().iloc[-1]


# Backward compatibility with V1
class SignalEngine(SignalGenerator):
    """Alias for V1 compatibility"""
    pass
