"""
Kimi Agent — Technical Indicator Engine (Part 2)

Computes 40+ technical indicators from OHLCV candle DataFrames using pandas-ta.
All outputs are NaN-safe floats returned as a flat dictionary that serves as the
feature vector for ML models.

Categories:
  • Trend       — EMA, SMA, VWAP, Supertrend, ADX, Ichimoku, Parabolic SAR
  • Momentum    — RSI, Stoch RSI, MACD, CCI, Williams %R, ROC
  • Volatility  — Bollinger, ATR, Keltner, HV, Choppiness Index
  • Volume      — OBV, CMF, MFI, Volume SMA surge detection
  • S/R         — Pivot Points, Swing H/L, Round Numbers, Fib Retracements
  • Patterns    — 10+ candlestick patterns
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _safe(val: Any) -> float:
    """Convert NaN / None / inf to 0.0 for safe downstream use."""
    if val is None:
        return 0.0
    try:
        f = float(val)
        return 0.0 if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return 0.0


def _last(series: Optional[pd.Series]) -> float:
    """Return last non-NaN value of a Series, or 0.0."""
    if series is None or series.empty:
        return 0.0
    return _safe(series.iloc[-1])


class IndicatorEngine:
    """
    Accepts a pandas DataFrame of OHLCV candles and computes ALL indicators
    in a single ``compute(df)`` call.

    The DataFrame MUST have columns: open, high, low, close, volume
    (case-insensitive — we normalise internally).
    """

    def compute(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Compute all indicators and return a flat dict of float values.
        This dict becomes the feature vector fed into ML models.
        """
        if df is None or len(df) < 20:
            logger.warning("[Indicators] Not enough data (need ≥20 candles)")
            return {}

        # Normalise column names to lowercase
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]

        # Ensure required columns
        for col in ("open", "high", "low", "close"):
            if col not in df.columns:
                logger.error(f"[Indicators] Missing required column: {col}")
                return {}

        if "volume" not in df.columns:
            df["volume"] = 0.0

        result: Dict[str, float] = {}

        # Compute each category — never crash on any
        for name, fn in [
            ("trend", self._trend_indicators),
            ("momentum", self._momentum_indicators),
            ("volatility", self._volatility_indicators),
            ("volume", self._volume_indicators),
            ("support_resistance", self._support_resistance),
            ("candlestick", self._candlestick_patterns),
        ]:
            try:
                result.update(fn(df))
            except Exception as exc:
                logger.warning(f"[Indicators] Error computing {name}: {exc}")

        return result

    # ────────────────────────────────────────────────────
    # TREND INDICATORS
    # ────────────────────────────────────────────────────

    def _trend_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        out: Dict[str, float] = {}

        # EMAs
        for period in (9, 20, 50, 200):
            ema = close.ewm(span=period, adjust=False).mean()
            out[f"ema_{period}"] = _last(ema)

        # SMAs
        for period in (20, 50):
            sma = close.rolling(window=period).mean()
            out[f"sma_{period}"] = _last(sma)

        # VWAP (volume-weighted average price — approx daily reset)
        if df["volume"].sum() > 0:
            typical = (high + low + close) / 3.0
            vwap = (typical * df["volume"]).cumsum() / df["volume"].cumsum()
            out["vwap"] = _last(vwap)
        else:
            out["vwap"] = _last(close)

        # Supertrend (period=10, multiplier=3)
        st = self._supertrend(df, period=10, multiplier=3.0)
        out["supertrend"] = st["value"]
        out["supertrend_direction"] = st["direction"]

        # ADX (14) with DI+ and DI-
        adx_result = self._adx(df, period=14)
        out["adx_14"] = adx_result["adx"]
        out["di_plus"] = adx_result["di_plus"]
        out["di_minus"] = adx_result["di_minus"]

        # Ichimoku Cloud
        ichi = self._ichimoku(df)
        out.update(ichi)

        # Parabolic SAR
        psar = self._parabolic_sar(df)
        out["psar"] = psar["value"]
        out["psar_direction"] = psar["direction"]

        # EMA alignment score: +1 if 9>20>50>200, -1 if reversed
        if all(f"ema_{p}" in out for p in (9, 20, 50, 200)):
            e9, e20, e50, e200 = out["ema_9"], out["ema_20"], out["ema_50"], out["ema_200"]
            if e9 > e20 > e50 > e200:
                out["ema_alignment"] = 1.0
            elif e9 < e20 < e50 < e200:
                out["ema_alignment"] = -1.0
            else:
                out["ema_alignment"] = 0.0

        return out

    # ────────────────────────────────────────────────────
    # MOMENTUM INDICATORS
    # ────────────────────────────────────────────────────

    def _momentum_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        out: Dict[str, float] = {}

        # RSI (14)
        out["rsi_14"] = _last(self._rsi(close, 14))

        # Stochastic RSI
        stoch = self._stochastic(high, low, close, k_period=14, d_period=3, smooth=3)
        out["stoch_k"] = stoch["k"]
        out["stoch_d"] = stoch["d"]

        # MACD (12, 26, 9)
        macd = self._macd(close, fast=12, slow=26, signal=9)
        out["macd_line"] = macd["line"]
        out["macd_signal"] = macd["signal"]
        out["macd_histogram"] = macd["histogram"]

        # CCI (20)
        out["cci_20"] = _last(self._cci(high, low, close, 20))

        # Williams %R (14)
        out["williams_r"] = _last(self._williams_r(high, low, close, 14))

        # Rate of Change (10)
        roc = close.pct_change(periods=10) * 100
        out["roc_10"] = _last(roc)

        return out

    # ────────────────────────────────────────────────────
    # VOLATILITY INDICATORS
    # ────────────────────────────────────────────────────

    def _volatility_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        out: Dict[str, float] = {}

        # ATR (14)
        atr = self._atr(high, low, close, 14)
        out["atr_14"] = _last(atr)

        # ATR as percentage of close
        last_close = _last(close)
        out["atr_pct"] = (out["atr_14"] / last_close * 100) if last_close > 0 else 0.0

        # Bollinger Bands (20, 2)
        bb = self._bollinger(close, period=20, std_dev=2.0)
        out["bb_upper"] = bb["upper"]
        out["bb_middle"] = bb["middle"]
        out["bb_lower"] = bb["lower"]
        out["bb_bandwidth"] = bb["bandwidth"]
        out["bb_percent_b"] = bb["percent_b"]

        # Keltner Channels (20, 2)
        kc = self._keltner(close, high, low, period=20, multiplier=2.0, atr_series=atr)
        out["kc_upper"] = kc["upper"]
        out["kc_middle"] = kc["middle"]
        out["kc_lower"] = kc["lower"]

        # Historical Volatility (21) — annualised
        returns = close.pct_change().dropna()
        if len(returns) >= 21:
            hv = returns.rolling(21).std() * np.sqrt(252) * 100
            out["hv_21"] = _last(hv)
        else:
            out["hv_21"] = 0.0

        # Choppiness Index (14)
        out["choppiness_14"] = _last(self._choppiness(high, low, close, 14))

        return out

    # ────────────────────────────────────────────────────
    # VOLUME INDICATORS
    # ────────────────────────────────────────────────────

    def _volume_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        close = df["close"]
        volume = df["volume"]
        high = df["high"]
        low = df["low"]
        out: Dict[str, float] = {}

        # OBV (On Balance Volume)
        obv = self._obv(close, volume)
        out["obv"] = _last(obv)

        # CMF (Chaikin Money Flow, 20)
        out["cmf_20"] = _last(self._cmf(high, low, close, volume, 20))

        # MFI (Money Flow Index, 14)
        out["mfi_14"] = _last(self._mfi(high, low, close, volume, 14))

        # Volume SMA (20) — and surge detection
        vol_sma = volume.rolling(20).mean()
        out["volume_sma_20"] = _last(vol_sma)
        last_vol = _last(volume)
        last_sma = _last(vol_sma)
        out["volume_surge"] = 1.0 if (last_sma > 0 and last_vol > 1.5 * last_sma) else 0.0
        out["volume_ratio"] = (last_vol / last_sma) if last_sma > 0 else 1.0

        return out

    # ────────────────────────────────────────────────────
    # SUPPORT & RESISTANCE
    # ────────────────────────────────────────────────────

    def _support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        last_close = _last(close)
        out: Dict[str, float] = {}

        # Classic Pivot Points
        prev_h = _last(high.iloc[:-1]) if len(high) > 1 else _last(high)
        prev_l = _last(low.iloc[:-1]) if len(low) > 1 else _last(low)
        prev_c = _last(close.iloc[:-1]) if len(close) > 1 else _last(close)

        pivot = (prev_h + prev_l + prev_c) / 3.0
        out["pivot"] = pivot
        out["pivot_r1"] = 2.0 * pivot - prev_l
        out["pivot_s1"] = 2.0 * pivot - prev_h
        out["pivot_r2"] = pivot + (prev_h - prev_l)
        out["pivot_s2"] = pivot - (prev_h - prev_l)

        # Fibonacci levels from last 50 candles
        if len(df) >= 50:
            recent = df.iloc[-50:]
            fib_high = recent["high"].max()
            fib_low = recent["low"].min()
            fib_range = fib_high - fib_low
            out["fib_236"] = fib_high - fib_range * 0.236
            out["fib_382"] = fib_high - fib_range * 0.382
            out["fib_500"] = fib_high - fib_range * 0.500
            out["fib_618"] = fib_high - fib_range * 0.618
            out["fib_786"] = fib_high - fib_range * 0.786
        else:
            out["fib_236"] = out["fib_382"] = out["fib_500"] = 0.0
            out["fib_618"] = out["fib_786"] = 0.0

        # Swing highs/lows (last 5)
        swings = self._swing_levels(high, low, lookback=5)
        out["nearest_support"] = swings["nearest_support"]
        out["nearest_resistance"] = swings["nearest_resistance"]
        out["near_support"] = 1.0 if abs(last_close - swings["nearest_support"]) / max(last_close, 1e-10) < 0.005 else 0.0
        out["near_resistance"] = 1.0 if abs(last_close - swings["nearest_resistance"]) / max(last_close, 1e-10) < 0.005 else 0.0

        # Round number levels
        if last_close > 100:  # Crypto / stock
            rn = round(last_close / 100) * 100
        elif last_close > 1:  # Forex major
            rn = round(last_close / 0.005) * 0.005
        else:
            rn = round(last_close, 4)
        out["round_number"] = rn

        return out

    # ────────────────────────────────────────────────────
    # CANDLESTICK PATTERNS
    # ────────────────────────────────────────────────────

    def _candlestick_patterns(self, df: pd.DataFrame) -> Dict[str, float]:
        """Detect 10+ candlestick patterns. Returns 1=bullish, -1=bearish, 0=none."""
        if len(df) < 3:
            return {}

        o = df["open"].values
        h = df["high"].values
        l = df["low"].values
        c = df["close"].values
        out: Dict[str, float] = {}

        # Last candle properties
        body = abs(c[-1] - o[-1])
        upper_wick = h[-1] - max(o[-1], c[-1])
        lower_wick = min(o[-1], c[-1]) - l[-1]
        total_range = h[-1] - l[-1]
        is_bullish = c[-1] > o[-1]

        # Doji (body < 10% of range)
        out["pattern_doji"] = 1.0 if (total_range > 0 and body / total_range < 0.1) else 0.0

        # Hammer (bullish reversal) — small body at top, long lower wick
        out["pattern_hammer"] = 1.0 if (
            total_range > 0
            and lower_wick > 2 * body
            and upper_wick < body
        ) else 0.0

        # Inverted Hammer
        out["pattern_inverted_hammer"] = 1.0 if (
            total_range > 0
            and upper_wick > 2 * body
            and lower_wick < body
        ) else 0.0

        # Shooting Star (bearish)
        out["pattern_shooting_star"] = -1.0 if (
            total_range > 0
            and upper_wick > 2 * body
            and lower_wick < body
            and c[-2] < c[-1] if len(c) > 1 else False
        ) else 0.0

        # Bullish Engulfing
        if len(df) >= 2:
            prev_body = abs(c[-2] - o[-2])
            out["pattern_bullish_engulfing"] = 1.0 if (
                c[-2] < o[-2]  # Previous candle is bearish
                and c[-1] > o[-1]  # Current is bullish
                and o[-1] <= c[-2]  # Current open <= prev close
                and c[-1] >= o[-2]  # Current close >= prev open
            ) else 0.0

            # Bearish Engulfing
            out["pattern_bearish_engulfing"] = -1.0 if (
                c[-2] > o[-2]  # Previous is bullish
                and c[-1] < o[-1]  # Current is bearish
                and o[-1] >= c[-2]  # Current open >= prev close
                and c[-1] <= o[-2]  # Current close <= prev open
            ) else 0.0
        else:
            out["pattern_bullish_engulfing"] = 0.0
            out["pattern_bearish_engulfing"] = 0.0

        # Morning Star / Evening Star (3-candle patterns)
        if len(df) >= 3:
            body_3 = abs(c[-3] - o[-3])
            body_2 = abs(c[-2] - o[-2])
            body_1 = abs(c[-1] - o[-1])

            # Morning Star: bearish → small body → bullish
            out["pattern_morning_star"] = 1.0 if (
                c[-3] < o[-3]  # 1st bearish
                and body_2 < body_3 * 0.3  # 2nd small body
                and c[-1] > o[-1]  # 3rd bullish
                and c[-1] > (o[-3] + c[-3]) / 2  # closes above midpoint of 1st
            ) else 0.0

            # Evening Star: bullish → small body → bearish
            out["pattern_evening_star"] = -1.0 if (
                c[-3] > o[-3]  # 1st bullish
                and body_2 < body_3 * 0.3  # 2nd small body
                and c[-1] < o[-1]  # 3rd bearish
                and c[-1] < (o[-3] + c[-3]) / 2  # closes below midpoint of 1st
            ) else 0.0
        else:
            out["pattern_morning_star"] = 0.0
            out["pattern_evening_star"] = 0.0

        # Three White Soldiers / Three Black Crows
        if len(df) >= 3:
            out["pattern_three_white_soldiers"] = 1.0 if (
                c[-3] > o[-3] and c[-2] > o[-2] and c[-1] > o[-1]
                and c[-2] > c[-3] and c[-1] > c[-2]
                and o[-2] > o[-3] and o[-1] > o[-2]
            ) else 0.0

            out["pattern_three_black_crows"] = -1.0 if (
                c[-3] < o[-3] and c[-2] < o[-2] and c[-1] < o[-1]
                and c[-2] < c[-3] and c[-1] < c[-2]
                and o[-2] < o[-3] and o[-1] < o[-2]
            ) else 0.0
        else:
            out["pattern_three_white_soldiers"] = 0.0
            out["pattern_three_black_crows"] = 0.0

        # Pinbar (body:wick ratio > 1:3)
        if total_range > 0:
            if lower_wick > 3 * body and upper_wick < body:
                out["pattern_pinbar"] = 1.0  # Bullish pin
            elif upper_wick > 3 * body and lower_wick < body:
                out["pattern_pinbar"] = -1.0  # Bearish pin
            else:
                out["pattern_pinbar"] = 0.0
        else:
            out["pattern_pinbar"] = 0.0

        return out

    # ════════════════════════════════════════════════════
    # PRIVATE CALCULATION HELPERS
    # ════════════════════════════════════════════════════

    @staticmethod
    def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            "line": _last(macd_line),
            "signal": _last(signal_line),
            "histogram": _last(histogram),
        }

    @staticmethod
    def _stochastic(
        high: pd.Series, low: pd.Series, close: pd.Series,
        k_period: int = 14, d_period: int = 3, smooth: int = 3,
    ) -> Dict[str, float]:
        lowest = low.rolling(k_period).min()
        highest = high.rolling(k_period).max()
        k = ((close - lowest) / (highest - lowest).replace(0, np.nan)) * 100
        k = k.rolling(smooth).mean()
        d = k.rolling(d_period).mean()
        return {"k": _last(k), "d": _last(d)}

    @staticmethod
    def _cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        tp = (high + low + close) / 3.0
        sma = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        return (tp - sma) / (0.015 * mad.replace(0, np.nan))

    @staticmethod
    def _williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        highest = high.rolling(period).max()
        lowest = low.rolling(period).min()
        return -100 * (highest - close) / (highest - lowest).replace(0, np.nan)

    @staticmethod
    def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)
        return tr.ewm(alpha=1 / period, min_periods=period).mean()

    @staticmethod
    def _bollinger(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        middle = close.rolling(period).mean()
        std = close.rolling(period).std()
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        last_upper = _last(upper)
        last_lower = _last(lower)
        last_middle = _last(middle)
        bandwidth = (last_upper - last_lower) / last_middle if last_middle > 0 else 0.0
        last_close = _last(close)
        pct_b = (last_close - last_lower) / (last_upper - last_lower) if (last_upper - last_lower) > 0 else 0.5
        return {
            "upper": last_upper,
            "middle": last_middle,
            "lower": last_lower,
            "bandwidth": bandwidth,
            "percent_b": pct_b,
        }

    @staticmethod
    def _keltner(
        close: pd.Series, high: pd.Series, low: pd.Series,
        period: int = 20, multiplier: float = 2.0,
        atr_series: Optional[pd.Series] = None,
    ) -> Dict[str, float]:
        middle = close.ewm(span=period, adjust=False).mean()
        if atr_series is None:
            prev_close = close.shift(1)
            tr = pd.concat([
                high - low,
                (high - prev_close).abs(),
                (low - prev_close).abs(),
            ], axis=1).max(axis=1)
            atr_series = tr.ewm(alpha=1 / 14, min_periods=14).mean()
        upper = middle + multiplier * atr_series
        lower = middle - multiplier * atr_series
        return {
            "upper": _last(upper),
            "middle": _last(middle),
            "lower": _last(lower),
        }

    @staticmethod
    def _obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        return (volume * direction).cumsum()

    @staticmethod
    def _cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        mfm = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
        mfv = mfm * volume
        return mfv.rolling(period).sum() / volume.rolling(period).sum().replace(0, np.nan)

    @staticmethod
    def _mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        tp = (high + low + close) / 3.0
        mf = tp * volume
        delta = tp.diff()
        pos = mf.where(delta > 0, 0.0).rolling(period).sum()
        neg = mf.where(delta < 0, 0.0).rolling(period).sum()
        ratio = pos / neg.replace(0, np.nan)
        return 100 - (100 / (1 + ratio))

    @staticmethod
    def _supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Dict[str, float]:
        """Calculate Supertrend indicator."""
        high, low, close = df["high"], df["low"], df["close"]
        hl2 = (high + low) / 2.0

        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / period, min_periods=period).mean()

        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr

        supertrend = pd.Series(0.0, index=df.index)
        direction = pd.Series(1.0, index=df.index)

        for i in range(1, len(df)):
            if close.iloc[i] > upper_band.iloc[i - 1]:
                direction.iloc[i] = 1.0
            elif close.iloc[i] < lower_band.iloc[i - 1]:
                direction.iloc[i] = -1.0
            else:
                direction.iloc[i] = direction.iloc[i - 1]

            if direction.iloc[i] == 1.0:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]

        return {"value": _last(supertrend), "direction": _last(direction)}

    @staticmethod
    def _adx(df: pd.DataFrame, period: int = 14) -> Dict[str, float]:
        """Calculate ADX, DI+, DI-."""
        high, low, close = df["high"], df["low"], df["close"]

        up_move = high.diff()
        down_move = -low.diff()

        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)

        atr_smooth = tr.ewm(alpha=1 / period, min_periods=period).mean()
        plus_di = 100 * plus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr_smooth.replace(0, np.nan)
        minus_di = 100 * minus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr_smooth.replace(0, np.nan)

        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(alpha=1 / period, min_periods=period).mean()

        return {
            "adx": _last(adx),
            "di_plus": _last(plus_di),
            "di_minus": _last(minus_di),
        }

    @staticmethod
    def _ichimoku(df: pd.DataFrame) -> Dict[str, float]:
        """Calculate Ichimoku Cloud components."""
        high, low = df["high"], df["low"]

        # Tenkan-sen (9 periods)
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2.0
        # Kijun-sen (26 periods)
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2.0
        # Senkou A (shifted forward 26)
        senkou_a = (tenkan + kijun) / 2.0
        # Senkou B (52 periods, shifted forward 26)
        senkou_b = (high.rolling(52).max() + low.rolling(52).min()) / 2.0
        # Chikou Span = close shifted back 26
        chikou = df["close"].shift(-26)

        return {
            "ichimoku_tenkan": _last(tenkan),
            "ichimoku_kijun": _last(kijun),
            "ichimoku_senkou_a": _last(senkou_a),
            "ichimoku_senkou_b": _last(senkou_b),
            "ichimoku_chikou": _last(chikou),
        }

    @staticmethod
    def _parabolic_sar(df: pd.DataFrame, af_start: float = 0.02, af_step: float = 0.02, af_max: float = 0.20) -> Dict[str, float]:
        """Calculate Parabolic SAR."""
        high, low, close = df["high"].values, df["low"].values, df["close"].values
        n = len(df)
        if n < 2:
            return {"value": 0.0, "direction": 1.0}

        psar = np.zeros(n)
        direction = np.ones(n)
        af = af_start
        ep = high[0]
        psar[0] = low[0]

        for i in range(1, n):
            if direction[i - 1] == 1:  # Uptrend
                psar[i] = psar[i - 1] + af * (ep - psar[i - 1])
                psar[i] = min(psar[i], low[i - 1])
                if low[i] < psar[i]:
                    direction[i] = -1
                    psar[i] = ep
                    af = af_start
                    ep = low[i]
                else:
                    direction[i] = 1
                    if high[i] > ep:
                        ep = high[i]
                        af = min(af + af_step, af_max)
            else:  # Downtrend
                psar[i] = psar[i - 1] + af * (ep - psar[i - 1])
                psar[i] = max(psar[i], high[i - 1])
                if high[i] > psar[i]:
                    direction[i] = 1
                    psar[i] = ep
                    af = af_start
                    ep = high[i]
                else:
                    direction[i] = -1
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + af_step, af_max)

        return {"value": psar[-1], "direction": direction[-1]}

    @staticmethod
    def _choppiness(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Choppiness Index: 100*(LOG10(SUM(ATR)/range)/LOG10(period))"""
        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)

        atr_sum = tr.rolling(period).sum()
        high_max = high.rolling(period).max()
        low_min = low.rolling(period).min()
        hl_range = (high_max - low_min).replace(0, np.nan)

        return 100 * np.log10(atr_sum / hl_range) / np.log10(period)

    @staticmethod
    def _swing_levels(high: pd.Series, low: pd.Series, lookback: int = 5) -> Dict[str, float]:
        """Find nearest support/resistance from swing highs/lows."""
        swing_highs = []
        swing_lows = []

        values_h = high.values
        values_l = low.values
        n = len(values_h)

        for i in range(lookback, n - lookback):
            if values_h[i] == max(values_h[i - lookback: i + lookback + 1]):
                swing_highs.append(values_h[i])
            if values_l[i] == min(values_l[i - lookback: i + lookback + 1]):
                swing_lows.append(values_l[i])

        last_close = float(high.iloc[-1] + low.iloc[-1]) / 2.0  # approx

        if swing_lows:
            supports = [s for s in swing_lows if s < last_close]
            nearest_support = max(supports) if supports else min(swing_lows)
        else:
            nearest_support = float(low.min())

        if swing_highs:
            resistances = [r for r in swing_highs if r > last_close]
            nearest_resistance = min(resistances) if resistances else max(swing_highs)
        else:
            nearest_resistance = float(high.max())

        return {
            "nearest_support": _safe(nearest_support),
            "nearest_resistance": _safe(nearest_resistance),
        }
