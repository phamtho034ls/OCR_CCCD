import os
import sys
from pathlib import Path

# Deactivate MKL-DNN / oneDNN and PIR globally to bypass graph execution compiler bugs
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['FLAGS_enable_pir_in_executor'] = '0'

# Inject NVIDIA python wheel DLL directories into Windows search paths
if sys.platform == "win32":
    for path in sys.path:
        p_path = Path(path)
        if p_path.name == "site-packages":
            nvidia_path = p_path / "nvidia"
            if nvidia_path.exists():
                for bin_dir in nvidia_path.glob("**/bin"):
                    if bin_dir.is_dir() and any(bin_dir.glob("*.dll")):
                        try:
                            os.add_dll_directory(str(bin_dir))
                            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ["PATH"]
                        except Exception:
                            pass

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import OCRException, ocr_exception_handler
from app.api.ocr_routes import router as ocr_router
from app.services.ocr_service import init_ocr_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up PP-OCRv6 model on startup to avoid delay on the first OCR request
    print(f"[{settings.APP_NAME}] Loading OCR model {settings.OCR_MODEL_ID} on {settings.OCR_DEVICE}...")
    try:
        init_ocr_service()
        print(f"[{settings.APP_NAME}] OCR model loaded successfully!")
    except Exception as e:
        print(f"[{settings.APP_NAME}] WARNING: Failed to load OCR model at startup: {e}")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Local OCR API using PaddleOCR PP-OCRv6",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register central error handler
app.add_exception_handler(OCRException, ocr_exception_handler)

# Include APIs
app.include_router(ocr_router, prefix="/api")
