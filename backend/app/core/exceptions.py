from fastapi import Request
from fastapi.responses import JSONResponse

class OCRException(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 400):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class FileValidationError(OCRException):
    def __init__(self, message: str, error_code: str = "INVALID_FILE"):
        super().__init__(error_code=error_code, message=message, status_code=400)

class ImageProcessingError(OCRException):
    def __init__(self, message: str):
        super().__init__(error_code="IMAGE_PROCESSING_FAILED", message=message, status_code=400)

class OCRInferenceError(OCRException):
    def __init__(self, message: str):
        super().__init__(error_code="OCR_INFERENCE_FAILED", message=message, status_code=500)

async def ocr_exception_handler(request: Request, exc: OCRException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message
        }
    )
