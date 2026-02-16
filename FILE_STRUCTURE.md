# AI Trading Agent Pro - Complete File Structure

## Root Files

| File | Purpose |
|------|---------|
| `README.md` | Complete documentation |
| `QUICK_START.md` | Quick start guide |
| `Dockerfile` | Multi-stage Docker build |
| `docker-compose.yml` | Docker Compose configuration |
| `nginx.conf` | Nginx configuration for production |
| `LICENSE` | MIT License |
| `.gitignore` | Git ignore patterns |

## Scripts (`scripts/`)

| File | Purpose |
|------|---------|
| `install.sh` | macOS/Linux installation script |
| `install.bat` | Windows installation script |
| `start.sh` | Docker startup script |
| `test.sh` | macOS/Linux test script |
| `test.bat` | Windows test script |

## Backend (`backend/`)

### Core Files
| File | Purpose |
|------|---------|
| `main.py` | FastAPI application entry point |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variables template |

### Configuration (`app/`)
| File | Purpose |
|------|---------|
| `config.py` | Settings, trading pairs, data sources config |
| `__init__.py` | Module initialization |

### AI Providers (`app/ai_providers/`)
| File | Purpose |
|------|---------|
| `__init__.py` | Exports AIClient, ChatEngine |
| `ai_client.py` | Unified AI client (OpenRouter, Gemini, Groq, Baseten) |
| `chat_engine.py` | Persistent chat sessions with message history |

### Browser Automation (`app/browser_automation/`)
| File | Purpose |
|------|---------|
| `__init__.py` | Exports BrowserAgent, ResearchEngine |
| `browser_agent.py` | Playwright/Selenium browser automation |
| `research_engine.py` | Research tasks and API documentation access |

### Data Collection (`app/data_collection/`)
| File | Purpose |
|------|---------|
| `__init__.py` | Exports all data collectors |
| `binance_client.py` | Binance REST API and WebSocket client |
| `mt5_client.py` | MetaTrader 5 desktop integration |
| `reddit_collector.py` | Reddit API sentiment collection |
| `telegram_collector.py` | Telegram API data collection |
| `rss_collector.py` | RSS feed aggregation |
| `news_collector.py` | NewsAPI and web news collection |
| `web_scraper.py` | Web scraping utilities |
| `market_data.py` | Yahoo Finance and other market data |
| `twitter_collector.py` | (Deprecated - Twitter not free) |

### Analysis (`app/analysis/`)
| File | Purpose |
|------|---------|
| `__init__.py` | Exports analysis modules |
| `technical_indicators.py` | 20+ technical indicators |
| `pattern_recognition.py` | Chart pattern detection |
| `market_regime.py` | Market regime detection |

### Signals (`app/signals/`)
| File | Purpose |
|------|---------|
| `__init__.py` | Exports signal modules |
| `signal_generator.py` | Trading signal generation |
| `sentiment_analyzer.py` | Sentiment analysis engine |
| `confluence_engine.py` | Multi-factor signal filtering |

### API (`app/api/`)
| File | Purpose |
|------|---------|
| `__init__.py` | Module initialization |
| `routes.py` | All REST API endpoints (1000+ lines) |

### WebSocket (`app/websocket/`)
| File | Purpose |
|------|---------|
| `__init__.py` | Module initialization |
| `server.py` | WebSocket server for real-time updates |

## Frontend (`frontend/`)

### Configuration
| File | Purpose |
|------|---------|
| `package.json` | Node.js dependencies |
| `tsconfig.json` | TypeScript configuration |
| `vite.config.ts` | Vite build configuration |
| `tailwind.config.js` | Tailwind CSS configuration |
| `postcss.config.js` | PostCSS configuration |
| `.env.example` | Frontend environment template |
| `index.html` | HTML entry point |

### Source (`src/`)

#### Entry
| File | Purpose |
|------|---------|
| `main.tsx` | React application entry |
| `App.tsx` | Main app with routes |
| `index.css` | Global styles |

#### Pages (`src/pages/`)
| File | Purpose |
|------|---------|
| `Dashboard.tsx` | Main dashboard with prices, charts |
| `Signals.tsx` | Trading signals list |
| `Analysis.tsx` | Technical analysis page |
| `Sentiment.tsx` | Market sentiment page |
| `Chat.tsx` | AI chat interface with image upload |
| `Settings.tsx` | API configuration and settings |

#### Components (`src/components/`)
| File | Purpose |
|------|---------|
| `Layout.tsx` | Main layout wrapper |
| `Sidebar.tsx` | Navigation sidebar with AI Chat link |
| `Header.tsx` | Top header with stats |
| `SignalCard.tsx` | Signal display card |
| `PriceChart.tsx` | Price chart component |
| `SentimentGauge.tsx` | Sentiment visualization |

#### Hooks (`src/hooks/`)
| File | Purpose |
|------|---------|
| `useApi.ts` | All API hooks (settings, chat, market, MT5, etc.) |
| `useWebSocket.ts` | WebSocket connection hook |

## Total Files: 72

## Key Features Implemented

✅ **Browser Automation** - Playwright + Selenium fallback
✅ **Settings Dashboard** - Full UI for API configuration
✅ **Binance API** - Real-time crypto data
✅ **Alpha Vantage** - Forex data
✅ **Telegram API** - Channel data collection
✅ **Reddit API** - Community sentiment
✅ **MT5 Desktop** - MetaTrader 5 integration
✅ **RSS Feeds** - News aggregation
✅ **AI Chat** - Persistent sessions with image analysis
✅ **Multi-Provider AI** - OpenRouter, Gemini, Groq, Baseten
✅ **Twitter Removed** - Not free anymore

## Installation Commands

```bash
# Extract
unzip trading-agent-pro.zip
cd trading-agent

# Install (macOS/Linux)
chmod +x scripts/install.sh
./scripts/install.sh

# Install (Windows)
scripts\install.bat

# Test (macOS/Linux)
./scripts/test.sh

# Test (Windows)
scripts\test.bat

# Start Backend
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py

# Start Frontend (new terminal)
cd frontend
npm run dev
```

## Docker Deployment

```bash
docker-compose up -d
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
