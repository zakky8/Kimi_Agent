# 🚀 Quick Start Guide — Kimi Agent v3.0

## Prerequisites
- **Docker** & **Docker Compose**
- **Python 3.11+**
- **Node.js 18+** (for frontend development)

---

## 1. Environment Setup

Copy the example configuration file:
```bash
cp .env.example .env
```

### ⚠️ CRITICAL SECURITY STEP for v3.0
You **MUST** set a secure password for the database in your `.env` file. The default password has been removed for security.

Open `.env` and set:
```ini
POSTGRES_PASSWORD=your_secure_password_here
```
*(If you fail to do this, the database container will trigger a security alert or fail to start.)*

---

## 2. Start the Stack (Development)

Run the full stack with hot-reloading:
```bash
docker compose -f docker-compose.dev.yml up --build
```

- **Dashboard**: [http://localhost:3000](http://localhost:3000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MLflow**: [http://localhost:5000](http://localhost:5000)

---

## 3. Configure AI & Trading Keys

1.  **AI Intelligence**: Open `.env` and set `OPENROUTER_API_KEY` or `GEMINI_API_KEY`. Without these, the dashboard will show **"Missing Keys"**.
2.  **MetaTrader 5 (Optional)**: If using MT5, set `MT5_ENABLED=True` and provide your credentials.
3.  **Validation**: Once configured, the dashboard status indicators will turn green.

---

## 4. Run Tests

To verify everything is working:

```bash
# Install test dependencies locally if needed
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run unit tests
pytest backend/tests/
```
