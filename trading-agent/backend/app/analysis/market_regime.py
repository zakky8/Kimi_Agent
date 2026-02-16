"""
Market Regime Detection Module
Identifies market conditions using statistical methods
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from sklearn.mixture import GaussianMixture
from sklearn.svm import SVC
import logging

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGE_BOUND = "range_bound"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class RegimeState:
    """Current market regime state"""
    regime: MarketRegime
    confidence: float
    duration: int  # bars in current regime
    features: Dict[str, float]


class MarketRegimeDetector:
    """
    Detects market regimes using:
    - Hidden Markov Model (HMM) approach with GMM
    - SVM classification
    - Volatility-based detection
    - Trend strength analysis
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.current_regime: Optional[RegimeState] = None
        self.regime_history: List[RegimeState] = []
        self.gmm: Optional[GaussianMixture] = None
        self.svm: Optional[SVC] = None
        
    def calculate_features(self) -> pd.DataFrame:
        """Calculate regime detection features"""
        # Returns
        self.df["returns"] = self.df["close"].pct_change()
        
        # Volatility features
        self.df["volatility_10"] = self.df["returns"].rolling(10).std() * np.sqrt(252)
        self.df["volatility_20"] = self.df["returns"].rolling(20).std() * np.sqrt(252)
        self.df["volatility_ratio"] = self.df["volatility_10"] / self.df["volatility_20"]
        
        # Trend features
        self.df["sma_ratio"] = self.df["close"] / self.df["close"].rolling(20).mean()
        
        # ADX for trend strength
        from pandas_ta import adx
        adx_data = adx(self.df["high"], self.df["low"], self.df["close"], length=14)
        self.df["adx"] = adx_data["ADX_14"]
        
        # Price range features
        self.df["daily_range"] = (self.df["high"] - self.df["low"]) / self.df["close"]
        self.df["range_ma"] = self.df["daily_range"].rolling(20).mean()
        self.df["range_ratio"] = self.df["daily_range"] / self.df["range_ma"]
        
        # Momentum features
        self.df["momentum_10"] = self.df["close"] / self.df["close"].shift(10) - 1
        self.df["momentum_20"] = self.df["close"] / self.df["close"].shift(20) - 1
        
        # Autocorrelation (trend persistence)
        self.df["autocorr_5"] = self.df["returns"].rolling(20).apply(
            lambda x: x.autocorr(lag=1) if len(x) > 5 else 0
        )
        
        return self.df
    
    def detect_regime(self) -> RegimeState:
        """Detect current market regime"""
        if len(self.df) < 30:
            return RegimeState(
                regime=MarketRegime.RANGE_BOUND,
                confidence=0.5,
                duration=0,
                features={}
            )
        
        self.calculate_features()
        
        latest = self.df.iloc[-1]
        
        # Extract features
        features = {
            "volatility_20": latest.get("volatility_20", 0),
            "adx": latest.get("adx", 0),
            "sma_ratio": latest.get("sma_ratio", 1),
            "momentum_10": latest.get("momentum_10", 0),
            "range_ratio": latest.get("range_ratio", 1),
            "autocorr": latest.get("autocorr_5", 0)
        }
        
        # Rule-based regime detection
        regime, confidence = self._rule_based_detection(features)
        
        # Calculate duration
        duration = 0
        if self.regime_history:
            if self.regime_history[-1].regime == regime:
                duration = self.regime_history[-1].duration + 1
        
        state = RegimeState(
            regime=regime,
            confidence=confidence,
            duration=duration,
            features=features
        )
        
        self.current_regime = state
        self.regime_history.append(state)
        
        return state
    
    def _rule_based_detection(self, features: Dict[str, float]) -> Tuple[MarketRegime, float]:
        """Rule-based regime detection"""
        volatility = features.get("volatility_20", 0)
        adx = features.get("adx", 0)
        sma_ratio = features.get("sma_ratio", 1)
        momentum = features.get("momentum_10", 0)
        
        # High volatility regime
        if volatility > 0.5:  # 50% annualized volatility
            return MarketRegime.HIGH_VOLATILITY, 0.8
        
        # Low volatility regime
        if volatility < 0.1:  # 10% annualized volatility
            return MarketRegime.LOW_VOLATILITY, 0.7
        
        # Trending regimes
        if adx > 25:  # Strong trend
            if sma_ratio > 1.02 and momentum > 0.02:
                return MarketRegime.TRENDING_UP, min(adx / 50, 0.9)
            elif sma_ratio < 0.98 and momentum < -0.02:
                return MarketRegime.TRENDING_DOWN, min(adx / 50, 0.9)
        
        # Range-bound
        if adx < 20 and abs(sma_ratio - 1) < 0.02:
            return MarketRegime.RANGE_BOUND, 0.7
        
        # Default
        return MarketRegime.RANGE_BOUND, 0.5
    
    def train_gmm(self, n_components: int = 4):
        """Train Gaussian Mixture Model for regime detection"""
        if len(self.df) < 100:
            logger.warning("Insufficient data for GMM training")
            return
        
        # Prepare features
        feature_cols = ["volatility_20", "adx", "sma_ratio", "momentum_10", "range_ratio"]
        data = self.df[feature_cols].dropna()
        
        if len(data) < 50:
            return
        
        # Train GMM
        self.gmm = GaussianMixture(
            n_components=n_components,
            covariance_type="full",
            random_state=42
        )
        self.gmm.fit(data)
        
        logger.info(f"GMM trained with {n_components} components")
    
    def predict_gmm_regime(self) -> Optional[MarketRegime]:
        """Predict regime using trained GMM"""
        if self.gmm is None or len(self.df) < 1:
            return None
        
        feature_cols = ["volatility_20", "adx", "sma_ratio", "momentum_10", "range_ratio"]
        latest = self.df[feature_cols].iloc[-1].values.reshape(1, -1)
        
        # Predict cluster
        cluster = self.gmm.predict(latest)[0]
        
        # Map cluster to regime (would need labeling in practice)
        regime_map = {
            0: MarketRegime.RANGE_BOUND,
            1: MarketRegime.TRENDING_UP,
            2: MarketRegime.TRENDING_DOWN,
            3: MarketRegime.HIGH_VOLATILITY
        }
        
        return regime_map.get(cluster, MarketRegime.RANGE_BOUND)
    
    def get_regime_statistics(self) -> Dict[str, Any]:
        """Get statistics about regime history"""
        if not self.regime_history:
            return {}
        
        regimes = [r.regime for r in self.regime_history]
        
        from collections import Counter
        regime_counts = Counter(regimes)
        
        # Average duration per regime
        avg_durations = {}
        for regime in MarketRegime:
            durations = [r.duration for r in self.regime_history if r.regime == regime]
            if durations:
                avg_durations[regime.value] = sum(durations) / len(durations)
        
        return {
            "current_regime": self.current_regime.regime.value if self.current_regime else None,
            "current_confidence": self.current_regime.confidence if self.current_regime else 0,
            "current_duration": self.current_regime.duration if self.current_regime else 0,
            "regime_distribution": {
                r.value: count / len(regimes) 
                for r, count in regime_counts.items()
            },
            "avg_durations": avg_durations,
            "total_observations": len(self.regime_history)
        }
    
    def get_trading_recommendation(self) -> Dict[str, Any]:
        """Get trading recommendation based on regime"""
        if not self.current_regime:
            return {"action": "neutral", "confidence": 0}
        
        regime = self.current_regime.regime
        
        recommendations = {
            MarketRegime.TRENDING_UP: {
                "action": "trend_following_long",
                "strategy": "Buy pullbacks, use trend-following indicators",
                "timeframe": "medium",
                "risk_profile": "moderate"
            },
            MarketRegime.TRENDING_DOWN: {
                "action": "trend_following_short",
                "strategy": "Sell rallies, use trend-following indicators",
                "timeframe": "medium",
                "risk_profile": "moderate"
            },
            MarketRegime.RANGE_BOUND: {
                "action": "mean_reversion",
                "strategy": "Buy support, sell resistance",
                "timeframe": "short",
                "risk_profile": "low"
            },
            MarketRegime.HIGH_VOLATILITY: {
                "action": "reduce_size",
                "strategy": "Reduce position sizes, widen stops",
                "timeframe": "short",
                "risk_profile": "high"
            },
            MarketRegime.LOW_VOLATILITY: {
                "action": "breakout_ready",
                "strategy": "Prepare for breakout, watch for expansion",
                "timeframe": "medium",
                "risk_profile": "low"
            }
        }
        
        rec = recommendations.get(regime, recommendations[MarketRegime.RANGE_BOUND])
        rec["confidence"] = self.current_regime.confidence
        rec["regime"] = regime.value
        
        return rec
