# 📂 Project File Structure (v3.0)

## Backend (`/backend`)

The backend is built with **FastAPI** and follows a modular service-oriented architecture.

### core/
| Path | Description |
|---|---|
| `app/main.py` | **Entry Point** — FastAPI app & lifecycle manager |
| `app/config.py` | Configuration settings (loads from `.env`) |
| `app/api/` | REST API routes (`routes.py`) |

### services/ (v3.0 Modular Architecture)
| Path | Description |
|---|---|
| `market_data/` | **Data Ingestion** — `ingestion.py` (Binance, YFinance, Scraper) |
| `analysis/` | **Technical Analysis** — `indicators.py` (TA-Lib), `confluence.py` |
| `ml/` | **Machine Learning** — `models.py` (LSTM/XGB), `online_learner.py` |
| `signals/` | **Signal Logic** — `generator.py` (Entry, Exit, Sizing) |
| `agents/` | **Orchestrator** — `orchestrator.py` (5-agent consensus) |
| `learning/` | **Self-improvement** — `mistake_tracker.py`, `learning_engine.py` |
| `browser/` | **Automation** — `automated_scraper.py` (Playwright) |
| `backtest/` | **Simulation** — `engine.py` (Vectorised backtester) |
| `charts/` | **Pattern Recog** — `analyser.py` (Triangle/H&S detection) |

### legacy/ & support
| Path | Description |
|---|---|
| `app/ai_engine/` | **Legacy v2 Agent** — `agent.py` (Swarm v2 monitoring loop) |
| `app/shared/` | Data schemas (`candle.py`, `signal.py`) |
| `app/mt5_client.py` | MetaTrader 5 client wrapper |

---

## Frontend (`/frontend`)

Built with **React 18**, **Vite**, and **TailwindCSS**.

| Path | Description |
|---|---|
| `src/components/` | React components (Dashboard, Panels, Charts) |
| `src/hooks/` | Custom hooks (`useAgentStatus`, `useMarketData`) |
| `src/services/` | API client services |
| `src/data/` | Mock data and constants |

---

## Infrastructure

| File | Description |
|---|---|
| `docker-compose.dev.yml` | **Development** stack (Hot-reload, Postgres, Redis, MLflow) |
| `docker-compose.yml` | **Production** stack |
| `Dockerfile` | Multi-stage Python build |
| `.env.example` | Configuration template (**Security Note**: Set `POSTGRES_PASSWORD`!) |
