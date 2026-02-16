"""
Technical Indicators Module
Comprehensive technical analysis using pandas-ta and ta libraries
"""
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"


@dataclass
class IndicatorSignal:
    """Structured indicator signal"""
    indicator: str
    signal: SignalType
    strength: float  # 0.0 to 1.0
    value: float
    description: str


class TechnicalIndicators:
    """
    Comprehensive technical analysis engine
    Implements institutional-grade indicators
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV dataframe
        
        Args:
            df: DataFrame with columns [open, high, low, close, volume]
        """
        self.df = df.copy()
        self.signals: List[IndicatorSignal] = []
        
    def add_all_indicators(self) -> pd.DataFrame:
        """Add all technical indicators to dataframe"""
        self.add_trend_indicators()
        self.add_momentum_indicators()
        self.add_volatility_indicators()
        self.add_volume_indicators()
        return self.df
    
    # ==================== TREND INDICATORS ====================
    
    def add_trend_indicators(self):
        """Add trend-following indicators"""
        # EMAs
        self.df["ema_9"] = ta.ema(self.df["close"], length=9)
        self.df["ema_21"] = ta.ema(self.df["close"], length=21)
        self.df["ema_50"] = ta.ema(self.df["close"], length=50)
        self.df["ema_200"] = ta.ema(self.df["close"], length=200)
        
        # SMAs
        self.df["sma_20"] = ta.sma(self.df["close"], length=20)
        self.df["sma_50"] = ta.sma(self.df["close"], length=50)
        
        # MACD
        macd = ta.macd(self.df["close"], fast=12, slow=26, signal=9)
        self.df["macd"] = macd["MACD_12_26_9"]
        self.df["macd_signal"] = macd["MACDs_12_26_9"]
        self.df["macd_hist"] = macd["MACDh_12_26_9"]
        
        # ADX (Trend Strength)
        adx = ta.adx(self.df["high"], self.df["low"], self.df["close"], length=14)
        self.df["adx"] = adx["ADX_14"]
        self.df["dmp"] = adx["DMP_14"]
        self.df["dmn"] = adx["DMN_14"]
        
        # Parabolic SAR
        psar = ta.psar(self.df["high"], self.df["low"], self.df["close"])
        self.df["psar"] = psar["PSARl_0.02_0.2"]
        
        # Ichimoku Cloud
        ichimoku = ta.ichimoku(
            self.df["high"], self.df["low"], self.df["close"]
        )
        self.df["ichi_tenkan"] = ichimoku[0]["ITS_9"]
        self.df["ichi_kijun"] = ichimoku[0]["IKS_26"]
        self.df["ichi_senkou_a"] = ichimoku[0]["ISA_9"]
        self.df["ichi_senkou_b"] = ichimoku[0]["ISB_26"]
        
    # ==================== MOMENTUM INDICATORS ====================
    
    def add_momentum_indicators(self):
        """Add momentum oscillators"""
        # RSI
        self.df["rsi_14"] = ta.rsi(self.df["close"], length=14)
        self.df["rsi_7"] = ta.rsi(self.df["close"], length=7)
        
        # Stochastic
        stoch = ta.stoch(self.df["high"], self.df["low"], self.df["close"])
        self.df["stoch_k"] = stoch["STOCHk_14_3_3"]
        self.df["stoch_d"] = stoch["STOCHd_14_3_3"]
        
        # Stochastic RSI
        stochrsi = ta.stochrsi(self.df["close"])
        self.df["stochrsi_k"] = stochrsi["STOCHRSIk_14_14_3_3"]
        self.df["stochrsi_d"] = stochrsi["STOCHRSId_14_14_3_3"]
        
        # Williams %R
        self.df["williams_r"] = ta.willr(self.df["high"], self.df["low"], self.df["close"])
        
        # CCI
        self.df["cci"] = ta.cci(self.df["high"], self.df["low"], self.df["close"])
        
        # Awesome Oscillator
        self.df["ao"] = ta.ao(self.df["high"], self.df["low"])
        
        # Momentum
        self.df["mom"] = ta.mom(self.df["close"])
        
        # ROC (Rate of Change)
        self.df["roc"] = ta.roc(self.df["close"])
        
    # ==================== VOLATILITY INDICATORS ====================
    
    def add_volatility_indicators(self):
        """Add volatility measures"""
        # Bollinger Bands
        bbands = ta.bbands(self.df["close"], length=20, std=2)
        self.df["bb_upper"] = bbands["BBU_20_2.0"]
        self.df["bb_middle"] = bbands["BBM_20_2.0"]
        self.df["bb_lower"] = bbands["BBL_20_2.0"]
        self.df["bb_width"] = bbands["BBB_20_2.0"]
        self.df["bb_percent"] = bbands["BBP_20_2.0"]
        
        # ATR (Average True Range)
        self.df["atr_14"] = ta.atr(self.df["high"], self.df["low"], self.df["close"])
        self.df["atr_7"] = ta.atr(self.df["high"], self.df["low"], self.df["close"], length=7)
        
        # Keltner Channels
        kc = ta.kc(self.df["high"], self.df["low"], self.df["close"])
        self.df["kc_upper"] = kc["KCUe_20_2"]
        self.df["kc_lower"] = kc["KCLe_20_2"]
        
        # Donchian Channels
        dc = ta.donchian(self.df["high"], self.df["low"])
        self.df["dc_upper"] = dc["DCU_20_20"]
        self.df["dc_lower"] = dc["DCL_20_20"]
        
        # Historical Volatility
        self.df["hv_20"] = self.df["close"].pct_change().rolling(20).std() * np.sqrt(252)
        
    # ==================== VOLUME INDICATORS ====================
    
    def add_volume_indicators(self):
        """Add volume-based indicators"""
        # OBV (On Balance Volume)
        self.df["obv"] = ta.obv(self.df["close"], self.df["volume"])
        
        # VWAP
        self.df["vwap"] = ta.vwap(
            self.df["high"], self.df["low"], self.df["close"], self.df["volume"]
        )
        
        # Volume EMA
        self.df["volume_ema_20"] = ta.ema(self.df["volume"], length=20)
        
        # MFI (Money Flow Index)
        self.df["mfi"] = ta.mfi(
            self.df["high"], self.df["low"], self.df["close"], self.df["volume"]
        )
        
        # Chaikin Money Flow
        self.df["cmf"] = ta.cmf(
            self.df["high"], self.df["low"], self.df["close"], self.df["volume"]
        )
        
        # Volume Profile (simplified)
        self.df["volume_delta"] = self.df["volume"].diff()
        
    # ==================== SIGNAL GENERATION ====================
    
    def generate_signals(self) -> List[IndicatorSignal]:
        """Generate trading signals from indicators"""
        self.signals = []
        
        if len(self.df) < 50:
            logger.warning("Insufficient data for signal generation")
            return self.signals
        
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else latest
        
        # RSI Signals
        self._check_rsi(latest)
        
        # MACD Signals
        self._check_macd(latest, prev)
        
        # Moving Average Signals
        self._check_moving_averages(latest)
        
        # Bollinger Bands Signals
        self._check_bollinger(latest)
        
        # Stochastic Signals
        self._check_stochastic(latest)
        
        # ADX Trend Strength
        self._check_adx(latest)
        
        # Volume Signals
        self._check_volume(latest, prev)
        
        return self.signals
    
    def _check_rsi(self, latest: pd.Series):
        """Check RSI for signals"""
        rsi = latest.get("rsi_14", 50)
        
        if rsi < 30:
            self.signals.append(IndicatorSignal(
                indicator="RSI",
                signal=SignalType.BUY,
                strength=(30 - rsi) / 30 * 0.8 + 0.2,
                value=rsi,
                description=f"RSI oversold at {rsi:.1f}"
            ))
        elif rsi > 70:
            self.signals.append(IndicatorSignal(
                indicator="RSI",
                signal=SignalType.SELL,
                strength=(rsi - 70) / 30 * 0.8 + 0.2,
                value=rsi,
                description=f"RSI overbought at {rsi:.1f}"
            ))
    
    def _check_macd(self, latest: pd.Series, prev: pd.Series):
        """Check MACD for signals"""
        macd = latest.get("macd", 0)
        signal = latest.get("macd_signal", 0)
        hist = latest.get("macd_hist", 0)
        prev_hist = prev.get("macd_hist", 0)
        
        # MACD crossover
        if prev_hist < 0 and hist > 0:
            self.signals.append(IndicatorSignal(
                indicator="MACD",
                signal=SignalType.BUY,
                strength=0.7,
                value=macd,
                description="MACD bullish crossover"
            ))
        elif prev_hist > 0 and hist < 0:
            self.signals.append(IndicatorSignal(
                indicator="MACD",
                signal=SignalType.SELL,
                strength=0.7,
                value=macd,
                description="MACD bearish crossover"
            ))
    
    def _check_moving_averages(self, latest: pd.Series):
        """Check moving average signals"""
        close = latest.get("close", 0)
        ema_9 = latest.get("ema_9", 0)
        ema_21 = latest.get("ema_21", 0)
        ema_50 = latest.get("ema_50", 0)
        
        # EMA crossover
        if ema_9 > ema_21:
            self.signals.append(IndicatorSignal(
                indicator="EMA",
                signal=SignalType.BUY,
                strength=0.6,
                value=ema_9,
                description="EMA9 above EMA21"
            ))
        elif ema_9 < ema_21:
            self.signals.append(IndicatorSignal(
                indicator="EMA",
                signal=SignalType.SELL,
                strength=0.6,
                value=ema_9,
                description="EMA9 below EMA21"
            ))
        
        # Golden/Death cross
        if ema_50 > 0:
            if close > ema_50:
                self.signals.append(IndicatorSignal(
                    indicator="MA_TREND",
                    signal=SignalType.BUY,
                    strength=0.5,
                    value=close,
                    description="Price above EMA50"
                ))
            else:
                self.signals.append(IndicatorSignal(
                    indicator="MA_TREND",
                    signal=SignalType.SELL,
                    strength=0.5,
                    value=close,
                    description="Price below EMA50"
                ))
    
    def _check_bollinger(self, latest: pd.Series):
        """Check Bollinger Bands signals"""
        close = latest.get("close", 0)
        bb_upper = latest.get("bb_upper", 0)
        bb_lower = latest.get("bb_lower", 0)
        bb_percent = latest.get("bb_percent", 0.5)
        
        if close <= bb_lower:
            self.signals.append(IndicatorSignal(
                indicator="Bollinger",
                signal=SignalType.BUY,
                strength=0.7,
                value=bb_percent,
                description="Price at lower Bollinger Band"
            ))
        elif close >= bb_upper:
            self.signals.append(IndicatorSignal(
                indicator="Bollinger",
                signal=SignalType.SELL,
                strength=0.7,
                value=bb_percent,
                description="Price at upper Bollinger Band"
            ))
    
    def _check_stochastic(self, latest: pd.Series):
        """Check Stochastic signals"""
        stoch_k = latest.get("stoch_k", 50)
        stoch_d = latest.get("stoch_d", 50)
        
        if stoch_k < 20 and stoch_d < 20:
            self.signals.append(IndicatorSignal(
                indicator="Stochastic",
                signal=SignalType.BUY,
                strength=(20 - stoch_k) / 20 * 0.7 + 0.3,
                value=stoch_k,
                description=f"Stochastic oversold at {stoch_k:.1f}"
            ))
        elif stoch_k > 80 and stoch_d > 80:
            self.signals.append(IndicatorSignal(
                indicator="Stochastic",
                signal=SignalType.SELL,
                strength=(stoch_k - 80) / 20 * 0.7 + 0.3,
                value=stoch_k,
                description=f"Stochastic overbought at {stoch_k:.1f}"
            ))
    
    def _check_adx(self, latest: pd.Series):
        """Check ADX trend strength"""
        adx = latest.get("adx", 0)
        dmp = latest.get("dmp", 0)
        dmn = latest.get("dmn", 0)
        
        if adx > 25:
            if dmp > dmn:
                self.signals.append(IndicatorSignal(
                    indicator="ADX",
                    signal=SignalType.BUY,
                    strength=min(adx / 50, 1.0),
                    value=adx,
                    description=f"Strong uptrend (ADX: {adx:.1f})"
                ))
            else:
                self.signals.append(IndicatorSignal(
                    indicator="ADX",
                    signal=SignalType.SELL,
                    strength=min(adx / 50, 1.0),
                    value=adx,
                    description=f"Strong downtrend (ADX: {adx:.1f})"
                ))
    
    def _check_volume(self, latest: pd.Series, prev: pd.Series):
        """Check volume signals"""
        volume = latest.get("volume", 0)
        volume_ema = latest.get("volume_ema_20", 0)
        close = latest.get("close", 0)
        prev_close = prev.get("close", close)
        
        if volume_ema > 0:
            volume_ratio = volume / volume_ema
            
            if volume_ratio > 1.5:
                if close > prev_close:
                    self.signals.append(IndicatorSignal(
                        indicator="Volume",
                        signal=SignalType.BUY,
                        strength=min((volume_ratio - 1) * 0.5, 0.8),
                        value=volume_ratio,
                        description=f"High volume on up move ({volume_ratio:.1f}x)"
                    ))
                else:
                    self.signals.append(IndicatorSignal(
                        indicator="Volume",
                        signal=SignalType.SELL,
                        strength=min((volume_ratio - 1) * 0.5, 0.8),
                        value=volume_ratio,
                        description=f"High volume on down move ({volume_ratio:.1f}x)"
                    ))
    
    # ==================== UTILITY METHODS ====================
    
    def get_support_resistance(self, lookback: int = 50) -> Dict[str, List[float]]:
        """Calculate support and resistance levels"""
        if len(self.df) < lookback:
            return {"support": [], "resistance": []}
        
        recent = self.df.tail(lookback)
        
        # Find local minima and maxima
        highs = recent["high"].values
        lows = recent["low"].values
        
        resistance_levels = []
        support_levels = []
        
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                resistance_levels.append(highs[i])
            
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                support_levels.append(lows[i])
        
        # Cluster levels
        def cluster_levels(levels: List[float], tolerance: float = 0.01) -> List[float]:
            if not levels:
                return []
            
            levels = sorted(levels)
            clusters = []
            current_cluster = [levels[0]]
            
            for level in levels[1:]:
                if abs(level - current_cluster[-1]) / current_cluster[-1] < tolerance:
                    current_cluster.append(level)
                else:
                    clusters.append(sum(current_cluster) / len(current_cluster))
                    current_cluster = [level]
            
            if current_cluster:
                clusters.append(sum(current_cluster) / len(current_cluster))
            
            return clusters
        
        return {
            "support": cluster_levels(support_levels),
            "resistance": cluster_levels(resistance_levels)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all indicators"""
        if len(self.df) == 0:
            return {}
        
        latest = self.df.iloc[-1]
        
        return {
            "trend": {
                "ema_9": latest.get("ema_9"),
                "ema_21": latest.get("ema_21"),
                "ema_50": latest.get("ema_50"),
                "macd": latest.get("macd"),
                "adx": latest.get("adx")
            },
            "momentum": {
                "rsi_14": latest.get("rsi_14"),
                "stoch_k": latest.get("stoch_k"),
                "cci": latest.get("cci")
            },
            "volatility": {
                "atr_14": latest.get("atr_14"),
                "bb_width": latest.get("bb_width"),
                "hv_20": latest.get("hv_20")
            },
            "volume": {
                "obv": latest.get("obv"),
                "vwap": latest.get("vwap"),
                "mfi": latest.get("mfi")
            },
            "signals": [
                {
                    "indicator": s.indicator,
                    "signal": s.signal.value,
                    "strength": s.strength,
                    "description": s.description
                }
                for s in self.signals
            ]
        }
