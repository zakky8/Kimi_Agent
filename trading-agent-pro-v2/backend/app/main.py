"""
Kimi Agent — Main Application Entry Point (v3.0)

Lifecycle:
  Startup:
    1. Configure logging
    2. Start MarketDataService (Binance WS, yfinance, ccxt)
    3. Initialize IndicatorEngine, ConfluenceEngine
    4. Initialize ML EnsemblePredictor
    5. Initialize Orchestrator (5 agents)
    6. Initialize SignalGenerator + LearningEngine
    7. Start Browser Scraper (Playwright, optional)
    8. Start scheduling loop (analyse every N seconds)

  Shutdown:
    1. Stop market data service
    2. Stop browser scraper
    3. Save ML models
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import routes

# Services
from app.services.market_data.ingestion import MarketDataService
from app.services.analysis.indicators import IndicatorEngine
from app.services.analysis.confluence import ConfluenceEngine
from app.services.ml.models import EnsemblePredictor
from app.services.agents.orchestrator import Orchestrator
from app.services.signals.generator import SignalGenerator
from app.services.learning.learning_engine import (
    OnlineLearner,
    MistakeTracker,
    PerformanceTracker,
    TradeOutcome,
)
from app.services.charts.analyser import ChartAnalyser
from app.services.backtest.engine import BacktestEngine

# Optional browser scraper
try:
    from app.services.browser.automated_scraper import AutomatedScraper
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("kimi_agent")


# ── Global service instances ──

class ServiceRegistry:
    """Central registry for all Kimi Agent services."""
    market_data: MarketDataService = None  # type: ignore
    indicator_engine: IndicatorEngine = None  # type: ignore
    confluence_engine: ConfluenceEngine = None  # type: ignore
    ensemble: EnsemblePredictor = None  # type: ignore
    orchestrator: Orchestrator = None  # type: ignore
    signal_generator: SignalGenerator = None  # type: ignore
    online_learner: OnlineLearner = None  # type: ignore
    mistake_tracker: MistakeTracker = None  # type: ignore
    performance_tracker: PerformanceTracker = None  # type: ignore
    chart_analyser: ChartAnalyser = None  # type: ignore
    backtest_engine: BacktestEngine = None  # type: ignore
    browser_scraper: Any = None
    _analysis_task: asyncio.Task = None  # type: ignore


services = ServiceRegistry()


# ── Analysis Loop ──

async def _analysis_loop():
    """
    Periodic analysis loop — runs every 60s.
    Pulls rolling candles → computes indicators → runs orchestrator → emits signals.
    """
    while True:
        try:
            for symbol in ["BTC/USDT"]:  # Expand via config
                candles: Dict[str, Any] = {}
                for tf in ["D1", "H4", "H1", "M15", "M5"]:
                    df = services.market_data.get_rolling(symbol, tf)
                    if df is not None and len(df) > 0:
                        candles[tf] = df

                if not candles:
                    continue

                # Compute indicators on primary TF
                primary_tf = "H1" if "H1" in candles else list(candles.keys())[0]
                indicators = services.indicator_engine.compute(candles[primary_tf])

                # Build context
                context: Dict[str, Any] = {
                    "indicators": indicators,
                    "health_metrics": services.market_data.get_health(),
                    "fear_greed": {},
                    "current_drawdown_pct": 0.0,
                    "daily_loss_pct": 0.0,
                    "open_positions": 0,
                }

                # Browser scraped data
                if services.browser_scraper:
                    cached = services.browser_scraper.get_all_cached()
                    for k, v in cached.items():
                        context[k] = v.payload

                # Check performance kill-switch
                if services.performance_tracker.is_paused:
                    logger.warning(
                        f"[Main] Trading paused: {services.performance_tracker.pause_reason}"
                    )
                    continue

                # Run orchestrator
                consensus = await services.orchestrator.decide(symbol, candles, context)

                if consensus.is_actionable:
                    current_price = indicators.get("ema_9", 0.0)
                    signal = services.signal_generator.generate(
                        consensus, indicators, current_price
                    )
                    if signal:
                        logger.info(
                            f"🔔 SIGNAL: {signal.direction} {signal.symbol} "
                            f"@ {signal.entry_price} "
                            f"SL={signal.stop_loss} TP={signal.take_profit} "
                            f"Size={signal.position_size}"
                        )
                        # TODO: Forward to execution engine (MT5/Binance)
                else:
                    logger.debug(f"[Main] {symbol}: no actionable consensus")

        except Exception as exc:
            logger.error(f"[Main] Analysis loop error: {exc}", exc_info=True)

        await asyncio.sleep(60)


# ── Application Lifespan ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("=" * 60)
    logger.info("  Kimi Agent v3.0 — Starting Up")
    logger.info("=" * 60)

    # 1. Market Data Service
    services.market_data = MarketDataService()
    await services.market_data.start()
    logger.info("✅ MarketDataService started")

    # 2. Analysis engines
    services.indicator_engine = IndicatorEngine()
    services.confluence_engine = ConfluenceEngine()
    services.chart_analyser = ChartAnalyser()
    logger.info("✅ Analysis engines initialized")

    # 3. ML Ensemble
    services.ensemble = EnsemblePredictor()
    logger.info("✅ ML EnsemblePredictor initialized (4 models)")

    # 4. Multi-Agent Orchestrator
    services.orchestrator = Orchestrator()
    logger.info("✅ Orchestrator initialized (5 agents)")

    # 5. Signal Generator
    services.signal_generator = SignalGenerator(
        account_balance=10000.0,  # TODO: from config/DB
    )
    logger.info("✅ SignalGenerator initialized")

    # 6. Learning Loop
    services.online_learner = OnlineLearner()
    services.mistake_tracker = MistakeTracker()
    services.performance_tracker = PerformanceTracker()
    services.performance_tracker.set_balance(10000.0)
    logger.info("✅ Learning system initialized")

    # 7. Backtesting engine (on-demand, not continuous)
    services.backtest_engine = BacktestEngine()

    # 8. Browser scraper (optional)
    if HAS_PLAYWRIGHT:
        services.browser_scraper = AutomatedScraper()
        try:
            await services.browser_scraper.start()
            logger.info("✅ Browser scraper started")
        except Exception as exc:
            logger.warning(f"⚠️ Browser scraper failed: {exc}")
    else:
        logger.info("ℹ️ Playwright not installed — browser scraper disabled")

    # 9. Start analysis loop
    services._analysis_task = asyncio.create_task(_analysis_loop())
    logger.info("✅ Analysis loop started (60s interval)")

    logger.info("=" * 60)
    logger.info("  Kimi Agent v3.0 — READY")
    logger.info("=" * 60)

    yield  # ── App runs here ──

    # ── Shutdown ──
    logger.info("Shutting down Kimi Agent...")

    if services._analysis_task:
        services._analysis_task.cancel()
        try:
            await services._analysis_task
        except asyncio.CancelledError:
            pass

    if services.browser_scraper:
        await services.browser_scraper.stop()

    await services.market_data.stop()
    logger.info("Kimi Agent stopped.")


# ── FastAPI App ──

app = FastAPI(
    title="Kimi Agent — AI Trading System",
    description="Multi-Agent Autonomous Trading Platform with Self-Improving ML",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1")


# ── Root endpoints ──

@app.get("/")
async def root():
    return {
        "name": "Kimi Agent",
        "version": "3.0.0",
        "status": "operational",
        "docs": "/docs",
        "services": {
            "market_data": services.market_data is not None,
            "analysis": services.indicator_engine is not None,
            "ml_ensemble": services.ensemble is not None,
            "orchestrator": services.orchestrator is not None,
            "learning": services.performance_tracker is not None,
            "browser_scraper": services.browser_scraper is not None,
            "performance_paused": (
                services.performance_tracker.is_paused
                if services.performance_tracker else False
            ),
        },
    }


@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "market_data_health": (
            services.market_data.get_health()
            if services.market_data else {}
        ),
        "performance": (
            {
                "is_paused": services.performance_tracker.is_paused,
                "pause_reason": services.performance_tracker.pause_reason,
            }
            if services.performance_tracker else {}
        ),
    }


@app.get("/api/v1/mistakes")
async def get_mistakes():
    if services.mistake_tracker:
        return services.mistake_tracker.get_summary()
    return {"total_mistakes": 0}


@app.get("/api/v1/performance")
async def get_performance():
    if services.performance_tracker:
        snap = services.performance_tracker.get_snapshot()
        return {
            "win_rate": snap.win_rate,
            "total_trades": snap.total_trades,
            "total_pnl": snap.total_pnl,
            "max_drawdown_pct": snap.max_drawdown_pct,
            "sharpe_ratio": snap.sharpe_ratio,
            "avg_rr": snap.avg_rr,
            "is_paused": services.performance_tracker.is_paused,
        }
    return {}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
