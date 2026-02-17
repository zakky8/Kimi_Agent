# 🚀 AI Trading Agent Pro v2 - Quick Start

## 🏁 Prerequisites
- **Python 3.10+** (Backend)
- **Node.js 18+** (Frontend)
- **Active AI API Key** (OpenRouter or Gemini)

## 🛠️ Installation

1. **Enter the project directory**:
   ```bash
   cd trading-agent-pro-v2
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**:
   ```bash
   cd ../frontend
   npm install
   ```

## 🏃 Running the Application

### 1. Start Backend (Port 8001)
```bash
cd backend
python main.py
```

### 2. Start Frontend (Port 3000)
```bash
cd frontend
npm run dev
```

## ⚙️ Initial Configuration
1. Open http://localhost:3000 in your browser.
2. Navigate to the **Settings** page.
3. Enter your **OpenRouter** or **Gemini** API key.
4. (Optional) Add **Binance** API keys for real-time crypto execution.
5. Save settings and start chatting with your AI agent!

## 🧪 Verification
To ensure everything is working, run the automated tests:
```bash
cd backend
python -m pytest tests/
```

---
*For more details, see [FILE_STRUCTURE.md](./FILE_STRUCTURE.md) or the project-level [README.md](./trading-agent-pro-v2/README.md).*
