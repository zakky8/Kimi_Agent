"""
Confluence Engine Module
Combines multiple signals for high-confidence trades
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConfluenceFactor(Enum):
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    PATTERN = "pattern"
    REGIME = "regime"
    FUNDAMENTAL = "fundamental"
    VOLUME = "volume"


@dataclass
class ConfluenceScore:
    """Confluence analysis result"""
    total_score: float
    confidence: float
    factors_present: int
    factors_required: int
    factor_breakdown: Dict[str, float]
    recommendation: str


class ConfluenceEngine:
    """
    Implements confluence-based signal filtering
    Requires multiple confirming factors for high-confidence signals
    """
    
    # Minimum factors required for different confidence levels
    FACTOR_THRESHOLDS = {
        "strong": 4,
        "moderate": 3,
        "weak": 2
    }
    
    # Factor weights
    FACTOR_WEIGHTS = {
        ConfluenceFactor.TECHNICAL: 1.0,
        ConfluenceFactor.SENTIMENT: 0.8,
        ConfluenceFactor.PATTERN: 0.9,
        ConfluenceFactor.REGIME: 0.7,
        ConfluenceFactor.FUNDAMENTAL: 0.8,
        ConfluenceFactor.VOLUME: 0.6
    }
    
    def __init__(self, factors_required: int = 3):
        self.factors_required = factors_required
        
    def calculate_confluence(
        self,
        technical_score: float,
        sentiment_score: float,
        pattern_score: float,
        regime_score: float,
        volume_score: float = 0.5,
        fundamental_score: float = 0.5
    ) -> ConfluenceScore:
        """
        Calculate confluence score from multiple factors
        
        Each score should be between -1 (bearish) and 1 (bullish)
        """
        factors = {
            ConfluenceFactor.TECHNICAL: technical_score,
            ConfluenceFactor.SENTIMENT: sentiment_score,
            ConfluenceFactor.PATTERN: pattern_score,
            ConfluenceFactor.REGIME: regime_score,
            ConfluenceFactor.VOLUME: volume_score,
            ConfluenceFactor.FUNDAMENTAL: fundamental_score
        }
        
        # Count confirming factors
        bullish_factors = sum(1 for s in factors.values() if s > 0.3)
        bearish_factors = sum(1 for s in factors.values() if s < -0.3)
        neutral_factors = sum(1 for s in factors.values() if abs(s) <= 0.3)
        
        # Calculate weighted score
        weighted_score = sum(
            score * self.FACTOR_WEIGHTS[factor]
            for factor, score in factors.items()
        ) / sum(self.FACTOR_WEIGHTS.values())
        
        # Determine direction and confidence
        if bullish_factors >= self.factors_required:
            direction = "bullish"
            confidence = min(bullish_factors / 5, 1.0)
        elif bearish_factors >= self.factors_required:
            direction = "bearish"
            confidence = min(bearish_factors / 5, 1.0)
        else:
            direction = "neutral"
            confidence = 0
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            direction, confidence, factors
        )
        
        return ConfluenceScore(
            total_score=round(weighted_score, 3),
            confidence=round(confidence, 3),
            factors_present=max(bullish_factors, bearish_factors),
            factors_required=self.factors_required,
            factor_breakdown={
                f.value: round(s, 3) for f, s in factors.items()
            },
            recommendation=recommendation
        )
    
    def _generate_recommendation(
        self,
        direction: str,
        confidence: float,
        factors: Dict[ConfluenceFactor, float]
    ) -> str:
        """Generate trading recommendation"""
        if confidence < 0.5:
            return "Insufficient confluence - avoid trading"
        
        # Find strongest factors
        sorted_factors = sorted(
            factors.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        strongest = sorted_factors[0]
        factor_name = strongest[0].value
        factor_score = strongest[1]
        
        if direction == "bullish":
            if confidence > 0.8:
                return f"Strong BUY - High confluence with {factor_name} leading ({factor_score:+.2f})"
            elif confidence > 0.6:
                return f"Moderate BUY - Good confluence, {factor_name} supportive"
            else:
                return f"Weak BUY - Some confluence but caution advised"
        elif direction == "bearish":
            if confidence > 0.8:
                return f"Strong SELL - High confluence with {factor_name} leading ({factor_score:+.2f})"
            elif confidence > 0.6:
                return f"Moderate SELL - Good confluence, {factor_name} supportive"
            else:
                return f"Weak SELL - Some confluence but caution advised"
        else:
            return "NEUTRAL - Mixed signals, wait for clarity"
    
    def validate_signal(
        self,
        signal_direction: str,
        confluence: ConfluenceScore
    ) -> Tuple[bool, str]:
        """
        Validate if a signal meets confluence requirements
        
        Returns:
            (is_valid, reason)
        """
        if confluence.factors_present < self.factors_required:
            return False, f"Insufficient factors: {confluence.factors_present}/{self.factors_required}"
        
        if confluence.confidence < 0.6:
            return False, f"Low confidence: {confluence.confidence:.2f}"
        
        # Check alignment
        if signal_direction == "long" and confluence.total_score < 0.3:
            return False, "Signal direction doesn't match confluence"
        
        if signal_direction == "short" and confluence.total_score > -0.3:
            return False, "Signal direction doesn't match confluence"
        
        return True, "Signal validated by confluence"
    
    def get_confluence_report(self, confluence: ConfluenceScore) -> Dict[str, Any]:
        """Generate detailed confluence report"""
        return {
            "score": confluence.total_score,
            "confidence": confluence.confidence,
            "factors_present": confluence.factors_present,
            "factors_required": confluence.factors_required,
            "meets_threshold": confluence.factors_present >= self.factors_required,
            "recommendation": confluence.recommendation,
            "breakdown": confluence.factor_breakdown,
            "quality": self._assess_quality(confluence)
        }
    
    def _assess_quality(self, confluence: ConfluenceScore) -> str:
        """Assess signal quality"""
        if confluence.confidence >= 0.8 and confluence.factors_present >= 4:
            return "institutional_grade"
        elif confluence.confidence >= 0.6 and confluence.factors_present >= 3:
            return "professional_grade"
        elif confluence.confidence >= 0.5:
            return "retail_grade"
        else:
            return "low_confidence"


# Singleton instance
_confluence_engine: Optional[ConfluenceEngine] = None


def get_confluence_engine(factors_required: int = 3) -> ConfluenceEngine:
    """Get or create confluence engine singleton"""
    global _confluence_engine
    if _confluence_engine is None:
        _confluence_engine = ConfluenceEngine(factors_required)
    return _confluence_engine
