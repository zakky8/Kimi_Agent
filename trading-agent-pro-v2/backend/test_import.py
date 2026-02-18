import sys
import os

# Add backend directory to path
sys.path.append(os.getcwd())


try:
    print("Attempting to import app.api.dashboard_data...")
    from app.api import dashboard_data
    print("dashboard_data imported successfully!")

    print("Attempting to import app.api.routes...")
    from app.api import routes
    print("routes imported successfully!")
except Exception as e:

    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
