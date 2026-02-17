# 🤖 AI Trading Agent Pro v2 - File Structure

## Root Workspace (`Kimi_Agent/`)

| File | Purpose |
|------|---------|
| `README.md` | Root-level documentation |
| `QUICK_START.md` | Entry point for new users |
| `FILE_STRUCTURE.md` | Detailed project map (this file) |
| `trading-agent-pro-v2/` | **Active Core Project Directory** |

## Core Project (`trading-agent-pro-v2/`)

### Root Files
| File | Purpose |
|------|---------|
| `.env.example` | Environment template |
| `.gitignore` | Git exclusion rules |
| `Dockerfile` | Container configuration |
| `docker-compose.yml` | Multi-container orchestration |
| `nginx.conf` | Web server config |
| `LICENSE` | MIT License |

### Backend (`backend/`)
| Directory | Purpose |
|-----------|---------|
| `app/ai_engine/` | LLM clients & Signal generation logic |
| `app/analysis/` | SMC (Liquidity, OB, FVG) & Technical analysis |
| `app/api/` | FastAPI REST endpoints (Port 8001) |
| `app/browser_automation/` | Playwright & Selenium scrapers |
| `app/core/` | System configuration & Schedulers |
| `app/data_collection/` | Binance, Telegram, Reddit, RSS collectors |
| `app/services/` | Market data & live price services |
| `app/websocket/` | Real-time price streaming server |
| `tests/` | Automated unit & integration tests |
| `data/` | Persistent storage (settings, chat history) |

### Frontend (`frontend/`)
| Directory | Purpose |
|-----------|---------|
| `src/pages/` | Dashboard, Signals, Analysis, Chat, Settings |
| `src/components/` | Visual UI components (Charts, Cards, Layout) |
| `src/hooks/` | API interaction & WebSocket hooks |
| `vite.config.ts` | Frontend build & proxy config (Port 3000) |

## Access Information
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
