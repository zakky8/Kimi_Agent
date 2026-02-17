# Changelog

All notable changes to the Kimi Agent project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0] — 2026-02-18

### Added

#### Part 1 — Free Data Ingestion
- Binance WebSocket real-time feed
- yfinance historical/delayed data
- Headless browser scraper for CoinGlass (funding rates, open interest)
- Removed OANDA paid API dependency
- `quality` and `latency_ms` fields on candle schema

#### Part 2 — Technical Indicator Engine
- `services/analysis/indicators.py` with 40+ indicators
- Trend: SMA, EMA (9/20/50/200), VWAP, Ichimoku, SuperTrend
- Momentum: RSI, Stochastic, MACD, Williams %R, CCI, MFI, ADX, Awesome Oscillator
- Volatility: ATR, Bollinger Bands, Keltner Channels, Donchian Channels
- Volume: OBV, VWAP, volume SMA ratio
- S/R: Pivot Points, Fibonacci retracements (0/0.236/0.382/0.5/0.618/0.786/1)
- Candlestick patterns: Doji, Hammer, Engulfing, Morning/Evening Star
- All outputs are NaN-safe and returned as flat dictionaries for ML compatibility

#### Part 3 — Multi-Timeframe Confluence Analyser
- `services/analysis/confluence.py`
- 5 timeframes: D1 (35%), H4 (25%), H1 (20%), M15 (12%), M5 (8%)
- Score range: -1.0 (strong sell) to +1.0 (strong buy)
- Signal labels: STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL

#### Part 4 — ML Ensemble Prediction
- `services/ml/models.py`
- LSTMPredictor (PyTorch sequence model)
- XGBoostPredictor (gradient boosting)
- RandomForestPredictor (ensemble tree)
- PPOAgent stub (reinforcement learning environment placeholder)
- EnsemblePredictor with weighted voting (XGB 40%, RF 30%, LSTM 20%, PPO 10%)

#### Part 5 — Multi-Agent Orchestrator
- `services/agents/orchestrator.py`
- 5 specialist agents: DataAgent, TechnicalAgent, SentimentAgent, MLAgent, RiskAgent
- Concurrent execution via `asyncio.gather`
- Consensus: ≥3/5 agreement required
- RiskAgent has veto power over LONG/SHORT decisions

#### Part 6 — Self-Improving Learning Loop
- `services/learning/learning_engine.py`
- `OnlineLearner`: Incremental XGBoost retraining from trade outcomes
- `MistakeTracker`: Categorises losing trades (counter-trend, low confidence, etc.)
- `PerformanceTracker`: Win rate, Sharpe, max drawdown, running P&L
- Trading kill switch: auto-pauses on poor performance

#### Part 7 — Browser Automation Scraper
- `services/browser/automated_scraper.py`
- Playwright headless Chromium
- CoinGlass funding rates and open interest scraping
- Anti-detection headers and random delays

#### Part 8 — Chart Analysis + Backtesting
- `services/charts/analyser.py`: Swing point analysis, linear regression fitting
  - Patterns: Double Top/Bottom, Head & Shoulders, Triangles, Wedges, Channels
- `services/backtest/engine.py`: Vectorised backtester
  - SL/TP simulation, slippage, commissions
  - Equity curve generation
  - Performance metrics: win rate, Sharpe, max DD, profit factor

#### Part 9 — Dashboard UI Enhancement
- `AgentStatusPanel.tsx`: Multi-agent votes, confidence bars, consensus score gauge
- `PerformancePanel.tsx`: P&L display, Recharts equity curve, metric cards
- `MistakeLog.tsx`: Mistake patterns with severity bars, corrective actions
- `EvolutionLog.tsx`: AI self-improvement timeline with event icons
- Integrated all 4 panels into Dashboard.tsx
- Updated agent banner to "Kimi Agent v3.0"

#### Part 10 — Integration & Wiring
- Rewrote `main.py` with full service lifecycle management
- 60-second analysis loop (market data → indicators → ML → consensus → signals)
- API endpoints: `/health`, `/performance`, `/mistakes`
- Database migration: `002_agent_evolution.sql`
  - `agent_evolution`, `trading_mistakes`, `performance_snapshots`, `trading_signals` tables
- `__init__.py` for all 7 new service packages

#### Unit Tests
- `test_indicators.py` — 14 test cases
- `test_confluence.py` — 5 test cases
- `test_chart_analyser.py` — 6 test cases
- `test_backtest.py` — 7 test cases
- `test_learning.py` — 9 test cases
- `test_ml_models.py` — 8 test cases

### Changed
- `ingestion.py` — Removed OANDA, added yfinance + browser source
- `candle.py` — Added `quality` and `latency_ms` fields
- `config.py` — Removed OANDA settings, added free source configs
- `.env.example` — Updated to v3.0 with agent/backtest configs
- `requirements.txt` — Added joblib dependency
- `README.md` — Complete rewrite for v3.0
- `Dockerfile` — Updated for v3.0 services
- `docker-compose.yml` — Updated container names
- `docker-compose.dev.yml` — Added migration volume

### Removed
- OANDA API integration and configuration

---

## [2.0.0] — 2026-01-15

### Added
- Initial release of AI Trading Agent Pro v2
- FastAPI backend with multi-provider AI (OpenRouter, Gemini, Groq, Anthropic)
- React + Vite + Tailwind frontend
- Liquidity zone detection (Smart Money Concepts)
- Order block identification
- Fair value gap analysis
- Price action pattern recognition
- Playwright browser automation for Forex Factory
- Telegram multi-channel data collection
- Reddit integration
- RSS feed aggregation
- 24/7 monitoring agent
- TradingView chart embed
- AI chat interface with image analysis
- Docker + nginx deployment
