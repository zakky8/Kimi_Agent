"""
Kimi Agent — Multi-Agent Orchestrator (Part 5)

Coordinates specialist agents that each analyse markets from a different
perspective.  A signal is only generated when the consensus threshold is met.

Agents:
  • DataAgent       — monitors data freshness and quality
  • TechnicalAgent  — runs IndicatorEngine + ConfluenceEngine
  • SentimentAgent  — processes Fear & Greed + supplementary data
  • MLAgent         — runs EnsemblePredictor (LSTM, XGBoost, RF, PPO)
  • RiskAgent       — validates position sizing and drawdown limits

Consensus: ≥ 3/5 agents must agree on direction before a signal is emitted.
"""
from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from app.services.analysis.confluence import ConfluenceEngine, ConfluenceResult, SignalDirection
from app.services.ml.models import EnsemblePredictor, PredictionDirection

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────
# Data Structures
# ────────────────────────────────────────────────────────

class AgentVote(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"
    ABSTAIN = "ABSTAIN"


@dataclass
class AgentOpinion:
    """A single agent's assessment."""
    agent_name: str
    vote: AgentVote
    confidence: float          # 0.0 to 1.0
    reasoning: str = ""
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsensusResult:
    """Aggregated decision from all agents."""
    symbol: str
    direction: AgentVote
    consensus_score: float      # 0.0 to 1.0
    agreement_count: int
    total_agents: int
    opinions: Dict[str, AgentOpinion] = field(default_factory=dict)
    is_actionable: bool = False
    reasons: List[str] = field(default_factory=list)
    timestamp: float = 0.0


# ────────────────────────────────────────────────────────
# Base Agent Interface
# ────────────────────────────────────────────────────────

class BaseAgent(ABC):
    """Base class for all specialist agents."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def analyse(
        self,
        symbol: str,
        candles: Dict[str, pd.DataFrame],
        context: Dict[str, Any],
    ) -> AgentOpinion:
        """Produce a vote based on analysis."""
        ...


# ────────────────────────────────────────────────────────
# Specialist Agents
# ────────────────────────────────────────────────────────

class DataAgent(BaseAgent):
    """
    Monitors data freshness, quality tiers, and staleness.
    ABSTAINS if data quality is too poor to trade on.
    """

    def __init__(self) -> None:
        super().__init__("DataAgent")

    async def analyse(
        self,
        symbol: str,
        candles: Dict[str, pd.DataFrame],
        context: Dict[str, Any],
    ) -> AgentOpinion:
        start = time.time()
        total_candles = sum(len(df) for df in candles.values())
        tf_count = len(candles)

        # Check for minimum data
        if total_candles < 100:
            return AgentOpinion(
                agent_name=self.name,
                vote=AgentVote.ABSTAIN,
                confidence=0.0,
                reasoning=f"Insufficient data: {total_candles} candles across {tf_count} timeframes",
                latency_ms=(time.time() - start) * 1000,
            )

        # Check freshness from health metrics
        health = context.get("health_metrics", {})
        stale_count = sum(1 for age in health.values() if age > 120)

        if stale_count > 0:
            return AgentOpinion(
                agent_name=self.name,
                vote=AgentVote.ABSTAIN,
                confidence=0.2,
                reasoning=f"{stale_count} symbol(s) with stale data (>120s old)",
                latency_ms=(time.time() - start) * 1000,
            )

        # Data is fresh — vote NEUTRAL (data agent doesn't pick direction)
        return AgentOpinion(
            agent_name=self.name,
            vote=AgentVote.NEUTRAL,
            confidence=0.9,
            reasoning=f"Data OK: {total_candles} candles, {tf_count} TFs, all fresh",
            latency_ms=(time.time() - start) * 1000,
        )


class TechnicalAgent(BaseAgent):
    """
    Runs ConfluenceEngine across all timeframes and votes based on
    the weighted confluence score.
    """

    def __init__(self) -> None:
        super().__init__("TechnicalAgent")
        self._confluence = ConfluenceEngine()

    async def analyse(
        self,
        symbol: str,
        candles: Dict[str, pd.DataFrame],
        context: Dict[str, Any],
    ) -> AgentOpinion:
        start = time.time()

        result: ConfluenceResult = await asyncio.get_event_loop().run_in_executor(
            None, self._confluence.analyse, symbol, candles
        )

        vote_map = {
            SignalDirection.LONG: AgentVote.LONG,
            SignalDirection.SHORT: AgentVote.SHORT,
            SignalDirection.NEUTRAL: AgentVote.NEUTRAL,
        }

        return AgentOpinion(
            agent_name=self.name,
            vote=vote_map.get(result.direction, AgentVote.NEUTRAL),
            confidence=result.confidence,
            reasoning=f"Confluence={result.confluence_score:+.3f}, "
                      f"direction={result.direction.value}",
            latency_ms=(time.time() - start) * 1000,
            metadata={"confluence_score": result.confluence_score},
        )


class SentimentAgent(BaseAgent):
    """
    Analyses Fear & Greed Index and other sentiment data.
    """

    def __init__(self) -> None:
        super().__init__("SentimentAgent")

    async def analyse(
        self,
        symbol: str,
        candles: Dict[str, pd.DataFrame],
        context: Dict[str, Any],
    ) -> AgentOpinion:
        start = time.time()
        fear_greed = context.get("fear_greed", {})
        value = fear_greed.get("value", 50)

        # Extreme fear = contrarian buy, extreme greed = contrarian sell
        if value <= 25:
            vote = AgentVote.LONG
            confidence = (50 - value) / 50.0
            reasoning = f"Extreme Fear ({value}) — contrarian bullish"
        elif value >= 75:
            vote = AgentVote.SHORT
            confidence = (value - 50) / 50.0
            reasoning = f"Extreme Greed ({value}) — contrarian bearish"
        else:
            vote = AgentVote.NEUTRAL
            confidence = 0.3
            reasoning = f"Neutral sentiment ({value})"

        return AgentOpinion(
            agent_name=self.name,
            vote=vote,
            confidence=confidence,
            reasoning=reasoning,
            latency_ms=(time.time() - start) * 1000,
        )


class MLAgent(BaseAgent):
    """
    Runs the EnsemblePredictor (LSTM + XGBoost + RF + PPO) and votes
    based on the ensemble's weighted direction.
    """

    def __init__(self, ensemble: Optional[EnsemblePredictor] = None) -> None:
        super().__init__("MLAgent")
        self._ensemble = ensemble or EnsemblePredictor()

    async def analyse(
        self,
        symbol: str,
        candles: Dict[str, pd.DataFrame],
        context: Dict[str, Any],
    ) -> AgentOpinion:
        start = time.time()
        indicators = context.get("indicators", {})

        if not indicators:
            return AgentOpinion(
                agent_name=self.name,
                vote=AgentVote.ABSTAIN,
                confidence=0.0,
                reasoning="No indicator features available",
                latency_ms=(time.time() - start) * 1000,
            )

        pred = await asyncio.get_event_loop().run_in_executor(
            None, self._ensemble.predict, indicators
        )

        vote_map = {
            PredictionDirection.LONG: AgentVote.LONG,
            PredictionDirection.SHORT: AgentVote.SHORT,
            PredictionDirection.NEUTRAL: AgentVote.NEUTRAL,
        }

        return AgentOpinion(
            agent_name=self.name,
            vote=vote_map.get(pred.direction, AgentVote.NEUTRAL),
            confidence=pred.confidence,
            reasoning=f"Ensemble: {pred.direction.value} ({pred.confidence:.2f}), "
                      f"agreement={pred.agreement_ratio:.0%}",
            latency_ms=(time.time() - start) * 1000,
            metadata={"agreement": pred.agreement_ratio},
        )


class RiskAgent(BaseAgent):
    """
    Validates whether a trade is safe given current risk parameters.
    Does NOT pick direction — only approve/reject.
    """

    def __init__(
        self,
        max_drawdown_pct: float = 10.0,
        daily_loss_limit_pct: float = 2.0,
        max_positions: int = 5,
    ) -> None:
        super().__init__("RiskAgent")
        self._max_dd = max_drawdown_pct
        self._daily_limit = daily_loss_limit_pct
        self._max_pos = max_positions

    async def analyse(
        self,
        symbol: str,
        candles: Dict[str, pd.DataFrame],
        context: Dict[str, Any],
    ) -> AgentOpinion:
        start = time.time()

        current_dd = context.get("current_drawdown_pct", 0.0)
        daily_loss = context.get("daily_loss_pct", 0.0)
        open_positions = context.get("open_positions", 0)

        reasons = []
        risk_ok = True

        if current_dd >= self._max_dd:
            reasons.append(f"Drawdown {current_dd:.1f}% ≥ max {self._max_dd}%")
            risk_ok = False

        if daily_loss >= self._daily_limit:
            reasons.append(f"Daily loss {daily_loss:.1f}% ≥ limit {self._daily_limit}%")
            risk_ok = False

        if open_positions >= self._max_pos:
            reasons.append(f"Positions {open_positions} ≥ max {self._max_pos}")
            risk_ok = False

        if not risk_ok:
            return AgentOpinion(
                agent_name=self.name,
                vote=AgentVote.ABSTAIN,
                confidence=0.0,
                reasoning=" | ".join(reasons),
                latency_ms=(time.time() - start) * 1000,
            )

        return AgentOpinion(
            agent_name=self.name,
            vote=AgentVote.NEUTRAL,  # Risk agent doesn't pick direction
            confidence=1.0,
            reasoning=f"Risk OK — DD={current_dd:.1f}%, daily={daily_loss:.1f}%, "
                      f"pos={open_positions}/{self._max_pos}",
            latency_ms=(time.time() - start) * 1000,
        )


# ════════════════════════════════════════════════════════
# Multi-Agent Orchestrator
# ════════════════════════════════════════════════════════

class Orchestrator:
    """
    Coordinates all specialist agents and produces a consensus decision.

    Consensus rules:
      1. RiskAgent and DataAgent must not ABSTAIN (veto power)
      2. ≥ 3 of 5 total agents must agree on a direction
      3. Average confidence across agreeing agents must exceed threshold

    Usage::

        orch = Orchestrator()
        result = orch.decide(
            symbol="BTC/USDT",
            candles={"D1": df_d1, "H4": df_h4, ...},
            context={"fear_greed": {...}, "indicators": {...}},
        )
    """

    def __init__(
        self,
        agents: Optional[List[BaseAgent]] = None,
        consensus_threshold: int = 3,
        min_confidence: float = 0.50,
    ) -> None:
        self._agents = agents or [
            DataAgent(),
            TechnicalAgent(),
            SentimentAgent(),
            MLAgent(),
            RiskAgent(),
        ]
        self._consensus_threshold = consensus_threshold
        self._min_confidence = min_confidence
        self._on_consensus: List[Callable[[ConsensusResult], Any]] = []

    def on_consensus(self, callback: Callable[[ConsensusResult], Any]) -> None:
        """Register callback for consensus events."""
        self._on_consensus.append(callback)

    async def decide(
        self,
        symbol: str,
        candles: Dict[str, pd.DataFrame],
        context: Dict[str, Any],
    ) -> ConsensusResult:
        """
        Run all agents concurrently and produce a consensus.
        """
        start = time.time()

        # Run all agents in parallel
        tasks = [
            agent.analyse(symbol, candles, context) for agent in self._agents
        ]
        opinions_list: List[AgentOpinion] = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        opinions: Dict[str, AgentOpinion] = {}
        for agent, opinion in zip(self._agents, opinions_list):
            if isinstance(opinion, Exception):
                logger.warning(f"[Orchestrator] {agent.name} failed: {opinion}")
                opinions[agent.name] = AgentOpinion(
                    agent_name=agent.name,
                    vote=AgentVote.ABSTAIN,
                    confidence=0.0,
                    reasoning=f"Error: {opinion}",
                )
            else:
                opinions[opinion.agent_name] = opinion

        # Check for vetoes (DataAgent & RiskAgent)
        reasons = []
        for veto_name in ("DataAgent", "RiskAgent"):
            op = opinions.get(veto_name)
            if op and op.vote == AgentVote.ABSTAIN:
                reasons.append(f"VETO: {veto_name} — {op.reasoning}")
                return ConsensusResult(
                    symbol=symbol,
                    direction=AgentVote.NEUTRAL,
                    consensus_score=0.0,
                    agreement_count=0,
                    total_agents=len(self._agents),
                    opinions=opinions,
                    is_actionable=False,
                    reasons=reasons,
                    timestamp=time.time(),
                )

        # Count votes
        vote_counts: Dict[AgentVote, int] = {
            AgentVote.LONG: 0,
            AgentVote.SHORT: 0,
            AgentVote.NEUTRAL: 0,
        }
        confidence_sums: Dict[AgentVote, float] = {
            AgentVote.LONG: 0.0,
            AgentVote.SHORT: 0.0,
            AgentVote.NEUTRAL: 0.0,
        }

        for op in opinions.values():
            if op.vote in vote_counts:
                vote_counts[op.vote] += 1
                confidence_sums[op.vote] += op.confidence

        # Find majority
        majority_vote = max(vote_counts, key=vote_counts.get)  # type: ignore
        majority_count = vote_counts[majority_vote]
        avg_confidence = (
            confidence_sums[majority_vote] / majority_count
            if majority_count > 0 else 0.0
        )

        is_actionable = (
            majority_vote in (AgentVote.LONG, AgentVote.SHORT)
            and majority_count >= self._consensus_threshold
            and avg_confidence >= self._min_confidence
        )

        # Build reasoning
        for name, op in opinions.items():
            reasons.append(
                f"  {name}: {op.vote.value} ({op.confidence:.2f}) — {op.reasoning}"
            )

        if is_actionable:
            reasons.insert(0, f"CONSENSUS: {majority_vote.value} — "
                             f"{majority_count}/{len(self._agents)} agents agree, "
                             f"avg confidence={avg_confidence:.2f}")
        else:
            reasons.insert(0, f"NO CONSENSUS: {majority_vote.value} — "
                             f"{majority_count}/{len(self._agents)} agents "
                             f"(need {self._consensus_threshold})")

        result = ConsensusResult(
            symbol=symbol,
            direction=majority_vote,
            consensus_score=round(avg_confidence, 4),
            agreement_count=majority_count,
            total_agents=len(self._agents),
            opinions=opinions,
            is_actionable=is_actionable,
            reasons=reasons,
            timestamp=time.time(),
        )

        # Notify callbacks
        for cb in self._on_consensus:
            try:
                r = cb(result)
                if asyncio.iscoroutine(r):
                    await r
            except Exception as exc:
                logger.warning(f"[Orchestrator] Callback error: {exc}")

        return result
