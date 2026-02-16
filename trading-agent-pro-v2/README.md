# 🤖 AI Trading Agent Pro v2

A comprehensive, fully automated AI-powered trading agent with advanced technical analysis, browser automation, multi-source data collection, and 24/7 market monitoring.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![React](https://img.shields.io/badge/react-18+-cyan.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

## ✨ Features

### 🔍 Advanced Technical Analysis
- **Liquidity Zones** - Detect buy-side and sell-side liquidity pools
- **Order Blocks** - Identify bullish and bearish order blocks (Smart Money Concepts)
- **Fair Value Gaps (FVG)** - Find price imbalances for high-probability entries
- **Price Action Patterns** - Recognize engulfing, pin bars, doji, and more
- **Market Structure** - Track market structure breaks and changes of character

### 🤖 AI-Powered Agent
- **Multi-Provider AI** - Support for OpenRouter, Gemini, Groq, and Anthropic
- **24/7 Monitoring** - Continuous market surveillance
- **Chat Interface** - Interactive AI assistant with image analysis
- **Signal Generation** - AI-driven trading signals with confidence scores
- **Full System Control** - Agent can access all system functions

### 🌐 Browser Automation
- **System Browser** - Uses your local Chrome/Edge/Firefox (no APIs needed)
- **Playwright + Selenium** - Dual automation engines for reliability
- **Forex Factory Calendar** - Scraped with IST timezone conversion
- **Web Research** - Automated research and documentation access

### 📱 Data Collection
- **Telegram Multi-Channel** - Real-time data from unlimited channels
- **Reddit Integration** - Subreddit monitoring and sentiment analysis
- **RSS Feeds** - News aggregation from multiple sources
- **Binance API** - Real-time crypto market data
- **Alpha Vantage** - Forex data with technical indicators

### 📊 Dashboard & Monitoring
- **Real-time Dashboard** - Live market prices and system status
- **Trading Signals** - View and manage AI-generated signals
- **Analysis Tools** - Interactive liquidity, OB, and FVG visualization
- **Forex Calendar** - Economic events with IST timezone
- **24/7 Monitoring Control** - Start/stop/pause automation

## 📁 File Structure

```
trading-agent-pro-v2/
├── 📂 backend/
│   ├── 📂 app/
│   │   ├── 📂 ai_engine/
│   │   │   ├── agent.py              # AI agent with 24/7 monitoring
│   │   │   ├── llm_client.py         # Multi-provider LLM client
│   │   │   └── signal_generator.py   # Trading signal generation
│   │   ├── 📂 analysis/
│   │   │   ├── liquidity_analysis.py # Liquidity zone detection
│   │   │   ├── price_action.py       # Price action patterns
│   │   │   └── technical_indicators.py # Technical indicators
│   │   ├── 📂 api/
│   │   │   └── routes.py             # FastAPI endpoints
│   │   ├── 📂 browser_automation/
│   │   │   ├── system_browser.py     # System browser automation
│   │   │   └── forex_factory.py      # Forex Factory scraper
│   │   ├── 📂 data_collection/
│   │   │   ├── telegram_collector.py # Multi-channel Telegram
│   │   │   ├── reddit_collector.py   # Reddit data collection
│   │   │   ├── news_collector.py     # RSS news feeds
│   │   │   └── market_data.py        # Market data providers
│   │   ├── config.py                 # Configuration settings
│   │   └── __init__.py
│   ├── main.py                       # FastAPI entry point
│   └── requirements.txt              # Python dependencies
├── 📂 frontend/
│   ├── 📂 src/
│   │   ├── 📂 components/
│   │   │   ├── Layout.tsx            # Main layout component
│   │   │   ├── Sidebar.tsx           # Navigation sidebar
│   │   │   └── Header.tsx            # Top header
│   │   ├── 📂 pages/
│   │   │   ├── Dashboard.tsx         # Main dashboard
│   │   │   ├── Chat.tsx              # AI chat interface
│   │   │   ├── Signals.tsx           # Trading signals
│   │   │   ├── Analysis.tsx          # Technical analysis
│   │   │   ├── Calendar.tsx          # Forex calendar
│   │   │   ├── Monitoring.tsx        # 24/7 monitoring control
│   │   │   └── Settings.tsx          # Settings dashboard
│   │   ├── App.tsx                   # React app entry
│   │   ├── main.tsx                  # React DOM entry
│   │   └── index.css                 # Global styles
│   ├── index.html                    # HTML template
│   ├── package.json                  # Node dependencies
│   ├── vite.config.ts                # Vite configuration
│   └── tailwind.config.js            # Tailwind CSS config
├── 📂 scripts/
│   ├── install.sh                    # Linux/macOS installer
│   ├── install.bat                   # Windows installer
│   ├── start_backend.sh              # Start backend (Unix)
│   ├── start_backend.bat             # Start backend (Windows)
│   ├── start_frontend.sh             # Start frontend (Unix)
│   ├── start_frontend.bat            # Start frontend (Windows)
│   ├── start_all.sh                  # Start all services (Unix)
│   └── start_all.bat                 # Start all services (Windows)
├── 📂 data/                          # Data storage
├── 📂 logs/                          # Log files
├── 📂 screenshots/                   # Browser screenshots
├── .env.example                      # Environment template
├── .gitignore                        # Git ignore rules
├── Dockerfile                        # Docker build file
├── docker-compose.yml                # Docker Compose config
├── nginx.conf                        # Nginx configuration
└── README.md                         # This file
```

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher
- Chrome, Edge, or Firefox browser
- Git (optional)

### Windows Installation

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd trading-agent-pro-v2
   ```

2. **Run the installer**
   ```bash
   cd scripts
   install.bat
   ```

3. **Configure API keys**
   - Open `.env` file in the root directory
   - Add your API keys (see Configuration section)

4. **Start the application**
   ```bash
   start_all.bat
   ```

### Linux/macOS Installation

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd trading-agent-pro-v2
   ```

2. **Run the installer**
   ```bash
   cd scripts
   chmod +x install.sh
   ./install.sh
   ```

3. **Configure API keys**
   ```bash
   nano ../.env
   ```

4. **Start the application**
   ```bash
   ./start_all.sh
   ```

### Docker Installation

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## ⚙️ Configuration

### AI Providers (Free Tiers Available)

| Provider | Website | Free Tier |
|----------|---------|-----------|
| OpenRouter | https://openrouter.ai | $5 credits |
| Gemini | https://makersuite.google.com | 60 req/min |
| Groq | https://console.groq.com | 1M tokens/day |
| Anthropic | https://console.anthropic.com | $5 credits |

### Trading APIs

| Service | Website | Free Tier |
|---------|---------|-----------|
| Binance | https://binance.com | Full access |
| Alpha Vantage | https://alphavantage.co | 25 calls/day |

### Telegram API

1. Go to https://my.telegram.org/apps
2. Create a new application
3. Copy `api_id` and `api_hash`
4. Add to `.env` file

### MetaTrader 5

1. Enable in `.env`: `MT5_ENABLED=true`
2. Add your MT5 account credentials
3. Ensure MT5 desktop is installed

## 🖥️ Usage

### Dashboard
- View real-time market prices
- Monitor system status
- See recent trading signals
- Track win rate and P&L

### AI Chat
- Chat with the AI trading agent
- Upload charts for analysis
- Start/stop 24/7 monitoring
- Get market insights

### Trading Signals
- View all generated signals
- Filter by status (active/pending/completed)
- See entry, stop loss, and take profit levels
- Track confidence scores

### Technical Analysis
- **Liquidity Zones** - View buy/side liquidity pools
- **Order Blocks** - See bullish/bearish OBs
- **Fair Value Gaps** - Monitor FVGs and fill status
- **Price Action** - Recognized patterns

### Forex Calendar
- Economic events from Forex Factory
- IST timezone conversion
- High/medium/low impact filtering
- Actual/forecast/previous data

### 24/7 Monitoring
- Start/pause/stop automation
- View live logs
- Monitor service status
- Track uptime and tasks

### Settings
- Configure AI providers
- Add trading API keys
- Set up Telegram channels
- Manage risk parameters

## 🔌 API Endpoints

### Agent Control
- `POST /api/agent/start` - Start 24/7 monitoring
- `POST /api/agent/stop` - Stop monitoring
- `GET /api/agent/status` - Get agent status

### Chat
- `POST /api/chat/message` - Send chat message
- `POST /api/chat/analyze-image` - Analyze uploaded image
- `GET /api/chat/history` - Get chat history

### Analysis
- `GET /api/analysis/liquidity/{pair}` - Get liquidity zones
- `GET /api/analysis/orderblocks/{pair}` - Get order blocks
- `GET /api/analysis/fvg/{pair}` - Get fair value gaps
- `GET /api/analysis/price-action/{pair}` - Get price action patterns

### Calendar
- `GET /api/calendar/events` - Get economic events
- `GET /api/calendar/today` - Get today's events

### Signals
- `GET /api/signals` - Get all signals
- `GET /api/signals/active` - Get active signals
- `POST /api/signals/generate` - Generate new signal

## 🛠️ Development

### Backend Development
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
cd backend
pytest tests/ -v
```

## 🔒 Security

- Never commit your `.env` file
- Use environment variables for all secrets
- Enable 2FA on all exchange accounts
- Use testnet for development
- Regularly rotate API keys

## 🐛 Troubleshooting

### Browser Automation Issues
```bash
# Reinstall Playwright browsers
playwright install chromium
playwright install-deps chromium
```

### Telegram Connection Issues
```bash
# Delete session and re-authenticate
rm data/telegram_session.session
```

### Port Already in Use
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

## 📈 Roadmap

- [ ] Machine learning model training
- [ ] Backtesting engine
- [ ] Portfolio optimization
- [ ] Social sentiment deep learning
- [ ] Multi-timeframe analysis
- [ ] Automated trade execution
- [ ] Mobile app
- [ ] Cloud deployment templates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational purposes only. Trading cryptocurrencies and forex carries significant risk. Never trade with money you cannot afford to lose. Always do your own research before making any investment decisions.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [React](https://react.dev/) - Frontend library
- [Playwright](https://playwright.dev/) - Browser automation
- [Telethon](https://docs.telethon.dev/) - Telegram client
- [CCXT](https://ccxt.readthedocs.io/) - Crypto trading library

---

**Made with ❤️ by AI Trading Agent Pro Team**

For support, please open an issue on GitHub or contact us.
