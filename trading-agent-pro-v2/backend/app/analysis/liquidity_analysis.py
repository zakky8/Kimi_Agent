"""
Liquidity Analysis Module
Identifies liquidity zones, order blocks, and institutional levels
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LiquidityType(Enum):
    BUY_SIDE = "buy_side"      # Liquidity below price (stops of longs)
    SELL_SIDE = "sell_side"    # Liquidity above price (stops of shorts)
    EQUAL = "equal"            # Equal highs/lows


class ZoneType(Enum):
    ORDER_BLOCK_BULLISH = "order_block_bullish"
    ORDER_BLOCK_BEARISH = "order_block_bearish"
    BREAKER_BLOCK = "breaker_block"
    FAIR_VALUE_GAP = "fair_value_gap"
    LIQUIDITY_ZONE = "liquidity_zone"


@dataclass
class LiquidityZone:
    """Liquidity zone data"""
    zone_type: ZoneType
    price_top: float
    price_bottom: float
    start_time: datetime
    end_time: Optional[datetime]
    strength: int  # 1-5 scale
    hit_count: int
    is_active: bool
    metadata: Dict[str, Any]


@dataclass
class OrderBlock:
    """Order block data"""
    block_type: str  # "bullish" or "bearish"
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    volume: float
    timestamp: datetime
    timeframe: str
    mitigation_level: Optional[float] = None
    is_mitigated: bool = False


@dataclass
class FairValueGap:
    """Fair Value Gap (FVG) data"""
    gap_type: str  # "bullish" or "bearish"
    top_price: float
    bottom_price: float
    timestamp: datetime
    is_filled: bool = False
    fill_percentage: float = 0.0


class LiquidityAnalyzer:
    """
    Advanced Liquidity Analysis
    - Identifies liquidity zones (equal highs/lows)
    - Detects order blocks
    - Finds fair value gaps
    - Tracks breaker blocks
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.liquidity_zones: List[LiquidityZone] = []
        self.order_blocks: List[OrderBlock] = []
        self.fair_value_gaps: List[FairValueGap] = []
        self.support_levels: List[float] = []
        self.resistance_levels: List[float] = []
        
    def analyze_all(self) -> Dict[str, Any]:
        """Run complete liquidity analysis"""
        self.find_liquidity_zones()
        self.find_order_blocks()
        self.find_fair_value_gaps()
        self.find_support_resistance()
        
        return {
            "liquidity_zones": len(self.liquidity_zones),
            "order_blocks": len(self.order_blocks),
            "fair_value_gaps": len(self.fair_value_gaps),
            "support_levels": self.support_levels,
            "resistance_levels": self.resistance_levels,
            "buy_side_liquidity": self.get_buy_side_liquidity(),
            "sell_side_liquidity": self.get_sell_side_liquidity(),
            "nearest_liquidity": self.get_nearest_liquidity()
        }
    
    def find_liquidity_zones(self, lookback: int = 100, merge_threshold: float = 0.001):
        """
        Find liquidity zones (equal highs/lows)
        
        Args:
            lookback: Number of candles to look back
            merge_threshold: Price difference threshold for merging zones (0.1%)
        """
        if len(self.df) < lookback:
            return
        
        recent = self.df.tail(lookback)
        highs = recent['high'].values
        lows = recent['low'].values
        
        # Find equal highs (sell-side liquidity)
        high_clusters = self._cluster_levels(highs, merge_threshold)
        for level, count in high_clusters.items():
            if count >= 2:  # At least 2 touches
                zone = LiquidityZone(
                    zone_type=ZoneType.LIQUIDITY_ZONE,
                    price_top=level * (1 + merge_threshold),
                    price_bottom=level * (1 - merge_threshold),
                    start_time=recent.index[0],
                    end_time=recent.index[-1],
                    strength=min(count, 5),
                    hit_count=count,
                    is_active=True,
                    metadata={"type": "sell_side", "level": level}
                )
                self.liquidity_zones.append(zone)
        
        # Find equal lows (buy-side liquidity)
        low_clusters = self._cluster_levels(lows, merge_threshold)
        for level, count in low_clusters.items():
            if count >= 2:
                zone = LiquidityZone(
                    zone_type=ZoneType.LIQUIDITY_ZONE,
                    price_top=level * (1 + merge_threshold),
                    price_bottom=level * (1 - merge_threshold),
                    start_time=recent.index[0],
                    end_time=recent.index[-1],
                    strength=min(count, 5),
                    hit_count=count,
                    is_active=True,
                    metadata={"type": "buy_side", "level": level}
                )
                self.liquidity_zones.append(zone)
    
    def find_order_blocks(self, lookback: int = 50):
        """
        Find order blocks (imbalanced candles before strong moves)
        
        An order block is the last opposing candle before a strong impulsive move
        """
        if len(self.df) < lookback + 3:
            return
        
        recent = self.df.tail(lookback + 3)
        
        for i in range(2, len(recent) - 1):
            try:
                # Current candle
                curr = recent.iloc[i]
                prev = recent.iloc[i-1]
                prev2 = recent.iloc[i-2]
                
                # Check for bullish order block
                # Last bearish candle before strong bullish move
                if (prev2['close'] < prev2['open'] and  # Bearish candle 2 bars ago
                    prev['close'] > prev['open'] and    # Bullish candle 1 bar ago
                    prev['close'] - prev['open'] > abs(prev2['close'] - prev2['open']) * 1.5):  # Stronger move
                    
                    ob = OrderBlock(
                        block_type="bullish",
                        open_price=prev2['open'],
                        close_price=prev2['close'],
                        high_price=prev2['high'],
                        low_price=prev2['low'],
                        volume=prev2['volume'],
                        timestamp=recent.index[i-2],
                        timeframe="unknown"
                    )
                    self.order_blocks.append(ob)
                
                # Check for bearish order block
                # Last bullish candle before strong bearish move
                elif (prev2['close'] > prev2['open'] and  # Bullish candle 2 bars ago
                      prev['close'] < prev['open'] and    # Bearish candle 1 bar ago
                      prev['open'] - prev['close'] > abs(prev2['close'] - prev2['open']) * 1.5):
                    
                    ob = OrderBlock(
                        block_type="bearish",
                        open_price=prev2['open'],
                        close_price=prev2['close'],
                        high_price=prev2['high'],
                        low_price=prev2['low'],
                        volume=prev2['volume'],
                        timestamp=recent.index[i-2],
                        timeframe="unknown"
                    )
                    self.order_blocks.append(ob)
                    
            except Exception as e:
                continue
    
    def find_fair_value_gaps(self, lookback: int = 100):
        """
        Find Fair Value Gaps (FVGs)
        
        A bullish FVG: Current low > Previous high
        A bearish FVG: Current high < Previous low
        """
        if len(self.df) < lookback + 2:
            return
        
        recent = self.df.tail(lookback + 2)
        
        for i in range(2, len(recent)):
            try:
                curr = recent.iloc[i]
                prev = recent.iloc[i-1]
                prev2 = recent.iloc[i-2]
                
                # Bullish FVG
                if curr['low'] > prev2['high']:
                    fvg = FairValueGap(
                        gap_type="bullish",
                        top_price=curr['low'],
                        bottom_price=prev2['high'],
                        timestamp=recent.index[i]
                    )
                    self.fair_value_gaps.append(fvg)
                
                # Bearish FVG
                elif curr['high'] < prev2['low']:
                    fvg = FairValueGap(
                        gap_type="bearish",
                        top_price=prev2['low'],
                        bottom_price=curr['high'],
                        timestamp=recent.index[i]
                    )
                    self.fair_value_gaps.append(fvg)
                    
            except Exception as e:
                continue
    
    def find_support_resistance(self, lookback: int = 100):
        """Find support and resistance levels"""
        if len(self.df) < lookback:
            return
        
        recent = self.df.tail(lookback)
        highs = recent['high'].values
        lows = recent['low'].values
        
        # Find swing highs (resistance)
        resistance = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                resistance.append(highs[i])
        
        # Find swing lows (support)
        support = []
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                support.append(lows[i])
        
        # Cluster levels
        self.resistance_levels = self._cluster_levels_list(resistance, 0.002)
        self.support_levels = self._cluster_levels_list(support, 0.002)
    
    def _cluster_levels(self, levels: np.ndarray, threshold: float) -> Dict[float, int]:
        """Cluster price levels"""
        if len(levels) == 0:
            return {}
        
        sorted_levels = np.sort(levels)
        clusters = {}
        current_cluster = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] < threshold:
                current_cluster.append(level)
            else:
                avg_level = np.mean(current_cluster)
                clusters[avg_level] = len(current_cluster)
                current_cluster = [level]
        
        if current_cluster:
            avg_level = np.mean(current_cluster)
            clusters[avg_level] = len(current_cluster)
        
        return clusters
    
    def _cluster_levels_list(self, levels: List[float], threshold: float) -> List[float]:
        """Cluster price levels from list"""
        if not levels:
            return []
        
        sorted_levels = sorted(levels)
        clusters = []
        current_cluster = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] < threshold:
                current_cluster.append(level)
            else:
                clusters.append(np.mean(current_cluster))
                current_cluster = [level]
        
        if current_cluster:
            clusters.append(np.mean(current_cluster))
        
        return sorted(clusters)
    
    def get_buy_side_liquidity(self) -> List[Dict]:
        """Get buy-side liquidity zones (below current price)"""
        if len(self.df) == 0:
            return []
        
        current_price = self.df['close'].iloc[-1]
        
        buy_liquidity = []
        for zone in self.liquidity_zones:
            if zone.metadata.get("type") == "buy_side":
                if zone.price_top < current_price:
                    buy_liquidity.append({
                        "top": zone.price_top,
                        "bottom": zone.price_bottom,
                        "strength": zone.strength,
                        "distance_pips": (current_price - zone.price_top) * 10000
                    })
        
        return sorted(buy_liquidity, key=lambda x: x['distance_pips'])
    
    def get_sell_side_liquidity(self) -> List[Dict]:
        """Get sell-side liquidity zones (above current price)"""
        if len(self.df) == 0:
            return []
        
        current_price = self.df['close'].iloc[-1]
        
        sell_liquidity = []
        for zone in self.liquidity_zones:
            if zone.metadata.get("type") == "sell_side":
                if zone.price_bottom > current_price:
                    sell_liquidity.append({
                        "top": zone.price_top,
                        "bottom": zone.price_bottom,
                        "strength": zone.strength,
                        "distance_pips": (zone.price_bottom - current_price) * 10000
                    })
        
        return sorted(sell_liquidity, key=lambda x: x['distance_pips'])
    
    def get_nearest_liquidity(self) -> Optional[Dict]:
        """Get the nearest liquidity zone to current price"""
        buy_side = self.get_buy_side_liquidity()
        sell_side = self.get_sell_side_liquidity()
        
        nearest_buy = buy_side[0] if buy_side else None
        nearest_sell = sell_side[0] if sell_side else None
        
        if nearest_buy and nearest_sell:
            if nearest_buy['distance_pips'] < nearest_sell['distance_pips']:
                return {"side": "buy", **nearest_buy}
            else:
                return {"side": "sell", **nearest_sell}
        elif nearest_buy:
            return {"side": "buy", **nearest_buy}
        elif nearest_sell:
            return {"side": "sell", **nearest_sell}
        
        return None
    
    def get_active_order_blocks(self) -> List[Dict]:
        """Get order blocks that haven't been mitigated"""
        if len(self.df) == 0:
            return []
        
        current_price = self.df['close'].iloc[-1]
        active_obs = []
        
        for ob in self.order_blocks:
            if not ob.is_mitigated:
                # Check if price has entered the block
                if ob.block_type == "bullish":
                    if current_price <= ob.high_price and current_price >= ob.low_price:
                        active_obs.append({
                            "type": "bullish",
                            "high": ob.high_price,
                            "low": ob.low_price,
                            "timestamp": ob.timestamp.isoformat()
                        })
                else:  # bearish
                    if current_price >= ob.low_price and current_price <= ob.high_price:
                        active_obs.append({
                            "type": "bearish",
                            "high": ob.high_price,
                            "low": ob.low_price,
                            "timestamp": ob.timestamp.isoformat()
                        })
        
        return active_obs
    
    def get_unfilled_fvgs(self) -> List[Dict]:
        """Get unfilled fair value gaps"""
        unfilled = []
        
        for fvg in self.fair_value_gaps:
            if not fvg.is_filled:
                unfilled.append({
                    "type": fvg.gap_type,
                    "top": fvg.top_price,
                    "bottom": fvg.bottom_price,
                    "timestamp": fvg.timestamp.isoformat()
                })
        
        return unfilled
    
    def get_summary(self) -> Dict[str, Any]:
        """Get complete liquidity analysis summary"""
        return {
            "liquidity_zones_count": len(self.liquidity_zones),
            "order_blocks_count": len(self.order_blocks),
            "fair_value_gaps_count": len(self.fair_value_gaps),
            "support_levels": self.support_levels[-5:] if self.support_levels else [],
            "resistance_levels": self.resistance_levels[-5:] if self.resistance_levels else [],
            "buy_side_liquidity": self.get_buy_side_liquidity()[:3],
            "sell_side_liquidity": self.get_sell_side_liquidity()[:3],
            "nearest_liquidity": self.get_nearest_liquidity(),
            "active_order_blocks": self.get_active_order_blocks()[:5],
            "unfilled_fvgs": self.get_unfilled_fvgs()[:5]
        }
