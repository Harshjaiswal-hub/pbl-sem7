import uvicorn
import os
import sys

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from backend.database import init_db
from backend.ml_engine import pricing_engine

def start_server():
    print("=" * 65)
    print("🚀 BOOKING ADVENTURES - DYNAMIC PRICING ENGINE (PBL SEM 7)")
    print("=" * 65)
    print("Initializing SQLite Database...")
    init_db()
    print("Verifying Scikit-Learn Gradient Boosting ML Model...")
    metrics = pricing_engine.get_metrics_and_insights()
    print(f"Champion Model: {metrics['champion_model']}")
    print(f"Gradient Boosting R² Score: {metrics['models_evaluated']['GradientBoosting']['r2_score']}")
    print("-" * 65)
    print("🌐 Full-Stack Application is LIVE at:")
    print("   👉 http://127.0.0.1:8000")
    print("   👉 http://localhost:8000")
    print("   👉 Mobile / Network URL: http://192.168.1.15:8000")
    print("📄 Interactive API Documentation (Swagger):")
    print("   👉 http://localhost:8000/docs")
    print("=" * 65)
    
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    start_server()
