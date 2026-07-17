import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.ocr_service import init_ocr_service

# Mock OCR service to avoid loading heavy PaddleOCR during unit tests
class DummyOCRService:
    def recognize(self, file_path: Path):
        return [
            {
                "index": 1,
                "text": "Dòng văn bản giả lập",
                "confidence": 0.99,
                "box": [[0, 0], [10, 0], [10, 5], [0, 5]]
            }
        ], "Dòng văn bản giả lập", 0.99

# Apply dependency override
app.dependency_overrides[init_ocr_service] = lambda: DummyOCRService()

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "local-ocr-api"
    assert data["ocr_model"] == settings.OCR_MODEL_ID
    assert data["device"] == settings.OCR_DEVICE

def test_ocr_missing_file():
    response = client.post("/api/ocr/cccd/upload")
    # FastAPI returns 422 for missing parameters
    assert response.status_code == 422

def test_ocr_invalid_file_type():
    files = {"file": ("document.txt", b"plain text content", "text/plain")}
    response = client.post("/api/ocr/cccd/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "INVALID_FILE_TYPE"

def test_ocr_file_too_large():
    original_limit = settings.MAX_FILE_SIZE_MB
    # Set limit to 0 MB to trigger error immediately
    settings.MAX_FILE_SIZE_MB = 0
    try:
        # Send a tiny image file but with limit set to 0
        files = {"file": ("document.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...", "image/png")}
        response = client.post("/api/ocr/cccd/upload", files=files)
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "FILE_TOO_LARGE"
    finally:
        settings.MAX_FILE_SIZE_MB = original_limit


def test_split_cccd_flow_ocr_successful_mock():
    # 1. Test Upload CCCD API
    files = {"file": ("document.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82", "image/png")}
    response = client.post("/api/ocr/cccd/upload", files=files)
    assert response.status_code == 200
    upload_data = response.json()
    assert upload_data["success"] is True
    assert "file_token" in upload_data
    assert upload_data["file_name"] == "document.png"
    
    file_token = upload_data["file_token"]
    
    # 2. Test Recognize CCCD API
    recognize_response = client.post("/api/ocr/cccd/recognize", data={"file_token": file_token})
    assert recognize_response.status_code == 200
    recognize_data = recognize_response.json()
    assert recognize_data["success"] is True
    assert recognize_data["full_text"] == "Dòng văn bản giả lập"
    assert "cccd_info" in recognize_data

def test_split_a4_flow_ocr_successful_mock():
    # 1. Test Upload A4 API
    files = {"file": ("document.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82", "image/png")}
    response = client.post("/api/ocr/a4/upload", files=files)
    assert response.status_code == 200
    upload_data = response.json()
    assert upload_data["success"] is True
    assert "file_token" in upload_data
    
    file_token = upload_data["file_token"]
    
    # 2. Test Recognize A4 API
    recognize_response = client.post("/api/ocr/a4/recognize", data={"file_token": file_token})
    assert recognize_response.status_code == 200
    recognize_data = recognize_response.json()
    assert recognize_data["success"] is True
    assert recognize_data["full_text"] == "Dòng văn bản giả lập"
    assert "cccd_info" not in recognize_data


