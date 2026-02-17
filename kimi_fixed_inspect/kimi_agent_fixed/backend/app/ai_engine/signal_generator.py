"""
FIXED Signal Generator with Smart Money Concepts (SMC)
Replaces missing signal_generator.py from V2
Ported logic from V1 and enhanced with SMC analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Trading signal with SMC components"""
    symbol: str
    direction: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 to 1.0
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    timestamp: datetime
    
    # SMC-specific fields
    order_block_detected: bool = False
    fair_value_gap: bool = False
    liquidity_sweep: bool = False
    market_structure_shift: bool = False
    
    # Supporting analysis
    technical_score: float = 0.0
    smc_score: float = 0.0
    sentiment_score: float = 0.0
    
    # Trade metadata
    lot_size: Optional[float] = None
    notes: str = ""


class SignalGenerator:
    """
    Generates trading signals using Smart Money Concepts + Technical Analysis
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.min_confidence = self.config.get('min_confidence', 0.70)
        self.risk_reward_min = self.config.get('risk_reward_min', 2.0)
        
        logger.info("SignalGenerator initialized with SMC analysis")
    
    def generate_signal(
        self, 
        symbol: str, 
        ohlcv_data: pd.DataFrame,
        news_sentiment: Optional[Dict] = None
    ) -> Optional[TradingSignal]:
        """
        Main signal generation method
        
        Args:
            symbol: Trading pair (e.g., 'EURUSD')
            ohlcv_data: Historical OHLCV data
            news_sentiment: Optional sentiment analysis from news
        
        Returns:
            TradingSignal if conditions met, None otherwise
        """
        try:
            # Validate data
            if ohlcv_data is None or len(ohlcv_data) < 100:
                logger.warning(f"Insufficient data for {symbol}")
                return None
            
            # 1. Technical Analysis Score
            technical_score = self._calculate_technical_score(ohlcv_data)
            
            # 2. Smart Money Concepts Analysis
            smc_score, smc_components = self._analyze_smc(ohlcv_data)
            
            # 3. Sentiment Score (if available)
            sentiment_score = self._calculate_sentiment_score(news_sentiment)
            
            # 4. Combine scores for overall confidence
            confidence = self._calculate_confidence(
                technical_score, 
                smc_score, 
                sentiment_score
            )
            
            # 5. Determine direction
            direction = self._determine_direction(
                ohlcv_data, 
                technical_score, 
                smc_score
            )
            
            # Skip if confidence too low or no clear direction
            if confidence < self.min_confidence or direction == 'HOLD':
                logger.info(f"{symbol}: Confidence {confidence:.2f} below threshold or HOLD signal")
                return None
            
            # 6. Calculate entry, SL, TP
            current_price = float(ohlcv_data['close'].iloc[-1])
            stop_loss, take_profit = self._calculate_sl_tp(
                current_price, 
                direction, 
                ohlcv_data,
                smc_components
            )
            
            risk_reward = abs(take_profit - current_price) / abs(stop_loss - current_price)
            
            # Reject if risk/reward too low
            if risk_reward < self.risk_reward_min:
                logger.info(f"{symbol}: Risk/reward {risk_reward:.2f} below minimum")
                return None
            
            # 7. Create signal
            signal = TradingSignal(
                symbol=symbol,
                direction=direction,
                confidence=confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_reward_ratio=risk_reward,
                timestamp=datetime.now(),
                order_block_detected=smc_components['order_block'],
                fair_value_gap=smc_components['fvg'],
                liquidity_sweep=smc_components['liquidity_sweep'],
                market_structure_shift=smc_components['structure_shift'],
                technical_score=technical_score,
                smc_score=smc_score,
                sentiment_score=sentiment_score,
                notes=self._generate_signal_notes(smc_components)
            )
            
            logger.info(f"✅ Signal generated: {symbol} {direction} @ {current_price:.5f} "
                       f"(Confidence: {confidence:.2f}, R:R={risk_reward:.2f})")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}", exc_info=True)
            return None
    
    def _calculate_technical_score(self, df: pd.DataFrame) -> float:
        """
        Technical analysis using indicators
        Returns score 0.0 to 1.0
        """
        try:
            scores = []
            
            # Moving Average Trend
            df['ma_20'] = df['close'].rolling(20).mean()
            df['ma_50'] = df['close'].rolling(50).mean()
            
            current_price = df['close'].iloc[-1]
            ma_20 = df['ma_20'].iloc[-1]
            ma_50 = df['ma_50'].iloc[-1]
            
            # Bullish if price > MA20 > MA50
            if current_price > ma_20 > ma_50:
                scores.append(0.8)
            # Bearish if price < MA20 < MA50
            elif current_price < ma_20 < ma_50:
                scores.append(0.8)
            else:
                scores.append(0.3)
            
            # RSI (Relative Strength Index)
            rsi = self._calculate_rsi(df['close'])
            if rsi < 30:  # Oversold - potential buy
                scores.append(0.7)
            elif rsi > 70:  # Overbought - potential sell
                scores.append(0.7)
            else:
                scores.append(0.4)
            
            # MACD
            macd, signal_line = self._calculate_macd(df['close'])
            if macd > signal_line:
                scores.append(0.6)
            else:
                scores.append(0.4)
            
            # Volume trend
            avg_volume = df['volume'].rolling(20).mean().iloc[-1]
            current_volume = df['volume'].iloc[-1]
            
            if current_volume > avg_volume * 1.2:  # High volume confirms signal
                scores.append(0.7)
            else:
                scores.append(0.5)
            
            return np.mean(scores)
            
        except Exception as e:
            logger.error(f"Error calculating technical score: {e}")
            return 0.5
    
    def _analyze_smc(self, df: pd.DataFrame) -> Tuple[float, Dict]:
        """
        Smart Money Concepts analysis
        Returns (score, components dict)
        """
        components = {
            'order_block': False,
            'fvg': False,
            'liquidity_sweep': False,
            'structure_shift': False
        }
        
        try:
            # 1. Order Block Detection
            components['order_block'] = self._detect_order_block(df)
            
            # 2. Fair Value Gap (FVG)
            components['fvg'] = self._detect_fair_value_gap(df)
            
            # 3. Liquidity Sweep
            components['liquidity_sweep'] = self._detect_liquidity_sweep(df)
            
            # 4. Market Structure Shift
            components['structure_shift'] = self._detect_structure_shift(df)
            
            # Calculate SMC score
            smc_score = sum([
                0.3 if components['order_block'] else 0,
                0.3 if components['fvg'] else 0,
                0.2 if components['liquidity_sweep'] else 0,
                0.2 if components['structure_shift'] else 0
            ])
            
            return smc_score, components
            
        except Exception as e:
            logger.error(f"Error in SMC analysis: {e}")
            return 0.0, components
    
    def _detect_order_block(self, df: pd.DataFrame) -> bool:
        """
        Detect Order Blocks - institutional buying/selling zones
        """
        try:
            # Look at last 20 candles
            recent = df.tail(20)
            
            # Bullish Order Block: Strong bullish candle with large volume
            for i in range(len(recent) - 5, len(recent)):
                candle_body = abs(recent['close'].iloc[i] - recent['open'].iloc[i])
                candle_range = recent['high'].iloc[i] - recent['low'].iloc[i]
                
                # Strong bullish candle (body > 70% of range)
                if (recent['close'].iloc[i] > recent['open'].iloc[i] and 
                    candle_body / candle_range > 0.7):
                    
                    # High volume
                    if recent['volume'].iloc[i] > recent['volume'].mean() * 1.5:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting order block: {e}")
            return False
    
    def _detect_fair_value_gap(self, df: pd.DataFrame) -> bool:
        """
        Detect Fair Value Gaps - imbalances indicating strong moves
        """
        try:
            # FVG: Gap between candles where price moved too fast
            recent = df.tail(10)
            
            for i in range(1, len(recent) - 1):
                prev_high = recent['high'].iloc[i-1]
                next_low = recent['low'].iloc[i+1]
                
                # Bullish FVG: gap between previous high and next low
                if next_low > prev_high:
                    gap_size = next_low - prev_high
                    avg_range = (recent['high'] - recent['low']).mean()
                    
                    # Significant gap (> 50% of avg range)
                    if gap_size > avg_range * 0.5:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting FVG: {e}")
            return False
    
    def _detect_liquidity_sweep(self, df: pd.DataFrame) -> bool:
        """
        Detect Liquidity Sweeps - stop hunts by smart money
        """
        try:
            recent = df.tail(30)
            
            # Find recent swing lows
            swing_lows = []
            for i in range(2, len(recent) - 2):
                if (recent['low'].iloc[i] < recent['low'].iloc[i-1] and
                    recent['low'].iloc[i] < recent['low'].iloc[i-2] and
                    recent['low'].iloc[i] < recent['low'].iloc[i+1] and
                    recent['low'].iloc[i] < recent['low'].iloc[i+2]):
                    swing_lows.append(recent['low'].iloc[i])
            
            if not swing_lows:
                return False
            
            # Check if recent price swept below swing low then reversed
            lowest_swing = min(swing_lows)
            current_low = recent['low'].iloc[-1]
            current_close = recent['close'].iloc[-1]
            
            # Swept below then closed above
            if current_low < lowest_swing and current_close > lowest_swing:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting liquidity sweep: {e}")
            return False
    
    def _detect_structure_shift(self, df: pd.DataFrame) -> bool:
        """
        Detect Market Structure Shifts - trend changes
        """
        try:
            recent = df.tail(50)
            
            # Find swing highs and lows
            highs = []
            lows = []
            
            for i in range(5, len(recent) - 5):
                # Swing high
                if (recent['high'].iloc[i] > recent['high'].iloc[i-1] and
                    recent['high'].iloc[i] > recent['high'].iloc[i+1]):
                    highs.append((i, recent['high'].iloc[i]))
                
                # Swing low
                if (recent['low'].iloc[i] < recent['low'].iloc[i-1] and
                    recent['low'].iloc[i] < recent['low'].iloc[i+1]):
                    lows.append((i, recent['low'].iloc[i]))
            
            # Bullish structure shift: higher highs and higher lows
            if len(highs) >= 2 and len(lows) >= 2:
                # Recent highs higher than previous
                if highs[-1][1] > highs[-2][1] and lows[-1][1] > lows[-2][1]:
                    return True
                # Bearish shift: lower lows and lower highs
                elif highs[-1][1] < highs[-2][1] and lows[-1][1] < lows[-2][1]:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting structure shift: {e}")
            return False
    
    def _calculate_sentiment_score(self, news_sentiment: Optional[Dict]) -> float:
        """
        Calculate sentiment score from news analysis
        """
        if not news_sentiment:
            return 0.5  # Neutral
        
        try:
            # Aggregate sentiment from multiple sources
            scores = []
            
            if 'overall_sentiment' in news_sentiment:
                # Normalize to 0-1 range
                sentiment = news_sentiment['overall_sentiment']  # Assume -1 to 1
                normalized = (sentiment + 1) / 2
                scores.append(normalized)
            
            if 'news_count' in news_sentiment:
                # More news = higher confidence in sentiment
                news_count = min(news_sentiment['news_count'], 20)
                weight = news_count / 20
                scores.append(weight)
            
            return np.mean(scores) if scores else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.5
    
    def _calculate_confidence(
        self, 
        technical: float, 
        smc: float, 
        sentiment: float
    ) -> float:
        """
        Combine scores into overall confidence
        """
        # Weighted average
        weights = {
            'technical': 0.3,
            'smc': 0.5,      # SMC weighted highest
            'sentiment': 0.2
        }
        
        confidence = (
            technical * weights['technical'] +
            smc * weights['smc'] +
            sentiment * weights['sentiment']
        )
        
        return min(confidence, 1.0)
    
    def _determine_direction(
        self, 
        df: pd.DataFrame, 
        technical_score: float, 
        smc_score: float
    ) -> str:
        """
        Determine trade direction based on analysis
        """
        try:
            # Trend from moving averages
            ma_20 = df['close'].rolling(20).mean().iloc[-1]
            ma_50 = df['close'].rolling(50).mean().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Price momentum
            price_change = (current_price - df['close'].iloc[-10]) / df['close'].iloc[-10]
            
            # Combine signals
            bullish_signals = 0
            bearish_signals = 0
            
            # MA trend
            if current_price > ma_20 > ma_50:
                bullish_signals += 1
            elif current_price < ma_20 < ma_50:
                bearish_signals += 1
            
            # Momentum
            if price_change > 0.002:  # 0.2% upward
                bullish_signals += 1
            elif price_change < -0.002:
                bearish_signals += 1
            
            # Scores
            if technical_score > 0.6:
                bullish_signals += 1
            elif technical_score < 0.4:
                bearish_signals += 1
            
            if smc_score > 0.5:
                bullish_signals += 1
            
            # Decision
            if bullish_signals > bearish_signals + 1:
                return 'BUY'
            elif bearish_signals > bullish_signals + 1:
                return 'SELL'
            else:
                return 'HOLD'
                
        except Exception as e:
            logger.error(f"Error determining direction: {e}")
            return 'HOLD'
    
    def _calculate_sl_tp(
        self, 
        entry: float, 
        direction: str, 
        df: pd.DataFrame,
        smc_components: Dict
    ) -> Tuple[float, float]:
        """
        Calculate Stop Loss and Take Profit using SMC principles
        """
        try:
            # ATR for volatility-based levels
            atr = self._calculate_atr(df, period=14)
            
            if direction == 'BUY':
                # Stop loss below recent swing low or order block
                recent_lows = df['low'].tail(20)
                swing_low = recent_lows.min()
                
                stop_loss = swing_low - (atr * 0.5)
                
                # Take profit using risk/reward ratio
                risk = entry - stop_loss
                take_profit = entry + (risk * 2.5)  # 2.5:1 R:R
                
            else:  # SELL
                # Stop loss above recent swing high
                recent_highs = df['high'].tail(20)
                swing_high = recent_highs.max()
                
                stop_loss = swing_high + (atr * 0.5)
                
                # Take profit
                risk = stop_loss - entry
                take_profit = entry - (risk * 2.5)
            
            return stop_loss, take_profit
            
        except Exception as e:
            logger.error(f"Error calculating SL/TP: {e}")
            # Fallback to simple percentage
            if direction == 'BUY':
                return entry * 0.99, entry * 1.025
            else:
                return entry * 1.01, entry * 0.975
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[float, float]:
        """Calculate MACD indicator"""
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        
        return macd.iloc[-1], signal.iloc[-1]
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        return atr.iloc[-1]
    
    def _generate_signal_notes(self, smc_components: Dict) -> str:
        """Generate explanatory notes for the signal"""
        notes = []
        
        if smc_components['order_block']:
            notes.append("Order Block detected")
        if smc_components['fvg']:
            notes.append("Fair Value Gap present")
        if smc_components['liquidity_sweep']:
            notes.append("Liquidity Sweep confirmed")
        if smc_components['structure_shift']:
            notes.append("Market Structure Shift")
        
        return " | ".join(notes) if notes else "Standard technical setup"
