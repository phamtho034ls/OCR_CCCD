import uvicorn
from dotenv import load_dotenv
import os

# Load variables from .env if present
load_dotenv()

if __name__ == "__main__":
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    
    print(f"Starting Local OCR API at http://{host}:{port}")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True
    )
