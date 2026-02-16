# AI Trading Agent Pro - Free Data Sources Edition

An institutional-grade AI trading agent with multi-provider AI support, real-time data from free sources, browser automation, and comprehensive market analysis.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![React](https://img.shields.io/badge/react-18+-61DAFB)

## Features

### AI Providers (Multi-Provider Support)
- **OpenRouter** - Access to Claude, GPT-4, Gemini, and more
- **Google Gemini** - Free tier with vision capabilities
- **Groq** - Ultra-fast inference with free tier
- **Baseten** - Model deployment platform

### Financial Data Sources (All Free)
- **Binance** - Real-time crypto spot & futures (WebSocket + REST)
- **Alpha Vantage** - Forex & stock data (25 calls/day)
- **CryptoCompare** - Crypto market data (100k calls/month)
- **Finnhub** - Financial data (60 calls/min)
- **Yahoo Finance** - Unlimited stock/crypto data

### Social Media & Messaging
- **Reddit API** - Community sentiment (60 req/min)
- **Telegram API** - Channel sentiment & bot integration
- **RSS Feeds** - News aggregation from multiple sources

### Desktop Integration
- **MetaTrader 5** - Connect to local MT5 terminal
- **Browser Automation** - Research & API documentation access

### AI Chat System
- **Persistent Chat** - Multi-session conversations with AI
- **Image Analysis** - Upload charts for AI analysis
- **Vision Models** - Support for image-capable AI models

### Technical Analysis
- 20+ Technical Indicators (RSI, MACD, Bollinger, ADX, etc.)
- Pattern Recognition (Head & Shoulders, Triangles, Flags)
- Market Regime Detection
- Support/Resistance Level Detection

### Signal Generation
- Confluence-based filtering (3+ confirming factors)
- Risk-adjusted position sizing
- ATR-based stops and targets
- Risk:Reward optimization

## Project Structure

```
trading-agent/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── ai_providers/    # Multi-provider AI integration
│   │   │   ├── ai_client.py       # Unified AI client
│   │   │   └── chat_engine.py     # Persistent chat system
│   │   ├── browser_automation/  # Browser automation
│   │   │   ├── browser_agent.py   # Playwright/Selenium
│   │   │   └── research_engine.py # Research automation
│   │   ├── data_collection/ # Data source connectors
│   │   │   ├── binance_client.py  # Binance API
│   │   │   ├── mt5_client.py      # MT5 integration
│   │   │   ├── telegram_collector.py
│   │   │   ├── reddit_collector.py
│   │   │   ├── rss_collector.py
│   │   │   └── market_data.py
│   │   ├── analysis/        # Technical analysis
│   │   ├── signals/         # Signal generation
│   │   ├── api/routes.py    # REST API endpoints
│   │   ├── websocket/       # WebSocket server
│   │   └── config.py        # Configuration
│   ├── main.py              # Entry point
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment template
├── frontend/                # React TypeScript frontend
│   ├── src/
│   │   ├── pages/           # Page components
│   │   │   ├── Chat.tsx     # AI chat interface
│   │   │   ├── Settings.tsx # API configuration
│   │   │   └── ...
│   │   ├── components/      # Reusable components
│   │   └── hooks/           # Custom React hooks
│   ├── package.json         # Node dependencies
│   └── .env.example         # Frontend env template
├── scripts/                 # Installation scripts
├── Dockerfile               # Container deployment
├── docker-compose.yml       # Multi-service deployment
└── README.md               # This file
```

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Git
- Chrome/Chromium (for browser automation)

### Installation

#### Option 1: Automated Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/trading-agent.git
cd trading-agent

# Run the installation script
chmod +x scripts/install.sh
./scripts/install.sh
```

#### Option 2: Manual Installation

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your API keys
```

**Frontend Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env
```

### Running the Application

**Start the Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```
Backend will start at: http://localhost:8000

**Start the Frontend:**
```bash
cd frontend
npm run dev
```
Frontend will start at: http://localhost:3000

## API Keys Setup (Free Tiers)

### AI Providers (At least one required)

1. **OpenRouter** (Recommended - Multi-model access)
   - Sign up: https://openrouter.ai/keys
   - Free tier available
   - Add to `.env`: `OPENROUTER_API_KEY`

2. **Google Gemini**
   - Sign up: https://ai.google.dev/
   - Free tier with generous limits
   - Add to `.env`: `GEMINI_API_KEY`

3. **Groq**
   - Sign up: https://console.groq.com/keys
   - Free tier available
   - Add to `.env`: `GROQ_API_KEY`

4. **Baseten**
   - Sign up: https://www.baseten.co/
   - Free tier available
   - Add to `.env`: `BASETEN_API_KEY`

### Financial Data APIs

1. **Binance** (Recommended for crypto)
   - Get key: https://www.binance.com/en/support/faq/how-to-create-api-keys-360002502072
   - Free WebSocket + REST API
   - Add to `.env`: `BINANCE_API_KEY`, `BINANCE_API_SECRET`

2. **Alpha Vantage** (Forex & stocks)
   - Get key: https://www.alphavantage.co/support/#api-key
   - Free tier: 25 calls/day
   - Add to `.env`: `ALPHA_VANTAGE_API_KEY`

3. **CryptoCompare**
   - Get key: https://www.cryptocompare.com/cryptopian/api-keys
   - Free tier: 100k calls/month
   - Add to `.env`: `CRYPTOCOMPARE_API_KEY`

4. **Finnhub**
   - Get key: https://finnhub.io/register
   - Free tier: 60 calls/minute
   - Add to `.env`: `FINNHUB_API_KEY`

### Social Media APIs

1. **Reddit**
   - Create app: https://www.reddit.com/prefs/apps
   - Free tier: 60 requests/minute
   - Add to `.env`: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`

2. **Telegram**
   - Get API ID: https://my.telegram.org/apps
   - Free tier: Unlimited
   - Add to `.env`: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`

### MetaTrader 5 (Optional)
- Enable in settings: `MT5_ENABLED=true`
- Configure account credentials in `.env`
- Requires MT5 desktop installed

## Usage

### Dashboard
- View live prices and charts
- Monitor active signals
- Track market sentiment
- Read latest news

### AI Chat
- Start conversations with the AI assistant
- Upload charts for analysis
- Get trading insights and recommendations
- Persistent chat history

### Settings
- Configure all API keys through the UI
- Test connections to providers
- Adjust risk management parameters
- Customize signal generation settings

### Signals
- Generate signals for any symbol
- Filter by direction (Long/Short)
- View signal confidence and R:R ratio
- Export signals

### Analysis
- Technical indicators for any symbol
- Pattern recognition
- Market regime detection
- Support/Resistance levels

## API Endpoints

### AI Chat
- `POST /api/v1/chat/session/create` - Create new chat session
- `GET /api/v1/chat/sessions` - List all sessions
- `GET /api/v1/chat/session/{id}/messages` - Get messages
- `POST /api/v1/chat/message` - Send message
- `POST /api/v1/chat/image` - Send image for analysis

### Settings
- `GET /api/v1/settings/schema` - Get settings schema
- `GET /api/v1/settings/current` - Get current settings
- `POST /api/v1/settings/update` - Update settings
- `POST /api/v1/settings/test-connection/{provider}` - Test provider

### Browser Research
- `POST /api/v1/research` - Start research task
- `GET /api/v1/research/{task_id}/status` - Get task status
- `POST /api/v1/research/symbol/{symbol}` - Research symbol

### Market Data
- `GET /api/v1/market/price/{symbol}` - Current price
- `GET /api/v1/market/prices?symbols=BTCUSDT,ETHUSDT` - Multiple prices
- `GET /api/v1/market/historical/{symbol}?timeframe=1h` - OHLCV data
- `GET /api/v1/market/binance/top-volume` - Top volume pairs

### MT5 Integration
- `GET /api/v1/mt5/status` - MT5 connection status
- `GET /api/v1/mt5/account` - Account info
- `GET /api/v1/mt5/positions` - Open positions

### Sentiment
- `GET /api/v1/sentiment/{symbol}` - Symbol sentiment
- `GET /api/v1/social/reddit/{symbol}` - Reddit data
- `GET /api/v1/social/telegram/{symbol}` - Telegram data

### News & RSS
- `GET /api/v1/news/market` - Latest market news
- `GET /api/v1/news/rss/summary` - RSS feeds summary
- `GET /api/v1/news/search?query=BTC` - Search news

## WebSocket

Connect to `ws://localhost:8001` for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8001');

ws.onopen = () => {
  ws.send(JSON.stringify({ action: 'subscribe', channel: 'all' }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

Channels: `prices`, `signals`, `sentiment`, `all`

## Configuration

### Default AI Provider
Set in `.env`:
```env
DEFAULT_AI_PROVIDER=openrouter
DEFAULT_AI_MODEL=anthropic/claude-3.5-sonnet
```

### Risk Management
```env
MAX_DRAWDOWN_PERCENT=10
DAILY_LOSS_LIMIT_PERCENT=2
PER_TRADE_RISK_PERCENT=1
```

### Signal Settings
```env
MIN_CONFIDENCE_THRESHOLD=0.75
CONFLUENCE_FACTORS_REQUIRED=3
```

## Testing

Run the test script to verify your installation:

```bash
# On macOS/Linux
chmod +x scripts/test.sh
./scripts/test.sh

# On Windows
scripts\test.bat
```

This will check:
- Python and Node.js installations
- Backend and frontend dependencies
- Configuration files
- Directory structure
- API endpoints (if server is running)

## Deployment

### Docker
```bash
docker-compose up -d
```

### Cloud Deployment (Free Options)
- **Backend**: Railway, Render, Fly.io
- **Frontend**: Vercel, Netlify

## Troubleshooting

### Browser Automation Issues
```bash
# Install Playwright browsers
playwright install chromium

# Or use Selenium (fallback)
# ChromeDriver should be in PATH
```

### MT5 Connection Issues
- Ensure MT5 desktop is installed
- Check terminal path in settings
- Verify account credentials

### API Rate Limits
- Binance: 1200 requests/minute
- Alpha Vantage: 25 requests/day
- Use multiple providers for redundancy

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Submit a pull request

## License

MIT License - see LICENSE file

## Disclaimer

This software is for educational and research purposes only. Not financial advice. Trading carries significant risk of loss.

## Support

- GitHub Issues: https://github.com/yourusername/trading-agent/issues
- Documentation: https://docs.trading-agent.com

---

**Built with Python, FastAPI, React, and free data sources.**
