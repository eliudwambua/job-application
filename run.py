import uvicorn
import os
import sys

# Ensure current workspace is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🚀 Starting ScholarPilot EU - Master's & Job Application Copilot")
    print("  📍 Local Web App: http://127.0.0.1:8000")
    print("  ⭐ Docs & API:   http://127.0.0.1:8000/docs")
    print("="*60 + "\n")
    
    init_db()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

