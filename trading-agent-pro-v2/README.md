# 🧠 Kimi Agent v3.0 — AI Trading Intelligence Platform

A fully autonomous, self-improving AI trading agent featuring multi-agent consensus, 40+ technical indicators, ML ensemble predictions, chart pattern recognition, vectorised backtesting, and a real-time React dashboard.

![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![React](https://img.shields.io/badge/react-18+-cyan.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

---

## ✨ What's New in v3.0

| Feature | Description |
|---------|-------------|
| 🔓 **Free Data Sources** | Binance WebSocket, yfinance, headless browser scraping — no paid APIs needed |
| 📊 **40+ Indicators** | Trend, momentum, volatility, volume, S/R, and candlestick pattern detection |
| 🧮 **Multi-TF Confluence** | Weighted scoring across D1 (35%), H4 (25%), H1 (20%), M15 (12%), M5 (8%) |
| 🤖 **ML Ensemble** | LSTM, XGBoost, Random Forest, PPO (RL stub) with weighted voting |
| 🧠 **5-Agent Orchestrator** | Data, Technical, Sentiment, ML, Risk agents with veto power + ≥3/5 consensus |
| 📡 **Signal Generator** | ATR-based SL, dynamic R:R targets, 1% risk position sizing |
| 🔄 **Self-Improving Loop** | Online learning, mistake tracking, performance kill switch |
| 🌐 **Browser Automation** | Playwright-powered CoinGlass scraping (funding rates, OI) |
| 📈 **Chart Patterns** | Double top/bottom, H&S, triangles, wedges, channels |
| 🧪 **Vectorised Backtester** | Simulated trades with SL/TP, slippage, commissions, equity curves |
| 🖥️ **Dashboard Upgrade** | Agent consensus panel, performance tracker, mistake log, evolution timeline |
| ✅ **Unit Tests** | 40+ test cases across 6 test files |

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          Kimi Agent v3.0                                  │
├───────────────┬───────────────┬──────────────┬────────────────────────────┤
│   DATA LAYER  │ ANALYSIS LAYER│   ML LAYER   │     DECISION LAYER        │
├───────────────┼───────────────┼──────────────┼────────────────────────────┤
│ Binance WS    │ 40+ Indicators│ LSTM         │ DataAgent                 │
│ yfinance      │ Confluence    │ XGBoost      │ TechnicalAgent            │
│ Browser Scrape│ Chart Patterns│ RandomForest │ SentimentAgent            │
│               │ S/R Levels    │ PPO (RL)     │ MLAgent                   │
│               │               │ Ensemble     │ RiskAgent (veto power)    │
├───────────────┴───────────────┴──────────────┼────────────────────────────┤
│              SIGNAL GENERATOR                │    LEARNING ENGINE        │
│  ATR SL · Dynamic TP · 1% Risk Sizing       │ OnlineLearner · Mistakes  │
│                                              │ PerformanceTracker        │
│                                              │ Kill Switch               │
├──────────────────────────────────────────────┴────────────────────────────┤
│                     BACKTEST ENGINE (vectorised)                          │
│            Simulated trades · Equity curve · Sharpe · Max DD             │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

See [FILE_STRUCTURE.md](FILE_STRUCTURE.md) for a detailed breakdown of the v3.0 modular architecture.

---

## 🚀 Quick Start

See [QUICK_START.md](QUICK_START.md) for detailed setup instructions, including **critical security steps**.

### ⚡ Fast Track
1. Copy config: `cp .env.example .env`
2. **SECURITY**: Set `POSTGRES_PASSWORD` in `.env`
3. Run: `docker compose -f docker-compose.dev.yml up --build`

---

## ⚙️ Configuration

### Free Data Sources (no API keys required)

| Source | Data | Notes |
|--------|------|-------|
| Binance WebSocket | BTC/ETH real-time OHLCV | Free, no key needed |
| yfinance | Forex, stocks, indices | ~15m delayed, free |
| Browser Scraper | CoinGlass funding/OI | Playwright headless |

### AI Providers (Free Tiers Available)

| Provider | Free Tier | Website |
|----------|-----------|---------|
| OpenRouter | $5 credits | https://openrouter.ai |
| Gemini | 60 req/min | https://makersuite.google.com |
| Groq | 1M tokens/day | https://console.groq.com |
| Anthropic | $5 credits | https://console.anthropic.com |
| OpenAI | Pay-as-you-go | https://platform.openai.com |

### Trading APIs

| Service | Free Tier | Website |
|---------|-----------|---------|
| Binance | Full access | https://binance.com |
| CCXT | Multi-exchange | https://ccxt.readthedocs.io |

---

## 🔌 API Endpoints

### v3.0 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | System health + uptime |
| `GET` | `/api/v1/performance` | Win rate, P&L, Sharpe, drawdown |
| `GET` | `/api/v1/mistakes` | Mistake patterns + corrective actions |
| `GET` | `/api/v1/consensus/latest` | Multi-agent consensus result |
| `GET` | `/api/v1/evolution/recent` | AI self-improvement events |

### Legacy Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/agent/start` | Start 24/7 monitoring |
| `POST` | `/api/agent/stop` | Stop monitoring |
| `GET` | `/api/agent/status` | Agent status |
| `POST` | `/api/chat/message` | Send chat message |
| `GET` | `/api/analysis/liquidity/{pair}` | Liquidity zones |
| `GET` | `/api/signals` | All trading signals |
| `GET` | `/api/calendar/events` | Economic events |

---

## 🧪 Testing

```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/ -v
```

### Test Coverage

| Test File | Module | Cases |
|-----------|--------|-------|
| `test_indicators.py` | IndicatorEngine | 14 |
| `test_confluence.py` | ConfluenceEngine | 5 |
| `test_chart_analyser.py` | ChartAnalyser | 6 |
| `test_backtest.py` | BacktestEngine | 7 |
| `test_learning.py` | Learning Engine | 9 |
| `test_ml_models.py` | ML Models | 8 |
| **Total** | | **49** |

---

## 🖥️ Dashboard Features

### Market Overview
- Real-time BTC/ETH/GOLD/EUR prices via WebSocket
- TradingView chart integration
- System health monitoring (uptime, CPU, memory)

### AI Intelligence Panels (v3.0)
- **Agent Consensus** — 5 agents' votes with confidence bars and score gauge
- **Performance Tracker** — P&L, equity curve, win rate, Sharpe, max DD
- **Mistake Log** — Detected patterns (counter-trend, low confidence, etc.)
- **Evolution Timeline** — AI self-improvement events (retraining, config changes)

### Other Pages
- **AI Chat** — Interactive chat with image analysis
- **Trading Signals** — Entry, SL, TP with confidence scores
- **Technical Analysis** — Liquidity zones, order blocks, FVGs
- **Forex Calendar** — Economic events with IST conversion
- **24/7 Monitoring** — Start/stop/pause automation
- **Settings** — API keys, risk parameters, AI providers

---

## 📈 Roadmap

- [x] Multi-agent consensus system
- [x] ML ensemble predictions
- [x] Self-improving learning loop
- [x] Vectorised backtesting
- [x] Chart pattern recognition
- [x] Dashboard intelligence panels
- [x] 40+ technical indicators
- [x] Multi-timeframe confluence
- [ ] Live trade execution engine
- [ ] Mobile-responsive PWA
- [ ] Cloud deployment templates (GCP/AWS)
- [ ] Advanced portfolio optimisation
- [ ] WebSocket real-time dashboard updates

---

## 🔒 Security

- Never commit your `.env` file
- Use environment variables for all secrets
- Enable 2FA on all exchange accounts
- Use testnet for development
- Regularly rotate API keys

## 🐛 Troubleshooting

### Browser Automation Issues
```bash
playwright install chromium
playwright install-deps chromium
```

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8000 | xargs kill -9
```

### Module Not Found Errors
```bash
cd backend
pip install -r requirements.txt
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading cryptocurrencies and forex carries significant risk. Never trade with money you cannot afford to lose. Past performance is not indicative of future results. Always do your own research.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Web framework
- [React](https://react.dev/) — Frontend library
- [Recharts](https://recharts.org/) — Chart library
- [Playwright](https://playwright.dev/) — Browser automation
- [scikit-learn](https://scikit-learn.org/) — ML library
- [XGBoost](https://xgboost.readthedocs.io/) — Gradient boosting
- [pandas-ta](https://github.com/twopirllc/pandas-ta) — Technical analysis
- [CCXT](https://ccxt.readthedocs.io/) — Crypto trading library
- [Zustand](https://zustand-demo.pmnd.rs/) — State management
- [Tailwind CSS](https://tailwindcss.com/) — Utility-first CSS

---

**Made with 🧠 by Kimi Agent Team** — Powered by multi-agent AI consensus

For support, please open an issue on [GitHub](https://github.com/zakky8/Kimi_Agent/issues).
