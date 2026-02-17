#!/bin/bash
# Quick Deployment Script for Kimi Agent

echo "🚀 Kimi Agent - Quick Deployment"
echo "================================"

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p backend/app/{ai_engine,mt5,risk,utils}
mkdir -p config
mkdir -p logs

# Create __init__.py files
touch backend/__init__.py
touch backend/app/__init__.py
touch backend/app/ai_engine/__init__.py
touch backend/app/mt5/__init__.py
touch backend/app/risk/__init__.py
touch backend/app/utils/__init__.py

# Copy files (files should already be in place)
echo "✅ Directory structure created"

# Create requirements.txt if not exists
if [ ! -f requirements.txt ]; then
    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
MetaTrader5==5.0.45
pandas==2.1.3
numpy==1.26.2
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
apscheduler==3.10.4
aiohttp==3.9.1
pyyaml==6.0.1
EOF
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Configure MT5 credentials in config/mt5_config.yaml"
echo "2. Run: cd backend && uvicorn app.routes:app --reload"
echo "3. Access API at http://localhost:8000"
echo "4. View docs at http://localhost:8000/docs"
