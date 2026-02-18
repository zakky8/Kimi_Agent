"""
OpenClaw-inspired Autonomous Reasoning Brain
Provides a Chain-of-Thought decision engine for AIAgent.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import AsyncOpenAI
import pandas as pd

from .signal_generator import SignalGenerator, TradingSignal
from ..config import settings

logger = logging.getLogger(__name__)

class OpenClawBrain:
    """
    Autonomous Reasoning engine that uses LLMs (Nemotron/Trinity) 
    to process multiple trading "skills" and generate high-confidence signals.
    """

    def __init__(self, agent_id: str, model_id: Optional[str] = None):
        self.agent_id = agent_id
        self.model_id = model_id or settings.DEFAULT_AI_MODEL
        self.signal_generator = SignalGenerator()
        self.last_thought: Optional[str] = None
        
        # Determine API key based on model
        self.api_key = settings.OPENROUTER_API_KEY
        if "nemotron" in self.model_id.lower() and settings.OPENROUTER_API_KEY_NEMOTRON:
            self.api_key = settings.OPENROUTER_API_KEY_NEMOTRON
        elif "trinity" in self.model_id.lower() and settings.OPENROUTER_API_KEY_TRINITY:
            self.api_key = settings.OPENROUTER_API_KEY_TRINITY

        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "AI Trading Agent Pro - OpenClaw Brain"
            }
        )

    async def think(self, symbol: str, df: pd.DataFrame, stats: Dict) -> Optional[TradingSignal]:
        """
        Primary reasoning loop.
        1. Access Skills (Technical, Context, News)
        2. Chain-of-Thought LLM Analysis
        3. Decision Generation
        """
        logger.info(f"Brain [{self.agent_id}] is thinking about {symbol}...")

        # 1. Access Skills
        tech_data = self._skill_technical_analysis(symbol, df)
        news_data = await self._skill_news_analysis(symbol)
        inst_context = await self._skill_institutional_context(symbol)
        
        # 2. Build Reasoning Context
        prompt = self._build_reasoning_prompt(symbol, tech_data, news_data, inst_context, stats)
        
        # 3. Request LLM Analysis
        try:
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": self._get_system_personality()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.4
            )
            
            self.last_thought = response.choices[0].message.content
            logger.debug(f"Brain Thought: {self.last_thought[:200]}...")
            
            # 4. Parse Decision
            return self._parse_decision(symbol, self.last_thought, tech_data)
            
        except Exception as e:
            logger.error(f"Brain reasoning failure for {symbol}: {e}")
            return None

    def _skill_technical_analysis(self, symbol: str, df: pd.DataFrame) -> Dict:
        """Technical Analysis Skill (SMC + Indicators)"""
        signal = self.signal_generator.generate_signal(symbol, df)
        # We return the raw data and the signal recommendation
        return {
            "current_price": df['close'].iloc[-1],
            "market_structure": str(self.signal_generator.smc.determine_market_structure(df)),
            "signal_recommendation": signal.direction if signal else "NEUTRAL",
            "confidence": signal.confidence if signal else 0.0,
            "atr": signal.metadata.get('atr') if signal else 0.0,
            "ob_zones": [f"{z.direction.value} OB at {z.price_low}-{z.price_high}" for z in getattr(signal, 'smc_zones', []) if z.type == 'order_block']
        }

    async def _skill_news_analysis(self, symbol: str) -> Dict:
        """News & Sentiment Analysis Skill (RSS + Reddit)"""
        try:
            from ..data_collection.sentiment_pulse import sentiment_pulse
            pulse = await sentiment_pulse.get_pulse()
            return {
                "impact": "High" if abs(pulse.get("sentiment_score", 0)) > 0.5 else "Medium",
                "summary": pulse.get("summary", "No significant social sentiment."),
                "score": pulse.get("sentiment_score", 0.0),
                "hot_topics": pulse.get("hot_topics", [])[:3]
            }
        except Exception as e:
            logger.error(f"SentimentPulse skill failure: {e}")
            return {"impact": "Low", "summary": "Sentiment skill offline.", "score": 0.0}

    async def _skill_institutional_context(self, symbol: str) -> Dict:
        """Institutional Context Skill (DXY, Sentiment)"""
        # Use existing helper logic from agent.py if possible, or reimplement
        from .agent import AIAgent
        return await AIAgent._get_institutional_context()

    def _get_system_personality(self) -> str:
        return """You are the OpenClaw Autonomous Trading Brain. 
Your goal is to provide a logical, institutional-grade analysis for the provided market data.
Follow a strict Chain-of-Thought process:
1. MARKET STRUCTURE: Analyze CHoCH, BOS, and Trend.
2. CONFLUENCE: Link Technicals (SMC/Order Blocks) with Institutional Context (DXY).
3. RISK ASSESSMENT: Evaluate News and Sentiment head-winds.
4. FINAL DECISION: Output a clear BUY, SELL, or ABSTAIN command.

Your output must end with a JSON block:
```json
{
  "decision": "BUY|SELL|ABSTAIN",
  "reasoning": "...",
  "entry_price": 0.0,
  "stop_loss": 0.0,
  "take_profit": 0.0,
  "confidence": 0.0
}
```"""

    def _build_reasoning_prompt(self, symbol: str, tech: Dict, news: Dict, inst: Dict, stats: Dict) -> str:
        return f"""Analyze {symbol} for an immediate trading decision.

TECHNICAL DATA:
- Price: {tech['current_price']}
- Structure: {tech['market_structure']}
- SMC Signal: {tech['signal_recommendation']} (Conf: {tech['confidence']})
- Order Blocks: {tech['ob_zones']}

INSTITUTIONAL CONTEXT:
- DXY: {inst.get('dxy')}
- Market Sentiment: {inst.get('sentiment')}

NEWS:
- Today's Impact: {news['impact']}

ACCOUNT CONTEXT:
- Daily P&L: {stats.get('daily_pnl', 0.0)}
- Active Trades: {stats.get('active_trades', 0)}

Think step-by-step and provide your final decision."""

    def _parse_decision(self, symbol: str, thought: str, tech: Dict) -> Optional[TradingSignal]:
        """Extract JSON from thought and build TradingSignal"""
        import json
        import re
        
        try:
            match = re.search(r'```json\s*(.*?)\s*```', thought, re.DOTALL)
            if not match:
                return None
            
            data = json.loads(match.group(1))
            decision = data.get("decision", "ABSTAIN").lower()
            
            if decision == "abstain":
                return None
            
            # Use LLM levels or fallback to technical levels
            entry = data.get("entry_price") or tech["current_price"]
            sl = data.get("stop_loss")
            tp = data.get("take_profit")
            
            # If LLM didn't provide good levels, calculate based on ATR
            if not sl or not tp:
                atr = tech.get("atr", 0.001)
                if decision == "buy":
                    sl = entry - (atr * 2)
                    tp = entry + (atr * 4)
                else:
                    sl = entry + (atr * 2)
                    tp = entry - (atr * 4)

            return TradingSignal(
                symbol=symbol,
                direction=decision,
                entry_price=entry,
                stop_loss=sl,
                take_profit=tp,
                confidence=data.get("confidence", 0.5),
                strategy="OpenClaw_Autonomous",
                smc_zones=[], # Handled via reasoning
                risk_reward=abs(tp-entry)/abs(entry-sl) if abs(entry-sl) > 0 else 1.0,
                timeframe="M15",
                timestamp=datetime.utcnow(),
                metadata={"reasoning": data.get("reasoning", "")}
            )
            
        except Exception as e:
            logger.error(f"Failed to parse brain decision: {e}")
            return None
