# AI Trading Agent Pro - Quick Start Guide

## 📦 Package Contents

Your GitHub-ready zip file contains a complete AI Trading Agent with the following features:

### ✅ Implemented Features

1. **Browser Automation** (`backend/app/browser_automation/`)
   - Playwright-based browser automation with Selenium fallback
   - Research engine for API documentation access
   - Web scraping capabilities

2. **Settings Dashboard** (`frontend/src/pages/Settings.tsx`)
   - Configure all API keys through the UI
   - Test connections to providers
   - Risk management parameters
   - Signal generation settings

3. **Financial Data APIs**
   - **Binance API** - Real-time crypto data (WebSocket + REST)
   - **Alpha Vantage** - Forex & stock data (25 calls/day free)
   - **CryptoCompare** - Crypto data (100k calls/month)
   - **Finnhub** - Financial data (60 calls/min)

4. **Social Media & Messaging**
   - **Reddit API** - Community sentiment (60 req/min)
   - **Telegram API** - Channel data collection
   - **RSS Feeds** - News aggregation

5. **MetaTrader 5 Integration** (`backend/app/data_collection/mt5_client.py`)
   - Connect to local MT5 desktop
   - Access account info and positions
   - Place orders (if configured)

6. **AI Chat System** (`frontend/src/pages/Chat.tsx`)
   - Persistent chat sessions
   - Image upload for chart analysis
   - Multi-provider AI support

7. **Multi-Provider AI Support**
   - **OpenRouter** - Claude, GPT-4, Gemini, Llama
   - **Google Gemini** - Free tier with vision
   - **Groq** - Fast inference
   - **Baseten** - Model deployment

8. **Technical Analysis**
   - 20+ indicators (RSI, MACD, Bollinger, ADX)
   - Pattern recognition
   - Market regime detection
   - Support/Resistance levels

---

## 🚀 Quick Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- Git

### Step 1: Extract the Zip
```bash
unzip trading-agent-pro.zip
cd trading-agent
```

### Step 2: Run Installation Script

**On macOS/Linux:**
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

**On Windows:**
```bash
scripts\install.bat
```

This will:
- Create Python virtual environment
- Install all backend dependencies (including Playwright browsers)
- Install frontend dependencies
- Create `.env` files from templates

### Step 3: Configure API Keys

1. Edit `backend/.env` and add your API keys:
   - At least one AI provider (OpenRouter recommended)
   - Binance API for crypto data
   - Reddit/Telegram for social sentiment (optional)

2. Get free API keys:
   - **OpenRouter**: https://openrouter.ai/keys
   - **Binance**: https://www.binance.com/en/support/faq/how-to-create-api-keys-360002502072
   - **Alpha Vantage**: https://www.alphavantage.co/support/#api-key
   - **Reddit**: https://www.reddit.com/prefs/apps
   - **Telegram**: https://my.telegram.org/apps

### Step 4: Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 5: Access the Dashboard

Open http://localhost:3000 in your browser

---

## 🧪 Testing

Run the test script to verify everything is working:

**macOS/Linux:**
```bash
chmod +x scripts/test.sh
./scripts/test.sh
```

**Windows:**
```bash
scripts\test.bat
```

---

## 📁 Project Structure

```
trading-agent/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── ai_providers/       # Multi-provider AI (OpenRouter, Gemini, Groq, Baseten)
│   │   ├── browser_automation/ # Playwright/Selenium automation
│   │   ├── data_collection/    # Binance, MT5, Reddit, Telegram, RSS
│   │   ├── analysis/           # Technical indicators, patterns
│   │   ├── signals/            # Signal generation, sentiment
│   │   ├── api/routes.py       # REST API endpoints
│   │   └── config.py           # Settings schema
│   ├── main.py                 # Entry point
│   └── requirements.txt        # Python dependencies
├── frontend/                   # React TypeScript frontend
│   ├── src/pages/              # Dashboard, Chat, Settings, etc.
│   ├── src/components/         # Reusable UI components
│   └── src/hooks/              # API hooks (TanStack Query)
├── scripts/                    # Installation & test scripts
├── docker-compose.yml          # Docker deployment
└── README.md                   # Full documentation
```

---

## 🔌 API Endpoints

### Settings
- `GET /api/v1/settings/schema` - Get settings UI schema
- `GET /api/v1/settings/current` - Get current settings
- `POST /api/v1/settings/update` - Update settings
- `POST /api/v1/settings/test-connection/{provider}` - Test provider

### AI Chat
- `POST /api/v1/chat/session/create` - Create chat session
- `GET /api/v1/chat/sessions` - List sessions
- `POST /api/v1/chat/message` - Send message
- `POST /api/v1/chat/image` - Upload chart for analysis

### Market Data
- `GET /api/v1/market/price/{symbol}` - Current price
- `GET /api/v1/market/historical/{symbol}` - OHLCV data
- `GET /api/v1/market/binance/top-volume` - Top volume pairs

### MT5
- `GET /api/v1/mt5/status` - Connection status
- `GET /api/v1/mt5/account` - Account info
- `GET /api/v1/mt5/positions` - Open positions

### Research
- `POST /api/v1/research` - Start research task
- `POST /api/v1/research/symbol/{symbol}` - Research symbol

---

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## ⚠️ Important Notes

1. **Twitter Removed**: Twitter API is no longer free, so it has been removed from this version.

2. **MT5 Desktop Required**: For MT5 integration, you need MetaTrader 5 installed on your computer.

3. **Playwright Browsers**: The install script automatically installs Chromium for browser automation.

4. **Free Tier Limits**:
   - Binance: 1200 requests/minute
   - Alpha Vantage: 25 requests/day
   - Reddit: 60 requests/minute
   - Use multiple providers for redundancy

5. **Security**: Never commit your `.env` files with real API keys to GitHub.

---

## 🐛 Troubleshooting

### Browser Automation Issues
```bash
playwright install chromium
```

### MT5 Connection Issues
- Ensure MT5 is installed
- Check the terminal path in settings
- Verify account credentials

### Backend Won't Start
- Check if port 8000 is free
- Verify all API keys are correct
- Check logs in `backend/logs/`

### Frontend Won't Start
- Ensure Node.js 18+ is installed
- Delete `node_modules` and run `npm install` again

---

## 📚 Next Steps

1. Configure your API keys in the Settings page
2. Test connections to providers
3. Start a chat session with the AI
4. Upload a chart for analysis
5. Generate trading signals
6. Monitor market sentiment

---

**Built with Python, FastAPI, React, and free data sources.**

For full documentation, see `README.md` in the package.
