import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("Checking imports...")
try:
    from app.config import settings
    print(f"OK: Settings loaded (App: {settings.APP_NAME})")
    
    from app.mt5_client import MT5Client
    print("OK: MT5Client imported")
    
    from app.ai_engine.agent import get_agent
    print("OK: get_agent imported")
    
    from app.api.routes import router
    print("OK: router imported")
    
    from app.websocket.server import get_websocket_server
    print("OK: WebSocket server imported")
    
    print("\nAttempting to initialize components...")
    agent = get_agent()
    print("OK: Agent initialized")
    
    ws = get_websocket_server()
    print("OK: WebSocket server initialized")
    
    print("\nAll systems GO!")
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
