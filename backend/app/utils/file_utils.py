import os
import re
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import FileValidationError

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".pdf"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/bmp",
    "image/tiff",
    "image/webp",
    "application/pdf"
}

def validate_uploaded_file(file: UploadFile) -> None:
    # Check if empty
    if not file.filename:
        raise FileValidationError("Tên file không hợp lệ hoặc rỗng.", error_code="EMPTY_FILE")
    
    # Check extension
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Định dạng file {ext} không được hỗ trợ. Chỉ hỗ trợ JPG, JPEG, PNG, BMP, TIFF, WEBP, PDF.",
            error_code="INVALID_FILE_TYPE"
        )
    
    # Check MIME type
    if file.content_type and file.content_type.lower() not in ALLOWED_MIME_TYPES:
        raise FileValidationError(
            f"MIME type {file.content_type} không được hỗ trợ.",
            error_code="INVALID_FILE_TYPE"
        )

def validate_file_size(file_path: Path) -> None:
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise FileValidationError(
            f"Dung lượng file vượt quá giới hạn cho phép ({settings.MAX_FILE_SIZE_MB}MB).",
            error_code="FILE_TOO_LARGE"
        )

def sanitize_filename(filename: str) -> str:
    # Keep only alphanumeric, dot, underscore, dash
    filename = os.path.basename(filename)
    filename = re.sub(r"[^\w\-_.]", "_", filename)
    return filename
